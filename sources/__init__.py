"""Source registry. Add a line here when a new source module is built & proven."""
from sources import adzuna

REGISTRY = {
    "adzuna": adzuna.fetch,
    # "greenhouse": greenhouse.fetch,   # added when ATS layer is built
    # "apify_linkedin": apify_linkedin.fetch,
}
