"""Synthetic job-posting generator — domain chunk: Healthcare IT, Bioinformatics,
Health Data.

Produces EXACTLY 600 rows matching the schema of `backend/data/kaggle_jobs.csv`:
    title,company,location,type,skills_required,salary_min,salary_max,category

This is a 100% synthetic/fictional dataset generated for capstone-scale load
testing of the ingestion/normalization pipeline. Company names are invented
word-combinations (never real organizations). Skills are drawn from
`backend/data/onet_skills.csv` so NormalizationAgent's exact/fuzzy matching
has real, representative data to work against at scale.

Run:
    python backend/data/generators/generate_healthcare-it.py

Output:
    backend/data/generators/chunk_healthcare-it.csv  (600 data rows + header)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 17  # domain-specific offset for "healthcare-it"
random.seed(SEED)

OUT_PATH = Path(__file__).parent / "chunk_healthcare-it.csv"

CATEGORY = "Health Data & Bioinformatics"

# --------------------------------------------------------------------------- #
# Company pool — invented word-combinations, never real organizations.
# --------------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Lumen", "Cobalt", "Sable",
    "Meridian", "Harborlight", "Northgate", "Bluepeak", "Redwood", "Silversage",
    "Amberfield", "Clearwater", "Solace", "Brightwell", "Ashgrove", "Pinecrest",
    "Wavecrest", "Ridgeline", "Foxglove", "Halcyon", "Windmere", "Copperline",
    "Granite", "Everstone", "Palisade", "Cascadia", "Brookfield", "Larkspur",
    "Marrow", "Nightingale", "Auralis", "Basecamp", "Cortex", "Vitalis",
    "Aequus", "Beacon", "Cardialis", "Genoma", "Helio", "Iris", "Juno",
    "Kernel", "Lucid", "Medix", "Novantia", "Optum", "Pulseline", "Quill",
]
COMPANY_SUFFIXES = [
    "Cloud Labs", "Bridge Tech", "Digital", "Systems", "Health Analytics",
    "Bio Systems", "Genomics", "Clinical Data", "Health Networks",
    "Informatics", "Care Technologies", "Medical Systems", "HealthTech",
    "Diagnostics", "Data Health", "Life Sciences", "Health Solutions",
    "Care Analytics", "Wellness Systems", "Precision Health",
]

random.shuffle(COMPANY_PREFIXES)
random.shuffle(COMPANY_SUFFIXES)
COMPANIES = sorted({
    f"{p} {s}"
    for p, s in zip(
        (COMPANY_PREFIXES * 3)[:90],
        (COMPANY_SUFFIXES * 5)[:90],
    )
})
random.shuffle(COMPANIES)
COMPANIES = COMPANIES[:85]

# --------------------------------------------------------------------------- #
# Locations — major US tech/health hubs, a few international, ~25% Remote.
# --------------------------------------------------------------------------- #
LOCATIONS = [
    "Remote", "Remote", "Remote",  # weighted below via explicit draw logic
    "Boston, MA", "New York, NY", "San Francisco, CA", "Seattle, WA",
    "Austin, TX", "Chicago, IL", "Raleigh, NC", "Minneapolis, MN",
    "Nashville, TN", "Denver, CO", "Atlanta, GA", "Philadelphia, PA",
    "San Diego, CA", "Pittsburgh, PA", "Washington, DC",
    "Toronto, Canada", "London, UK", "Berlin, Germany", "Bengaluru, India",
    "Singapore", "Dublin, Ireland", "Sydney, Australia",
]

# --------------------------------------------------------------------------- #
# Skills — drawn from onet_skills.csv (Healthcare IT + Data & Machine Learning
# + a few general/tooling skills for realistic co-occurrence).
# --------------------------------------------------------------------------- #
HEALTHCARE_CORE = [
    "Electronic Health Records (EHR)", "HL7", "FHIR Standards", "Epic Systems",
    "Cerner", "Clinical Data Management", "Telehealth Systems",
    "Medical Coding (ICD-10)", "Healthcare Interoperability",
    "HIPAA Security Rule", "HIPAA Compliance", "Health Informatics",
    "Population Health Analytics",
]
DATA_ML = [
    "Python", "R", "SQL", "Statistics", "Machine Learning", "Deep Learning",
    "Data Analysis", "Data Visualization", "Pandas", "NumPy", "Scikit-learn",
    "TensorFlow", "PyTorch", "Natural Language Processing", "Tableau",
    "Power BI", "ETL Pipelines", "Data Warehousing", "Apache Spark",
    "A/B Testing",
]
ENGINEERING = [
    "Java", "C#", "REST API Design", "Microservices Architecture",
    "Docker", "Kubernetes", "Amazon Web Services", "PostgreSQL", "MySQL",
    "MongoDB", "System Design",
]
GENERAL = [
    "Git", "Communication", "Agile Methodology", "Team Leadership", "Jira",
    "Confluence", "Project Management",
]

# --------------------------------------------------------------------------- #
# Role templates: (title_base, seniority-eligible, skill_pool_weights, salary_band)
# --------------------------------------------------------------------------- #
SENIORITY_BANDS = {
    "Intern": (20000, 40000),
    "Junior": (58000, 80000),
    "Mid-level": (78000, 112000),
    "Senior": (105000, 152000),
    "Staff": (135000, 182000),
    "Lead": (132000, 178000),
    "Principal": (148000, 192000),
    "Manager": (118000, 172000),
}

ROLE_TEMPLATES = [
    # (role title without seniority, eligible seniorities, primary skill pools)
    ("Health Informatics Analyst", ["Intern", "Junior", "Mid-level", "Senior"], (HEALTHCARE_CORE, DATA_ML)),
    ("Clinical Data Analyst", ["Intern", "Junior", "Mid-level", "Senior", "Lead"], (HEALTHCARE_CORE, DATA_ML)),
    ("Bioinformatics Scientist", ["Junior", "Mid-level", "Senior", "Staff", "Principal"], (DATA_ML, HEALTHCARE_CORE)),
    ("Bioinformatics Engineer", ["Junior", "Mid-level", "Senior", "Lead", "Staff"], (DATA_ML, ENGINEERING)),
    ("Health Data Engineer", ["Junior", "Mid-level", "Senior", "Lead", "Staff"], (DATA_ML, ENGINEERING)),
    ("Healthcare Software Engineer", ["Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"], (ENGINEERING, HEALTHCARE_CORE)),
    ("EHR Systems Analyst", ["Junior", "Mid-level", "Senior"], (HEALTHCARE_CORE, ENGINEERING)),
    ("EHR Integration Engineer", ["Mid-level", "Senior", "Lead", "Staff"], (HEALTHCARE_CORE, ENGINEERING)),
    ("Clinical Systems Engineer", ["Mid-level", "Senior", "Lead", "Staff"], (HEALTHCARE_CORE, ENGINEERING)),
    ("Health Data Scientist", ["Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"], (DATA_ML, HEALTHCARE_CORE)),
    ("Population Health Analyst", ["Intern", "Junior", "Mid-level", "Senior"], (HEALTHCARE_CORE, DATA_ML)),
    ("Healthcare Interoperability Engineer", ["Mid-level", "Senior", "Lead", "Staff", "Principal"], (HEALTHCARE_CORE, ENGINEERING)),
    ("Medical Coding Data Specialist", ["Junior", "Mid-level", "Senior"], (HEALTHCARE_CORE, DATA_ML)),
    ("Telehealth Platform Engineer", ["Junior", "Mid-level", "Senior", "Lead", "Staff"], (HEALTHCARE_CORE, ENGINEERING)),
    ("Health IT Project Manager", ["Mid-level", "Senior", "Manager"], (HEALTHCARE_CORE, GENERAL)),
    ("Clinical Data Management Lead", ["Senior", "Lead", "Manager"], (HEALTHCARE_CORE, DATA_ML)),
    ("Genomics Data Analyst", ["Intern", "Junior", "Mid-level", "Senior"], (DATA_ML, HEALTHCARE_CORE)),
    ("HIPAA Compliance Engineer", ["Mid-level", "Senior", "Lead", "Staff"], (HEALTHCARE_CORE, ENGINEERING)),
    ("Health Analytics Manager", ["Manager", "Senior", "Lead"], (DATA_ML, HEALTHCARE_CORE)),
    ("Director of Health Informatics", ["Principal", "Manager", "Lead"], (HEALTHCARE_CORE, DATA_ML)),
]

JOB_TYPES_WEIGHTED = (
    ["Full-time"] * 65 + ["Internship"] * 15 + ["Contract"] * 10 + ["Part-time"] * 10
)


def pick_seniority(role):
    _, eligible, _ = role
    return random.choice(eligible)


def build_title(role_name: str, seniority: str) -> str:
    if seniority == "Mid-level":
        return f"Mid-level {role_name}"
    if seniority == "Manager":
        # Avoid double "Manager Manager"-style titles.
        if "Manager" in role_name or "Director" in role_name:
            return role_name
        return f"{role_name} Manager"
    return f"{seniority} {role_name}"


def pick_skills(role) -> list[str]:
    _, _, (primary_pool, secondary_pool) = role
    n_primary = random.randint(2, 5)
    n_secondary = random.randint(1, 3)
    primary = random.sample(primary_pool, k=min(n_primary, len(primary_pool)))
    secondary = random.sample(secondary_pool, k=min(n_secondary, len(secondary_pool)))
    skills = primary + secondary
    # occasionally add exactly one general skill (Git, Communication, Agile, etc.)
    if random.random() < 0.55:
        skills.append(random.choice(GENERAL))
    # de-dup preserving order, clamp to 3-8
    seen = set()
    deduped = []
    for s in skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            deduped.append(s)
    if len(deduped) > 8:
        deduped = deduped[:8]
    while len(deduped) < 3:
        candidate = random.choice(primary_pool)
        if candidate.lower() not in seen:
            seen.add(candidate.lower())
            deduped.append(candidate)
    return deduped


def pick_location() -> str:
    if random.random() < 0.25:
        return "Remote"
    non_remote = [loc for loc in LOCATIONS if loc != "Remote"]
    return random.choice(non_remote)


def salary_for(seniority: str) -> tuple[int, int]:
    lo, hi = SENIORITY_BANDS[seniority]
    salary_min = random.randint(lo, hi - 5000)
    salary_max = random.randint(salary_min + 3000, hi)
    return salary_min, salary_max


def messify_skill(skill: str) -> str:
    """Return a messy variant of a skill string (typo / casing / whitespace /
    abbreviation) to give NormalizationAgent's fuzzy matching real signal."""
    choice = random.random()
    if choice < 0.25:
        return f" {skill} "  # extra whitespace
    if choice < 0.5:
        return skill.upper() if random.random() < 0.5 else skill.lower()
    if choice < 0.7:
        # crude typo: drop a vowel or swap letters near the middle
        if len(skill) > 4:
            idx = len(skill) // 2
            return skill[:idx] + skill[idx + 1:]
        return skill
    # abbreviation-style shortenings for a few known long names
    abbrev_map = {
        "Electronic Health Records (EHR)": "EHR",
        "Machine Learning": "ML",
        "Natural Language Processing": "NLP",
        "Amazon Web Services": "AWS",
        "Agile Methodology": "Agile",
        "HIPAA Compliance": "HIPAA",
        "HIPAA Security Rule": "HIPAA",
        "Medical Coding (ICD-10)": "ICD-10",
    }
    return abbrev_map.get(skill, skill)


def maybe_messify_row(skills: list[str]) -> list[str]:
    if random.random() >= 0.065:  # 6.5% messy rows target within 5-8% range
        return skills
    messy = list(skills)
    idx = random.randrange(len(messy))
    messy[idx] = messify_skill(messy[idx])
    # occasionally duplicate a skill with different casing too (extra messiness)
    if random.random() < 0.3 and len(messy) < 8:
        dup_idx = random.randrange(len(messy))
        messy.append(messy[dup_idx].upper())
    return messy


def generate_rows(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        role = random.choice(ROLE_TEMPLATES)
        seniority = pick_seniority(role)
        title = build_title(role[0], seniority)
        company = random.choice(COMPANIES)
        location = pick_location()
        job_type = random.choice(JOB_TYPES_WEIGHTED)
        skills = pick_skills(role)
        skills = maybe_messify_row(skills)
        salary_min, salary_max = salary_for(seniority)
        rows.append({
            "title": title,
            "company": company,
            "location": location,
            "type": job_type,
            "skills_required": ", ".join(skills),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": CATEGORY,
        })
    return rows


def main():
    rows = generate_rows(600)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title", "company", "location", "type", "skills_required",
                "salary_min", "salary_max", "category",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
