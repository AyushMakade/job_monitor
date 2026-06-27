"""Central config. Turning a source on = add its name here once its module exists."""

# Which sources run. Only names with a built module in sources/ may appear here.
# Roadmap (added one proven layer at a time): greenhouse, lever, ashby,
# apify_linkedin, apify_indeed, and (off-by-default toggles) jooble, reed.
ENABLED_SOURCES = ["jooble"]   # backbone. (Adzuna removed: it has no Ireland API.)

# ---- freshness ----
LOOKBACK_HOURS = 48          # steady-state window: each daily run looks back this many hours
                             # (wider than 24h so a delayed/skipped run never leaves a gap;
                             #  de-duplication makes the overlap free)


# ---- Jooble (aggregator backbone — covers Ireland) ----
JOOBLE_LOCATION = "Ireland"
JOOBLE_RESULTS_PER_PAGE = 50
JOOBLE_MAX_PAGES = 2              # pages per daily run (sips the 500-request free budget)
JOOBLE_FIRST_RUN_MAX_PAGES = 10  # one-time deeper pull to seed a fuller baseline

# ---- Adzuna (UNUSED: no Ireland endpoint; kept for reference) ----
ADZUNA_COUNTRY = "ie"
ADZUNA_RESULTS_PER_PAGE = 50
ADZUNA_MAX_PAGES = 5

SEARCH_TERMS = [
    "data analyst", "data scientist", "data engineer", "analytics engineer",
    "machine learning engineer", "ai engineer", "business intelligence",
]

# ---- ATS company boards (filled when the ATS layer is built & approved) ----
GREENHOUSE_COMPANIES = []    # board tokens, e.g. "stripe"
LEVER_COMPANIES = []
ASHBY_COMPANIES = []

# ---- richest-record-wins priority for cross-source de-duplication ----
SOURCE_RICHNESS = {
    "greenhouse": 4, "lever": 4, "ashby": 4, "workable": 4,
    "apify_linkedin": 3, "apify_indeed": 2,
    "adzuna": 1, "jooble": 1, "reed": 1,
}

# ---- output files (committed by the workflow) ----
OUT_CSV    = "fresh_jobs.csv"
DIGEST_MD  = "digest.md"
STATE_FILE = "state.json"
