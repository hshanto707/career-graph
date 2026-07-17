"""Synthetic data generator: DevOps, Cloud, SRE, Infrastructure, Networking domain.

Produces exactly 1000 rows matching the kaggle_jobs.csv schema:
    title,company,location,type,skills_required,salary_min,salary_max,category

Skills are drawn from backend/data/onet_skills.csv so downstream fuzzy
matching / synonym resolution in NormalizationAgent has real, taxonomy-
aligned signal at scale. A small fraction of rows are deliberately
"messy" (typos, casing, whitespace, abbreviations) to exercise that logic.

Run:
    python backend/data/generators/generate_devops-cloud.py

Writes:
    backend/data/generators/chunk_devops-cloud.csv  (1000 data rows + header)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 17  # domain-specific offset for "devops-cloud"
random.seed(SEED)

OUT_PATH = Path(__file__).parent / "chunk_devops-cloud.csv"
TARGET_ROWS = 1000
CATEGORY = "DevOps & Infrastructure"

# --------------------------------------------------------------------- #
# Companies — fictional word-combination pool (never real organizations)
# --------------------------------------------------------------------- #
COMPANY_PREFIXES = [
    "Vertex", "Onyx", "Crestline", "Ironwood", "Pinecrest", "Harborline",
    "Skyline", "Bluepeak", "Nova", "Meridian", "Redwood", "Cobalt",
    "Northgate", "Silverline", "Amberfield", "Granite", "Cascade", "Wraith",
    "Solstice", "Fernwood", "Brightwell", "Deepwater", "Ashgrove", "Lumina",
    "Ridgeback", "Copperline", "Frostpeak", "Emberfall", "Slateford",
    "Windmere", "Thornbury", "Palisade", "Basalt", "Zephyr", "Highgrove",
    "Marbleton", "Quartzline", "Steelwater", "Duskmere", "Havencrest",
]
COMPANY_MIDS = [
    "Cloud", "Bridge", "Field", "Data", "Grid", "Node", "Stack", "Mesh",
    "Systems", "Ventures", "Network", "Signal", "Orbit", "Circuit",
    "Pulse", "Vector", "Anchor", "Beacon", "Fleet", "Relay",
]
COMPANY_SUFFIXES = [
    "Labs", "Tech", "Digital", "Systems Group", "IT", "Technologies",
    "Software", "Networks", "Infrastructure", "Solutions", "Works",
    "Platforms",
]


def _build_company_pool(n: int) -> list[str]:
    seen: set[str] = set()
    pool: list[str] = []
    combos = [(p, m, s) for p in COMPANY_PREFIXES for m in COMPANY_MIDS for s in COMPANY_SUFFIXES]
    random.shuffle(combos)
    for p, m, s in combos:
        name = f"{p} {m} {s}"
        if name in seen:
            continue
        seen.add(name)
        pool.append(name)
        if len(pool) >= n:
            break
    return pool


COMPANIES = _build_company_pool(90)

# --------------------------------------------------------------------- #
# Locations
# --------------------------------------------------------------------- #
LOCATIONS_ONSITE = [
    "San Francisco, CA", "Austin, TX", "Seattle, WA", "New York, NY",
    "Denver, CO", "Chicago, IL", "Boston, MA", "Atlanta, GA",
    "Raleigh, NC", "Portland, OR", "Dallas, TX", "Reston, VA",
    "San Jose, CA", "Salt Lake City, UT",
    "Toronto, ON", "London, UK", "Berlin, Germany", "Dublin, Ireland",
    "Amsterdam, Netherlands", "Bengaluru, India", "Singapore",
    "Sydney, Australia",
]
REMOTE_WEIGHT = 0.25

# --------------------------------------------------------------------- #
# Job types
# --------------------------------------------------------------------- #
JOB_TYPES_WEIGHTED = (
    ["Full-time"] * 65 + ["Part-time"] * 10 + ["Internship"] * 15 + ["Contract"] * 10
)

# --------------------------------------------------------------------- #
# Skill pools (canonical O*NET names, matching onet_skills.csv)
# --------------------------------------------------------------------- #
CLOUD_DEVOPS = [
    "Amazon Web Services", "Microsoft Azure", "Google Cloud Platform",
    "Docker", "Kubernetes", "Terraform", "Jenkins", "GitHub Actions",
    "Ansible", "CI/CD Pipelines", "Prometheus", "Grafana", "Helm",
    "Nginx", "Linux Administration", "AWS Lambda", "AWS EC2", "AWS S3",
    "AWS RDS", "Azure DevOps", "Azure Functions", "Google Kubernetes Engine",
    "Cloud Architecture", "Infrastructure as Code", "Pulumi",
    "CloudFormation", "Chef", "Puppet", "Vagrant",
    "Site Reliability Engineering", "Observability", "Datadog", "Splunk",
    "New Relic", "PagerDuty", "GitLab CI", "CircleCI", "Argo CD",
    "Service Mesh (Istio)", "Container Orchestration", "Docker Compose",
    "Blue-Green Deployment", "Canary Deployment", "Cost Optimization (FinOps)",
    "Multi-cloud Strategy",
]
NETWORKING = [
    "TCP/IP", "DNS Administration", "Network Routing & Switching",
    "VoIP Systems", "Load Balancers (F5)", "Network Monitoring",
    "Windows Server Administration", "Active Directory",
    "Virtualization (VMware)", "Storage Area Networks",
    "Network Automation", "SD-WAN", "IPv6",
]
SECURITY_ADJACENT = [
    "DevSecOps", "Zero Trust Architecture", "VPN Configuration",
    "Firewall Configuration", "SIEM Tools", "Incident Response",
]
PROGRAMMING = ["Python", "Go", "Bash", "Shell Scripting", "PowerShell", "Ruby"]
TOOLS_METHODOLOGY = [
    "Git", "Version Control", "GitHub", "GitLab", "Bitbucket",
    "Continuous Integration", "Continuous Deployment",
    "Documentation Best Practices", "Monorepo Management", "Feature Flags",
    "Trunk-Based Development",
]
GENERAL_SOFT = [
    "Communication", "Team Leadership", "Problem Solving", "Mentoring",
    "Time Management", "Critical Thinking", "Agile Methodology",
    "Cross-functional Collaboration",
]

# --------------------------------------------------------------------- #
# Roles + seniority + salary bands (USD annual, realistic for infra/cloud)
# --------------------------------------------------------------------- #
# Each role entry: (base_title, skill_emphasis) where skill_emphasis picks
# which pools to draw "core" skills from most heavily.
ROLES = [
    ("DevOps Engineer", ["cloud", "tools"]),
    ("Site Reliability Engineer", ["cloud", "programming"]),
    ("Cloud Engineer", ["cloud"]),
    ("Cloud Architect", ["cloud"]),
    ("Infrastructure Engineer", ["cloud", "networking"]),
    ("Platform Engineer", ["cloud", "tools"]),
    ("Network Engineer", ["networking"]),
    ("Systems Administrator", ["networking", "cloud"]),
    ("Cloud Security Engineer", ["cloud", "security"]),
    ("Release Engineer", ["tools", "cloud"]),
    ("Build & Release Engineer", ["tools", "cloud"]),
    ("Kubernetes Administrator", ["cloud"]),
    ("Cloud Operations Engineer", ["cloud", "networking"]),
    ("IT Infrastructure Engineer", ["networking", "cloud"]),
    ("Network Administrator", ["networking"]),
    ("DevOps Architect", ["cloud", "tools"]),
    ("Cloud Infrastructure Engineer", ["cloud", "networking"]),
    ("Observability Engineer", ["cloud", "programming"]),
    ("Systems Engineer", ["networking", "cloud"]),
]

SENIORITY_LEVELS = ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"]
# Not every seniority applies to every role naturally; weight simple.
SENIORITY_WEIGHTS = {
    "Intern": 6, "Junior": 14, "Mid-level": 24, "Senior": 28,
    "Lead": 12, "Staff": 9, "Principal": 7,
}

MANAGER_ROLES = [
    "DevOps Manager", "Infrastructure Manager", "Cloud Operations Manager",
    "Site Reliability Manager", "Network Operations Manager",
    "IT Infrastructure Manager",
]

# Salary bands (min, max) in USD annual, by seniority label.
SALARY_BANDS = {
    "Intern": (24000, 42000),
    "Junior": (58000, 82000),
    "Mid-level": (80000, 115000),
    "Senior": (108000, 155000),
    "Lead": (135000, 175000),
    "Staff": (140000, 185000),
    "Principal": (150000, 195000),
    "Manager": (120000, 172000),
}


def _title_for(role: str, seniority: str | None) -> str:
    if seniority is None:
        return role
    if seniority == "Intern":
        # More natural phrasing for internship postings.
        return f"{role} Intern" if not role.endswith("Intern") else role
    return f"{seniority} {role}"


def _pick_seniority() -> str:
    levels = list(SENIORITY_WEIGHTS.keys())
    weights = list(SENIORITY_WEIGHTS.values())
    return random.choices(levels, weights=weights, k=1)[0]


def _salary_for(seniority: str) -> tuple[int, int]:
    lo, hi = SALARY_BANDS[seniority]
    # Add some jitter so not every "Senior" row shares one exact band.
    span = hi - lo
    salary_min = random.randint(lo, lo + int(span * 0.4))
    salary_max = random.randint(max(salary_min + 8000, hi - int(span * 0.4)), hi)
    return salary_min, salary_max


def _pick_location() -> str:
    if random.random() < REMOTE_WEIGHT:
        return "Remote"
    return random.choice(LOCATIONS_ONSITE)


def _pick_job_type() -> str:
    return random.choice(JOB_TYPES_WEIGHTED)


def _skills_for(emphasis: list[str], seniority: str) -> list[str]:
    pools = []
    for tag in emphasis:
        if tag == "cloud":
            pools.append(CLOUD_DEVOPS)
        elif tag == "networking":
            pools.append(NETWORKING)
        elif tag == "security":
            pools.append(SECURITY_ADJACENT)
        elif tag == "programming":
            pools.append(PROGRAMMING)
        elif tag == "tools":
            pools.append(TOOLS_METHODOLOGY)

    n_core = random.randint(3, 6)
    core: list[str] = []
    seen = set()
    attempts = 0
    while len(core) < n_core and attempts < 50:
        attempts += 1
        pool = random.choice(pools)
        pick = random.choice(pool)
        if pick.lower() in seen:
            continue
        seen.add(pick.lower())
        core.append(pick)

    # Occasionally add a couple of cross-pool skills (networking on a cloud
    # role, security on an SRE role, etc.) for realistic overlap.
    if random.random() < 0.5:
        extra_pool = random.choice([NETWORKING, PROGRAMMING, TOOLS_METHODOLOGY, SECURITY_ADJACENT])
        pick = random.choice(extra_pool)
        if pick.lower() not in seen:
            seen.add(pick.lower())
            core.append(pick)

    # Occasionally add 1 general/soft skill — more common for senior/lead/
    # manager roles (leadership, mentoring) than for interns/juniors.
    general_chance = 0.35
    if seniority in ("Lead", "Staff", "Principal", "Manager"):
        general_chance = 0.65
    if random.random() < general_chance:
        pick = random.choice(GENERAL_SOFT)
        if pick.lower() not in seen:
            core.append(pick)

    # Clamp to the 3-8 range required.
    if len(core) > 8:
        core = core[:8]
    if len(core) < 3:
        # top up from the primary pool
        pool = pools[0]
        while len(core) < 3:
            pick = random.choice(pool)
            if pick.lower() not in seen:
                seen.add(pick.lower())
                core.append(pick)

    random.shuffle(core)
    return core


# --------------------------------------------------------------------- #
# Messiness injection (~5-8% of rows)
# --------------------------------------------------------------------- #
TYPO_MAP = {
    "Kubernetes": "Kuberentes",
    "Python": "Pyhton",
    "Terraform": "Terafrom",
    "Ansible": "Ansibel",
    "Prometheus": "Prometheous",
    "Grafana": "Grafanna",
    "Jenkins": "Jenkings",
    "Linux Administration": "Linux Adminstration",
    "Communication": "Communcation",
}
ABBREVIATIONS = {
    "Amazon Web Services": "AWS",
    "Microsoft Azure": "Azure",
    "Google Cloud Platform": "GCP",
    "Kubernetes": "K8s",
    "CI/CD Pipelines": "CI/CD",
    "Infrastructure as Code": "IaC",
    "Site Reliability Engineering": "SRE",
    "Continuous Integration": "CI",
    "Continuous Deployment": "CD",
    "Identity and Access Management": "IAM",
    "DNS Administration": "DNS",
    "TCP/IP": "Networking (TCP/IP)",
}


def _messify_skill(name: str) -> str:
    roll = random.random()
    if roll < 0.30 and name in TYPO_MAP:
        return TYPO_MAP[name]
    if roll < 0.65 and name in ABBREVIATIONS:
        return ABBREVIATIONS[name]
    if roll < 0.85:
        return f" {name} "  # stray whitespace
    # inconsistent casing
    return name.upper() if random.random() < 0.5 else name.lower()


def _maybe_messify_row(skills: list[str]) -> list[str]:
    """Mutate a copy of skills with a light-touch messiness pass."""
    messy = list(skills)
    idx = random.randrange(len(messy))
    messy[idx] = _messify_skill(messy[idx])
    # Occasionally duplicate a skill (case-varied) to exercise dedup.
    if random.random() < 0.3 and len(messy) < 8:
        dup = random.choice(skills)
        messy.append(dup.upper() if random.random() < 0.5 else dup.lower())
    return messy


def generate_rows(n: int) -> list[dict]:
    rows: list[dict] = []
    messy_row_indices = set(random.sample(range(n), k=int(n * random.uniform(0.05, 0.08))))

    for i in range(n):
        use_manager = random.random() < 0.08
        if use_manager:
            role = random.choice(MANAGER_ROLES)
            seniority = "Manager"
            title = role
            emphasis = ["cloud", "tools"]
        else:
            role, emphasis = random.choice(ROLES)
            seniority = _pick_seniority()
            title = _title_for(role, seniority)

        company = random.choice(COMPANIES)
        location = _pick_location()
        job_type = _pick_job_type()
        # Interns/juniors shouldn't get Contract-heavy or wildly senior salary bands.
        if seniority == "Intern":
            job_type = "Internship" if random.random() < 0.8 else job_type
        salary_min, salary_max = _salary_for(seniority)

        skills = _skills_for(emphasis, seniority)
        if i in messy_row_indices:
            skills = _maybe_messify_row(skills)

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
    rows = generate_rows(TARGET_ROWS)
    fieldnames = [
        "title", "company", "location", "type", "skills_required",
        "salary_min", "salary_max", "category",
    ]
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
