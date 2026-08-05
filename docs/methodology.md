# Methodology

## Introduction

CareerGraph is an agent-based career intelligence platform designed to bridge the gap between university students' current skill profiles and the real demands of the modern jobmarket. The methodology underpinning this system combines knowledge graph reasoning, algorithmic analysis, and optional large language model (LLM) integration to deliver personalized, explainable, and actionable career guidance.

The development process follows a **Test-Driven Development (TDD)** approach embedded within an iterative Agile workflow. A full backend with 87 passing tests was built before any frontend work began, ensuring a stable and well-defined API contract. The system design is informed by an extensive literature review of over 20 papers covering career recommendation systems, knowledge graphs for skill modeling, explainable AI, and jobmarket intelligence.

Rather than relying on opaque machine learning models, CareerGraph employs a transparent, multi-agent architecture. Four pure algorithmic agents — operating without any LLM dependency — compute skill gap scores, ranked job recommendations, learning roadmaps, and market demand trends using well-understood graph algorithms (Jaccard similarity, BFS, Kahn's topological sort). An optional LLM-powered Reasoning Agent sits on top of these results to generate natural language explanations, degrading gracefully to template-based responses when no LLM provider is configured.

This chapter details the system architecture, feasibility analysis, requirements specification, and complete design artifacts for the CareerGraph platform.

---

## 1.1 System Architecture

CareerGraph is structured as a three-tier architecture: a **Presentation Layer** (React frontend), an **Application Layer** (FastAPI backend with a multi-agent Intelligence Engine), and a **Data Layer** (dual-database: PostgreSQL + Neo4j).

```mermaid
%%{init: {"layout": "elk"}}%%
graph TB
    subgraph "Presentation Layer"
        FE["React Frontend\nTypeScript · Vite · TailwindCSS"]
    end

    subgraph "Application Layer"
        API["FastAPI · Python 3.11\n8 Student Routers + Admin Ingest"]
        IE["Intelligence Engine\nEngineOrchestrator + 7 Agents"]
        GS["GraphService\nNeo4j Cypher Abstraction"]
    end

    subgraph "Data Layer"
        PG[("PostgreSQL 15\nUsers & Profiles")]
        NEO[("Neo4j 5\nKnowledge Graph")]
    end

    subgraph "External Services"
        LLM["LLM Providers\nClaude · OpenAI · Ollama"]
        DS["Data Sources\nKaggle CSV · O*NET · synonyms.json"]
    end

    FE -->|"REST + JWT"| API
    API --> IE
    API --> PG
    IE --> GS
    GS --> NEO
    IE -.->|"optional"| LLM
    DS -->|"admin ingest"| IE
```

The diagram illustrates CareerGraph's three-tier architecture. The React frontend communicates with the FastAPI backend over REST, which delegates intelligence tasks to the multi-agent Engine while persisting relational data in PostgreSQL and graph data in Neo4j. LLM providers are an optional external dependency, invoked only when natural language explanations are requested.

**Presentation Layer** — A React 18 single-page application built with TypeScript and Vite. It communicates exclusively via REST API calls, using TanStack Query for server-state caching and Axios for HTTP transport.

**Application Layer** — A FastAPI application exposing 13 REST endpoints across 8 resource groups, all prefixed under `/api/v1`. The Intelligence Engine is composed of seven specialized agents, each with a single responsibility, coordinated by the `EngineOrchestrator`.

**Data Layer** — A dual-database strategy: PostgreSQL stores structured relational data (users, authentication, profiles) with ACID guarantees; Neo4j stores the semantic knowledge graph (skills, jobs, prerequisites, courses) enabling graph traversal queries that are expensive or impossible in a relational model.

---

## 1.2 Feasibility Study

### 1.2.1 Economic Feasibility

CareerGraph is designed to be deployable at near-zero infrastructure cost during the academic phase, with a clear path to production scalability.

**Development Cost:**
All core technologies — FastAPI, React, PostgreSQL, Neo4j Community Edition, and Python — are open-source and free to use. The Intelligence Engine's algorithmic agents (Jaccard similarity, BFS, topological sort) operate without LLM API calls, keeping inference costs at zero for all core functionality. LLM integration is fully optional; the system degrades gracefully to template-based responses when no LLM provider is configured, eliminating mandatory API fees.

**Deployment Cost:**
A Docker Compose configuration enables a complete local deployment with four containers (PostgreSQL, Neo4j, FastAPI, and Vite frontend) using a single command. Cloud deployment requires only a small VM (2 vCPU, 4 GB RAM) for development use. PostgreSQL and Neo4j Community Edition are both free; Neo4j Enterprise is only necessary at enterprise scale.

**Data Cost:**
The system uses a custom-authored Kaggle dataset of 10,000 realistic job postings and the freely available O\*NET skill taxonomy. A curated synonym map (`synonyms.json`) eliminates ongoing data-cleaning jobby automating skill name canonicalization.

**Return on Investment:**

- Reduction in career counseling overhead for academic institutions
- Personalized, data-driven guidance reduces misaligned educational investment
- Transparent, explainable recommendations improve student trust and engagement
- Reusable multi-agent architecture can be extended to new datasets or institutions at marginal cost

---

### 1.2.2 Technical Feasibility

All technologies chosen for CareerGraph are production-proven, well-documented, and available as stable releases:

| Component           | Technology              | Version        | Maturity                      |
| ------------------- | ----------------------- | -------------- | ----------------------------- |
| Web Framework       | FastAPI                 | 0.115.6        | Production-grade ASGI         |
| Graph Database      | Neo4j                   | 5              | Industry standard, 10+ years  |
| Relational Database | PostgreSQL              | 15             | Industry standard, 30+ years  |
| ORM & Migrations    | SQLAlchemy + Alembic    | 2.0.36 / 1.14  | Production-grade              |
| Frontend            | React + TypeScript      | 18.3.1 / 5.6.3 | Industry standard             |
| Containerization    | Docker Compose          | v2             | Industry standard             |
| LLM Integration     | Anthropic SDK           | 0.40.0         | Production-grade              |
| Fuzzy Matching      | rapidfuzz               | 3.11.0         | C-extension, production-grade |
| Testing             | pytest + pytest-asyncio | 8.3.4 / 0.24.0 | Industry standard             |

The multi-agent architecture leverages established graph algorithms — Jaccard similarity, breadth-first search, and Kahn's topological sort — all with known time complexity bounds and deterministic, unit-testable behavior. The pluggable LLM provider layer (with Claude, OpenAI, and Ollama implementations behind a shared abstract base class) ensures no vendor lock-in.

Technical feasibility is validated by a completed backend implementation with 87 passing tests across all agents, routers, and services.

---

### 1.2.3 Operational Feasibility

**For Students:**
The platform is web-based and accessible from any modern browser with no installation required. Profile creation takes under five minutes (skills, major, target roles). Recommendations and skill gap analyses are generated in real time (under two seconds). All recommendations include human-readable explanations, not just raw scores, improving student comprehension and trust.

**For Administrators:**
A single protected endpoint (`POST /admin/ingest/csv`) handles all data ingestion. CSV-based ingestion accommodates the standard Kaggle dataset format. Fuzzy skill normalization reduces the burden of maintaining exact skill name mappings, with the `NormalizationAgent` handling synonym resolution automatically.

**For Institutions:**
Docker Compose deployment allows IT staff to start the entire system with a single command. Environment-variable-based configuration (no hardcoded secrets) matches standard DevOps practices. Alembic database migrations provide reproducible, version-controlled schema setup across environments.

---

## 1.3 Requirement Analysis

### 1.3.1 Functional Requirements

The functional requirements define what the system must do from the perspective of its users. The twelve requirements below were derived from the core use cases of the platform — student career guidance and administrator data management — and are prioritised by their impact on the system's primary value proposition. High-priority requirements cover the full intelligence pipeline (authentication, profile management, gap analysis, recommendations, roadmap, and market trends), while medium and low priorities address supporting features such as the dashboard, job explorer, and LLM-enriched explanations.

| ID    | Requirement                                                                                                                                     | Priority |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| FR-01 | Users shall be able to register and log in using email and password                                                                             | High     |
| FR-02 | Authenticated users shall be able to create and update a student profile with skills, major, graduation year, and target roles                  | High     |
| FR-03 | The system shall compute a weighted readiness score for a student against any target job based on their skill profile                           | High     |
| FR-04 | The system shall generate a ranked list of job recommendations using Jaccard similarity and partial skill overlap scoring                       | High     |
| FR-05 | The system shall identify skill gaps (missing and partially met skills) for any target job                                                      | High     |
| FR-06 | The system shall generate an ordered learning roadmap from the student's current skills to target job requirements via BFS and topological sort | High     |
| FR-07 | The system shall provide market demand intelligence showing in-demand skills and categories across all ingested jobs                            | High     |
| FR-08 | The system shall provide a dashboard with summary KPIs (readiness score, matched jobs, skill counts, missing high-demand skills)                | Medium   |
| FR-09 | Administrators shall be able to ingest job data from CSV files via a protected endpoint                                                         | Medium   |
| FR-10 | The system shall provide LLM-generated natural language explanations for all algorithmic outputs when an LLM provider is configured             | Medium   |
| FR-11 | The system shall provide a searchable, filterable job explorer with pagination                                                                  | Medium   |
| FR-12 | The system shall expose a paginated skill catalog and market skill demand listing                                                               | Low      |

---

### 1.3.2 Non-Functional Requirements

The non-functional requirements define the quality attributes the system must satisfy regardless of specific features. They span six dimensions critical for an academic-grade platform: performance ensures recommendations are returned within two seconds; reliability guarantees the system remains fully operational even without an LLM provider; security protects user data through JWT gating, bcrypt password hashing, and parameterised queries; maintainability is enforced through a comprehensive test suite; and portability and scalability ensure the system can be deployed and extended with minimal friction.

| ID     | Requirement                                                                                 | Measure                                                               |
| ------ | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| NFR-01 | **Performance** — API response time for recommendation and gap analysis queries             | < 2 seconds for up to 1,000 jobs                                      |
| NFR-02 | **Reliability** — System shall degrade gracefully when no LLM provider is configured        | Template fallback always returns a valid, structured response         |
| NFR-03 | **Security** — All non-public endpoints shall require JWT authentication                    | 11 of 13 endpoints require a valid Bearer token                       |
| NFR-04 | **Security** — Passwords shall be stored as bcrypt hashes                                   | bcrypt cost factor ≥ 12                                               |
| NFR-05 | **Security** — All database queries shall use parameterized inputs to prevent injection     | Zero string-interpolated SQL or Cypher queries                        |
| NFR-06 | **Maintainability** — Test coverage shall span all agents, routers, and services            | 87 tests across 19 test files, all passing                            |
| NFR-07 | **Portability** — The full system shall run in Docker without host environment dependencies | Single `docker-compose up` startup                                    |
| NFR-08 | **Scalability** — Database connections shall use async pooling                              | asyncpg for PostgreSQL; neo4j native driver for Neo4j                 |
| NFR-09 | **Explainability** — All recommendations shall include a human-readable explanation         | Responses include matched skills, missing skills, and readiness score |
| NFR-10 | **Usability** — UI shall be responsive and accessible from standard desktop browsers        | React 18 + TailwindCSS + shadcn/ui                                    |

---

### 1.3.3 Tools & Technology

**Backend**

| Tool           | Version | Purpose                                            |
| -------------- | ------- | -------------------------------------------------- |
| Python         | 3.11    | Core language                                      |
| FastAPI        | 0.115.6 | REST API framework (ASGI)                          |
| Uvicorn        | 0.32.1  | ASGI production/dev server                         |
| Pydantic       | 2.10.4  | Request/response validation and LLM output schemas |
| SQLAlchemy     | 2.0.36  | ORM for PostgreSQL                                 |
| Alembic        | 1.14.0  | Database schema migrations                         |
| asyncpg        | 0.30.0  | Async PostgreSQL driver                            |
| neo4j          | 5.26.0  | Neo4j graph database driver                        |
| python-jose    | 3.3.0   | JWT encoding and decoding                          |
| bcrypt         | 4.2.1   | Password hashing                                   |
| rapidfuzz      | 3.11.0  | Fuzzy skill name matching (C-extension)            |
| anthropic      | 0.40.0  | Claude LLM SDK                                     |
| openai         | 1.58.1  | GPT-4o LLM SDK                                     |
| pandas         | 2.2.3   | CSV data processing for ingestion                  |
| pytest         | 8.3.4   | Test framework                                     |
| pytest-asyncio | 0.24.0  | Async test support                                 |

**Frontend**

| Tool           | Version | Purpose                      |
| -------------- | ------- | ---------------------------- |
| React          | 18.3.1  | UI component framework       |
| TypeScript     | 5.6.3   | Static type safety           |
| Vite           | 6.0.5   | Build tool and dev server    |
| React Router   | v6      | Client-side routing          |
| TanStack Query | 5.62.7  | Server-state caching         |
| Axios          | 1.7.9   | HTTP client                  |
| TailwindCSS    | 3.4.17  | Utility-first CSS framework  |
| shadcn/ui      | Latest  | Accessible component library |

**Infrastructure & Databases**

| Tool           | Version       | Purpose                                     |
| -------------- | ------------- | ------------------------------------------- |
| PostgreSQL     | 15            | Relational database — users, auth, profiles |
| Neo4j          | 5 (Community) | Graph database — knowledge graph            |
| Docker         | Latest        | Containerization                            |
| Docker Compose | v2            | Multi-service orchestration                 |
| python-dotenv  | Latest        | Environment variable management             |

**Data Sources**

| Source                                    | Content                                                             | Use                                     |
| ----------------------------------------- | ------------------------------------------------------------------- | --------------------------------------- |
| Kaggle Job Dataset (`kaggle_jobs.csv`)    | 10,000 job postings: title, company, location, type, salary, skills | Primary job data for ingestion          |
| O\*NET Skill Taxonomy (`onet_skills.csv`) | Standard skill vocabulary and categories                            | Canonical skill names for normalization |
| Synonym Map (`synonyms.json`)             | ~500 skill name variants (e.g., `ReactJS → React`)                  | Bootstrap for fuzzy matching            |

---

## 1.4 System Design

### 1.4.1 Development Model

CareerGraph follows an **Agile TDD (Test-Driven Development)** model executed in four sequential phases. Each phase begins with writing tests before any implementation — the canonical Red → Green → Refactor cycle.

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    subgraph "Phase 1 — Foundation"
        P1A[Requirements\n& Design]
        P1B[Database Schema\n& Migrations]
        P1A --> P1B
    end

    subgraph "Phase 2 — Intelligence Engine"
        P2A["Write Agent Tests\n(Red)"]
        P2B["Implement Agents\n(Green)"]
        P2C["Refactor\n(Clean)"]
        P2A --> P2B --> P2C
    end

    subgraph "Phase 3 — API Layer"
        P3A["Write Router Tests\n(Red)"]
        P3B["Implement REST API\n(Green)"]
        P3C["Refactor\n(Clean)"]
        P3A --> P3B --> P3C
    end

    subgraph "Phase 4 — Frontend"
        P4A[React UI\nComponents]
        P4B[Integration\n& Testing]
        P4A --> P4B
    end

    P1B --> P2A
    P2C --> P3A
    P3C --> P4A
```

The diagram maps the four sequential development phases followed during the project. Each phase adheres to the TDD Red → Green → Refactor cycle, with later phases building on the stable contracts established by earlier ones. This ensured all 87 backend tests were passing before any frontend work began.

**TDD Cycle:**

1. Write a failing test that describes the required behavior
2. Implement the minimum code necessary to pass the test
3. Refactor for clarity without breaking tests
4. Repeat for the next requirement

This approach produced 87 unit and integration tests (all passing) before the frontend work began, ensuring a stable, reliable API contract for frontend integration.

---

### 1.4.2 Use Case Diagram

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    Student(["Student"])
    Admin(["System Administrator"])
    LLM(["LLM Provider\nClaude / OpenAI / Ollama"])

    subgraph "CareerGraph System"
        UC1["Register & Login"]
        UC2["Manage Profile & Skills"]
        UC3["View Dashboard KPIs"]
        UC4["Explore Job Listings"]
        UC5["Get Job Recommendations"]
        UC6["Analyze Skill Gaps"]
        UC7["View Learning Roadmap"]
        UC8["Explore Market Trends"]
        UC9["Ingest Job Data from CSV"]
        UC10["Generate AI Explanations\n(optional)"]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8

    Admin --> UC1
    Admin --> UC9

    UC5 -.->|"«extend»"| UC10
    UC6 -.->|"«extend»"| UC10
    UC7 -.->|"«extend»"| UC10
    UC8 -.->|"«extend»"| UC10
    UC10 --> LLM

    UC2 -.->|"«include»"| UC3
    UC6 -.->|"«include»"| UC7
```

The diagram identifies the two primary actors — Student and System Administrator — and the ten use cases available to them. Four intelligence features optionally extend to AI-generated explanations via an external LLM provider. Profile management is included in the dashboard view, and gap analysis includes the learning roadmap as a dependent sub-feature.

---

### 1.4.3 Context Diagram

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    subgraph "External Entities"
        S["Student\n(Browser)"]
        A["System Admin"]
        K["Kaggle CSV\nJob Dataset"]
        ONET["O*NET Taxonomy\nSkill Standards"]
        CLD["Anthropic API\n(Claude)"]
        OAI["OpenAI API\n(GPT-4o)"]
        OLL["Ollama\n(Local LLM)"]
    end

    subgraph "CareerGraph System Boundary"
        CG["CareerGraph\nPlatform"]
    end

    subgraph "Internal Data Stores"
        PG[("PostgreSQL\nRelational DB")]
        N4[("Neo4j\nKnowledge Graph")]
    end

    S -->|"Credentials, Profile,\nSkills, Career Goals"| CG
    CG -->|"Recommendations, Gap Scores,\nRoadmap, Dashboard KPIs"| S

    A -->|"CSV Job Data\n(Admin Ingest)"| CG
    K -->|"10,000 Job Postings\nwith Skill Requirements"| CG
    ONET -->|"Canonical Skill Names\n& Taxonomy"| CG

    CG -->|"User Auth &\nProfile CRUD"| PG
    CG -->|"Graph Queries\n& Traversal"| N4

    CG -->|"Explanation Prompt\n+ Algorithmic Context"| CLD
    CG -->|"Explanation Prompt\n+ Algorithmic Context"| OAI
    CG -->|"Explanation Prompt\n+ Algorithmic Context"| OLL

    CLD -->|"Natural Language\nExplanation"| CG
    OAI -->|"Natural Language\nExplanation"| CG
    OLL -->|"Natural Language\nExplanation"| CG
```

The diagram defines the system boundary of CareerGraph and its interactions with all external entities. Students submit profile and career goal data and receive personalised recommendations and analyses in return. Administrators supply job data via CSV upload, while optional LLM providers are called only to generate natural language explanations on top of algorithmic outputs.

---

### 1.4.4 Data Flow Diagram

**Level 0 — Top-Level System**

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart LR
    STU(["Student"])
    ADM(["Admin"])
    SYS["CareerGraph\nSystem"]
    PG[("PostgreSQL")]
    N4[("Neo4j")]

    STU -->|"Profile, Skills,\nCareer Goals"| SYS
    SYS -->|"Recommendations,\nGap Analysis, Roadmap"| STU

    ADM -->|"CSV Job Data"| SYS

    SYS <-->|"Auth & Profile Data"| PG
    SYS <-->|"Knowledge Graph Data"| N4
```

This top-level diagram presents CareerGraph as a single processing unit, showing the two primary inputs — student career data and administrator job uploads — and the two internal data stores that underpin all system operations.

**Level 1 — Core Processes**

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    STU(["Student"])
    ADM(["Admin"])
    PG[("PostgreSQL")]
    N4[("Neo4j\nKnowledge Graph")]

    subgraph P1["Process 1: Auth & Profile"]
        P1A["Register / Login"]
        P1B["Manage Profile"]
    end

    subgraph P2["Process 2: Intelligence Engine"]
        P2A["Skill Gap Analysis\nSkillGapAgent"]
        P2B["Job Recommendations\nRecommendationAgent"]
        P2C["Learning Roadmap\nPathFinderAgent"]
        P2D["Market Intelligence\nMarketAgent"]
    end

    subgraph P3["Process 3: Data Ingestion"]
        P3A["Parse CSV\nIngestionAgent"]
        P3B["Normalize Skills\nNormalizationAgent"]
        P3C["Write to Graph\nGraphService"]
    end

    subgraph P4["Process 4: LLM Reasoning"]
        P4A["Generate Explanation\nReasoningAgent"]
    end

    STU -->|"Credentials"| P1A
    P1A -->|"JWT Token"| STU
    P1A -->|"User Record"| PG
    STU -->|"Skills, Goals"| P1B
    P1B -->|"Profile Data"| PG
    P1B -->|"Student Node"| N4

    STU -->|"Analyze Gap"| P2A
    P2A -->|"Student + Job Skills"| N4
    P2A -->|"Gap Result + Score"| P2C
    P2A -->|"Gap Result"| P4A
    P2C -->|"Prereq Graph"| N4
    P2C -->|"Learning Path"| P4A

    STU -->|"Get Recommendations"| P2B
    P2B -->|"All Jobs + Skills"| N4
    P2B -->|"Ranked Jobs"| P4A

    STU -->|"Market Trends"| P2D
    P2D -->|"Skill Demand Data"| N4
    P2D -->|"Trend Data"| P4A

    P4A -->|"Recommendations, Gap Analysis,\nRoadmap, Market Insights"| STU

    ADM -->|"CSV File"| P3A
    P3A -->|"Raw Job Records"| P3B
    P3B -->|"Normalized Jobs"| P3C
    P3C -->|"Job + Skill Nodes\n& Relationships"| N4
```

The Level 1 diagram decomposes the system into four core processes: authentication and profile management, the intelligence engine, data ingestion, and LLM reasoning. Data flows illustrate how student inputs trigger graph queries, and how algorithmic results are optionally enriched by the ReasoningAgent before being returned to the user.

**Level 2 — Skill Gap Analysis Detail**

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    REQ(["API Request\nPOST /gap-analysis\n{target_job_id}"])

    REQ --> G1["Fetch Student Skills\nHAS_SKILL edges from Neo4j"]
    REQ --> G2["Fetch Job Requirements\nREQUIRES edges from Neo4j"]

    G1 --> CALC["SkillGapAgent\nWeighted Readiness Calculation"]
    G2 --> CALC

    CALC --> C1["Must-Have Skills\nmatched / total × 0.7"]
    CALC --> C2["Nice-to-Have Skills\nmatched / total × 0.3"]
    C1 --> SCORE["readiness_score =\nmust_score + nice_score\n+ proficiency_bonus"]
    C2 --> SCORE

    SCORE --> PATH["PathFinderAgent\nBFS on LEADS_TO graph\nfrom missing skills\nTopological sort → ordered path\nAttach TEACHES courses"]

    PATH --> LLM_CHK{"LLM Provider\nConfigured?"}
    LLM_CHK -->|"Yes"| LLM["ReasoningAgent\nexplain_gap() + write_roadmap()\nvia LLMProvider.complete()"]
    LLM_CHK -->|"No"| TPL["Template Fallback\nStructured Response"]

    LLM --> RESP(["GapAnalysisResponse\n+ RoadmapResponse"])
    TPL --> RESP
```

This diagram details the internal data flows of the skill gap analysis feature. The SkillGapAgent fetches the student's skills and the job's requirements from Neo4j and computes a weighted readiness score, which is then passed to the PathFinderAgent to generate an ordered learning path. The final response is either enriched by the ReasoningAgent or constructed from a structured template fallback.

---

### 1.4.5 Entity-Relationship Diagram

```mermaid
%%{init: {"layout": "elk"}}%%
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar name
        timestamp created_at
        timestamp updated_at
    }

    STUDENT_PROFILES {
        uuid id PK
        uuid user_id FK
        varchar major
        int graduation_year
        jsonb skills
        jsonb target_roles
        jsonb experience
        timestamp updated_at
    }

    SKILL {
        string name PK
        string normalized_name
        string category
        string level
    }

    JOB {
        string id PK
        string title
        string company
        string location
        string employment_type
        int salary_min
        int salary_max
        text description
        date posted_date
    }

    COURSE {
        string id PK
        string title
        string provider
        string url
        string difficulty
        bool free
    }

    CATEGORY {
        string name PK
        string description
        string parent_category
    }

    USERS ||--|| STUDENT_PROFILES : "has one"

    STUDENT_PROFILES }o--o{ SKILL : "HAS_SKILL\n{proficiency: 0-10, years: float}"
    STUDENT_PROFILES }o--o{ JOB : "TARGETS"
    JOB }o--o{ SKILL : "REQUIRES\n{importance: must/nice, frequency: int}"
    SKILL ||--o{ SKILL : "LEADS_TO\n{difficulty_jump: int}"
    COURSE }o--o{ SKILL : "TEACHES"
    SKILL }o--|| CATEGORY : "BELONGS_TO"
    JOB }o--|| CATEGORY : "IN_CATEGORY"
```

The diagram models all data entities and their relationships across both databases. Users and student profiles are stored in PostgreSQL for ACID compliance, while skills, jobs, courses, and categories — along with their semantic relationships — reside in the Neo4j knowledge graph. Relationship attributes such as proficiency level, skill importance, and difficulty jump are captured directly on the edges.

> **Note on dual-database design:** `USERS` and `STUDENT_PROFILES` are stored in PostgreSQL for ACID-compliant relational operations. All other entities (`SKILL`, `JOB`, `COURSE`, `CATEGORY`) and their relationships exist in the Neo4j knowledge graph, where graph traversal queries enable prerequisite reasoning and skill proximity scoring.

---

### 1.4.6 Database Schema Diagram

**PostgreSQL — Relational Schema**

```mermaid
%%{init: {"layout": "elk"}}%%
classDiagram
    class users {
        +UUID id PK
        +VARCHAR(255) email UNIQUE NOT NULL
        +VARCHAR(255) hashed_password
        +VARCHAR(255) name
        +TIMESTAMP created_at
        +TIMESTAMP updated_at
    }

    class student_profiles {
        +UUID id PK
        +UUID user_id FK NOT NULL
        +VARCHAR(255) major
        +INT graduation_year
        +JSONB skills
        +JSONB target_roles
        +JSONB experience
        +TIMESTAMP updated_at
    }

    users "1" --> "0..1" student_profiles : "user_id (FK)"
```

The relational schema stores only the data that requires ACID compliance: user credentials and student profiles. A one-to-one foreign key relationship links each authenticated user to their corresponding profile record in PostgreSQL.

**Neo4j — Knowledge Graph Node & Relationship Schema**

```mermaid
%%{init: {"layout": "elk"}}%%
graph LR
    STU(["Student\n─────────────\nid: string\nuser_id: string\nname: string\nemail: string\ntarget_roles: list"])
    SKL(["Skill\n─────────────\nid: string\nname: string\nnormalized_name: string\ncategory: string\nlevel: string"])
    JOB(["Job\n─────────────\nid: string\ntitle: string\ncompany: string\nlocation: string\nemployment_type: string\nsalary_min: int\nsalary_max: int"])
    CRS(["Course\n─────────────\nid: string\ntitle: string\nprovider: string\nurl: string\ndifficulty: string\nfree: boolean"])
    CAT(["Category\n─────────────\nname: string\ndescription: string\nparent_category: string"])

    STU -->|"HAS_SKILL\n{proficiency: 0–10\nyears: float}"| SKL
    STU -->|"TARGETS"| JOB
    JOB -->|"REQUIRES\n{importance: must/nice\nfrequency: int}"| SKL
    SKL -->|"LEADS_TO\n{difficulty_jump: int}"| SKL
    CRS -->|"TEACHES"| SKL
    SKL -->|"BELONGS_TO"| CAT
    JOB -->|"IN_CATEGORY"| CAT
```

The relational schema stores only the data that requires ACID compliance: user credentials and student profiles. A one-to-one foreign key relationship links each authenticated user to their corresponding profile record in PostgreSQL.

**Seed Data at Demo Scale / Full Scale**

| Node Type | Demo Seed | Full Dataset (Kaggle)  |
| --------- | --------- | ---------------------- |
| Student   | 3         | — (user-created)       |
| Job       | 50        | 10,000+                |
| Skill     | 80        | 500+ (O\*NET taxonomy) |
| Course    | 30        | 30                     |
| Category  | 7         | 20+                    |

---

### 1.4.7 System Flowchart — Part A: User Session & Job Exploration

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    START(["User Visits CareerGraph"])

    START --> AUTH{"Authenticated\n(JWT Valid)?"}
    AUTH -->|"No"| LOGIN["Login / Register Page"]
    LOGIN -->|"Submit Credentials"| VALIDATE{"Valid\nCredentials?"}
    VALIDATE -->|"No"| ERR["Show Error Message"]
    ERR --> LOGIN
    VALIDATE -->|"Yes"| JWT_ISSUE["Issue JWT Token\nHS256 · 24h Expiry"]
    JWT_ISSUE --> DASH

    AUTH -->|"Yes"| DASH["Load Dashboard\nFetch KPIs from EngineOrchestrator"]

    DASH --> PROFILE_CHK{"Profile\nComplete?"}
    PROFILE_CHK -->|"No"| SETUP["Profile Setup\nAdd Skills, Major, Target Roles"]
    SETUP --> SAVE_PROF["Save to PostgreSQL\nSync Student Node → Neo4j"]
    SAVE_PROF --> DASH
    PROFILE_CHK -->|"Yes"| NAV["Main Navigation"]

    NAV -->|"Explore Jobs"| JOB_PAGE["Job Explorer\nSearch & Filter · GET /jobs"]
    NAV -->|"Recommendations"| REC(["→ See Part B"])
    NAV -->|"Skill Gap"| GAP(["→ See Part B"])
    NAV -->|"Learning Roadmap"| ROAD(["→ See Part B"])
    NAV -->|"Market Trends"| MKT(["→ See Part B"])

    JOB_PAGE --> JOB_DETAIL["View Job Detail\nGET /jobs/:id"]
    JOB_DETAIL --> DO_GAP{"Analyze\nThis Job?"}
    DO_GAP -->|"Yes"| GAP2(["→ Gap Analysis · Part B"])
    DO_GAP -->|"No"| NAV
```

Part A covers everything that happens before a student reaches the core intelligence features. When a user first visits the platform, the system checks whether a valid JWT token exists. If not, the user is directed to the login or registration page; on successful credential validation, a signed HS256 token with a 24-hour expiry is issued and the Dashboard is loaded. The Dashboard then checks whether the student's profile is complete — if skills, major, and target roles have not been filled in, the user is redirected to the Profile Setup page, which saves the data to PostgreSQL and simultaneously syncs a Student node into Neo4j. Once the profile is confirmed complete, the student reaches the Main Navigation hub, from which they can explore the Job Explorer or proceed to any of the four intelligence features covered in Part B. Within the Job Explorer, a student can browse and filter job listings and open a specific job's detail page; from there they may choose to trigger a gap analysis for that job, which hands off to the flow described in Part B.

---

### 1.4.7 System Flowchart — Part B: Intelligence Engine & Admin Flow

```mermaid
%%{init: {"layout": "elk"}}%%
flowchart TD
    NAV(["Main Navigation\n← from Part A"])

    NAV --> REC_REQ["GET /recommendations/jobs"]
    REC_REQ --> JAC["RecommendationAgent\nJaccard exact + LEADS_TO partial\nfinal = exact×0.8 + partial×0.2"]
    JAC --> REC_LLM{"LLM\nConfigured?"}
    REC_LLM -->|"Yes"| REC_NARRATE["ReasoningAgent\nnarrate_recommendations()\nRe-rank + why_recommended"]
    REC_LLM -->|"No"| REC_TMPL["Top 10 with\nTemplate Narratives"]
    REC_NARRATE --> REC_DISPLAY["Display Ranked Jobs\nwith Explanations"]
    REC_TMPL --> REC_DISPLAY

    NAV --> GAP_REQ["POST /gap-analysis · {target_job_id}"]
    GAP_REQ --> GAP_FETCH["GraphService\nFetch HAS_SKILL + REQUIRES edges"]
    GAP_FETCH --> GAP_CALC["SkillGapAgent\nreadiness = must×0.7 + nice×0.3\n+ proficiency_bonus"]
    GAP_CALC --> GAP_PATH["PathFinderAgent\nBFS on LEADS_TO → topological sort\nAttach TEACHES courses"]
    GAP_PATH --> GAP_LLM{"LLM\nConfigured?"}
    GAP_LLM -->|"Yes"| GAP_EXPLAIN["ReasoningAgent\nexplain_gap() + write_roadmap()"]
    GAP_LLM -->|"No"| GAP_TMPL["Template Response"]
    GAP_EXPLAIN --> GAP_DISPLAY["Display Gap Score\nMissing Skills + Roadmap"]
    GAP_TMPL --> GAP_DISPLAY

    NAV --> ROAD_REQ["GET /skills/gap\nPathFinderAgent learning path"]
    ROAD_REQ --> ROAD_DISPLAY["Weekly Milestones\nSkill → Course → Goal"]

    NAV --> MKT_REQ["GET /market/insights"]
    MKT_REQ --> MKT_AGG["MarketAgent\nREQUIRES count per Skill\nNormalized 0–100"]
    MKT_AGG --> MKT_LLM{"LLM\nConfigured?"}
    MKT_LLM -->|"Yes"| MKT_SUM["ReasoningAgent\nsummarize_market()\n3 trend bullets"]
    MKT_LLM -->|"No"| MKT_TMPL["Raw Demand Data"]
    MKT_SUM --> MKT_DISPLAY["Market Trends\nTop Skills & Categories"]
    MKT_TMPL --> MKT_DISPLAY

    REC_DISPLAY --> NAV
    GAP_DISPLAY --> NAV
    ROAD_DISPLAY --> NAV
    MKT_DISPLAY --> NAV

    subgraph "Admin Flow"
        ADM_LOGIN(["Admin Login"])
        ADM_UPLOAD["POST /admin/ingest/csv"]
        INGEST_AGENT["IngestionAgent\nParse & validate CSV"]
        NORM_AGENT["NormalizationAgent\nSynonym match + rapidfuzz ≥ 90"]
        GRAPH_WRITE["GraphService\nMERGE Job + Skill nodes\nCREATE REQUIRES edges"]
        ADM_DONE(["Ingest Complete"])

        ADM_LOGIN --> ADM_UPLOAD --> INGEST_AGENT --> NORM_AGENT --> GRAPH_WRITE --> ADM_DONE
    end
```

Part B covers the four intelligence features branching from the Main Navigation hub, plus the separate administrator ingestion flow. For recommendations, the RecommendationAgent scores every job using a composite Jaccard similarity (80% exact skill match, 20% LEADS_TO proximity) and returns the ranked results. For skill gap analysis, the SkillGapAgent computes a weighted readiness score against the target job, and the PathFinderAgent follows up with a BFS over the prerequisite graph to produce an ordered learning roadmap with attached courses. The market trends feature aggregates REQUIRES edge counts per skill across all jobs and normalises them to a 0–100 demand score. All four features share the same final step: results are either enriched with natural language by the ReasoningAgent when an LLM provider is configured, or returned as structured template responses. The admin flow runs independently — uploaded CSV data is parsed by the IngestionAgent, skill names are normalised via synonym matching and fuzzy scoring, and the resulting job and skill nodes are written into the Neo4j knowledge graph.
