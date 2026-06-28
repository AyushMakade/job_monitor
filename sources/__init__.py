"""Source registry. Add a line here when a new source module is built & proven."""
from sources import jooble, apify_linkedin

REGISTRY = {
    "jooble": jooble.fetch,
    "apify_linkedin": apify_linkedin.fetch,
    # "adzuna": adzuna.fetch,   # NOTE: Adzuna has NO Ireland endpoint — do not use for IE
    # "greenhouse": greenhouse.fetch,   # ATS layer (next)
}
