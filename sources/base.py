"""The single normalized record shape every source must return."""
import re
from datetime import timezone

FIELDS = [
    "source", "source_id", "dedup_key", "created_utc", "age_hours",
    "title", "company", "location", "is_dublin",
    "salary_min", "salary_max", "currency", "contract_type",
    "family", "stack_relevance", "accessibility", "visa_flag",
    "description", "url", "query_term", "fetched_at_utc",
]

def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def dedup_key(company, title, location):
    """Same job across sources collapses to one key (company|title|city)."""
    city = (location or "").split(",")[0]
    return f"{_norm(company)}|{_norm(title)}|{_norm(city)}"

def record(**kw):
    """Build a record with every field present (missing -> '')."""
    return {f: kw.get(f, "") for f in FIELDS}
