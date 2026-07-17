"""Synthetic data generator — domain chunk: Project/Program Management,
Operations, Supply Chain.

Produces EXACTLY 700 synthetic (fictional) job-posting rows matching the
schema used by `backend/data/kaggle_jobs.csv`:

    title,company,location,type,skills_required,salary_min,salary_max,category

Run:
    python generate_project-ops.py

Writes `chunk_project-ops.csv` next to this script.

All company names are invented (never real organizations). Seed is fixed
(42 + domain offset) for reproducibility.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 17  # domain-specific offset for "project-ops"
random.seed(SEED)

OUT_PATH = Path(__file__).parent / "chunk_project-ops.csv"
TARGET_ROWS = 700

# --------------------------------------------------------------------- #
# Roles: (base title, [applicable seniority prefixes or None-for-as-is],
#         role family used to pick skill pools, category)
# --------------------------------------------------------------------- #
ROLE_FAMILIES = {
    "project_mgmt": {
        "titles": [
            "Project Coordinator",
            "Project Manager",
            "Program Manager",
            "PMO Analyst",
            "PMO Lead",
            "Scrum Master",
            "Agile Coach",
            "Technical Program Manager",
        ],
        "category": "Project & Program Management",
        "core_skills": [
            "Program Management",
            "Risk Assessment (Projects)",
            "Resource Allocation",
            "Gantt Chart Planning",
            "PMP Certification",
            "PRINCE2",
            "Change Management",
            "Vendor Coordination",
            "SAFe (Scaled Agile Framework)",
            "Sprint Planning",
            "Retrospective Facilitation",
            "Portfolio Management",
            "Milestone Tracking",
            "Confluence",
            "Asana",
            "Monday.com",
            "Trello",
            "Microsoft Project",
            "Budget Management (Projects)",
            "Cross-team Coordination",
            "Agile Methodology",
            "Scrum",
            "Kanban",
            "Jira",
            "Stakeholder Management",
            "Roadmap Planning",
            "Requirements Gathering",
        ],
    },
    "operations": {
        "titles": [
            "Operations Analyst",
            "Operations Coordinator",
            "Operations Manager",
            "Business Operations Manager",
            "Director of Operations",
            "Operations Associate",
            "Strategy & Operations Manager",
            "Revenue Operations Analyst",
        ],
        "category": "Business Operations",
        "core_skills": [
            "Business Analysis",
            "KPI Development",
            "Data-Driven Decision Making",
            "Process Improvement",
            "Cost-Benefit Analysis",
            "Vendor Management",
            "P&L Management",
            "Budgeting & Forecasting",
            "Excel",
            "Excel Financial Modeling",
            "SAP",
            "NetSuite",
            "QuickBooks",
            "Cross-team Coordination",
            "Stakeholder Management",
        ],
    },
    "supply_chain": {
        "titles": [
            "Supply Chain Analyst",
            "Supply Chain Manager",
            "Supply Chain Coordinator",
            "Logistics Coordinator",
            "Logistics Manager",
            "Demand Planner",
            "Inventory Analyst",
            "Fulfillment Operations Manager",
        ],
        "category": "Supply Chain",
        "core_skills": [
            "Supply Chain Analysis",
            "Procurement",
            "Vendor Management",
            "Contract Negotiation",
            "Data Analysis",
            "Excel",
            "Excel Financial Modeling",
            "SAP",
            "NetSuite",
            "Risk Management",
            "Budgeting & Forecasting",
            "Cost-Benefit Analysis",
            "KPI Development",
        ],
    },
    "procurement": {
        "titles": [
            "Procurement Specialist",
            "Procurement Manager",
            "Sourcing Analyst",
            "Vendor Manager",
            "Purchasing Coordinator",
            "Category Manager",
        ],
        "category": "Supply Chain",
        "core_skills": [
            "Procurement",
            "Vendor Management",
            "Contract Negotiation",
            "Cost-Benefit Analysis",
            "Risk Management",
            "Budgeting & Forecasting",
            "Excel",
            "SAP",
            "NetSuite",
            "Data Analysis",
            "KPI Development",
        ],
    },
}

GENERAL_SKILLS = [
    "Communication",
    "Agile Methodology",
    "Time Management",
    "Problem Solving",
    "Critical Thinking",
    "Presentation Skills",
    "Negotiation",
    "Team Leadership",
    "Git",
    "Cross-functional Collaboration",
    "Facilitation",
    "Decision Making",
]

# Seniority ladder -> (prefix or None, salary range, applicable to which roles)
SENIORITY = [
    ("Intern", (20000, 40000), {"project_mgmt", "operations", "supply_chain", "procurement"}),
    ("Junior", (55000, 75000), {"project_mgmt", "operations", "supply_chain", "procurement"}),
    ("", (75000, 100000), {"project_mgmt", "operations", "supply_chain", "procurement"}),  # mid-level, no prefix
    ("Senior", (95000, 135000), {"project_mgmt", "operations", "supply_chain", "procurement"}),
    ("Lead", (115000, 155000), {"project_mgmt", "operations", "supply_chain", "procurement"}),
    ("Staff", (125000, 165000), {"project_mgmt"}),
    ("Principal", (135000, 180000), {"project_mgmt", "operations"}),
    ("Manager", (110000, 165000), {"project_mgmt", "operations", "supply_chain", "procurement"}),
    ("Director", (145000, 195000), {"operations", "supply_chain"}),
]

LOCATIONS = [
    "San Francisco, CA",
    "New York, NY",
    "Austin, TX",
    "Seattle, WA",
    "Boston, MA",
    "Chicago, IL",
    "Denver, CO",
    "Atlanta, GA",
    "Los Angeles, CA",
    "Toronto, ON",
    "Vancouver, BC",
    "London, UK",
    "Berlin, Germany",
    "Singapore",
    "Dublin, Ireland",
    "Bangalore, India",
    "Remote",
]
# ~25% Remote target achieved via weighting below.
LOCATION_WEIGHTS = [6, 6, 5, 5, 4, 4, 3, 3, 4, 3, 2, 3, 2, 2, 2, 2, 22]

JOB_TYPES = ["Full-time", "Part-time", "Internship", "Contract"]
JOB_TYPE_WEIGHTS = [65, 10, 15, 10]

COMPANIES = [
    "Vertex Cloud Labs", "Onyx Bridge Tech", "Crestline Digital", "Ironwood Systems",
    "Pinecrest Digital", "Harborline Technologies", "Skyline Ventures IT", "Bluepeak Software",
    "Nova Field Labs", "Meridian Apps", "Redwood Data Systems",
    "Cobalt Harbor Group", "Summit Ledger Partners", "Amberfield Logistics",
    "Brightwave Supply Co", "Northgate Operations Inc", "Fernbridge Holdings",
    "Cascade Freight Systems", "Ashgrove Consulting", "Timberline Sourcing Group",
    "Wellspring Procurement Partners", "Granite Vale Enterprises", "Silverton Logistics",
    "Copperfield Ventures", "Marlow Bay Group", "Stonewick Supply Chain Co",
    "Palisade Operations Group", "Thornfield Industries", "Larkspur Freight Partners",
    "Windmere Consulting Group", "Ridgemont Sourcing Solutions", "Auburn Peak Logistics",
    "Elmswood Trading Co", "Havencrest Partners", "Kestrel Point Enterprises",
    "Millbrook Distribution Group", "Oakhaven Supply Solutions", "Brightfield Sourcing",
    "Cedarpine Logistics", "Foxglove Operations", "Glenridge Procurement Group",
    "Hollowbrook Ventures", "Ironhollow Freight Co", "Juniper Ridge Partners",
    "Kingsford Supply Group", "Lockwood Trading Partners", "Moorland Distribution",
    "Norwich Point Consulting", "Overlook Sourcing Co", "Pemberton Logistics Group",
    "Quarrystone Enterprises", "Rosewood Freight Partners", "Saltmarsh Supply Co",
    "Thistledown Operations", "Underhill Ventures Group", "Valemont Distribution",
    "Wrenfield Sourcing Partners", "Yardley Logistics Co", "Zephyrhold Enterprises",
    "Ashwater Consulting", "Briarcliff Supply Group", "Coldharbor Ventures",
    "Duskwood Logistics Partners", "Emberline Trading Co", "Farrowdale Operations Group",
    "Greystone Freight Solutions", "Hartsfield Supply Chain Partners",
    "Ivyholt Consulting Group", "Justwell Sourcing Co", "Kettlebrook Enterprises",
    "Longmoor Logistics Group", "Mistwood Distribution Partners", "Nettlefield Ventures",
    "Oldbridge Supply Solutions", "Pinegrove Freight Co", "Ravensmoor Operations",
]

MESSINESS_RATE = 0.065  # 6.5% target within the 5-8% band

TYPO_MAP = {
    "Communication": "Comunication",
    "Negotiation": "Negociation",
    "Procurement": "Procurment",
    "Budgeting & Forecasting": "Budgeting & Forcasting",
    "Vendor Management": "Vender Management",
    "Excel": "Excell",
    "Agile Methodology": "Agile Methodolgy",
    "Contract Negotiation": "Contract Negotation",
    "Supply Chain Analysis": "Supply Chain Analisys",
    "Program Management": "Program Managment",
}

ABBREV_MAP = {
    "Program Management": "PM",
    "Change Management": "Change Mgmt",
    "Agile Methodology": "Agile",
    "Communication": "Communication Skills",
    "Negotiation": "Negotiation Skills",
    "Confluence": "Confluence Wiki",
    "Monday.com": "Monday",
    "Microsoft Project": "MS Project",
    "SAFe (Scaled Agile Framework)": "SAFe",
    "PMP Certification": "PMP",
    "PRINCE2": "Prince2",
}


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


SENIOR_PREFIXES = {"Director", "Principal", "Staff"}
JUNIOR_NOUNS = ("Coordinator", "Associate", "Intern")


def make_title(family_key: str, family: dict) -> tuple[str, str]:
    """Return (title, seniority_label) picking a base title + seniority
    compatible with that role family."""
    applicable = [s for s in SENIORITY if family_key in s[2]]
    prefix, salary_range, _ = random.choice(applicable)

    # Avoid grammatically awkward combos like "Director Operations
    # Coordinator" — senior prefixes should land on manager/lead/analyst
    # style nouns, not entry-level coordinator/associate nouns.
    candidates = family["titles"]
    if prefix in SENIOR_PREFIXES:
        filtered = [t for t in candidates if not t.endswith(JUNIOR_NOUNS)]
        candidates = filtered or candidates
    base = random.choice(candidates)

    if prefix:
        # Avoid double "Manager Manager" style collisions.
        if prefix == "Manager" and "Manager" in base:
            title = base
        elif prefix == "Director" and "Director" in base:
            title = base
        else:
            title = f"{prefix} {base}"
    else:
        title = base
    return title, prefix, salary_range


def pick_skills(family: dict) -> list[str]:
    pool = family["core_skills"]
    n_core = random.randint(3, 7)
    n_core = min(n_core, len(pool))
    chosen = random.sample(pool, n_core)
    # occasionally add 1 general skill
    if random.random() < 0.55:
        general = random.choice(GENERAL_SKILLS)
        if general not in chosen:
            chosen.append(general)
    # cap at 8
    chosen = chosen[:8]
    random.shuffle(chosen)
    return chosen


def messify_skill(name: str) -> str:
    """Apply one of several messiness transforms to a skill string."""
    choice = random.random()
    if name in TYPO_MAP and choice < 0.35:
        return TYPO_MAP[name]
    if name in ABBREV_MAP and choice < 0.65:
        return ABBREV_MAP[name]
    if choice < 0.8:
        return name.upper() if random.random() < 0.5 else name.lower()
    return f"  {name} "  # extra whitespace


def make_salary(salary_range: tuple[int, int]) -> tuple[int, int]:
    lo_bound, hi_bound = salary_range
    span = hi_bound - lo_bound
    salary_min = lo_bound + random.randint(0, int(span * 0.4))
    salary_max = salary_min + random.randint(int(span * 0.2), int(span * 0.6) + 5000)
    salary_max = max(salary_max, salary_min + 3000)
    return salary_min, salary_max


def generate_rows(n: int) -> list[dict]:
    rows = []
    family_keys = list(ROLE_FAMILIES.keys())
    for _ in range(n):
        family_key = random.choice(family_keys)
        family = ROLE_FAMILIES[family_key]
        title, seniority, salary_range = make_title(family_key, family)
        company = random.choice(COMPANIES)
        location = weighted_choice(LOCATIONS, LOCATION_WEIGHTS)
        job_type = weighted_choice(JOB_TYPES, JOB_TYPE_WEIGHTS)
        # Internship seniority should generally mean Internship job type,
        # but keep some natural variance rather than forcing it.
        if seniority == "Intern" and random.random() < 0.7:
            job_type = "Internship"

        skills = pick_skills(family)

        # inject messiness into a subset of rows
        if random.random() < MESSINESS_RATE:
            idx = random.randrange(len(skills))
            skills[idx] = messify_skill(skills[idx])
            # occasionally duplicate a skill (common real-world messiness)
            if random.random() < 0.3 and len(skills) < 8:
                skills.append(skills[idx])

        salary_min, salary_max = make_salary(salary_range)

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "type": job_type,
                "skills_required": ", ".join(skills),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "category": family["category"],
            }
        )
    return rows


def main():
    rows = generate_rows(TARGET_ROWS)
    fieldnames = [
        "title",
        "company",
        "location",
        "type",
        "skills_required",
        "salary_min",
        "salary_max",
        "category",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
