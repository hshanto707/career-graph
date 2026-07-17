"""Synthetic job-posting generator: Product Management / UX-UI Design domain.

Generates EXACTLY 800 rows into chunk_product-design.csv, matching the
schema used by IngestionAgent / NormalizationAgent:
    title,company,location,type,skills_required,salary_min,salary_max,category

Fixed seed (42 + domain offset) for reproducibility. Skills are drawn from
onet_skills.csv (the shared taxonomy) so NormalizationAgent's exact/fuzzy
matching has real signal. ~5-8% of rows get a deliberate messiness
injection (typo, casing, whitespace, abbreviation) to exercise the fuzzy
matcher; the rest are clean.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

DOMAIN_SEED_OFFSET = 7  # "product-design" domain offset
SEED = 42 + DOMAIN_SEED_OFFSET
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = Path(__file__).resolve().parent / "chunk_product-design.csv"

NUM_ROWS = 800

VALID_TYPES = ["Full-time", "Part-time", "Internship", "Contract"]
TYPE_WEIGHTS = [0.65, 0.10, 0.15, 0.10]

# ---------------------------------------------------------------------- #
# Role families: (title base, seniority tiers applicable, category, skill pool)
# ---------------------------------------------------------------------- #

PM_TITLES = [
    "Product Manager",
    "Product Owner",
    "Technical Product Manager",
    "Associate Product Manager",
    "Growth Product Manager",
    "Platform Product Manager",
    "Product Analyst",
]

UX_TITLES = [
    "UX Designer",
    "UI Designer",
    "Product Designer",
    "UX Researcher",
    "Interaction Designer",
    "Visual Designer",
    "UX/UI Designer",
]

SENIORITY_BY_FAMILY = {
    "pm": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Principal", "Manager"],
    "ux": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
}

# Salary ranges (min_low, min_high, max_low, max_high) per seniority tier, USD/yr.
SALARY_BANDS = {
    "Intern": (22000, 30000, 34000, 42000),
    "Junior": (56000, 66000, 72000, 84000),
    "Mid-level": (78000, 92000, 98000, 114000),
    "Senior": (105000, 122000, 130000, 155000),
    "Lead": (132000, 148000, 156000, 178000),
    "Staff": (138000, 152000, 160000, 182000),
    "Principal": (145000, 160000, 168000, 192000),
    "Manager": (115000, 132000, 140000, 168000),
}

PM_SKILLS = [
    "Product Management",
    "Roadmap Planning",
    "Stakeholder Management",
    "Requirements Gathering",
    "Agile Methodology",
    "Scrum",
    "Kanban",
    "Jira",
    "OKRs",
    "Feature Prioritization",
    "Competitive Analysis",
    "Product Discovery",
    "User Story Mapping",
    "A/B Test Design",
    "Data-Driven Decision Making",
    "Market Research",
    "Business Analysis",
    "KPI Development",
    "Customer Journey Mapping",
    "SAFe (Scaled Agile Framework)",
]

UX_SKILLS = [
    "UI Design",
    "UX Research",
    "Figma",
    "Adobe Photoshop",
    "Adobe Illustrator",
    "Wireframing",
    "Prototyping",
    "Design Systems",
    "Sketch",
    "User Research",
    "Usability Testing",
    "Information Architecture",
    "Interaction Design",
    "Persona Development",
    "Design Thinking",
    "Figma Prototyping",
    "Miro",
    "Adobe XD",
    "InVision",
    "Motion Design",
    "Design Critique Facilitation",
    "Accessibility Design",
    "Accessibility (WCAG)",
    "Responsive Design",
]

GENERAL_SKILLS = [
    "Communication",
    "Agile Methodology",
    "Git",
    "Confluence",
    "Stakeholder Management",
    "Interpersonal Skills",
    "Excel",
]

# Skills that only make sense at higher-seniority PM/design leadership roles.
LEADERSHIP_SKILLS = ["Stakeholder Management", "Roadmap Planning", "OKRs", "Vendor Management"]

FICTIONAL_COMPANIES = [
    "Vertex Cloud Labs", "Onyx Bridge Tech", "Crestline Digital", "Ironwood Systems",
    "Bramblewood Studio", "Nova Harbor Design", "Slate Fox Product", "Cobalt Reach Labs",
    "Amberline Ventures", "Fernwave Collective", "Granite Loop Studio", "Wispcraft UX",
    "Halcyon Grid Labs", "Thistle & Vane Design", "Quartzline Product Co", "Marrow Peak Tech",
    "Lucent Path Studio", "Driftwood UX Lab", "Cinderhall Digital", "Meridian Crest Product",
    "Palewind Interactive", "Rustling Oak Studio", "Sable Ridge Labs", "Cobblestone UX Co",
    "Brightloom Product", "Kestrel Bay Design", "Northfall Interactive", "Pinecrest Digital",
    "Emberline Studio", "Foxglove Product Co", "Wanderlight Labs", "Hollowreed Design",
    "Sterling Vale Tech", "Cloverfield UX Studio", "Aldergate Product", "Thornbury Digital",
    "Mistwood Labs", "Silverbrook Design", "Copperfield UX", "Larkspur Product Co",
    "Windmere Studio", "Fieldstone Digital Labs", "Ashgrove Product", "Bluepeak UX Studio",
    "Redshale Design", "Glimmerwell Labs", "Timberlyn Product Co", "Duskridge Digital",
    "Harborlight UX", "Moonfern Studio", "Cragmoor Product", "Vellum Path Design",
    "Alderwood Labs", "Sunspire Digital", "Wrenfield UX Co", "Basalt Grove Product",
    "Everline Studio", "Frostvale Design Labs", "Marlowe Bridge Product", "Nightshade UX",
    "Rowancroft Digital", "Gladewind Labs", "Ashenfall Product Co", "Brightfern Studio",
    "Copperhaven UX", "Ironvale Product", "Willowmere Digital", "Sagebrush Labs",
    "Clearwater UX Studio", "Stonebridge Product Co", "Hazelwick Design", "Ravenmoor Labs",
    "Goldleaf Product Studio", "Duneshore Digital", "Pinehollow UX", "Cedarfall Product Co",
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Boston, MA",
    "Chicago, IL", "Denver, CO", "Los Angeles, CA", "Atlanta, GA", "Portland, OR",
    "Toronto, Canada", "London, UK", "Berlin, Germany", "Amsterdam, Netherlands",
    "Singapore", "Sydney, Australia", "Dublin, Ireland", "Bangalore, India",
    "Remote",
]
# Remote should hit ~25% overall — weight accordingly below.

MESSY_RATE = 0.065  # ~6.5% of rows get an injected typo/formatting issue

TYPO_MAP = {
    "Figma": "Fgima",
    "Communication": "Comunication",
    "Prototyping": "Prototypeing",
    "Wireframing": "Wireframeing",
    "Agile Methodology": "Agile Methodolgy",
    "Stakeholder Management": "Stakholder Management",
    "Usability Testing": "Usabilty Testing",
}
ABBREV_MAP = {
    "User Experience Research": "UX Research",
    "Agile Methodology": "Agile",
    "User Interface Design": "UI Design",
    "Product Management": "PM",
    "Key Performance Indicators": "KPI",
}


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def pick_location() -> str:
    # ~25% Remote, remainder split across the other cities.
    if random.random() < 0.25:
        return "Remote"
    return random.choice([loc for loc in LOCATIONS if loc != "Remote"])


def messify(skill: str) -> str:
    """Apply one of a few realistic messiness transforms to a skill string."""
    choice = random.random()
    if skill in TYPO_MAP and choice < 0.35:
        return TYPO_MAP[skill]
    if choice < 0.55:
        return skill.upper()
    if choice < 0.75:
        return skill.lower()
    if choice < 0.9:
        return f" {skill} "
    if skill in ABBREV_MAP.values():
        return skill
    for full, abbrev in ABBREV_MAP.items():
        if skill == full:
            return abbrev
    return f"  {skill}"


def build_title(family: str, seniority: str) -> str:
    base = random.choice(PM_TITLES if family == "pm" else UX_TITLES)
    if seniority == "Manager":
        # "Manager" reads oddly prefixed to some titles; use suffix style.
        return f"{base} Manager" if "Manager" not in base else base
    if seniority in ("Mid-level",):
        return base  # mid-level often has no explicit prefix
    return f"{seniority} {base}"


def pick_skills(family: str, seniority: str) -> list[str]:
    pool = PM_SKILLS if family == "pm" else UX_SKILLS
    n = random.randint(3, 8)
    n = min(n, len(pool))
    chosen = random.sample(pool, n)

    # Leadership-flavored skills more likely at senior+ tiers.
    if seniority in ("Senior", "Lead", "Staff", "Principal", "Manager"):
        if random.random() < 0.5:
            extra = random.choice(LEADERSHIP_SKILLS)
            if extra not in chosen:
                chosen.append(extra)

    # Occasionally add one general skill.
    if random.random() < 0.4:
        gen = random.choice(GENERAL_SKILLS)
        if gen not in chosen:
            chosen.append(gen)

    return chosen


def salary_for(seniority: str) -> tuple[int, int]:
    lo_lo, lo_hi, hi_lo, hi_hi = SALARY_BANDS[seniority]
    salary_min = random.randint(lo_lo, lo_hi)
    salary_max = random.randint(max(hi_lo, salary_min + 3000), hi_hi)
    return salary_min, salary_max


def build_row() -> dict:
    family = random.choice(["pm", "ux"])
    seniority = random.choice(SENIORITY_BY_FAMILY[family])
    title = build_title(family, seniority)
    company = random.choice(FICTIONAL_COMPANIES)
    location = pick_location()
    job_type = weighted_choice(VALID_TYPES, TYPE_WEIGHTS)
    # Interns should skew toward Internship type realistically, but keep it
    # probabilistic (not absolute) for variety.
    if seniority == "Intern" and random.random() < 0.7:
        job_type = "Internship"

    skills = pick_skills(family, seniority)

    is_messy_row = random.random() < MESSY_RATE
    if is_messy_row:
        num_messed = random.randint(1, min(2, len(skills)))
        idxs = random.sample(range(len(skills)), num_messed)
        for i in idxs:
            skills[i] = messify(skills[i])
        # Occasionally duplicate a skill with different casing (extra signal).
        if random.random() < 0.3:
            dup = random.choice(skills)
            skills.append(dup.upper() if dup.islower() else dup.lower())

    salary_min, salary_max = salary_for(seniority)
    category = "Product" if family == "pm" else "Design"

    return {
        "title": title,
        "company": company,
        "location": location,
        "type": job_type,
        "skills_required": ", ".join(skills),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "category": category,
    }


def main() -> None:
    rows = [build_row() for _ in range(NUM_ROWS)]
    fieldnames = ["title", "company", "location", "type", "skills_required", "salary_min", "salary_max", "category"]
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
