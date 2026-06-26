"""Rules-based tagging: family / accessibility / stack relevance / visa flag.
Approximate (~85%). Treat as a triage aid, not gospel; tune the keyword lists
when something misclassifies."""
import re

OFF_TARGET = ["payroll", "it support", "service desk", "help desk", "account executive",
              "sales executive", "health & safety", "health and safety", "recruiter",
              "talent acquisition", "annotation specialist", "transport model"]

FAMILY_RULES = [   # checked in order; first match wins
    ("ML/AI Eng",         ["machine learning", "ml engineer", "mlops", "ai engineer",
                            "applied scientist", "nlp", "computer vision", "llm",
                            "genai", "generative ai", "deep learning", "ai/ml"]),
    ("Research",          ["research scientist", "research engineer"]),
    ("Data Science",      ["data scientist", "data science", "statistician", "quantitative analyst"]),
    ("Analytics/Data Eng",["data engineer", "analytics engineer", "etl developer", "bi developer",
                            "data architect", "data modeller", "data modeler", "dbt",
                            "database engineer", "platform engineer", "data platform"]),
    ("Analyst",           ["data analyst", "bi analyst", "business intelligence", "insights analyst",
                            "reporting analyst", "product analyst", "analytics", "data steward"]),
]

ADJACENT = ["dba", "database administrator", "oracle developer", "pl/sql", "pl-sql",
            "neo4j", "systems analyst", "business analyst", "master data", "sap "]

def family(title, desc):
    t = f"{title} {desc}".lower()
    if any(k in t for k in OFF_TARGET):
        return "Off-target"
    for fam, kws in FAMILY_RULES:
        if any(k in t for k in kws):
            return fam
    return "Unclassified"

def stack_relevance(fam, title, desc):
    if fam == "Off-target":
        return "Out-of-scope"
    if fam == "Unclassified":
        return "Review"
    t = f"{title} {desc}".lower()
    if any(k in t for k in ADJACENT):
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
    if any(w in title.lower() for w in ["senior", "lead", "principal", "staff",
                                        "manager", "director", " vp", "head of"]):
        return "Senior / Lead+"
    if any(w in title.lower() for w in ["junior", "associate", "entry"]):
        return "Near (~1-3 yr)"
    return "Unknown"

def visa_flag(desc):
    t = (desc or "").lower()
    if "no sponsorship" in t or "not provide sponsorship" in t or "without sponsorship" in t:
        return "no-sponsorship"
    if "stamp 4" in t or ("eu passport" in t) or "eea citizen" in t:
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
