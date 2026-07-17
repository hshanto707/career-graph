"""Synthetic data generator: Business Analytics, Finance, BI, Accounting domain chunk.

Produces exactly 1000 synthetic (fictional) job-posting rows matching the
schema used by `backend/data/kaggle_jobs.csv`:

    title,company,location,type,skills_required,salary_min,salary_max,category

Companies are all invented word-combinations (never real organizations).
Run directly:

    python3 backend/data/generators/generate_business-finance.py

Writes `backend/data/generators/chunk_business-finance.csv`.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED_OFFSET = 7  # domain-specific offset on top of base seed 42
random.seed(42 + SEED_OFFSET)

OUT_PATH = Path(__file__).parent / "chunk_business-finance.csv"
TARGET_ROWS = 1000

# --------------------------------------------------------------------- #
# Role families -> (base title, seniority levels applicable, category)
# --------------------------------------------------------------------- #
ROLE_FAMILIES = [
    ("Financial Analyst", "Business, Finance & Analytics"),
    ("Business Analyst", "Business, Finance & Analytics"),
    ("Business Intelligence Analyst", "Data & Analytics"),
    ("Accountant", "Business, Finance & Analytics"),
    ("Staff Accountant", "Business, Finance & Analytics"),
    ("Accounting Manager", "Business, Finance & Analytics"),
    ("Finance Manager", "Business, Finance & Analytics"),
    ("Investment Analyst", "Business, Finance & Analytics"),
    ("Risk Analyst", "Business, Finance & Analytics"),
    ("Risk Manager", "Business, Finance & Analytics"),
    ("FP&A Analyst", "Business, Finance & Analytics"),
    ("Controller", "Business, Finance & Analytics"),
    ("Auditor", "Business, Finance & Analytics"),
    ("Internal Auditor", "Business, Finance & Analytics"),
    ("Data Analyst", "Data & Analytics"),
    ("BI Developer", "Data & Analytics"),
    ("Financial Planning Analyst", "Business, Finance & Analytics"),
    ("Procurement Analyst", "Business, Finance & Analytics"),
    ("Supply Chain Analyst", "Business Operations"),
    ("Pricing Analyst", "Business, Finance & Analytics"),
    ("Revenue Analyst", "Business, Finance & Analytics"),
    ("Treasury Analyst", "Business, Finance & Analytics"),
    ("Credit Analyst", "Business, Finance & Analytics"),
    ("Compliance Analyst", "Business, Finance & Analytics"),
    ("Operations Analyst", "Business Operations"),
    ("Strategy Analyst", "Business, Finance & Analytics"),
    ("Bookkeeper", "Business, Finance & Analytics"),
    ("Payroll Specialist", "Business, Finance & Analytics"),
    ("Tax Analyst", "Business, Finance & Analytics"),
    ("Portfolio Analyst", "Business, Finance & Analytics"),
]

# Seniority levels with weight, applicable roles filter, and salary bands (USD annual).
SENIORITY_LEVELS = [
    ("Intern", 0.08, (22000, 42000)),
    ("Junior", 0.16, (52000, 78000)),
    ("", 0.30, (72000, 108000)),          # "Mid-level" -> no prefix (bare title), most common
    ("Senior", 0.22, (98000, 148000)),
    ("Lead", 0.09, (128000, 172000)),
    ("Staff", 0.04, (135000, 180000)),
    ("Principal", 0.03, (145000, 190000)),
    ("Manager", 0.08, (112000, 168000)),
]

# Roles for which "Intern" / entry-style titles make sense (avoid "Intern Controller")
NO_INTERN_ROLES = {"Controller", "Accounting Manager", "Finance Manager", "Risk Manager"}
NO_MANAGER_DUP_ROLES = {"Accounting Manager", "Finance Manager", "Risk Manager", "Controller"}

LOCATIONS = [
    "New York, NY", "Chicago, IL", "Boston, MA", "San Francisco, CA",
    "Austin, TX", "Atlanta, GA", "Denver, CO", "Seattle, WA",
    "Charlotte, NC", "Dallas, TX", "Toronto, ON", "London, UK",
    "Singapore", "Dublin, Ireland", "Sydney, Australia", "Remote",
]
# ~25% Remote weight handled via explicit weighting below.
LOCATION_WEIGHTS = [0.09, 0.08, 0.06, 0.07, 0.06, 0.05, 0.04, 0.05,
                    0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.02, 0.30]

JOB_TYPES = ["Full-time", "Part-time", "Internship", "Contract"]
JOB_TYPE_WEIGHTS = [0.65, 0.10, 0.15, 0.10]

# --------------------------------------------------------------------- #
# Fictional company pool (~90 unique, invented word-combinations, never
# real organizations).
# --------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Pinecrest", "Harborline",
    "Skyline", "Bluepeak", "Northfield", "Cobalt", "Amberstone", "Silverbrook",
    "Granite", "Meridian", "Redwood", "Sterling", "Highfield", "Brightpath",
    "Cedarline", "Falcon Ridge", "Lakeshore", "Summit", "Clearwater", "Ashford",
    "Wrenfield", "Hollowbrook", "Marlowe", "Thornwood", "Kestrel", "Elmgate",
    "Rivergate", "Oakhaven", "Foxglen", "Brambleton", "Copperfield", "Windmere",
    "Palisade", "Ravenscroft", "Fernbrook", "Stonebridge",
]
COMPANY_SUFFIXES = [
    "Capital Group", "Financial Partners", "Ledger Co.", "Advisory Group",
    "Holdings", "Wealth Partners", "Analytics", "Consulting", "Trust Group",
    "Asset Management", "Ventures", "Financial Group", "Accounting Partners",
    "Strategy Group", "Investment Partners", "Bridge Capital", "Insights",
    "Solutions Group", "Financial Services", "& Associates",
]
COMPANIES = sorted({f"{p} {s}" for p, s in zip(
    [COMPANY_PREFIXES[i % len(COMPANY_PREFIXES)] for i in range(90)],
    [COMPANY_SUFFIXES[i % len(COMPANY_SUFFIXES)] for i in range(90)],
)})
random.shuffle(COMPANIES)
# Ensure a good spread: build ~80 unique combos via cartesian sampling.
COMPANY_POOL = []
seen_companies = set()
attempts = 0
while len(COMPANY_POOL) < 80 and attempts < 5000:
    attempts += 1
    name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
    if name not in seen_companies:
        seen_companies.add(name)
        COMPANY_POOL.append(name)

# --------------------------------------------------------------------- #
# Skill pools (drawn from onet_skills.csv "Business, Finance & Analytics"
# plus adjacent Data & Analytics / general skills for realistic co-occurrence)
# --------------------------------------------------------------------- #
CORE_FINANCE_SKILLS = [
    "Budgeting & Forecasting", "Financial Analysis", "Investment Analysis",
    "Risk Management", "Accounting Principles", "Cost-Benefit Analysis",
    "Business Development", "Contract Negotiation", "Vendor Management",
    "P&L Management", "Pricing Strategy", "Competitive Intelligence",
    "KPI Development", "Data-Driven Decision Making", "Excel Financial Modeling",
    "QuickBooks", "SAP", "NetSuite", "Procurement", "Supply Chain Analysis",
]
DATA_BI_SKILLS = [
    "SQL", "Tableau", "Power BI", "Excel", "Financial Modeling", "Salesforce",
]
GENERAL_SKILLS = [
    "Communication", "Presentation Skills", "Negotiation", "Critical Thinking",
    "Time Management", "Problem Solving", "Stakeholder Management",
    "Agile Methodology", "Git",
]

# Role -> preferred skill subset (keeps co-occurrence realistic; e.g. an
# Accountant shouldn't require "Tableau" as often as a BI Analyst).
ROLE_SKILL_BIAS = {
    "Business Intelligence Analyst": DATA_BI_SKILLS + ["KPI Development", "Data-Driven Decision Making"],
    "BI Developer": DATA_BI_SKILLS + ["Data-Driven Decision Making"],
    "Data Analyst": DATA_BI_SKILLS + ["Data-Driven Decision Making", "KPI Development"],
    "Accountant": ["Accounting Principles", "QuickBooks", "SAP", "NetSuite", "Excel"],
    "Staff Accountant": ["Accounting Principles", "QuickBooks", "Excel", "SAP"],
    "Accounting Manager": ["Accounting Principles", "SAP", "NetSuite", "P&L Management", "Vendor Management"],
    "Controller": ["Accounting Principles", "P&L Management", "SAP", "Risk Management", "Budgeting & Forecasting"],
    "Bookkeeper": ["Accounting Principles", "QuickBooks", "Excel"],
    "Payroll Specialist": ["Accounting Principles", "QuickBooks", "SAP", "Excel"],
    "Tax Analyst": ["Accounting Principles", "Excel", "SAP", "Risk Management"],
    "Auditor": ["Risk Management", "Accounting Principles", "Excel", "SAP"],
    "Internal Auditor": ["Risk Management", "Accounting Principles", "Excel", "Cost-Benefit Analysis"],
    "Risk Analyst": ["Risk Management", "Financial Analysis", "Excel", "SQL"],
    "Risk Manager": ["Risk Management", "Financial Analysis", "P&L Management", "Vendor Management"],
    "Credit Analyst": ["Risk Management", "Financial Analysis", "Investment Analysis", "Excel"],
    "Investment Analyst": ["Investment Analysis", "Financial Modeling", "Excel Financial Modeling", "Financial Analysis"],
    "Portfolio Analyst": ["Investment Analysis", "Financial Modeling", "Risk Management", "Excel Financial Modeling"],
    "Treasury Analyst": ["Financial Analysis", "Risk Management", "Excel", "Budgeting & Forecasting"],
    "Financial Analyst": ["Financial Analysis", "Excel Financial Modeling", "Budgeting & Forecasting", "Financial Modeling"],
    "Financial Planning Analyst": ["Budgeting & Forecasting", "Financial Analysis", "Excel Financial Modeling", "KPI Development"],
    "FP&A Analyst": ["Budgeting & Forecasting", "Financial Analysis", "Excel Financial Modeling", "SQL"],
    "Finance Manager": ["Budgeting & Forecasting", "P&L Management", "Financial Analysis", "Vendor Management"],
    "Pricing Analyst": ["Pricing Strategy", "Financial Analysis", "Excel", "Competitive Intelligence"],
    "Revenue Analyst": ["Financial Analysis", "KPI Development", "SQL", "Pricing Strategy"],
    "Business Analyst": ["Business Development", "Data-Driven Decision Making", "KPI Development", "Excel", "SQL"],
    "Strategy Analyst": ["Competitive Intelligence", "Business Development", "Data-Driven Decision Making", "Cost-Benefit Analysis"],
    "Compliance Analyst": ["Risk Management", "Accounting Principles", "Excel"],
    "Procurement Analyst": ["Procurement", "Vendor Management", "Contract Negotiation", "Cost-Benefit Analysis"],
    "Supply Chain Analyst": ["Supply Chain Analysis", "Procurement", "Vendor Management", "Excel"],
    "Operations Analyst": ["Data-Driven Decision Making", "KPI Development", "Excel", "SQL"],
}

# Messiness helpers: typo map + inconsistent-casing/abbreviation variants.
MESSY_VARIANTS = {
    "Excel": ["Exel", "excel", "EXCEL", "MS Excel"],
    "SQL": ["Sql", "sql"],
    "Financial Modeling": ["Financal Modeling", "financial modeling"],
    "Accounting Principles": ["Accounting Principals", "accounting principles"],
    "QuickBooks": ["Quickbooks", "quick books"],
    "Communication": ["Communication Skills", "communication"],
    "Power BI": ["PowerBI", "power bi"],
    "Risk Management": ["Risk Mgmt", "risk management"],
    "Budgeting & Forecasting": ["Budgeting and Forecasting", "budgeting & forecasting"],
    "Negotiation": ["Negotation", "negotiation"],
}


def pick_seniority():
    levels, weights, _ = zip(*[(l, w, b) for l, w, b in SENIORITY_LEVELS])
    bands = {l: b for l, w, b in SENIORITY_LEVELS}
    level = random.choices(levels, weights=weights, k=1)[0]
    return level, bands[level]


def build_title(role: str, level: str) -> str:
    if level == "Intern" and role in NO_INTERN_ROLES:
        level = "Junior"
    if level == "Manager" and role in NO_MANAGER_DUP_ROLES:
        # avoid "Manager Accounting Manager" style duplication
        level = ""
    if not level:
        return role
    if level == "Intern":
        return f"{role} Intern"
    if level == "Manager":
        return f"{role} Manager"
    return f"{level} {role}"


def pick_location():
    return random.choices(LOCATIONS, weights=LOCATION_WEIGHTS, k=1)[0]


def pick_job_type():
    return random.choices(JOB_TYPES, weights=JOB_TYPE_WEIGHTS, k=1)[0]


def pick_salary(band, level):
    lo, hi = band
    salary_min = random.randint(lo, hi - int((hi - lo) * 0.2))
    span = random.randint(int((hi - lo) * 0.15), int((hi - lo) * 0.4))
    salary_max = min(hi + int((hi - lo) * 0.1), salary_min + span)
    if salary_max <= salary_min:
        salary_max = salary_min + 5000
    return salary_min, salary_max


def pick_skills(role: str) -> list[str]:
    biased = ROLE_SKILL_BIAS.get(role, CORE_FINANCE_SKILLS)
    pool = list(dict.fromkeys(biased + CORE_FINANCE_SKILLS))
    n = random.randint(3, 8)
    n_core = min(n, len(pool))
    chosen = random.sample(pool, k=n_core)
    # occasionally add one general skill
    if random.random() < 0.35 and len(chosen) < 8:
        chosen.append(random.choice(GENERAL_SKILLS))
    random.shuffle(chosen)
    return chosen


def messify_skill(skill: str) -> str:
    if skill in MESSY_VARIANTS and random.random() < 0.5:
        return random.choice(MESSY_VARIANTS[skill])
    # generic messiness: random extra whitespace or case flip
    r = random.random()
    if r < 0.3:
        return f" {skill} "
    if r < 0.5:
        return skill.upper()
    if r < 0.6:
        return skill.lower()
    return skill


def generate_rows(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        role, category = random.choice(ROLE_FAMILIES)
        job_type = pick_job_type()
        if job_type == "Internship":
            level, band = "Intern", next(b for l, w, b in SENIORITY_LEVELS if l == "Intern")
        else:
            level, band = pick_seniority()
            while level == "Intern":
                level, band = pick_seniority()
        title = build_title(role, level)
        company = random.choice(COMPANY_POOL)
        location = pick_location()
        salary_min, salary_max = pick_salary(band, level)
        skills = pick_skills(role)

        is_messy_row = random.random() < 0.065  # ~6.5% messy rows
        if is_messy_row:
            idx = random.randrange(len(skills))
            skills = list(skills)
            skills[idx] = messify_skill(skills[idx])
            # sometimes duplicate a skill (case-different) to mimic fixture style
            if random.random() < 0.4:
                dup = random.choice(skills)
                skills.append(dup)

        rows.append({
            "title": title,
            "company": company,
            "location": location,
            "type": job_type,
            "skills_required": ", ".join(skills),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": category,
        })
    return rows


def main():
    rows = generate_rows(TARGET_ROWS)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["title", "company", "location", "type", "skills_required",
                        "salary_min", "salary_max", "category"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
