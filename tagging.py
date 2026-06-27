"""Rules-based tagging: family / accessibility / stack relevance / visa flag.
Title-first (description only disambiguates a title that's already data-ish), so
incidental keyword mentions in unrelated job descriptions no longer mis-tag."""
import re

# Titles that are clearly NOT data roles -> Off-target, regardless of description.
_HARD_OFF = ["payroll", "it support", "service desk", "help desk", "account executive",
             "sales executive", "recruiter", "talent acquisition", "health & safety",
             "health and safety", "scrum master", "project manager", "program manager",
             "engineering manager", "sdet", " in test", "qa engineer", "test engineer",
             "site reliability", "devops", "network engineer", "security engineer",
             "systems administrator", "support engineer", "growth hacker", "salesforce admin"]

_DATA_WORDS = ["data", "analyst", "analytic", "intelligence", "scientist",
               "machine learning", " ml ", " ml/", "ai ", "ai/", "nlp", "etl", "dbt"]

def _is_off_target_title(t):
    if any(h in t for h in _HARD_OFF):
        return True
    # "platform engineer/engineering" or generic "software engineer/development" with
    # NO data qualifier = infrastructure / generic SWE, not a data role.
    if ("platform engineer" in t or "platform engineering" in t
            or "software engineer" in t or "software development engineer" in t
            or "software engineering" in t):
        if not any(d in t for d in ["data", "analytic", "machine learning", "ml", "ai"]):
            return True
    return False

# Family by TITLE keyword. Order matters; first match wins.
_FAMILY_TITLE = [
    ("Analytics/Data Eng", ["data engineer", "analytics engineer", "etl developer",
                            "bi developer", "data architect", "data modeller", "data modeler",
                            "data platform", "business intelligence developer", "dbt"]),
    ("Data Science",       ["data scientist", "data science", "statistician",
                            "quantitative analyst"]),
    ("ML/AI Eng",          ["machine learning", "ml engineer", "mlops", "ai engineer",
                            "applied scientist", "nlp engineer", "computer vision",
                            "llm", "generative ai", "deep learning", "ai/ml"]),
    ("Research",           ["research scientist", "research engineer"]),
    ("Analyst",            ["data analyst", "bi analyst", "business intelligence",
                            "insights analyst", "reporting analyst", "product analyst",
                            "data steward"]),
]

ADJACENT = ["dba", "database administrator", "database engineer", "oracle developer",
            "pl/sql", "pl-sql", "neo4j", "systems analyst", "business analyst",
            "master data", "sap "]

def family(title, desc):
    t = title.lower()
    if _is_off_target_title(t):
        return "Off-target"
    for fam, kws in _FAMILY_TITLE:                 # strong: title match
        if any(k in t for k in kws):
            return fam
    if any(w in t for w in _DATA_WORDS):           # weak: title is data-ish, check desc
        full = f"{title} {desc}".lower()
        for fam, kws in _FAMILY_TITLE:
            if any(k in full for k in kws):
                return fam
    return "Unclassified"

def stack_relevance(fam, title, desc):
    if fam == "Off-target":
        return "Out-of-scope"
    if fam == "Unclassified":
        return "Review"
    if any(k in title.lower() for k in ADJACENT):
        return "Adjacent"
    return "Core"

_YEARS = re.compile(r"(\d+)\s*(?:\+|to|-|–)?\s*(\d+)?\s*(?:\+)?\s*years?", re.I)

def accessibility(title, desc):
    t = f"{title} {desc}".lower()
    if any(w in t for w in ["intern", "graduate", "trainee", "placement", "apprentice"]):
        return "Entry / graduate"
    yrs = None
    for m in _YEARS.finditer(t):
        lo = int(m.group(1))
        yrs = lo if yrs is None else min(yrs, lo)
    if yrs is not None:
        if yrs >= 5:  return "Senior / Lead+"
        if yrs >= 3:  return "Mid (3-5 yr)"
        if yrs >= 1:  return "Near (~1-3 yr)"
        return "Entry / graduate"
    tl = title.lower()
    if any(w in tl for w in ["senior", "lead", "principal", "staff", "manager",
                             "director", " vp", "head of", " ii", " iii"]):
        return "Senior / Lead+"
    if any(w in tl for w in ["junior", "associate", "entry", " i "]):
        return "Near (~1-3 yr)"
    return "Unknown"

def visa_flag(desc):
    t = (desc or "").lower()
    if "no sponsorship" in t or "not provide sponsorship" in t or "without sponsorship" in t:
        return "no-sponsorship"
    if "stamp 4" in t or "eu passport" in t or "eea citizen" in t:
        return "may require EU/Stamp4 - check"
    if "internal" in t and "only" in t:
        return "possibly internal-only"
    return ""

def tag(rec):
    fam = family(rec["title"], rec["description"])
    rec["family"] = fam
    rec["stack_relevance"] = stack_relevance(fam, rec["title"], rec["description"])
    rec["accessibility"] = accessibility(rec["title"], rec["description"])
    rec["visa_flag"] = visa_flag(rec["description"])
    return rec
