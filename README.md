# Ireland data-jobs daily monitor

One GitHub Action runs once a day, pulls freshly-posted Irish data/AI roles from
each enabled source, tags + de-duplicates them, and commits:
- `fresh_jobs.csv` — cumulative, de-duplicated, tagged feed
- `digest.md` — that day's new Core / entry-near roles, ready to skim

## Setup
1. Free Adzuna key at https://developer.adzuna.com/ → gives app_id + app_key.
2. Repo → Settings → Secrets and variables → Actions → add `ADZUNA_APP_ID`,
   `ADZUNA_APP_KEY`. (Keys live ONLY here, never in the code or commits.)
3. Push, then Actions tab → "Run workflow" to test. It self-runs daily after.

## Architecture
- `config.py` — what's on, search terms, ATS company lists, dedup priority.
- `sources/` — one module per source, each `fetch(cutoff, now) -> [records]`.
- `tagging.py` — rules for family / accessibility / stack-relevance / visa.
- `store.py` — CSV history, de-dup, digest, state.
- `pipeline.py` — orchestrates the run.

Add a source = add `sources/<name>.py`, register it in `sources/__init__.py`,
add its name to `ENABLED_SOURCES`. Nothing else changes.
