"""Central config. Turning a source on = add its name here once its module exists."""

# Which sources run. Only names with a built module in sources/ may appear here.
# Roadmap (added one proven layer at a time): greenhouse, lever, ashby,
# apify_linkedin, apify_indeed, and (off-by-default toggles) jooble, reed.
ENABLED_SOURCES = ["jooble", "apify_linkedin"]   # backbone + LinkedIn (Adzuna has no Ireland API)

# ---- freshness ----
LOOKBACK_HOURS = 48          # steady-state window: each daily run looks back this many hours
                             # (wider than 24h so a delayed/skipped run never leaves a gap;
                             #  de-duplication makes the overlap free)



# ---- Apify LinkedIn (cookieless actor — full descriptions, real city locations) ----
# Cost ~$3/1,000 saved listings. past24Hours keeps daily volume (and cost) low.
# Watch the Apify Console "Usage" tab the first week; trim terms/caps if it runs hot.
APIFY_LINKEDIN_ACTOR = "nexgendata/linkedin-jobs-scraper"
APIFY_LOCATION = "Ireland"
APIFY_SEARCH_TERMS = ["data analyst", "data engineer", "data scientist",
                      "machine learning engineer", "business intelligence"]
APIFY_MAX_ITEMS = 25             # per-term cap, daily
APIFY_FIRST_RUN_MAX = 50         # per-term cap, one-time first run
APIFY_DATE_DAILY = "past24Hours"      # actor-specific value; tune after calibration
APIFY_DATE_FIRST_RUN = "pastWeek"

def apify_input(term, location, date_filter, max_items):
    """The actor's input payload. If the CALIBRATION log shows different keys,
    edit ONLY this function — nothing else in the system changes."""
    return {
        "keyword": term,
        "location": location,
        "datePosted": date_filter,
        "rows": max_items,
        "saveOnlyUniqueItems": True,
    }

# ---- Jooble (aggregator backbone — covers Ireland) ----
JOOBLE_LOCATION = "Ireland"
JOOBLE_RESULTS_PER_PAGE = 50
JOOBLE_MAX_PAGES = 2              # pages per daily run (sips the 500-request free budget)
JOOBLE_FIRST_RUN_MAX_PAGES = 10  # one-time deeper pull to seed a fuller baseline

# ---- Apify / LinkedIn (cookieless actor; no account risk) ----
APIFY_LOCATION = "Ireland"
APIFY_POSTED_WITHIN = "7d"        # actor freshness window; our 48h filter + dedup narrow it
APIFY_MAX_ITEMS = 60             # daily saved-row cap (~$0.09/run at $1.50/1k)
APIFY_FIRST_RUN_MAX = 200        # one-time baseline cap (~$0.30)
APIFY_MAX_PAGES = 3
APIFY_MAX_WAIT_SEC = 300         # poll up to 5 min for the run to finish

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
