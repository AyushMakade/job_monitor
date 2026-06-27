"""Source registry. Add a line here when a new source module is built & proven."""
from sources import jooble

REGISTRY = {
    "jooble": jooble.fetch,
    # "adzuna": adzuna.fetch,   # NOTE: Adzuna has NO Ireland endpoint — do not use for IE
    # "greenhouse": greenhouse.fetch,   # added when ATS layer is built
    # "apify_linkedin": apify_linkedin.fetch,
}
