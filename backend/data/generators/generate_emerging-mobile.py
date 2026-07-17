"""Synthetic job-posting generator: Blockchain/Web3, AR/VR, Robotics,
Embedded, Mobile Dev domain chunk.

Produces EXACTLY 700 rows matching the kaggle_jobs.csv fixture schema:
    title,company,location,type,skills_required,salary_min,salary_max,category

Reproducible via a fixed seed (42 + a domain-specific offset). Not a
real dataset — all company names are invented word-combinations.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 17  # domain-specific offset for "emerging-mobile"
random.seed(SEED)

OUT_PATH = Path(__file__).parent / "chunk_emerging-mobile.csv"

ROW_COUNT = 700

# --------------------------------------------------------------------- #
# Sub-domains and their role/title pools
# --------------------------------------------------------------------- #
SUBDOMAINS = {
    "blockchain": {
        "titles": [
            "Blockchain Engineer",
            "Blockchain Developer",
            "Smart Contract Engineer",
            "Web3 Developer",
            "Solidity Developer",
            "DeFi Protocol Engineer",
            "Crypto Backend Engineer",
            "Blockchain Architect",
        ],
        "skills": [
            "Blockchain Development", "Smart Contracts", "Solidity", "Ethereum",
            "Web3", "Cryptocurrency Systems", "Decentralized Finance (DeFi)",
            "Distributed Ledger Technology", "Hyperledger Fabric", "NFT Platforms",
            "Cryptography", "Rust", "Go", "Node.js", "TypeScript",
        ],
        "category": "Software Engineering",
    },
    "arvr": {
        "titles": [
            "AR/VR Engineer",
            "Augmented Reality Developer",
            "Virtual Reality Developer",
            "XR Software Engineer",
            "3D Graphics Engineer",
            "Immersive Experience Engineer",
            "Spatial Computing Engineer",
        ],
        "skills": [
            "Augmented Reality Development", "Virtual Reality Development",
            "C++", "C#", "Computer Vision", "3D Graphics",
            "Unity", "Unreal Engine", "Machine Learning", "Sensor Integration",
            "Python", "Data Visualization",
        ],
        "category": "Software Engineering",
    },
    "robotics": {
        "titles": [
            "Robotics Engineer",
            "Robotics Software Engineer",
            "Autonomous Systems Engineer",
            "Robotics Perception Engineer",
            "Motion Control Engineer",
            "Robotics Controls Engineer",
        ],
        "skills": [
            "Robotics Programming", "Sensor Integration", "C++", "Python",
            "Computer Vision", "Machine Learning", "Embedded C",
            "Microcontroller Programming", "RTOS (Real-Time Operating Systems)",
            "PCB Design", "MATLAB", "Reinforcement Learning",
        ],
        "category": "Software Engineering",
    },
    "embedded": {
        "titles": [
            "Embedded Software Engineer",
            "Firmware Engineer",
            "Embedded Systems Engineer",
            "Hardware/Firmware Engineer",
            "IoT Firmware Engineer",
            "FPGA Engineer",
        ],
        "skills": [
            "Embedded C", "Microcontroller Programming", "FPGA Design",
            "RTOS (Real-Time Operating Systems)", "PCB Design", "Arduino",
            "Raspberry Pi Development", "VHDL", "SPI/I2C Protocols",
            "Firmware Development", "C++", "IoT Systems Design",
        ],
        "category": "DevOps & Infrastructure",
    },
    "mobile": {
        "titles": [
            "Mobile Developer",
            "iOS Developer",
            "Android Developer",
            "React Native Developer",
            "Flutter Developer",
            "Mobile Software Engineer",
            "Cross-platform Mobile Engineer",
        ],
        "skills": [
            "iOS Development", "Android Development", "React Native", "Flutter",
            "SwiftUI", "Jetpack Compose", "Swift", "Kotlin", "Dart",
            "Xcode", "Android Studio", "Cross-platform Development",
            "Mobile App Architecture", "Mobile Performance Optimization",
            "Mobile Testing", "Push Notifications", "In-app Purchases",
            "Kotlin Multiplatform", "App Store Optimization", "Mobile CI/CD",
            "Ionic", "Xamarin", "Cordova", "Objective-C for iOS",
        ],
        "category": "Software Engineering",
    },
}

GENERAL_SKILLS = [
    "Git", "Communication", "Agile Methodology", "CI/CD Pipelines",
    "Docker", "System Design", "Jira", "Cross-functional Collaboration",
    "Stakeholder Management", "Requirements Gathering",
]

SENIORITIES = [
    ("Intern", 0.10),
    ("Junior", 0.16),
    ("Mid-level", 0.26),
    ("Senior", 0.26),
    ("Lead", 0.09),
    ("Staff", 0.05),
    ("Principal", 0.04),
    ("Manager", 0.04),
]

SALARY_RANGES = {
    "Intern": (24000, 42000),
    "Junior": (58000, 85000),
    "Mid-level": (80000, 115000),
    "Senior": (108000, 158000),
    "Lead": (135000, 185000),
    "Staff": (140000, 190000),
    "Principal": (150000, 200000),
    "Manager": (115000, 172000),
}

LOCATIONS = [
    ("Remote", 0.25),
    ("San Francisco, CA", 0.09),
    ("New York, NY", 0.09),
    ("Austin, TX", 0.07),
    ("Seattle, WA", 0.06),
    ("Boston, MA", 0.06),
    ("Denver, CO", 0.05),
    ("Chicago, IL", 0.05),
    ("Atlanta, GA", 0.04),
    ("Toronto, ON", 0.05),
    ("London, UK", 0.05),
    ("Berlin, Germany", 0.04),
    ("Singapore", 0.04),
    ("Bangalore, India", 0.04),
    ("Tel Aviv, Israel", 0.03),
    ("Sydney, Australia", 0.03),
]

JOB_TYPES = [
    ("Full-time", 0.65),
    ("Internship", 0.15),
    ("Part-time", 0.10),
    ("Contract", 0.10),
]

# --------------------------------------------------------------------- #
# Fictional company name pool (~90 unique, invented word-combinations)
# --------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Nimbus", "Quantum", "Halcyon",
    "Fenix", "Brightloop", "Cobalt", "Lattice", "Summit", "Driftwood", "Aurora",
    "Zenith", "Pinnacle", "Meridian", "Catalyst", "Solace", "Wraith", "Emberline",
    "Nova", "Copperfield", "Ridgeback", "Starforge", "Basalt", "Silverline",
    "Grayline", "Cascade", "Northgate", "Foxglove", "Amberlight", "Voxel",
    "Cypher", "Ledgerly", "Chainforge", "Protoform", "Circuitry", "Skyline",
    "Bluefin", "Redshift", "Glasswing", "Hollow", "Frostbyte", "Pixelforge",
    "Vantage", "Keystone", "Slate", "Bramblewood", "Thornfield", "Wildcore",
]
COMPANY_SUFFIXES = [
    "Cloud Labs", "Bridge Tech", "Digital", "Systems", "Robotics", "Dynamics",
    "Networks", "Interactive", "Studios", "Forge", "Works", "Technologies",
    "Innovations", "Collective", "Solutions", "Ventures", "Foundry", "Group",
    "Industries", "Software", "Mechatronics", "Labs",
]


def build_company_pool(rng: random.Random, n: int) -> list[str]:
    seen = set()
    companies = []
    while len(companies) < n:
        name = f"{rng.choice(COMPANY_PREFIXES)} {rng.choice(COMPANY_SUFFIXES)}"
        if name not in seen:
            seen.add(name)
            companies.append(name)
    return companies


def weighted_choice(rng: random.Random, options: list[tuple[str, float]]) -> str:
    labels = [o[0] for o in options]
    weights = [o[1] for o in options]
    return rng.choices(labels, weights=weights, k=1)[0]


def pick_seniority_for_subdomain(rng: random.Random) -> str:
    return weighted_choice(rng, SENIORITIES)


def build_title(seniority: str, base_title: str) -> str:
    if seniority == "Mid-level":
        return base_title  # plain title reads as mid-level by default
    if seniority in ("Intern",):
        return f"{base_title} Intern"
    if seniority in ("Manager",):
        return f"{base_title} Manager"
    return f"{seniority} {base_title}"


def salary_for(seniority: str, rng: random.Random) -> tuple[int, int]:
    lo, hi = SALARY_RANGES[seniority]
    span = hi - lo
    smin = rng.randint(lo, lo + int(span * 0.5))
    smax = rng.randint(max(smin + 5000, lo + int(span * 0.4)), hi)
    if smax < smin:
        smin, smax = smax, smin
    return smin, smax


def pick_skills(rng: random.Random, subdomain_key: str, seniority: str) -> list[str]:
    pool = SUBDOMAINS[subdomain_key]["skills"]
    k = rng.randint(3, 8)
    k = min(k, len(pool))
    skills = rng.sample(pool, k)
    # Occasionally add 1 general skill; more likely for senior+ roles.
    add_general_prob = 0.35 if seniority in ("Senior", "Lead", "Staff", "Principal", "Manager") else 0.2
    if rng.random() < add_general_prob:
        skills.append(rng.choice(GENERAL_SKILLS))
    return skills


def messify(rng: random.Random, skills: list[str]) -> list[str]:
    """Inject realistic messiness into a skills list: typo, casing,
    whitespace, or abbreviation swap."""
    if not skills:
        return skills
    idx = rng.randrange(len(skills))
    skill = skills[idx]
    kind = rng.choice(["typo", "case", "whitespace", "abbrev"])

    typo_map = {
        "JavaScript": "Javascrpt",
        "Python": "Pyhton",
        "Kubernetes": "Kuberentes",
        "PostgreSQL": "Postgress",
        "TypeScript": "Typescrpt",
    }
    abbrev_map = {
        "Python": "Py",
        "JavaScript": "JS",
        "Amazon Web Services": "AWS",
        "Continuous Integration": "CI",
        "Continuous Deployment": "CD",
        "Augmented Reality Development": "AR",
        "Virtual Reality Development": "VR",
        "Machine Learning": "ML",
        "Structured Query Language": "SQL",
    }

    if kind == "typo":
        skills[idx] = typo_map.get(skill, skill[:-1] + skill[-1] + skill[-1] if len(skill) > 3 else skill)
        if skill in typo_map:
            skills[idx] = typo_map[skill]
        elif len(skill) > 4:
            # swap two adjacent letters near the end to fake a typo
            chars = list(skill)
            i = len(chars) - 2
            chars[i], chars[i - 1] = chars[i - 1], chars[i]
            skills[idx] = "".join(chars)
    elif kind == "case":
        skills[idx] = skill.upper() if rng.random() < 0.5 else skill.lower()
    elif kind == "whitespace":
        skills[idx] = f" {skill} "
    elif kind == "abbrev":
        skills[idx] = abbrev_map.get(skill, skill)

    return skills


def generate_rows(rng: random.Random) -> list[dict]:
    subdomain_keys = list(SUBDOMAINS.keys())
    # Roughly even split across the 5 sub-domains, with mobile getting a
    # slightly bigger share since "Mobile Dev" is broad.
    subdomain_weights = {
        "blockchain": 0.19,
        "arvr": 0.17,
        "robotics": 0.17,
        "embedded": 0.17,
        "mobile": 0.30,
    }

    companies_by_domain = {
        key: build_company_pool(rng, rng.randint(15, 22)) for key in subdomain_keys
    }
    # Flatten into one shared-ish pool per domain but allow reuse across all.
    all_companies = []
    for lst in companies_by_domain.values():
        all_companies.extend(lst)
    all_companies = list(dict.fromkeys(all_companies))

    rows = []
    messy_target = int(ROW_COUNT * rng.uniform(0.05, 0.08))
    messy_indices = set(rng.sample(range(ROW_COUNT), messy_target))

    for i in range(ROW_COUNT):
        subdomain_key = rng.choices(
            subdomain_keys,
            weights=[subdomain_weights[k] for k in subdomain_keys],
            k=1,
        )[0]
        domain = SUBDOMAINS[subdomain_key]
        base_title = rng.choice(domain["titles"])
        seniority = pick_seniority_for_subdomain(rng)

        # Interns shouldn't get "Lead"/"Principal" style titles; already
        # handled since seniority independently picked, but avoid Intern
        # + Manager nonsense combos by simple guard.
        title = build_title(seniority, base_title)

        company = rng.choice(all_companies)
        location = weighted_choice(rng, LOCATIONS)
        job_type = weighted_choice(rng, JOB_TYPES)
        if seniority == "Intern":
            job_type = "Internship"

        skills = pick_skills(rng, subdomain_key, seniority)

        if i in messy_indices:
            skills = messify(rng, list(skills))

        smin, smax = salary_for(seniority, rng)

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "type": job_type,
                "skills_required": ", ".join(skills),
                "salary_min": smin,
                "salary_max": smax,
                "category": domain["category"],
            }
        )

    return rows


def main() -> None:
    rng = random.Random(SEED)
    rows = generate_rows(rng)
    assert len(rows) == ROW_COUNT, f"expected {ROW_COUNT} rows, got {len(rows)}"

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
