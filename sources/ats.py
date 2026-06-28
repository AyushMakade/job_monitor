"""ATS depth layer: pulls first-party job postings straight from companies'
public Greenhouse / Lever / Ashby boards (full descriptions, working apply links).

You give COMPANY NAMES (config.ATS_COMPANIES). For each, the module tries
name-based candidate tokens against all three ATS at runtime and keeps whichever
returns a live board. Resolved company->(ats, token) pairs are cached in
ats_tokens.json so we don't re-detect every run. Unresolved names are retried
(and logged) each run so you can see what didn't stick.

Network note: token resolution only works where there's internet (GitHub
Actions), not in a sandbox. First live run does the detection and writes cache."""
import json, os, re, time, requests
from datetime import datetime, timezone
import config
from sources.base import record, dedup_key, iso

CACHE = "ats_tokens.json"
UA = {"User-Agent": "ie-job-monitor/1.0"}

IE = ["ireland", "dublin", "cork", "galway", "limerick", "waterford", "letterkenny",
      "maynooth", "sligo", "athlone", "kilkenny", "drogheda", "remote - ireland",
      "remote, ireland", "ie", "eu remote", "emea"]
DATA_KW = ["data", "analyst", "analytics", "intelligence", "scientist", "ml ",
           "machine learning", " ai ", "ai/", "nlp", "etl", "bi ", "dbt", "looker"]

def _is_ie(loc):
    l = (loc or "").lower()
    return any(k in l for k in IE)

def _is_data(title):
    t = (title or "").lower()
    return any(k in t for k in DATA_KW)

def _ts(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

# ---- per-ATS fetchers: return list of normalized dicts, or None if board not found ----
def _greenhouse(token):
    u = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    r = requests.get(u, headers=UA, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        out.append({"title": j.get("title", ""),
                    "location": (j.get("location") or {}).get("name", ""),
                    "desc": re.sub("<[^>]+>", " ", j.get("content", "") or "")[:2000],
                    "url": j.get("absolute_url", ""),
                    "ts": _ts(j.get("updated_at", "")), "sid": str(j.get("id", ""))})
    return out

def _lever(token):
    u = f"https://api.lever.co/v0/postings/{token}?mode=json"
    r = requests.get(u, headers=UA, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    out = []
    for j in r.json():
        cat = j.get("categories") or {}
        out.append({"title": j.get("text", ""),
                    "location": cat.get("location", ""),
                    "desc": (j.get("descriptionPlain") or "")[:2000],
                    "url": j.get("hostedUrl", ""),
                    "ts": (datetime.fromtimestamp(j["createdAt"]/1000, timezone.utc)
                           if j.get("createdAt") else None),
                    "sid": str(j.get("id", ""))})
    return out

def _ashby(token):
    u = f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"
    r = requests.get(u, headers=UA, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    if not data.get("jobs") and "apiVersion" not in data:
        return None
    out = []
    for j in data.get("jobs", []):
        out.append({"title": j.get("title", ""),
                    "location": j.get("location", "") or "",
                    "desc": (j.get("descriptionPlain") or "")[:2000],
                    "url": j.get("jobUrl", "") or j.get("applyUrl", ""),
                    "ts": _ts(j.get("publishedAt", "")), "sid": str(j.get("title", ""))})
    return out

ATS_FNS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}

def _candidate_tokens(name):
    base = name.lower().strip()
    base = re.sub(r"\b(inc|ltd|llc|plc|group|technologies|labs|the)\b", "", base)
    base = base.strip()
    nospace = re.sub(r"[^a-z0-9]", "", base)
    hyphen = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return list(dict.fromkeys([nospace, hyphen, base.replace(" ", "")]))

def _resolve(name, cache):
    if name in cache:                      # already known (or known-unresolved)
        return cache[name]
    for token in _candidate_tokens(name):
        for ats, fn in ATS_FNS.items():
            try:
                jobs = fn(token)
            except requests.RequestException:
                jobs = None
            time.sleep(0.3)
            if jobs is not None:           # board exists
                cache[name] = {"ats": ats, "token": token}
                return cache[name]
    cache[name] = None                     # mark unresolved (retry next run via miss-log)
    return None

def fetch(cutoff, now):
    companies = config.ATS_COMPANIES
    if not companies:
        return []
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            cache = {}

    first_run = cutoff is None
    out, resolved, unresolved = [], [], []
    for name in companies:
        info = _resolve(name, cache)
        if not info:
            unresolved.append(name)
            continue
        fn = ATS_FNS[info["ats"]]
        try:
            jobs = fn(info["token"]) or []
        except requests.RequestException as e:
            print(f"  ! ats {name} ({info['ats']}:{info['token']}): {e}")
            continue
        resolved.append(f"{name}->{info['ats']}:{info['token']}({len(jobs)})")
        for j in jobs:
            if not _is_ie(j["location"]) or not _is_data(j["title"]):
                continue
            ts = j["ts"]
            if not first_run and (ts is None or ts <= cutoff):
                continue
            out.append(record(
                source=info["ats"], source_id=j["sid"],
                dedup_key=dedup_key(name, j["title"]),
                created_utc=iso(ts) if ts else "",
                age_hours=round((now - ts).total_seconds()/3600, 1) if ts else "",
                title=j["title"].strip(), company=name, location=j["location"],
                is_dublin="dublin" in j["location"].lower(),
                description=j["desc"].replace("\n", " ").strip(),
                url=j["url"], query_term=f"ats:{info['ats']}", fetched_at_utc=iso(now)))

    try:
        json.dump(cache, open(CACHE, "w"), indent=2)
    except Exception:
        pass
    print(f"  ats: resolved {len([v for v in cache.values() if v])}/{len(companies)} "
          f"companies, kept {len(out)} IE data role(s)")
    if unresolved:
        print(f"  ats: could not resolve {len(unresolved)}: {', '.join(unresolved[:15])}")
    return out
