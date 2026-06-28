"""Source registry. Add a line here when a new source module is built & proven."""
from sources import jooble, apify_linkedin, ats

REGISTRY = {
    "jooble": jooble.fetch,
    "apify_linkedin": apify_linkedin.fetch,
    "ats": ats.fetch,
    # "adzuna": adzuna.fetch,   # NOTE: Adzuna has NO Ireland endpoint — do not use for IE
}
