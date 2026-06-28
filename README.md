# Ireland data-jobs daily monitor

An automated daily monitor for fresh data / analytics / ML-AI roles in Ireland.
One GitHub Action runs once a day, pulls newly-posted roles from several sources,
tags and de-duplicates them, and commits two files:

- **`fresh_jobs.csv`** — the cumulative, de-duplicated, tagged database (raw, filterable)
- **`digest.md`** — that day's new **Core / entry-near** roles, ready to skim each morning

## Sources (layered by strength)

| Source | Role | Notes |
| ------ | ---- | ----- |
| **Jooble** | broad backbone | Free REST API, covers Ireland. Aggregator breadth; snippet descriptions, no city detail. |
| **LinkedIn (via Apify)** | fresh + diverse | Cookieless actor `chronometrica/linkedin-jobs-scraper` — **no login, no account risk**. Full descriptions, city-level location, posting dates. Pay-per-result (~cents/day). |
| **ATS direct** | first-party depth | Pulls straight from companies' public Greenhouse / Lever / Ashby boards. Auto-detects which ATS each company uses. Full descriptions, working apply links. No key needed. |

> Adzuna was the original backbone but has **no Ireland endpoint**, so it was
> replaced by Jooble. Its module is kept (disabled) for reference only.

## How a run works

1. **First run** (no `state.json`) → takes *everything* available, to seed a baseline.
2. **Every run after** → looks back `LOOKBACK_HOURS` (default **48h**); de-duplication
   means a delayed/skipped run never gaps and re-runs never double-count.
3. Each role is tagged: **family** (Analyst / Data Science / Analytics-Data Eng /
   ML-AI Eng / Research / Off-target), **stack relevance** (Core / Adjacent / Review /
   Out-of-scope), **accessibility** (Entry / Near / Mid / Senior), and a **visa flag**.
4. The same job seen from multiple sources collapses to one row — **richest source wins**
   (ATS > LinkedIn > Jooble), so you keep the fullest description available.

## Setup

1. **Secrets** (repo → Settings → Secrets and variables → Actions):
   - `JOOBLE_API_KEY` — free key from https://jooble.org/api/about
   - `APIFY_TOKEN` — from Apify Console → Integrations
   - (ATS needs no key — the boards are public.)
2. Push. The workflow runs daily at **11:00 Irish time**; trigger it any time from
   the **Actions** tab → **Run workflow**.
3. To rebuild a fresh baseline, delete `state.json` and run once.

## Project layout

```
config.py              what's on, search terms, ATS company list, freshness window, dedup priority
pipeline.py            orchestrates a run: fetch -> tag -> dedupe -> CSV + digest -> state
tagging.py             rules for family / accessibility / stack-relevance / visa
store.py               CSV history, de-dup, digest writer, run state
sources/
  base.py              the shared normalized record shape + dedup key
  jooble.py            Jooble aggregator (backbone)
  apify_linkedin.py    LinkedIn via Apify cookieless actor
  ats.py               Greenhouse / Lever / Ashby auto-detecting connector
  __init__.py          source registry
.github/workflows/
  daily-jobs.yml       the daily schedule + commit step
```

**Adding a source** = add `sources/<name>.py` (exposing `fetch(cutoff, now)`), register
it in `sources/__init__.py`, and add its name to `ENABLED_SOURCES`. Nothing else changes.

**Adding an ATS company** = add its name to `ATS_COMPANIES` in `config.py`. The auto-detector
resolves which platform it's on at the next run (cached in `ats_tokens.json`); names it
can't resolve are listed in the run log.

## Cost

- **Jooble** — free tier (500 requests; the monitor uses ~2/day).
- **Apify** — pay-per-result, ~$0.09/day, inside Apify's free $5/month credit.
- **ATS** — free (public endpoints).

## Tuning

- Tagging is rule-based (~85% accurate). Misclassifications are fixed by editing the
  keyword lists in `tagging.py`. "Unclassified" roles still appear in the digest's
  review section so nothing is hidden.
- Cost / volume knobs live in `config.py` (`APIFY_MAX_ITEMS`, `JOOBLE_MAX_PAGES`, etc.).
