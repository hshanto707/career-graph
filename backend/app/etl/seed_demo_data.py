"""seed_demo_data.py — module B4.

Seeds a small, fast local-dev/demo dataset into the graph, per
system-design.md §10 ("Demo / Seed" sources) and §14 startup step 4:

    - A curated 50-job subset of `data/kaggle_jobs.csv`, run through the
      real Ingestion + Normalization pipeline (so it exercises the exact
      same code path production ingestion does).
    - 30 courses, hand-curated, each `TEACHES` one or more Skill nodes.
    - 3 demo student profiles (junior dev, career switcher, business
      analyst) with `HAS_SKILL` / `TARGETS` edges.

Usage:
    python -m app.etl.seed_demo_data

Idempotent: every write goes through the same MERGE-based GraphService
methods the ingestion pipeline uses, so running this more than once does
not duplicate nodes/edges.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database.neo4j import get_driver
from app.engine.ingestion.ingestion_agent import IngestionAgent
from app.engine.ingestion.normalization_agent import NormalizationAgent
from app.services.graph_service import GraphService

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_ROOT / "data"

DEMO_JOB_COUNT = 50

DEMO_COURSES: list[dict[str, Any]] = [
    {"id": "course-python-basics", "title": "Python for Everybody", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/python", "duration": "8 weeks", "free": False,
     "teaches_skills": ["Python"]},
    {"id": "course-js-basics", "title": "The Complete JavaScript Course", "provider": "Udemy",
     "url": "https://www.udemy.com/course/the-complete-javascript-course/", "duration": "6 weeks", "free": False,
     "teaches_skills": ["JavaScript"]},
    {"id": "course-ts-fundamentals", "title": "Understanding TypeScript", "provider": "Udemy",
     "url": "https://www.udemy.com/course/understanding-typescript/", "duration": "4 weeks", "free": False,
     "teaches_skills": ["TypeScript"]},
    {"id": "course-react-fundamentals", "title": "React - The Complete Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "duration": "6 weeks", "free": False,
     "teaches_skills": ["React"]},
    {"id": "course-vue-mastery", "title": "Vue.js 3 Fundamentals", "provider": "Vue Mastery",
     "url": "https://www.vuemastery.com/courses/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["Vue.js"]},
    {"id": "course-node-api", "title": "Node.js, Express, MongoDB & More", "provider": "Udemy",
     "url": "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/", "duration": "6 weeks", "free": False,
     "teaches_skills": ["Node.js", "Express.js"]},
    {"id": "course-django-basics", "title": "Django for Everybody", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/django", "duration": "6 weeks", "free": True,
     "teaches_skills": ["Django"]},
    {"id": "course-fastapi", "title": "FastAPI - The Complete Course", "provider": "Udemy",
     "url": "https://www.udemy.com/course/fastapi-the-complete-course/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["FastAPI"]},
    {"id": "course-sql-basics", "title": "SQL for Data Science", "provider": "Coursera",
     "url": "https://www.coursera.org/learn/sql-for-data-science", "duration": "4 weeks", "free": True,
     "teaches_skills": ["SQL"]},
    {"id": "course-postgres-deep-dive", "title": "PostgreSQL Deep Dive", "provider": "Udemy",
     "url": "https://www.udemy.com/course/postgresql-database/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["PostgreSQL"]},
    {"id": "course-mongodb-basics", "title": "MongoDB - The Complete Developer's Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/mongodb-the-complete-developers-guide/", "duration": "4 weeks", "free": False,
     "teaches_skills": ["MongoDB"]},
    {"id": "course-docker-k8s", "title": "Docker & Kubernetes: The Practical Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/", "duration": "6 weeks", "free": False,
     "teaches_skills": ["Docker", "Kubernetes"]},
    {"id": "course-terraform", "title": "Terraform for Beginners", "provider": "Udemy",
     "url": "https://www.udemy.com/course/terraform-beginner-to-advanced/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["Terraform"]},
    {"id": "course-aws-cloud-practitioner", "title": "AWS Certified Cloud Practitioner", "provider": "A Cloud Guru",
     "url": "https://acloudguru.com/course/aws-certified-cloud-practitioner", "duration": "4 weeks", "free": False,
     "teaches_skills": ["Amazon Web Services"]},
    {"id": "course-gcp-fundamentals", "title": "Google Cloud Fundamentals", "provider": "Coursera",
     "url": "https://www.coursera.org/learn/gcp-fundamentals", "duration": "3 weeks", "free": True,
     "teaches_skills": ["Google Cloud Platform"]},
    {"id": "course-azure-fundamentals", "title": "Microsoft Azure Fundamentals AZ-900", "provider": "Microsoft Learn",
     "url": "https://learn.microsoft.com/training/paths/azure-fundamentals/", "duration": "2 weeks", "free": True,
     "teaches_skills": ["Microsoft Azure"]},
    {"id": "course-ml-andrew-ng", "title": "Machine Learning Specialization", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/machine-learning-introduction", "duration": "10 weeks", "free": False,
     "teaches_skills": ["Machine Learning"]},
    {"id": "course-deep-learning", "title": "Deep Learning Specialization", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/deep-learning", "duration": "12 weeks", "free": False,
     "teaches_skills": ["Deep Learning"]},
    {"id": "course-nlp-specialization", "title": "Natural Language Processing Specialization", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/natural-language-processing", "duration": "8 weeks", "free": False,
     "teaches_skills": ["Natural Language Processing"]},
    {"id": "course-pandas-numpy", "title": "Data Analysis with Pandas and NumPy", "provider": "Udemy",
     "url": "https://www.udemy.com/course/data-analysis-with-pandas/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["Pandas", "NumPy"]},
    {"id": "course-tensorflow-cert", "title": "TensorFlow Developer Certificate", "provider": "Coursera",
     "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "duration": "8 weeks", "free": False,
     "teaches_skills": ["TensorFlow"]},
    {"id": "course-pytorch-basics", "title": "PyTorch for Deep Learning", "provider": "Udemy",
     "url": "https://www.udemy.com/course/pytorch-for-deep-learning/", "duration": "6 weeks", "free": False,
     "teaches_skills": ["PyTorch"]},
    {"id": "course-tableau-basics", "title": "Data Visualization with Tableau", "provider": "Coursera",
     "url": "https://www.coursera.org/specializations/data-visualization", "duration": "5 weeks", "free": False,
     "teaches_skills": ["Tableau"]},
    {"id": "course-powerbi-basics", "title": "Microsoft Power BI Desktop for Business", "provider": "Udemy",
     "url": "https://www.udemy.com/course/microsoft-power-bi-up-running-with-power-bi-desktop/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["Power BI"]},
    {"id": "course-figma-ui", "title": "Figma UI/UX Design Essentials", "provider": "Udemy",
     "url": "https://www.udemy.com/course/figma-ux-ui-design-user-experience/", "duration": "3 weeks", "free": False,
     "teaches_skills": ["Figma", "UI Design"]},
    {"id": "course-ux-research", "title": "UX Research at Scale", "provider": "Coursera",
     "url": "https://www.coursera.org/learn/ux-research-at-scale", "duration": "4 weeks", "free": True,
     "teaches_skills": ["UX Research"]},
    {"id": "course-agile-scrum", "title": "Agile with Atlassian Jira", "provider": "Coursera",
     "url": "https://www.coursera.org/learn/agile-atlassian-jira", "duration": "3 weeks", "free": True,
     "teaches_skills": ["Agile Methodology", "Jira"]},
    {"id": "course-selenium-testing", "title": "Selenium WebDriver with Python", "provider": "Udemy",
     "url": "https://www.udemy.com/course/selenium-webdriver-with-python3/", "duration": "4 weeks", "free": False,
     "teaches_skills": ["Selenium", "Test Automation"]},
    {"id": "course-appsec-owasp", "title": "OWASP Top 10 for Web Developers", "provider": "Pluralsight",
     "url": "https://www.pluralsight.com/courses/owasp-top-10-web-application-security-risks", "duration": "2 weeks", "free": False,
     "teaches_skills": ["OWASP", "Application Security"]},
    {"id": "course-git-github", "title": "Git & GitHub Complete Guide", "provider": "Udemy",
     "url": "https://www.udemy.com/course/git-and-github-complete-guide/", "duration": "2 weeks", "free": True,
     "teaches_skills": ["Git"]},
]
assert len(DEMO_COURSES) == 30

DEMO_STUDENTS: list[dict[str, Any]] = [
    {
        "id": "student-junior-dev",
        "label": "Junior Developer",
        "skills": [
            {"name": "Python", "proficiency": 6, "years": 1.0},
            {"name": "JavaScript", "proficiency": 5, "years": 1.0},
            {"name": "Git", "proficiency": 6, "years": 1.5},
            {"name": "SQL", "proficiency": 4, "years": 0.5},
        ],
        "target_roles": ["Junior Software Engineer"],
    },
    {
        "id": "student-career-switcher",
        "label": "Career Switcher",
        "skills": [
            {"name": "Excel", "proficiency": 8, "years": 4.0},
            {"name": "SQL", "proficiency": 3, "years": 0.5},
            {"name": "Communication", "proficiency": 9, "years": 6.0},
        ],
        "target_roles": ["Junior Data Scientist"],
    },
    {
        "id": "student-business-analyst",
        "label": "Business Analyst",
        "skills": [
            {"name": "Business Analysis", "proficiency": 7, "years": 2.0},
            {"name": "Excel", "proficiency": 8, "years": 3.0},
            {"name": "Tableau", "proficiency": 5, "years": 1.0},
            {"name": "Requirements Gathering", "proficiency": 6, "years": 2.0},
        ],
        "target_roles": [],
    },
]
assert len(DEMO_STUDENTS) == 3

STANDARDIZED_ROLES: list[dict[str, Any]] = [
    {
        "job": {
            "id": "Intern Software Engineer",
            "title": "Intern Software Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Internship",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "JavaScript", "normalized_name": "JavaScript", "importance": "must"},
            {"raw_name": "Git", "normalized_name": "Git", "importance": "must"},
            {"raw_name": "SQL", "normalized_name": "SQL", "importance": "nice"},
            {"raw_name": "HTML", "normalized_name": "HTML", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Junior Software Engineer",
            "title": "Junior Software Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "JavaScript", "normalized_name": "JavaScript", "importance": "must"},
            {"raw_name": "Git", "normalized_name": "Git", "importance": "must"},
            {"raw_name": "SQL", "normalized_name": "SQL", "importance": "must"},
            {"raw_name": "React", "normalized_name": "React", "importance": "nice"},
            {"raw_name": "Node.js", "normalized_name": "Node.js", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Mid Software Engineer",
            "title": "Mid Software Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "JavaScript", "normalized_name": "JavaScript", "importance": "must"},
            {"raw_name": "Git", "normalized_name": "Git", "importance": "must"},
            {"raw_name": "SQL", "normalized_name": "SQL", "importance": "must"},
            {"raw_name": "Docker", "normalized_name": "Docker", "importance": "nice"},
            {"raw_name": "REST API", "normalized_name": "REST API", "importance": "must"},
        ],
    },
    {
        "job": {
            "id": "Senior Software Engineer",
            "title": "Senior Software Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "System Architecture", "normalized_name": "System Architecture", "importance": "must"},
            {"raw_name": "Docker", "normalized_name": "Docker", "importance": "must"},
            {"raw_name": "Kubernetes", "normalized_name": "Kubernetes", "importance": "nice"},
            {"raw_name": "PostgreSQL", "normalized_name": "PostgreSQL", "importance": "must"},
            {"raw_name": "Git", "normalized_name": "Git", "importance": "must"},
        ],
    },
    {
        "job": {
            "id": "Junior Data Scientist",
            "title": "Junior Data Scientist",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "SQL", "normalized_name": "SQL", "importance": "must"},
            {"raw_name": "Pandas", "normalized_name": "Pandas", "importance": "must"},
            {"raw_name": "NumPy", "normalized_name": "NumPy", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Mid Data Scientist",
            "title": "Mid Data Scientist",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "SQL", "normalized_name": "SQL", "importance": "must"},
            {"raw_name": "Pandas", "normalized_name": "Pandas", "importance": "must"},
            {"raw_name": "Machine Learning", "normalized_name": "Machine Learning", "importance": "must"},
            {"raw_name": "Scikit-Learn", "normalized_name": "Scikit-Learn", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Senior Data Scientist",
            "title": "Senior Data Scientist",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "Python", "normalized_name": "Python", "importance": "must"},
            {"raw_name": "Machine Learning", "normalized_name": "Machine Learning", "importance": "must"},
            {"raw_name": "Deep Learning", "normalized_name": "Deep Learning", "importance": "must"},
            {"raw_name": "PyTorch", "normalized_name": "PyTorch", "importance": "nice"},
            {"raw_name": "TensorFlow", "normalized_name": "TensorFlow", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Junior Frontend Engineer",
            "title": "Junior Frontend Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "HTML", "normalized_name": "HTML", "importance": "must"},
            {"raw_name": "CSS", "normalized_name": "CSS", "importance": "must"},
            {"raw_name": "JavaScript", "normalized_name": "JavaScript", "importance": "must"},
            {"raw_name": "React", "normalized_name": "React", "importance": "nice"},
        ],
    },
    {
        "job": {
            "id": "Senior Frontend Engineer",
            "title": "Senior Frontend Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "JavaScript", "normalized_name": "JavaScript", "importance": "must"},
            {"raw_name": "TypeScript", "normalized_name": "TypeScript", "importance": "must"},
            {"raw_name": "React", "normalized_name": "React", "importance": "must"},
            {"raw_name": "Web Performance", "normalized_name": "Web Performance", "importance": "must"},
        ],
    },
    {
        "job": {
            "id": "3D Graphics Engineer",
            "title": "3D Graphics Engineer",
            "company": None,
            "location": "Remote / Various",
            "type": "Full-time",
            "source": "standardized_role",
        },
        "skills": [
            {"raw_name": "C++", "normalized_name": "C++", "importance": "must"},
            {"raw_name": "OpenGL", "normalized_name": "OpenGL", "importance": "must"},
            {"raw_name": "Vulkan", "normalized_name": "Vulkan", "importance": "nice"},
            {"raw_name": "Linear Algebra", "normalized_name": "Linear Algebra", "importance": "must"},
        ],
    },
]


def run_seed(graph_service: Any, data_dir: Path = DATA_DIR, job_count: int = DEMO_JOB_COUNT) -> dict[str, Any]:
    """Seed jobs (via the real ingestion pipeline), courses, and demo
    students into `graph_service`. Returns a small summary dict, useful for
    both the CLI entrypoint and tests."""
    kaggle_csv = data_dir / "kaggle_jobs.csv"
    synonyms_path = data_dir / "synonyms.json"
    onet_path = data_dir / "onet_skills.csv"

    ingestion_agent = IngestionAgent()
    ingestion_result = ingestion_agent.read_csv(kaggle_csv)
    curated_records = ingestion_result.records[:job_count]

    normalization_agent = NormalizationAgent(
        graph_service=graph_service,
        synonyms_path=synonyms_path,
        onet_skills_path=onet_path,
    )
    normalization_stats = normalization_agent.process_and_write(curated_records)

    for role_data in STANDARDIZED_ROLES:
        graph_service.ingest_job_posting(role_data["job"], role_data["skills"])

    for course in DEMO_COURSES:
        graph_service.seed_course(course)

    for student in DEMO_STUDENTS:
        graph_service.upsert_student_node(
            student_id=student["id"],
            skills=student["skills"],
            target_roles=student["target_roles"],
        )

    return {
        "jobs_seeded": len(curated_records),
        "standardized_roles_seeded": len(STANDARDIZED_ROLES),
        "courses_seeded": len(DEMO_COURSES),
        "students_seeded": len(DEMO_STUDENTS),
        **normalization_stats.as_dict(),
    }


def main() -> None:
    graph_service = GraphService(get_driver())
    graph_service.ensure_constraints()
    summary = run_seed(graph_service)
    print("Demo data seed complete:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
