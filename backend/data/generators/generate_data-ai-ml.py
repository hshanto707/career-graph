"""Synthetic data generator — domain chunk: Data Science, AI/ML, Analytics Engineering.

Produces EXACTLY 1200 rows matching the schema used across the project:
    title,company,location,type,skills_required,salary_min,salary_max,category

Reproducible via a fixed seed (42 + a domain-specific offset). Purely
synthetic / fictional data — no real companies, no real job postings.

Run:
    python3 generate_data-ai-ml.py
Output:
    chunk_data-ai-ml.csv (written alongside this script)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

DOMAIN_SEED_OFFSET = 7  # domain-specific offset on top of the base seed 42
random.seed(42 + DOMAIN_SEED_OFFSET)

OUTPUT_ROWS = 1200
OUTPUT_PATH = Path(__file__).parent / "chunk_data-ai-ml.csv"

CATEGORY = "Data & Analytics"

# --------------------------------------------------------------------------- #
# Roles: base title -> list of seniority levels realistic for that role, plus
# the domain-relevant skill pools to draw from for that role.
# --------------------------------------------------------------------------- #

SENIORITY_ORDER = [
    "Intern",
    "Junior",
    "Mid-level",
    "Senior",
    "Lead",
    "Staff",
    "Principal",
    "Manager",
]

# Salary bands (USD annual), roughly per the brief, nudged slightly upward
# for AI/ML given current market norms.
SALARY_BANDS = {
    "Intern": (22000, 42000),
    "Junior": (60000, 85000),
    "Mid-level": (85000, 120000),
    "Senior": (115000, 165000),
    "Lead": (140000, 185000),
    "Staff": (150000, 195000),
    "Principal": (160000, 200000),
    "Manager": (125000, 180000),
}

ROLES = {
    "Data Scientist": {
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "Python", "Statistics", "Machine Learning", "Pandas", "NumPy",
            "Scikit-learn", "SQL", "Data Analysis", "A/B Testing",
            "Statistical Modeling", "Predictive Analytics",
        ],
        "secondary": [
            "R", "TensorFlow", "PyTorch", "Deep Learning", "Time Series Analysis",
            "Data Visualization", "Jupyter",
        ],
    },
    "Machine Learning Engineer": {
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "Python", "Machine Learning", "TensorFlow", "PyTorch", "Deep Learning",
            "MLOps", "Feature Engineering", "Scikit-learn",
        ],
        "secondary": [
            "Apache Spark", "Docker", "Kubernetes", "XGBoost", "Vector Embeddings",
            "Reinforcement Learning", "Model Interpretability (SHAP/LIME)",
        ],
    },
    "AI Research Engineer": {
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "Python", "Deep Learning", "PyTorch", "Large Language Models",
            "Generative AI", "Natural Language Processing", "Hugging Face Transformers",
        ],
        "secondary": [
            "Reinforcement Learning", "Prompt Engineering", "Vector Embeddings",
            "Computer Vision", "Statistics",
        ],
    },
    "Data Engineer": {
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "Python", "SQL", "ETL Pipelines", "Apache Spark", "Apache Airflow",
            "Data Warehousing", "Data Pipeline Design",
        ],
        "secondary": [
            "dbt", "Databricks", "Apache Kafka", "Snowflake", "BigQuery", "Redshift",
            "Apache Hadoop", "Big Data",
        ],
    },
    "Analytics Engineer": {
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "core": [
            "SQL", "dbt", "Data Modeling", "Data Warehousing", "Python",
            "Business Intelligence",
        ],
        "secondary": [
            "Snowflake", "BigQuery", "Looker", "Tableau", "Power BI",
            "Data Quality Management", "Data Governance",
        ],
    },
    "Data Analyst": {
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead"],
        "core": [
            "SQL", "Excel", "Data Analysis", "Tableau", "Power BI",
            "Data Visualization",
        ],
        "secondary": [
            "Python", "Statistics", "A/B Testing", "Google Analytics",
            "Data Storytelling", "Amplitude", "Mixpanel",
        ],
    },
    "Business Intelligence Analyst": {
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Manager"],
        "core": [
            "SQL", "Business Intelligence", "Power BI", "Tableau", "Data Modeling",
        ],
        "secondary": [
            "Looker", "Qlik Sense", "Google Data Studio", "Excel VBA",
            "Metabase", "Data Governance",
        ],
    },
    "NLP Engineer": {
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "core": [
            "Python", "Natural Language Processing", "Large Language Models",
            "Hugging Face Transformers", "Deep Learning",
        ],
        "secondary": [
            "PyTorch", "TensorFlow", "Prompt Engineering", "Generative AI",
            "Vector Embeddings", "Statistics",
        ],
    },
    "Computer Vision Engineer": {
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "core": [
            "Python", "Computer Vision", "Deep Learning", "PyTorch", "TensorFlow",
        ],
        "secondary": [
            "OpenCV", "Machine Learning", "Feature Engineering", "MLOps",
            "Docker",
        ],
    },
    "MLOps Engineer": {
        "seniorities": ["Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "MLOps", "Docker", "Kubernetes", "Python", "CI/CD Pipelines",
        ],
        "secondary": [
            "Apache Airflow", "Terraform", "Machine Learning", "Amazon Web Services",
            "Microsoft Azure", "Google Cloud Platform",
        ],
    },
    "Quantitative Analyst": {
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Principal"],
        "core": [
            "Statistics", "Python", "Statistical Modeling", "Time Series Analysis",
            "R",
        ],
        "secondary": [
            "Machine Learning", "SQL", "Predictive Analytics", "Financial Modeling",
        ],
    },
    "Data Science Manager": {
        "seniorities": ["Manager"],
        "core": [
            "Machine Learning", "Statistics", "Python", "Data Analysis",
            "Team Leadership",
        ],
        "secondary": [
            "Stakeholder Management", "Roadmap Planning", "SQL", "Predictive Analytics",
        ],
    },
    "Analytics Engineering Manager": {
        "seniorities": ["Manager"],
        "core": [
            "Data Modeling", "SQL", "dbt", "Data Warehousing", "Team Leadership",
        ],
        "secondary": [
            "Stakeholder Management", "Data Governance", "Roadmap Planning",
        ],
    },
    "Research Scientist, AI": {
        "seniorities": ["Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "core": [
            "Deep Learning", "PyTorch", "Generative AI", "Large Language Models",
            "Reinforcement Learning",
        ],
        "secondary": [
            "Python", "Natural Language Processing", "Computer Vision",
            "Prompt Engineering", "Statistics",
        ],
    },
}

GENERAL_SKILLS = [
    "Git", "Communication", "Agile Methodology", "Jira", "Problem Solving",
    "Technical Writing", "Cross-functional Collaboration", "Scrum",
    "Time Management", "Critical Thinking",
]

# --------------------------------------------------------------------------- #
# Companies: ~80 fictional companies in the existing invented-word-combo style.
# --------------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Pinecrest", "Harborline",
    "Skyline", "Bluepeak", "Nova", "Meridian", "Redwood", "Cobalt",
    "Northfield", "Silverlake", "Amberton", "Cascadia", "Brightwell",
    "Ridgeback", "Solstice", "Granite", "Fernwood", "Lumen", "Quartzline",
    "Halcyon", "Driftwood", "Cinderpeak", "Wavelength", "Copperfield",
    "Starling", "Ashgrove", "Basecamp", "Palisade", "Thornfield", "Windward",
]
COMPANY_MIDS = [
    "Cloud", "Bridge", "Data", "Analytics", "Insight", "Field", "Systems",
    "Digital", "Signal", "Vector", "Cognition", "Neural", "Compute",
    "Metrics", "Pattern", "Quantum", "Stream", "Grid",
]
COMPANY_SUFFIXES = [
    "Labs", "Tech", "Group", "IT", "Ventures", "Systems", "Digital",
    "Analytics", "AI", "Works", "Partners", "Collective", "Studio",
    "Robotics Group", "Software",
]


def _build_company_pool(n: int) -> list[str]:
    pool: set[str] = set()
    combos = [
        (p, m, s)
        for p in COMPANY_PREFIXES
        for m in COMPANY_MIDS
        for s in COMPANY_SUFFIXES
    ]
    random.shuffle(combos)
    for p, m, s in combos:
        if len(pool) >= n:
            break
        pool.add(f"{p} {m} {s}")
    return sorted(pool)


COMPANIES = _build_company_pool(90)

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Chicago, IL", "Denver, CO", "Atlanta, GA",
    "Los Angeles, CA", "Washington, DC", "Toronto, ON", "Vancouver, BC",
    "London, UK", "Berlin, Germany", "Bangalore, India", "Singapore",
    "Dublin, Ireland", "Amsterdam, Netherlands", "Sydney, Australia",
    "Remote",
]
# Weight Remote to ~25% via explicit weighting below rather than list repeats.

JOB_TYPES = ["Full-time", "Part-time", "Internship", "Contract"]
JOB_TYPE_WEIGHTS = [0.65, 0.10, 0.15, 0.10]


def _pick_location() -> str:
    if random.random() < 0.25:
        return "Remote"
    non_remote = [loc for loc in LOCATIONS if loc != "Remote"]
    return random.choice(non_remote)


NON_INTERN_TYPES = ["Full-time", "Part-time", "Contract"]
NON_INTERN_WEIGHTS = [0.75, 0.12, 0.13]


def _pick_job_type(seniority: str) -> str:
    if seniority == "Intern":
        return "Internship"
    if seniority == "Manager":
        # Managers are essentially never part-time/contract mixes;
        # keep mostly Full-time with an occasional Contract.
        return random.choices(["Full-time", "Contract"], weights=[0.9, 0.1])[0]
    # Non-intern seniorities never get "Internship" as a job type.
    return random.choices(NON_INTERN_TYPES, weights=NON_INTERN_WEIGHTS)[0]


def _salary_for(seniority: str) -> tuple[int, int]:
    lo, hi = SALARY_BANDS[seniority]
    # Randomize a sub-window within the band so not every row has identical bounds.
    band_width = hi - lo
    start = lo + random.randint(0, int(band_width * 0.5))
    end = start + random.randint(int(band_width * 0.2), int(band_width * 0.6))
    end = min(end, hi + 5000)
    if end <= start:
        end = start + 5000
    return start, end


def _title_for(role: str, seniority: str) -> str:
    if role.endswith("Manager"):
        # Role itself already conveys seniority (e.g. "Data Science Manager").
        return role
    if seniority == "Manager":
        return f"{role} Manager"
    if seniority == "Mid-level":
        return f"Mid-level {role}"
    return f"{seniority} {role}"


def _pick_skills(role_cfg: dict) -> list[str]:
    core = role_cfg["core"]
    secondary = role_cfg["secondary"]
    n_core = random.randint(2, min(4, len(core)))
    chosen = random.sample(core, n_core)

    remaining_budget = random.randint(3, 8) - len(chosen)
    if remaining_budget > 0 and secondary:
        n_sec = min(remaining_budget, len(secondary), random.randint(1, 4))
        chosen += random.sample(secondary, n_sec)

    # Occasionally add one general skill (Git, Communication, Agile, etc.)
    if random.random() < 0.4:
        chosen.append(random.choice(GENERAL_SKILLS))

    # Final size clamp to the 3-8 requested range.
    if len(chosen) > 8:
        chosen = chosen[:8]
    if len(chosen) < 3:
        pool = [s for s in (core + secondary) if s not in chosen]
        while len(chosen) < 3 and pool:
            chosen.append(pool.pop(random.randrange(len(pool))))

    random.shuffle(chosen)
    return chosen


# --------------------------------------------------------------------------- #
# Messiness injection (~5-8% of rows): typo, casing, whitespace, abbreviation.
# --------------------------------------------------------------------------- #
TYPO_MAP = {
    "Python": "Pyhton",
    "JavaScript": "Javascrpt",
    "SQL": "Sql",
    "Machine Learning": "Machien Learning",
    "TensorFlow": "Tensorflow",
    "PyTorch": "Pytorch",
    "Statistics": "Statisitcs",
    "Scikit-learn": "Scikit learn",
}
ABBREV_MAP = {
    "Python": "Py",
    "Machine Learning": "ML",
    "Natural Language Processing": "NLP",
    "Large Language Models": "LLM",
    "Deep Learning": "DL",
    "Business Intelligence": "BI",
    "Reinforcement Learning": "RL",
    "Generative AI": "GenAI",
    "Amazon Web Services": "AWS",
    "Google Cloud Platform": "GCP",
    "Microsoft Azure": "Azure",
    "Computer Vision": "CV",
}


def _messify_skill(name: str) -> str:
    choice = random.random()
    if choice < 0.3 and name in TYPO_MAP:
        return TYPO_MAP[name]
    if choice < 0.55 and name in ABBREV_MAP:
        return ABBREV_MAP[name]
    if choice < 0.75:
        return name.upper() if random.random() < 0.5 else name.lower()
    # extra whitespace
    return f" {name} "


def _maybe_messify_row(skills: list[str]) -> list[str]:
    messy = list(skills)
    idx = random.randrange(len(messy))
    messy[idx] = _messify_skill(messy[idx])
    if random.random() < 0.3 and len(messy) > 1:
        idx2 = random.randrange(len(messy))
        messy[idx2] = _messify_skill(messy[idx2])
    return messy


# Relative weight for picking each seniority level (when available for a
# given role) — skews toward Internship a bit more than a flat pyramid would,
# so the overall job-type mix lands near the ~15% Internship target.
SENIORITY_WEIGHTS = {
    "Intern": 45,
    "Junior": 20,
    "Mid-level": 18,
    "Senior": 15,
    "Lead": 7,
    "Staff": 5,
    "Principal": 3,
    "Manager": 7,
}


def _pick_seniority(available: list[str]) -> str:
    weights = [SENIORITY_WEIGHTS[s] for s in available]
    return random.choices(available, weights=weights)[0]


def generate_rows(n: int) -> list[dict]:
    rows = []
    role_names = list(ROLES.keys())
    messy_row_indices = set(
        random.sample(range(n), k=int(n * random.uniform(0.05, 0.08)))
    )

    for i in range(n):
        role = random.choice(role_names)
        role_cfg = ROLES[role]
        seniority = _pick_seniority(role_cfg["seniorities"])

        title = _title_for(role, seniority)
        company = random.choice(COMPANIES)
        location = _pick_location()
        job_type = _pick_job_type(seniority)
        salary_min, salary_max = _salary_for(seniority)
        skills = _pick_skills(role_cfg)

        if i in messy_row_indices:
            skills = _maybe_messify_row(skills)
            if random.random() < 0.2:
                company = company.strip()  # placeholder no-op, casing kept for companies

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "type": job_type,
                "skills_required": ", ".join(skills),
                "salary_min": salary_min,
                "salary_max": salary_max,
                "category": CATEGORY,
            }
        )
    return rows


def main() -> None:
    rows = generate_rows(OUTPUT_ROWS)
    fieldnames = [
        "title", "company", "location", "type", "skills_required",
        "salary_min", "salary_max", "category",
    ]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
