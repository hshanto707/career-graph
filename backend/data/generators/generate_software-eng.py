"""Generator for the "Software Engineering" domain chunk of the synthetic
job dataset (backend/frontend/fullstack/mobile roles).

Produces EXACTLY 1500 rows matching the schema of backend/data/kaggle_jobs.csv:
    title,company,location,type,skills_required,salary_min,salary_max,category

Reproducible via a fixed seed (42 + domain offset). Run directly:
    python generate_software-eng.py
Writes to chunk_software-eng.csv in the same directory.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 7  # domain-specific offset for "software-eng"
random.seed(SEED)

OUT_PATH = Path(__file__).parent / "chunk_software-eng.csv"
TARGET_ROWS = 1500
CATEGORY = "Software Engineering"

# --------------------------------------------------------------------- #
# Fictional companies (invented word-combinations, never real orgs)
# --------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Northwind", "Pinecrest",
    "Harborline", "Skyline", "Bluepeak", "Nova", "Meridian", "Redwood",
    "Cobalt", "Amber", "Solstice", "Lattice", "Granite", "Fernwood",
    "Coral", "Timberline", "Cinderfall", "Silverbrook", "Emberfield",
    "Quartzline", "Driftwood", "Copperbend", "Slatestone", "Foxglove",
    "Marrow", "Windemere", "Brightbay", "Cascadia", "Thistledown",
    "Hollowreach", "Ashgrove", "Palisade", "Wrenfield", "Basalt",
    "Gullhaven", "Tidefall",
]
COMPANY_SUFFIXES = [
    "Cloud Labs", "Bridge Tech", "Digital", "Systems", "Ventures IT",
    "Software", "Field Labs", "Apps", "Data Systems", "Robotics Group",
    "Path Studios", "Data Co", "Works", "Peak Tech", "Interactive",
    "Reef Software", "Analytics", "Technologies", "Dynamics", "Networks",
    "Foundry", "Collective", "Systems Group", "Innovations", "Solutions",
    "Studio", "Platforms", "Forge", "Labs",
]


def _build_company_pool(n: int) -> list[str]:
    seen: set[str] = set()
    pool: list[str] = []
    prefixes = COMPANY_PREFIXES[:]
    suffixes = COMPANY_SUFFIXES[:]
    random.shuffle(prefixes)
    random.shuffle(suffixes)
    idx_p, idx_s = 0, 0
    while len(pool) < n:
        p = prefixes[idx_p % len(prefixes)]
        s = suffixes[idx_s % len(suffixes)]
        name = f"{p} {s}"
        idx_p += 1
        if idx_p % len(prefixes) == 0:
            idx_s += 1
        if name not in seen:
            seen.add(name)
            pool.append(name)
    return pool


COMPANIES = _build_company_pool(85)

# --------------------------------------------------------------------- #
# Locations
# --------------------------------------------------------------------- #
US_HUBS = [
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
    "Boston, MA", "Denver, CO", "Atlanta, GA",
    "Chicago, IL", "Los Angeles, CA", "Raleigh, NC", "Portland, OR",
    "Washington, DC",
]
INTL_HUBS = [
    "Toronto, ON", "London, UK", "Berlin, Germany", "Bengaluru, India",
    "Dublin, Ireland", "Singapore", "Sydney, Australia", "Amsterdam, Netherlands",
]
REMOTE = "Remote"

LOCATION_WEIGHTS = (
    [(loc, 5) for loc in US_HUBS]
    + [(loc, 2) for loc in INTL_HUBS]
    + [(REMOTE, 20)]
)
_LOC_POOL = [loc for loc, w in LOCATION_WEIGHTS for _ in range(w)]


def pick_location() -> str:
    return random.choice(_LOC_POOL)


# --------------------------------------------------------------------- #
# Job types (~65% Full-time, ~10% Part-time, ~15% Internship, ~10% Contract)
# --------------------------------------------------------------------- #
_TYPE_POOL = (
    ["Full-time"] * 65 + ["Part-time"] * 10 + ["Internship"] * 15 + ["Contract"] * 10
)


_NON_INTERN_TYPE_POOL = ["Full-time"] * 72 + ["Part-time"] * 12 + ["Contract"] * 16


def pick_type(seniority: str) -> str:
    if seniority == "Intern":
        return "Internship"
    if seniority in ("Manager", "Principal", "Staff", "Lead"):
        # senior-most roles basically never internships/part-time
        pool = ["Full-time"] * 85 + ["Contract"] * 15
        return random.choice(pool)
    return random.choice(_NON_INTERN_TYPE_POOL)


# --------------------------------------------------------------------- #
# Roles: (role_name, base_title, applicable seniorities, skill_pool_key)
# --------------------------------------------------------------------- #
SENIORITY_ORDER = [
    "Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal", "Manager",
]

ROLES = [
    ("backend", "Backend Developer"),
    ("backend", "Backend Engineer"),
    ("frontend", "Frontend Developer"),
    ("frontend", "Frontend Engineer"),
    ("fullstack", "Full Stack Developer"),
    ("fullstack", "Full Stack Engineer"),
    ("generic", "Software Engineer"),
    ("generic", "Software Developer"),
    ("mobile_ios", "Mobile Developer (iOS)"),
    ("mobile_ios", "iOS Engineer"),
    ("mobile_android", "Mobile Developer (Android)"),
    ("mobile_android", "Android Engineer"),
    ("mobile_cross", "Mobile Engineer"),
]

# Title formatting per seniority
def format_title(seniority: str, base_title: str) -> str:
    if seniority == "Mid-level":
        return base_title
    if seniority == "Manager":
        # e.g. "Engineering Manager" instead of "Manager Software Engineer"
        if "Mobile" in base_title or "iOS" in base_title or "Android" in base_title:
            return f"Engineering Manager, Mobile"
        if "Frontend" in base_title:
            return "Engineering Manager, Frontend"
        if "Backend" in base_title:
            return "Engineering Manager, Backend"
        return "Engineering Manager"
    return f"{seniority} {base_title}"


# --------------------------------------------------------------------- #
# Skill pools (drawn from onet_skills.csv canonical names), by role family
# --------------------------------------------------------------------- #
GENERAL_SKILLS = [
    "Git", "Communication", "Agile Methodology", "Problem Solving",
    "Code Review Practices", "Team Leadership", "Scrum", "Mentoring",
    "Continuous Integration", "Technical Writing",
]

BACKEND_SKILLS = [
    "Python", "Java", "Go", "Node.js", "C#", "Ruby", "Kotlin",
    "Django", "Flask", "FastAPI", "Spring Boot", "Express.js", "NestJS",
    "Ruby on Rails", "ASP.NET",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "DynamoDB", "Cassandra",
    "REST API Design", "GraphQL", "gRPC", "Microservices Architecture",
    "System Design", "Distributed Systems", "Event-Driven Architecture",
    "Message Queues (RabbitMQ)", "Caching Strategies", "Docker",
    "Kubernetes", "Amazon Web Services", "Microsoft Azure",
    "Google Cloud Platform", "CI/CD Pipelines",
]

FRONTEND_SKILLS = [
    "JavaScript", "TypeScript", "React", "Vue.js", "Angular", "Next.js",
    "Svelte", "HTML", "CSS", "Sass", "Tailwind CSS", "Bootstrap",
    "Redux", "Webpack", "Vite", "jQuery", "Responsive Design",
    "Cross-browser Compatibility", "Accessibility (WCAG)", "Storybook",
    "Figma", "GraphQL Client (Apollo)", "Progressive Web Apps",
    "Material UI", "Jest",
]

FULLSTACK_SKILLS = list(dict.fromkeys(BACKEND_SKILLS + FRONTEND_SKILLS))

MOBILE_IOS_SKILLS = [
    "Swift", "SwiftUI", "iOS Development", "Xcode", "Objective-C",
    "Mobile App Architecture", "Mobile CI/CD", "App Store Optimization",
    "Push Notifications", "Mobile Performance Optimization", "REST API Design",
]

MOBILE_ANDROID_SKILLS = [
    "Kotlin", "Jetpack Compose", "Android Development", "Android Studio",
    "Mobile App Architecture", "Mobile CI/CD", "App Store Optimization",
    "Push Notifications", "Mobile Performance Optimization", "REST API Design",
]

MOBILE_CROSS_SKILLS = [
    "React Native", "Flutter", "Dart", "Kotlin Multiplatform",
    "Cross-platform Development", "Mobile App Architecture",
    "Mobile CI/CD", "Mobile Performance Optimization", "REST API Design",
]

SENIOR_ONLY_SKILLS = [
    "System Design", "Distributed Systems", "Team Leadership", "Mentoring",
    "Domain-Driven Design", "Hexagonal Architecture", "Load Balancing",
]

SKILL_POOLS = {
    "backend": BACKEND_SKILLS,
    "frontend": FRONTEND_SKILLS,
    "fullstack": FULLSTACK_SKILLS,
    "generic": FULLSTACK_SKILLS,
    "mobile_ios": MOBILE_IOS_SKILLS,
    "mobile_android": MOBILE_ANDROID_SKILLS,
    "mobile_cross": MOBILE_CROSS_SKILLS,
}


def pick_skills(role_key: str, seniority: str) -> list[str]:
    pool = SKILL_POOLS[role_key]
    n = random.randint(3, 8)
    n_general = 1 if random.random() < 0.35 else 0
    n_core = max(2, n - n_general)

    core_pool = pool[:]
    if seniority in ("Senior", "Lead", "Staff", "Principal", "Manager"):
        # weight in some senior-flavored skills without excluding core skills
        core_pool = list(dict.fromkeys(pool + random.sample(
            SENIOR_ONLY_SKILLS, k=min(2, len(SENIOR_ONLY_SKILLS))
        )))

    n_core = min(n_core, len(core_pool))
    chosen = random.sample(core_pool, k=n_core)

    if n_general:
        chosen.append(random.choice(GENERAL_SKILLS))

    random.shuffle(chosen)
    return chosen


# --------------------------------------------------------------------- #
# Salary ranges by seniority (USD annual), with mild role-based nudge
# --------------------------------------------------------------------- #
SALARY_BANDS = {
    "Intern": (20000, 40000),
    "Junior": (55000, 80000),
    "Mid-level": (75000, 110000),
    "Senior": (100000, 150000),
    "Lead": (130000, 175000),
    "Staff": (140000, 185000),
    "Principal": (150000, 190000),
    "Manager": (120000, 170000),
}

# Seniority mix weighting (fewer principal/manager postings than mid/senior)
SENIORITY_WEIGHTS = {
    "Intern": 14,
    "Junior": 16,
    "Mid-level": 23,
    "Senior": 20,
    "Lead": 9,
    "Staff": 8,
    "Principal": 5,
    "Manager": 5,
}
_SENIORITY_POOL = [s for s, w in SENIORITY_WEIGHTS.items() for _ in range(w)]


def pick_seniority() -> str:
    return random.choice(_SENIORITY_POOL)


def pick_salary(seniority: str) -> tuple[int, int]:
    lo, hi = SALARY_BANDS[seniority]
    # Random sub-window within the band, mimicking real listing variance.
    band_width = hi - lo
    window = random.randint(int(band_width * 0.35), band_width)
    start = random.randint(lo, hi - window) if hi - window > lo else lo
    salary_min = start
    salary_max = start + window
    # Internships occasionally quoted as a stipend total, already in-band.
    return salary_min, salary_max


# --------------------------------------------------------------------- #
# Messiness injection (~5-8% of rows)
# --------------------------------------------------------------------- #
TYPO_MAP = {
    "JavaScript": "Javascrpt",
    "Python": "Pyhton",
    "Kubernetes": "Kuberentes",
    "PostgreSQL": "Postgresql",
    "TypeScript": "Typescrpt",
}
ABBREV_MAP = {
    "JavaScript": "JS",
    "Python": "Py",
    "Amazon Web Services": "AWS",
    "Google Cloud Platform": "GCP",
    "Microsoft Azure": "Azure",
    "Kubernetes": "K8s",
    "Continuous Integration": "CI",
    "PostgreSQL": "Postgres",
    "TypeScript": "TS",
}


def messify_skill(skill: str) -> str:
    choice = random.random()
    if choice < 0.30 and skill in TYPO_MAP:
        return TYPO_MAP[skill]
    if choice < 0.60 and skill in ABBREV_MAP:
        return ABBREV_MAP[skill]
    if choice < 0.80:
        return skill.upper() if random.random() < 0.5 else skill.lower()
    # extra whitespace
    return f" {skill} "


def maybe_messify_row(skills: list[str]) -> list[str]:
    if not skills:
        return skills
    messy = skills[:]
    idx = random.randrange(len(messy))
    messy[idx] = messify_skill(messy[idx])
    # occasionally duplicate a skill (common real-world messiness)
    if random.random() < 0.25:
        dup_idx = random.randrange(len(messy))
        messy.append(messy[dup_idx])
    return messy


# --------------------------------------------------------------------- #
# Row generation
# --------------------------------------------------------------------- #
def generate_rows(n: int) -> list[dict]:
    rows: list[dict] = []
    for _ in range(n):
        role_key, base_title = random.choice(ROLES)
        seniority = pick_seniority()

        # Interns never get "Manager"/"Principal" style titles; skip mismatches
        if seniority == "Manager" and role_key.startswith("mobile"):
            # still fine ("Engineering Manager, Mobile") — no skip needed
            pass

        title = format_title(seniority, base_title)
        company = random.choice(COMPANIES)
        location = pick_location()
        job_type = pick_type(seniority)
        skills = pick_skills(role_key, seniority)
        salary_min, salary_max = pick_salary(seniority)

        is_messy = random.random() < 0.065  # ~6.5% messy rows
        if is_messy:
            skills = maybe_messify_row(skills)

        skills_str = ", ".join(skills)

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "type": job_type,
                "skills_required": skills_str,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "category": CATEGORY,
            }
        )
    return rows


def main() -> None:
    rows = generate_rows(TARGET_ROWS)
    fieldnames = [
        "title", "company", "location", "type", "skills_required",
        "salary_min", "salary_max", "category",
    ]
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
