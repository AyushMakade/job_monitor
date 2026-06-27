"""Jooble source module: aggregator that DOES cover Ireland (unlike Adzuna).
Free REST key from https://jooble.org/api/about . Official endpoint:
POST https://jooble.org/api/{key}  with JSON body {keywords, location, page,...}.

Efficiency: all target terms are sent as one comma-joined (OR) query per page,
so a daily run costs only a handful of API calls — kind to the free tier.
Fails loudly on a bad key; prints raw vs in-window counts."""
import os, time, requests
from datetime import datetime, timezone
import config
from sources.base import record, dedup_key, iso

API = "https://jooble.org/api/{key}"

def _updated(s):
    # Jooble: "2026-06-26T12:55:35.3870000" (UTC, no tz) -> first 19 chars
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

def fetch(cutoff, now):
    key = os.environ.get("JOOBLE_API_KEY")
    if not key:
        raise RuntimeError("JOOBLE_API_KEY not set")

    keywords = ", ".join(config.SEARCH_TERMS)   # comma = OR in Jooble
    out, raw_total = [], 0
    for page in range(1, config.JOOBLE_MAX_PAGES + 1):
        body = {"keywords": keywords, "location": config.JOOBLE_LOCATION,
                "page": str(page), "ResultOnPage": config.JOOBLE_RESULTS_PER_PAGE}
        try:
            r = requests.post(API.format(key=key), json=body,
                              headers={"User-Agent": "ie-job-monitor/1.0"}, timeout=30)
        except requests.RequestException as e:
            print(f"  ! jooble network error p{page}: {e}")
            break
        if r.status_code == 403:
            raise RuntimeError("Jooble auth failed (403) — check JOOBLE_API_KEY is correct.")
        if r.status_code != 200:
            print(f"  ! jooble HTTP {r.status_code} p{page} — stopping")
            break

        jobs = r.json().get("jobs", [])
        raw_total += len(jobs)
        if not jobs:
            break
        for j in jobs:
            upd = _updated(j.get("updated", ""))
            if upd is None or upd <= cutoff:
                continue
            loc = j.get("location", "") or ""
            title = (j.get("title") or "").replace("\n", " ").strip()
            co = j.get("company", "") or ""
            out.append(record(
                source="jooble", source_id=str(j.get("id", "")),
                dedup_key=dedup_key(co, title, loc), created_utc=iso(upd),
                age_hours=round((now - upd).total_seconds() / 3600, 1),
                title=title, company=co, location=loc,
                is_dublin="dublin" in loc.lower(),
                contract_type=j.get("type", ""),
                description=(j.get("snippet") or "").replace("\n", " ").strip(),
                url=j.get("link", ""), query_term="jooble", fetched_at_utc=iso(now),
            ))
        time.sleep(1.0)
    print(f"  jooble: API returned {raw_total} ad(s) total, {len(out)} inside the freshness window")
    return out
