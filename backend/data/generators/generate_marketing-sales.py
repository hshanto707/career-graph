"""Synthetic data generator: Marketing, Sales, Growth, Content domain chunk.

Produces exactly 900 realistic (but fully synthetic) job-posting rows into
chunk_marketing-sales.csv, matching the schema expected by IngestionAgent:
    title,company,location,type,skills_required,salary_min,salary_max,category

Fixed seed (42 + domain offset) for reproducibility. Companies are
invented word-combinations (never real organizations). ~5-8% of rows get
injected messiness (typos, casing, whitespace, abbreviations) to exercise
NormalizationAgent's fuzzy-matching / synonym resolution at scale.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 7  # domain-specific offset for marketing/sales chunk
random.seed(SEED)

TOTAL_ROWS = 900

HERE = Path(__file__).resolve().parent
OUTPUT_PATH = HERE / "chunk_marketing-sales.csv"
CATEGORY = "Marketing, Sales & Growth"

# --------------------------------------------------------------------- #
# Roles & seniority
# --------------------------------------------------------------------- #

# Each role family: (base_title, allowed seniorities, skill pool key)
ROLE_FAMILIES = [
    ("Content Marketing", ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Manager"], "content"),
    ("Content Strategist", ["Junior", "Mid-level", "Senior", "Lead"], "content"),
    ("Copywriter", ["Intern", "Junior", "Mid-level", "Senior", "Lead"], "content"),
    ("SEO Specialist", ["Junior", "Mid-level", "Senior", "Lead"], "seo"),
    ("SEO Manager", ["Mid-level", "Senior", "Manager"], "seo"),
    ("Digital Marketing Specialist", ["Intern", "Junior", "Mid-level", "Senior"], "digital"),
    ("Digital Marketing Manager", ["Mid-level", "Senior", "Manager"], "digital"),
    ("Growth Marketer", ["Junior", "Mid-level", "Senior", "Lead"], "growth"),
    ("Growth Hacker", ["Junior", "Mid-level", "Senior"], "growth"),
    ("Growth Manager", ["Mid-level", "Senior", "Manager", "Lead"], "growth"),
    ("Social Media Manager", ["Junior", "Mid-level", "Senior", "Manager"], "social"),
    ("Social Media Coordinator", ["Intern", "Junior", "Mid-level"], "social"),
    ("Brand Manager", ["Mid-level", "Senior", "Manager", "Lead"], "brand"),
    ("Brand Strategist", ["Junior", "Mid-level", "Senior"], "brand"),
    ("Email Marketing Specialist", ["Junior", "Mid-level", "Senior"], "email"),
    ("Marketing Automation Specialist", ["Junior", "Mid-level", "Senior", "Lead"], "automation"),
    ("Marketing Analyst", ["Intern", "Junior", "Mid-level", "Senior"], "analytics"),
    ("Marketing Analytics Manager", ["Mid-level", "Senior", "Manager", "Lead"], "analytics"),
    ("Sales Development Representative", ["Intern", "Junior", "Mid-level"], "sales_dev"),
    ("Account Executive", ["Junior", "Mid-level", "Senior"], "sales_exec"),
    ("Sales Manager", ["Mid-level", "Senior", "Manager", "Lead"], "sales_exec"),
    ("Sales Operations Analyst", ["Junior", "Mid-level", "Senior"], "sales_ops"),
    ("Business Development Representative", ["Intern", "Junior", "Mid-level"], "sales_dev"),
    ("Business Development Manager", ["Mid-level", "Senior", "Manager", "Lead"], "sales_exec"),
    ("Public Relations Specialist", ["Junior", "Mid-level", "Senior"], "pr"),
    ("Public Relations Manager", ["Mid-level", "Senior", "Manager"], "pr"),
    ("Influencer Marketing Manager", ["Mid-level", "Senior", "Manager"], "influencer"),
    ("Affiliate Marketing Manager", ["Mid-level", "Senior", "Manager"], "affiliate"),
    ("Product Marketing Manager", ["Mid-level", "Senior", "Manager", "Lead"], "pmm"),
    ("VP of Marketing", ["Lead", "Principal"], "leadership"),
    ("VP of Sales", ["Lead", "Principal"], "leadership"),
    ("Head of Growth", ["Lead", "Principal", "Staff"], "leadership"),
    ("CRM Manager", ["Mid-level", "Senior", "Manager"], "crm"),
    ("Demand Generation Manager", ["Mid-level", "Senior", "Manager", "Lead"], "demand_gen"),
]

SENIORITY_SALARY = {
    "Intern": (20000, 40000),
    "Junior": (55000, 80000),
    "Mid-level": (75000, 110000),
    "Senior": (100000, 150000),
    "Lead": (130000, 175000),
    "Staff": (135000, 185000),
    "Principal": (145000, 190000),
    "Manager": (110000, 170000),
}

# --------------------------------------------------------------------- #
# Skill pools per role family (from onet_skills.csv taxonomy)
# --------------------------------------------------------------------- #

SKILL_POOLS = {
    "content": ["Content Marketing", "Content Strategy", "Copywriting", "SEO",
                "Social Media Marketing", "Email Marketing", "Public Relations"],
    "seo": ["SEO", "Content Strategy", "Marketing Analytics", "Digital Marketing",
            "Conversion Rate Optimization", "Content Marketing"],
    "digital": ["Digital Marketing", "SEO", "Paid Search Advertising", "Paid Social Advertising",
                "Marketing Automation", "Marketing Analytics", "Email Marketing"],
    "growth": ["Growth Hacking", "Conversion Rate Optimization", "Marketing Analytics",
               "Paid Search Advertising", "Paid Social Advertising", "Lead Generation",
               "Customer Retention Strategy"],
    "social": ["Social Media Marketing", "Content Marketing", "Influencer Marketing",
               "Paid Social Advertising", "Brand Strategy", "Copywriting"],
    "brand": ["Brand Strategy", "Content Strategy", "Public Relations", "Market Research",
              "Marketing Analytics", "Social Media Marketing"],
    "email": ["Email Marketing", "Marketing Automation", "CRM Management",
              "Lead Generation", "Marketing Analytics", "Copywriting"],
    "automation": ["Marketing Automation", "HubSpot", "CRM Management", "Email Marketing",
                   "Lead Generation", "Marketing Analytics"],
    "analytics": ["Marketing Analytics", "Market Research", "Excel", "SQL",
                  "Conversion Rate Optimization", "Digital Marketing"],
    "sales_dev": ["Lead Generation", "CRM Management", "Salesforce", "Sales Forecasting",
                  "Account-Based Marketing", "Negotiation"],
    "sales_exec": ["Salesforce", "CRM Management", "Sales Forecasting", "Negotiation",
                   "Lead Generation", "Account-Based Marketing", "Customer Retention Strategy"],
    "sales_ops": ["Sales Forecasting", "CRM Management", "Salesforce", "Excel",
                  "Marketing Analytics", "Market Research"],
    "pr": ["Public Relations", "Brand Strategy", "Content Strategy", "Copywriting",
           "Social Media Marketing", "Market Research"],
    "influencer": ["Influencer Marketing", "Social Media Marketing", "Brand Strategy",
                   "Content Marketing", "Marketing Analytics"],
    "affiliate": ["Affiliate Marketing", "Marketing Analytics", "Digital Marketing",
                  "Lead Generation", "Conversion Rate Optimization"],
    "pmm": ["Product Marketing" if False else "Brand Strategy", "Market Research", "Content Strategy",
            "Marketing Analytics", "Lead Generation", "Public Relations"],
    "leadership": ["Marketing Analytics", "Brand Strategy", "Sales Forecasting",
                   "Growth Hacking", "CRM Management", "Public Relations", "Market Research"],
    "crm": ["CRM Management", "Salesforce", "HubSpot", "Marketing Automation",
            "Sales Forecasting", "Customer Retention Strategy"],
    "demand_gen": ["Lead Generation", "Account-Based Marketing", "Marketing Automation",
                   "CRM Management", "Marketing Analytics", "Paid Search Advertising"],
}

GENERAL_SKILLS = ["Communication", "Agile Methodology", "Excel", "Presentation Skills",
                   "Negotiation", "Project Management", "Collaboration", "Public Speaking"]

# --------------------------------------------------------------------- #
# Locations, companies, job types
# --------------------------------------------------------------------- #

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Boston, MA",
    "Chicago, IL", "Denver, CO", "Los Angeles, CA", "Atlanta, GA", "Portland, OR",
    "Miami, FL", "Toronto, Canada", "London, UK", "Berlin, Germany", "Dublin, Ireland",
    "Singapore", "Sydney, Australia", "Amsterdam, Netherlands", "Austin, TX",
]

JOB_TYPES_WEIGHTED = (
    ["Full-time"] * 65 + ["Part-time"] * 10 + ["Internship"] * 15 + ["Contract"] * 10
)

COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Bluepeak", "Northgate", "Silverlane",
    "Amberfield", "Cobalt", "Redwood", "Solstice", "Pinnacle", "Havenwood", "Brightpath",
    "Sterling", "Meridian", "Cascade", "Wildflower", "Granite", "Lumen", "Foxglove",
    "Anchorpoint", "Marble", "Copperfield", "Windmere", "Everline", "Falconhurst",
    "Driftwood", "Auroraline", "Timbergate", "Quartzridge", "Emberly", "Larkspur",
    "Northwind", "Fernbrook", "Halcyon", "Basalt", "Rosemount", "Clearwater", "Ashgrove",
]
COMPANY_SUFFIXES = [
    "Cloud Labs", "Bridge Tech", "Digital", "Systems", "Growth Co", "Media Group",
    "Ventures", "Marketing Collective", "Brands", "Partners", "Analytics", "Studio",
    "Networks", "Holdings", "Commerce", "Group", "Solutions", "Interactive", "Labs",
]

COMPANIES = sorted({f"{p} {s}" for p in COMPANY_PREFIXES for s in COMPANY_SUFFIXES})
random.shuffle(COMPANIES)
COMPANIES = COMPANIES[:90]  # pool of ~90 unique fictional companies

# --------------------------------------------------------------------- #
# Messiness injection helpers
# --------------------------------------------------------------------- #

TYPO_MAP = {
    "SEO": "S.E.O.",
    "Copywriting": "Copywritting",
    "Marketing Analytics": "Marketing Analitics",
    "Salesforce": "Sales force",
    "Negotiation": "Negociation",
    "CRM Management": "CRM Mgmt",
    "Email Marketing": "email marketing",
    "Content Marketing": "content marketing ",
    "Social Media Marketing": "Social Media Mktg",
    "Public Relations": "PR",
    "Lead Generation": "Lead Gen",
    "Digital Marketing": "Digital Mktg",
    "Communication": "Communication Skills",
    "Agile Methodology": "Agile",
}


def messify_skill(skill: str) -> str:
    """Apply a random messiness transform to a skill string."""
    choice = random.random()
    if skill in TYPO_MAP and choice < 0.5:
        return TYPO_MAP[skill]
    if choice < 0.65:
        return skill.upper()
    if choice < 0.8:
        return skill.lower()
    if choice < 0.9:
        return f"  {skill}  "
    return f" {skill},{skill}"  # accidental duplicate fragment / extra comma noise


def build_title(role: str, seniority: str) -> str:
    if seniority == "Mid-level":
        return f"{role}"  # mid-level often has no prefix in postings
    if role.startswith(("VP of", "Head of")):
        return role
    return f"{seniority} {role}"


def pick_skills(pool_key: str, rng: random.Random) -> list[str]:
    domain_pool = SKILL_POOLS[pool_key]
    n_domain = rng.randint(3, min(6, len(domain_pool)))
    skills = rng.sample(domain_pool, n_domain)
    # occasionally add 1 general skill
    if rng.random() < 0.55:
        skills.append(rng.choice(GENERAL_SKILLS))
    # cap total at 8
    if len(skills) > 8:
        skills = skills[:8]
    return skills


def generate_rows(n: int) -> list[dict]:
    rows = []
    for i in range(n):
        role, seniorities, pool_key = random.choice(ROLE_FAMILIES)
        seniority = random.choice(seniorities)
        title = build_title(role, seniority)
        company = random.choice(COMPANIES)
        location = "Remote" if random.random() < 0.25 else random.choice(LOCATIONS)
        job_type = random.choice(JOB_TYPES_WEIGHTED)

        lo, hi = SENIORITY_SALARY[seniority]
        # add jitter within the band, keep salary_min < salary_max
        salary_min = random.randint(lo, int(lo + (hi - lo) * 0.4))
        salary_max = random.randint(int(salary_min + (hi - lo) * 0.15), hi)
        if job_type == "Internship":
            # interns are paid stipend-like, scale down regardless of seniority band
            salary_min = min(salary_min, random.randint(20000, 35000))
            salary_max = min(max(salary_max, salary_min + 2000), 42000)
        if job_type == "Part-time":
            salary_min = int(salary_min * 0.55)
            salary_max = int(salary_max * 0.55)

        skills = pick_skills(pool_key, random)
        messy_row = random.random() < 0.065  # ~6.5% messiness rate
        if messy_row:
            idx = random.randrange(len(skills))
            skills[idx] = messify_skill(skills[idx])
            # sometimes also mess up casing on the whole title or add whitespace
            noise_choice = random.random()
            if noise_choice < 0.3:
                title = title.upper()
            elif noise_choice < 0.5:
                title = f"  {title}  "
            elif noise_choice < 0.65:
                company = company.upper()

        skills_str = ", ".join(skills)

        rows.append({
            "title": title,
            "company": company,
            "location": location,
            "type": job_type,
            "skills_required": skills_str,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": CATEGORY,
        })
    return rows


def main() -> None:
    rows = generate_rows(TOTAL_ROWS)
    fieldnames = ["title", "company", "location", "type", "skills_required",
                  "salary_min", "salary_max", "category"]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
