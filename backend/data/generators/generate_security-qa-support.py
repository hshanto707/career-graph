"""Synthetic data generator — domain chunk: Cybersecurity / QA-Testing / IT Support-Helpdesk.

Produces exactly 900 synthetic (fictional) job-posting rows matching the
kaggle_jobs.csv schema:

    title,company,location,type,skills_required,salary_min,salary_max,category

Run directly:
    python backend/data/generators/generate_security-qa-support.py

Output:
    backend/data/generators/chunk_security-qa-support.csv

All company names are invented word-combinations (e.g. "Vertex Cloud Labs"
style) — never real organizations. This is a SYNTHETIC fixture used to
exercise IngestionAgent / NormalizationAgent at scale; it is not a claim of
real job-market data.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42 + 7  # domain-specific offset ("security-qa-support" chunk)
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = Path(__file__).resolve().parent / "chunk_security-qa-support.csv"

N_ROWS = 900

# --------------------------------------------------------------------- #
# Role groups: title stems, seniority ladder, salary bands, skill pools,
# location bias, category.
# --------------------------------------------------------------------- #

SENIORITY_ORDER = ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal", "Manager"]

# Base USD annual salary bands per seniority (min, max) - will be jittered
# per-row and nudged per role group below.
SENIORITY_BANDS = {
    "Intern": (20000, 40000),
    "Junior": (55000, 80000),
    "Mid-level": (75000, 110000),
    "Senior": (100000, 150000),
    "Lead": (130000, 175000),
    "Staff": (135000, 185000),
    "Principal": (145000, 190000),
    "Manager": (115000, 170000),
}

GENERAL_SKILLS = [
    "Git", "Communication", "Agile Methodology", "Documentation Best Practices",
    "Problem Solving", "Time Management", "Jira", "Collaboration",
    "Interpersonal Skills", "Presentation Skills",
]

SECURITY_SKILLS = [
    "Application Security", "Penetration Testing", "Network Security",
    "Identity and Access Management", "Cryptography", "OWASP",
    "SIEM Tools", "Threat Modeling", "Incident Response",
    "Vulnerability Assessment", "Security Auditing", "Zero Trust Architecture",
    "SOC Operations", "Firewall Configuration", "Endpoint Security",
    "Malware Analysis", "Digital Forensics", "GRC (Governance, Risk & Compliance)",
    "ISO 27001", "SOC 2 Compliance", "GDPR Compliance", "HIPAA Compliance",
    "DevSecOps", "Secure Code Review", "Public Key Infrastructure",
    "VPN Configuration", "TCP/IP", "Linux Administration", "Cloud Security",
    "Amazon Web Services (AWS)", "Microsoft Azure", "Python", "Shell Scripting",
]

QA_SKILLS = [
    "Unit Testing", "Test Automation", "Selenium", "Cypress", "Pytest", "Jest",
    "Quality Assurance", "Performance Testing", "Playwright", "Appium",
    "Postman", "API Testing", "Regression Testing", "Load Testing (JMeter)",
    "Test Case Design", "Test Plan Development", "Behavior-Driven Development",
    "Continuous Testing", "Mobile Testing", "Accessibility Testing",
    "Exploratory Testing", "Bug Tracking", "CI/CD Pipelines", "Python",
    "JavaScript", "SQL", "Jira",
]

IT_SUPPORT_SKILLS = [
    "Windows Server Administration", "Active Directory", "TCP/IP",
    "DNS Administration", "Network Routing & Switching", "VoIP Systems",
    "Load Balancers (F5)", "Network Monitoring", "Virtualization (VMware)",
    "Storage Area Networks", "Network Automation", "SD-WAN", "IPv6",
    "Linux Administration", "VPN Configuration", "Endpoint Security",
    "Customer Service", "Documentation Best Practices",
]

# Role definitions. Each: (title_stem, seniority_list, skill_pool, category, salary_bias)
ROLE_GROUPS = [
    {
        "stems": ["Security Analyst", "Cybersecurity Analyst", "SOC Analyst"],
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Manager"],
        "skills": SECURITY_SKILLS,
        "category": "Security",
        "bias": 1.0,
    },
    {
        "stems": ["Security Engineer", "Cybersecurity Engineer", "Application Security Engineer"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff", "Principal"],
        "skills": SECURITY_SKILLS,
        "category": "Security",
        "bias": 1.08,
    },
    {
        "stems": ["Penetration Tester", "Offensive Security Engineer"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "skills": SECURITY_SKILLS,
        "category": "Security",
        "bias": 1.1,
    },
    {
        "stems": ["Security Architect", "Cloud Security Architect"],
        "seniorities": ["Senior", "Lead", "Staff", "Principal"],
        "skills": SECURITY_SKILLS,
        "category": "Security",
        "bias": 1.2,
    },
    {
        "stems": ["Compliance & Risk Analyst", "GRC Analyst"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Manager"],
        "skills": SECURITY_SKILLS,
        "category": "Security",
        "bias": 0.95,
    },
    {
        "stems": ["QA Engineer", "Quality Assurance Engineer"],
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior", "Lead", "Manager"],
        "skills": QA_SKILLS,
        "category": "QA & Testing",
        "bias": 0.95,
    },
    {
        "stems": ["QA Analyst", "Manual QA Tester"],
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior"],
        "skills": QA_SKILLS,
        "category": "QA & Testing",
        "bias": 0.85,
    },
    {
        "stems": ["SDET", "Test Automation Engineer"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "skills": QA_SKILLS,
        "category": "QA & Testing",
        "bias": 1.02,
    },
    {
        "stems": ["QA Lead", "QA Manager"],
        "seniorities": ["Lead", "Manager", "Staff", "Principal"],
        "skills": QA_SKILLS,
        "category": "QA & Testing",
        "bias": 1.05,
    },
    {
        "stems": ["IT Support Specialist", "Help Desk Technician", "IT Support Analyst"],
        "seniorities": ["Intern", "Junior", "Mid-level", "Senior"],
        "skills": IT_SUPPORT_SKILLS,
        "category": "IT Support",
        "bias": 0.7,
    },
    {
        "stems": ["Desktop Support Engineer", "Technical Support Engineer"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead"],
        "skills": IT_SUPPORT_SKILLS,
        "category": "IT Support",
        "bias": 0.78,
    },
    {
        "stems": ["Systems Administrator", "Network Administrator"],
        "seniorities": ["Junior", "Mid-level", "Senior", "Lead", "Staff"],
        "skills": IT_SUPPORT_SKILLS,
        "category": "IT Support",
        "bias": 0.9,
    },
    {
        "stems": ["IT Support Manager", "Help Desk Manager"],
        "seniorities": ["Manager", "Lead", "Staff"],
        "skills": IT_SUPPORT_SKILLS,
        "category": "IT Support",
        "bias": 0.95,
    },
]

COMPANIES = [
    "Vertex Cloud Labs", "Onyx Bridge Tech", "Crestline Digital", "Ironwood Systems",
    "Northwind Analytics", "Nova Field Labs", "Redwood Data Systems", "Solstice Data Co",
    "Timberline Analytics", "Voidline Inc", "Skyline Ventures IT", "Lattice Works",
    "Meridian Apps", "Pinecrest Digital", "Coral Reef Software", "Bluepeak Software",
    "Fernwood Interactive", "Harborline Technologies", "Granite Peak Tech", "Cobalt Robotics Group",
    "Amber Path Studios", "Ghost Corp", "Sentinel Ridge Security", "Ironclad Cyber Group",
    "Bastion Point Systems", "Cipher Harbor Labs", "Shieldwall Technologies", "Fortress Grove Inc",
    "Nightwatch Security Co", "Vanguard Mesh Systems", "Redteam Ridge Labs", "Blueforge Cyber",
    "Quietstone Security", "Ironveil Networks", "Aegis Loop Technologies", "Perimeter Nine Labs",
    "Cryptbridge Systems", "Watchtower Data Co", "Keyline Security Group", "Threadneedle Cyber",
    "Palisade Systems Inc", "Argus Point Technologies", "Stonewall Cyber Labs", "Trustline Networks",
    "Beacon Ridge Security", "Faultline Technologies", "Anchorpoint Systems", "Deadbolt Digital",
    "Testforge Labs", "Qualitrix Systems", "Assurewave Software", "Bugtrail Technologies",
    "Verityloop Digital", "Checkframe Labs", "Precisionpath QA", "Truescope Software",
    "Validex Systems", "Suretest Technologies", "Frameworth Digital", "Signalcheck Labs",
    "Clearbench Systems", "Rigortest Software", "Deskline Support Co", "Helprail Technologies",
    "Ticketforge Systems", "Uptime Grove IT", "Nodecare Technologies", "Basecamp Support Labs",
    "Fieldwire IT Systems", "Bridgeline Networks", "Terminalpoint Tech", "Consolebridge Systems",
    "Gridline Support Co", "Patchbay Technologies", "Netframe Solutions", "Circuitline IT",
    "Meshpoint Systems", "Routewise Networks", "Endpointe Technologies", "Hardwireline Support",
    "Systemcove Technologies", "Datastack Ventures", "Coreloop Systems", "Byteforge Labs",
    "Streamline Cyber Co", "Peaksec Technologies", "Vertexguard Systems", "Ridgeline Security Labs",
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Boston, MA",
    "Chicago, IL", "Denver, CO", "Atlanta, GA", "Washington, DC", "Dallas, TX",
    "Raleigh, NC", "Toronto, ON", "Vancouver, BC", "London, UK", "Berlin, Germany",
    "Dublin, Ireland", "Singapore", "Bengaluru, India", "Sydney, Australia",
]

JOB_TYPE_WEIGHTS = [("Full-time", 0.65), ("Part-time", 0.10), ("Internship", 0.15), ("Contract", 0.10)]


def weighted_choice(pairs):
    r = random.random()
    upto = 0.0
    for item, weight in pairs:
        upto += weight
        if r <= upto:
            return item
    return pairs[-1][0]


def pick_location() -> str:
    if random.random() < 0.25:
        return "Remote"
    return random.choice(LOCATIONS)


def pick_seniority(role) -> str:
    return random.choice(role["seniorities"])


def salary_range(seniority: str, bias: float) -> tuple[int, int]:
    lo, hi = SENIORITY_BANDS[seniority]
    lo = int(lo * bias)
    hi = int(hi * bias)
    # jitter the band edges a bit for variety, keep min < max
    jitter_lo = random.randint(-3000, 3000)
    jitter_hi = random.randint(-3000, 5000)
    smin = max(15000, lo + jitter_lo)
    smax = max(smin + 5000, hi + jitter_hi)
    return smin, smax


def build_title(role, seniority: str) -> str:
    stem = random.choice(role["stems"])
    if "Manager" in stem:
        # stem already conveys seniority (e.g. "QA Manager") — don't double up
        return stem
    if seniority == "Mid-level" and random.random() < 0.4:
        return stem
    return f"{seniority} {stem}"


def pick_skills(role) -> list[str]:
    pool = role["skills"]
    n = random.randint(3, 8)
    n_general = 1 if random.random() < 0.35 else 0
    n_domain = max(1, n - n_general)
    domain_skills = random.sample(pool, k=min(n_domain, len(pool)))
    general_skills = random.sample(GENERAL_SKILLS, k=min(n_general, len(GENERAL_SKILLS)))
    combined = domain_skills + general_skills
    random.shuffle(combined)
    return combined


def messify(skills: list[str]) -> list[str]:
    """Inject realistic messiness into a skills list (typo / casing /
    whitespace / abbreviation) — applied to ~5-8% of rows by the caller."""
    messy = list(skills)
    idx = random.randrange(len(messy))
    original = messy[idx]
    variant_kind = random.choice(["typo", "case", "whitespace", "abbrev", "dup"])

    if variant_kind == "typo" and original == "Application Security":
        messy[idx] = "Applicaton Security"
    elif variant_kind == "typo" and "Python" in original:
        messy[idx] = "Pyhton"
    elif variant_kind == "typo" and original == "JavaScript":
        messy[idx] = "Javascrpt"
    elif variant_kind == "case":
        messy[idx] = original.upper() if random.random() < 0.5 else original.lower()
    elif variant_kind == "whitespace":
        messy[idx] = f"  {original} "
    elif variant_kind == "abbrev":
        abbrev_map = {
            "Application Security": "AppSec",
            "Penetration Testing": "PenTest",
            "Quality Assurance": "QA",
            "Identity and Access Management": "IAM",
            "Active Directory": "AD",
            "Amazon Web Services (AWS)": "AWS",
            "Microsoft Azure": "Azure",
            "GRC (Governance, Risk & Compliance)": "GRC",
            "Continuous Testing": "CI",
            "Behavior-Driven Development": "BDD",
        }
        messy[idx] = abbrev_map.get(original, original)
    elif variant_kind == "dup":
        messy.append(original)

    return messy


def format_skills(skills: list[str]) -> str:
    return ", ".join(skills)


def generate_rows(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        role = random.choice(ROLE_GROUPS)
        seniority = pick_seniority(role)
        title = build_title(role, seniority)
        company = random.choice(COMPANIES)
        location = pick_location()
        job_type = weighted_choice(JOB_TYPE_WEIGHTS)
        smin, smax = salary_range(seniority, role["bias"])
        skills = pick_skills(role)

        # ~5-8% messiness injection
        if random.random() < 0.065:
            skills = messify(skills)

        rows.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "type": job_type,
                "skills_required": format_skills(skills),
                "salary_min": smin,
                "salary_max": smax,
                "category": role["category"],
            }
        )
    return rows


def main() -> None:
    rows = generate_rows(N_ROWS)
    fieldnames = ["title", "company", "location", "type", "skills_required", "salary_min", "salary_max", "category"]
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
