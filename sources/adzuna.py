"""Adzuna source module: official API, broad Ireland coverage, snippet descriptions."""
import os, time, requests
from datetime import datetime, timezone
import config
from sources.base import record, dedup_key, iso

API = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

def _created(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def fetch(cutoff, now):
    app_id  = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise RuntimeError("ADZUNA_APP_ID / ADZUNA_APP_KEY not set")

    out = []
    for term in config.SEARCH_TERMS:
        for page in range(1, config.ADZUNA_MAX_PAGES + 1):
            params = {
                "app_id": app_id, "app_key": app_key,
                "results_per_page": config.ADZUNA_RESULTS_PER_PAGE,
                "what": term, "sort_by": "date", "max_days_old": 1,
                "content-type": "application/json",
            }
            url = API.format(country=config.ADZUNA_COUNTRY, page=page)
            try:
                r = requests.get(url, params=params,
                                 headers={"User-Agent": "ie-job-monitor/1.0"}, timeout=30)
                r.raise_for_status()
            except requests.RequestException as e:
                print(f"  ! adzuna {term} p{page}: {e}")
                break
            results = r.json().get("results", [])
            if not results:
                break
            hit_old = False
            for ad in results:
                created = _created(ad["created"])
                if created <= cutoff:
                    hit_old = True
                    continue
                loc = (ad.get("location") or {}).get("display_name", "")
                out.append(record(
                    source="adzuna", source_id=str(ad["id"]),
                    dedup_key=dedup_key((ad.get("company") or {}).get("display_name"),
                                        ad.get("title"), loc),
                    created_utc=ad["created"],
                    age_hours=round((now - created).total_seconds() / 3600, 1),
                    title=(ad.get("title") or "").replace("\n", " ").strip(),
                    company=(ad.get("company") or {}).get("display_name", ""),
                    location=loc, is_dublin="dublin" in loc.lower(),
                    salary_min=ad.get("salary_min", ""), salary_max=ad.get("salary_max", ""),
                    currency="EUR", contract_type=ad.get("contract_type", ""),
                    description=(ad.get("description") or "").replace("\n", " ").strip(),
                    url=ad.get("redirect_url", ""), query_term=term,
                    fetched_at_utc=iso(now),
                ))
            time.sleep(1.2)
            if hit_old:
                break
    return out
