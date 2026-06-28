"""LinkedIn jobs via Apify cookieless actor (chronometrica/linkedin-jobs-scraper).
No LinkedIn login/cookie -> no risk to your account. Returns full descriptions,
city-level location, and an ISO postedAt timestamp.

Async pattern (robust for unattended runs): start run -> poll -> fetch dataset.
cutoff=None -> first run: deeper pull, keep all. else -> keep postedAt > cutoff."""
import os, time, requests
from datetime import datetime, timezone
import config
from sources.base import record, dedup_key, iso

ACTOR = "chronometrica~linkedin-jobs-scraper"
BASE = "https://api.apify.com/v2"

def _posted(s):
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

def fetch(cutoff, now):
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise RuntimeError("APIFY_TOKEN not set")
    first_run = cutoff is None

    payload = {
        "searchTerm": "\n".join(config.SEARCH_TERMS),
        "location": config.APIFY_LOCATION,
        "postedWithin": config.APIFY_POSTED_WITHIN,
        "sortBy": "date",
        "maxItems": config.APIFY_FIRST_RUN_MAX if first_run else config.APIFY_MAX_ITEMS,
        "maxPagesPerSearch": config.APIFY_MAX_PAGES,
        "balanceKeywordCoverage": True,
        "saveOnlyUniqueItems": True,
        "fetchJobDetails": True,
        "jobType": "any", "workplaceType": "any", "experienceLevel": "any",
    }

    # 1) start the run
    r = requests.post(f"{BASE}/acts/{ACTOR}/runs?token={token}", json=payload, timeout=60)
    if r.status_code in (401, 403):
        raise RuntimeError(f"Apify auth failed (HTTP {r.status_code}) — check APIFY_TOKEN.")
    r.raise_for_status()
    run_id = r.json()["data"]["id"]

    # 2) poll until the run finishes (or we hit our wait budget)
    status, deadline = None, time.time() + config.APIFY_MAX_WAIT_SEC
    while time.time() < deadline:
        time.sleep(10)
        s = requests.get(f"{BASE}/actor-runs/{run_id}?token={token}", timeout=30)
        s.raise_for_status()
        status = s.json()["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
    if status != "SUCCEEDED":
        print(f"  ! apify run status={status} (fetching whatever was saved)")

    # 3) pull dataset items
    ds = requests.get(f"{BASE}/actor-runs/{run_id}/dataset/items?token={token}&clean=true",
                      timeout=120)
    ds.raise_for_status()
    items = ds.json()

    out = []
    for j in items:
        posted = _posted(j.get("postedAt", ""))
        if not first_run and (posted is None or posted <= cutoff):
            continue
        loc = j.get("locationRaw") or j.get("searchLocation") or ""
        city = j.get("locationCity") or ""
        desc = (j.get("descriptionText") or j.get("descriptionSnippet") or "")
        out.append(record(
            source="apify_linkedin", source_id=str(j.get("jobId", "")),
            dedup_key=dedup_key(j.get("companyName"), j.get("title")),
            created_utc=iso(posted) if posted else "",
            age_hours=round((now - posted).total_seconds() / 3600, 1) if posted else "",
            title=(j.get("title") or "").strip(),
            company=(j.get("companyName") or "").strip(),
            location=(city + (", " if city and loc else "") + loc) if city else loc,
            is_dublin="dublin" in f"{city} {loc}".lower(),
            salary_min=j.get("salaryMin", ""), salary_max=j.get("salaryMax", ""),
            currency=j.get("salaryCurrency", ""),
            contract_type=j.get("employmentType", ""),
            description=desc.replace("\n", " ").strip()[:2000],
            url=j.get("jobUrl", ""), query_term=j.get("query", "linkedin"),
            fetched_at_utc=iso(now),
        ))
    tag = "FIRST RUN" if first_run else f"window {config.LOOKBACK_HOURS}h"
    print(f"  apify_linkedin [{tag}]: {len(items)} scraped, kept {len(out)}")
    return out
