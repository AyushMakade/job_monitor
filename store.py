"""CSV history, state, de-duplication, and digest writing."""
import csv, json, os
from datetime import datetime, timezone
import config
from sources.base import FIELDS, iso

def _parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def load_state():
    try:
        with open(config.STATE_FILE) as f:
            return _parse(json.load(f)["last_run_utc"])
    except Exception:
        return None

def save_state(now):
    with open(config.STATE_FILE, "w") as f:
        json.dump({"last_run_utc": iso(now)}, f)

def load_history_keys():
    keys = set()
    if os.path.exists(config.OUT_CSV):
        with open(config.OUT_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add(row.get("dedup_key", ""))
    return keys

def dedupe_within_run(records):
    """Collapse same job seen from multiple sources -> keep richest, then newest."""
    best = {}
    for r in records:
        k = r["dedup_key"]
        rich = config.SOURCE_RICHNESS.get(r["source"], 0)
        cur = best.get(k)
        if cur is None:
            best[k] = (rich, r["created_utc"], r)
        else:
            if (rich, r["created_utc"]) > (cur[0], cur[1]):
                best[k] = (rich, r["created_utc"], r)
    return [v[2] for v in best.values()]

def append(records):
    new = not os.path.exists(config.OUT_CSV)
    with open(config.OUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for r in sorted(records, key=lambda x: x["created_utc"], reverse=True):
            w.writerow({k: r.get(k, "") for k in FIELDS})

def write_digest(records, now):
    core_near = [r for r in records if r["stack_relevance"] == "Core"
                 and r["accessibility"] in ("Entry / graduate", "Near (~1-3 yr)")]
    other_core = [r for r in records if r["stack_relevance"] == "Core" and r not in core_near]
    review = [r for r in records if r["stack_relevance"] == "Review"]
    def line(r):
        sal = f" | EUR {r['salary_min']}-{r['salary_max']}" if r["salary_min"] else ""
        visa = f" | ⚠ {r['visa_flag']}" if r["visa_flag"] else ""
        return (f"- **{r['title']}** — {r['company']} — {r['location']} "
                f"({r['family']} / {r['accessibility']}, {r['age_hours']}h old{sal}{visa})\n"
                f"  {r['url']}")
    off = [r for r in records if r["stack_relevance"] == "Out-of-scope"]
    summary = (f"{len(records)} new this run — "
               f"{len(core_near)+len(other_core)} Core, {len(review)} to review, "
               f"{len(off)} off-target (filtered out).")
    if records and not (core_near or other_core or review):
        summary += "  Nothing relevant for you this run."
    lines = [f"# Fresh data roles — {now.strftime('%Y-%m-%d %H:%M UTC')}",
             f"\n_{summary}_\n"]
    lines.append(f"\n## ⭐ Core, entry/near ({len(core_near)})\n")
    lines += [line(r) for r in sorted(core_near, key=lambda x: x["created_utc"], reverse=True)] or ["_none_"]
    lines.append(f"\n## Other Core roles ({len(other_core)})\n")
    lines += [line(r) for r in sorted(other_core, key=lambda x: x["created_utc"], reverse=True)] or ["_none_"]
    lines.append(f"\n## Unclassified — quick review ({len(review)})\n")
    lines += [line(r) for r in sorted(review, key=lambda x: x["created_utc"], reverse=True)] or ["_none_"]
    with open(config.DIGEST_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
