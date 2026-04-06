# CareerGraph — System Design Document
### Agent-Based Labor Market Intelligence Platform for Student Career Guidance

> **Version:** 3.0 | **Date:** April 2026
> **Stack:** React · FastAPI · Neo4j · PostgreSQL · Multi-Agent Intelligence Engine · Pluggable LLM

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Scope](#2-project-scope)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Technology Stack](#4-technology-stack)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Backend Architecture](#6-backend-architecture)
7. [Database Design](#7-database-design)
   - 7.1 [PostgreSQL — Relational Schema](#71-postgresql--relational-schema)
   - 7.2 [Neo4j — Knowledge Graph Schema](#72-neo4j--knowledge-graph-schema)
8. [API Contract](#8-api-contract)
9. [Intelligence Engine — Agent Architecture](#9-intelligence-engine--agent-architecture)
   - 9.1 [Agent Overview](#91-agent-overview)
   - 9.2 [Ingestion Pipeline](#92-ingestion-pipeline)
   - 9.3 [Algorithmic Agents](#93-algorithmic-agents)
   - 9.4 [LLM Provider Abstraction](#94-llm-provider-abstraction)
   - 9.5 [Reasoning Agent](#95-reasoning-agent)
   - 9.6 [Engine Orchestrator](#96-engine-orchestrator)
10. [Data Sources](#10-data-sources)
11. [Data Flow Diagrams](#11-data-flow-diagrams)
    - 11.1 [Authentication Flow](#111-authentication-flow)
    - 11.2 [Recommendation Flow](#112-recommendation-flow)
    - 11.3 [Skill Gap Analysis Flow](#113-skill-gap-analysis-flow)
    - 11.4 [Ingestion Pipeline Flow](#114-ingestion-pipeline-flow)
12. [Sequence Diagrams](#12-sequence-diagrams)
    - 12.1 [User Login & Dashboard Load](#121-user-login--dashboard-load)
    - 12.2 [Skill Gap Analysis Request](#122-skill-gap-analysis-request)
    - 12.3 [Job Recommendation Request](#123-job-recommendation-request)
13. [Component Diagram](#13-component-diagram)
14. [Deployment Architecture](#14-deployment-architecture)
15. [Security Design](#15-security-design)
16. [Data Models — API Contracts](#16-data-models--api-contracts)

---

## 1. Executive Summary

CareerGraph is a full-stack, agent-based platform that helps university students navigate career transitions by combining **graph-based reasoning** with **AI-driven insights**. The system ingests real labor market data from Kaggle job datasets and O*NET skill taxonomies, models it as a knowledge graph in Neo4j, and runs a multi-agent Intelligence Engine to produce personalized, explainable recommendations.

The Intelligence Engine is the core contribution of this project. It is composed of four types of agents:

- **IngestionAgent** — ingests raw CSV and scraper data, validates schema, and feeds the normalization pipeline.
- **NormalizationAgent** — resolves skill synonyms (`ReactJS → React`, `Node → Node.js`), deduplicates entries, and ensures graph consistency before data enters Neo4j.
- **Algorithmic Agents** — four pure-Python agents (SkillGapAgent, RecommendationAgent, PathFinderAgent, MarketAgent) that compute scores, rankings, and learning paths using graph algorithms. These work with zero LLM dependency.
- **ReasoningAgent** — sits on top of algorithmic output and uses a pluggable LLM provider (Claude, OpenAI, or a local Ollama model) to generate natural language explanations and coaching narratives.

The LLM is a configurable enhancement. Removing it degrades the system gracefully — algorithmic agents continue to produce scored, structured results independently.

**Core user journeys:**
- Student registers and declares their skills and target roles
- SkillGapAgent scores their readiness against live market data using weighted graph intersection
- PathFinderAgent traverses the skill prerequisite graph (BFS + topological sort) to generate an ordered learning roadmap
- ReasoningAgent explains the gap in plain English via the configured LLM provider
- Student browses jobs matched by RecommendationAgent, filtered by type, location, and skill overlap
- Dashboard surfaces market-wide skill demand trends and readiness KPIs

**One-line pitch:**
> *CareerGraph helps students understand what skills they need to get hired by aligning their profiles with real labor market demand using a knowledge graph and explainable agent-based reasoning.*

---

## 2. Project Scope

```mermaid
graph LR
    classDef yes  fill:#10B981,stroke:#047857,color:#fff
    classDef no   fill:#EF4444,stroke:#B91C1C,color:#fff
    classDef post fill:#F59E0B,stroke:#B45309,color:#fff

    subgraph IS["This Project IS"]
        Y1[Graph-based skill reasoning]:::yes
        Y2[Explainable recommendations]:::yes
        Y3[Real labor market data]:::yes
        Y4[Modular agent architecture]:::yes
        Y5[Pluggable LLM providers]:::yes
        Y6[Skill gap analysis with roadmap]:::yes
        Y7[Scalable ingestion pipeline]:::yes
    end

    subgraph ISNOT["This Project is NOT"]
        N1[A chatbot]:::no
        N2[A resume builder]:::no
        N3[Social media]:::no
        N4[Black-box ML system]:::no
        N5[A job application platform]:::no
    end

    subgraph FUTURE["Post-Capstone Scope"]
        P1[RAG Market Insights Assistant]:::post
        P2[Real-time job ingestion]:::post
        P3[Resume parsing]:::post
        P4[Advanced ranking models]:::post
        P5[Multi-region analysis]:::post
    end
```

---

## 3. System Architecture Overview

```mermaid
graph TB
    classDef frontend fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef router   fill:#6366F1,stroke:#4338CA,color:#fff
    classDef orch     fill:#F59E0B,stroke:#B45309,color:#fff
    classDef algo     fill:#10B981,stroke:#047857,color:#fff
    classDef llm      fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef reason   fill:#F97316,stroke:#C2410C,color:#fff
    classDef db       fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef ingest   fill:#6B7280,stroke:#374151,color:#fff
    classDef ext      fill:#EC4899,stroke:#BE185D,color:#fff
    classDef admin    fill:#DC2626,stroke:#991B1B,color:#fff

    subgraph CLIENT["Frontend — React / TypeScript / Vite"]
        UI_LOGIN[Login]:::frontend
        UI_DASH[Dashboard]:::frontend
        UI_PROFILE[Profile]:::frontend
        UI_JOBS[Job Explorer]:::frontend
        UI_SKILLS[Skill Analysis]:::frontend
        UI_REC[Recommendations]:::frontend
    end

    subgraph API["Backend — FastAPI · Python 3.11"]
        subgraph ROUTERS["Student Routers"]
            R_AUTH[auth]:::router
            R_PROFILE[profile]:::router
            R_JOBS[jobs]:::router
            R_SKILLS[skills]:::router
            R_REC[recommendations]:::router
            R_GAP[gap-analysis]:::router
            R_MARKET[market]:::router
            R_DASH[dashboard]:::router
        end

        R_ADMIN[admin/ingest]:::admin

        subgraph ENGINE["Intelligence Engine"]
            ORCH[EngineOrchestrator]:::orch

            subgraph INGEST_AGENTS["Ingestion Pipeline"]
                ING[IngestionAgent]:::ingest
                NORM[NormalizationAgent]:::ingest
            end

            subgraph ALGO_AGENTS["Algorithmic Agents"]
                SGAP[SkillGapAgent]:::algo
                RECOM[RecommendationAgent]:::algo
                PATHF[PathFinderAgent]:::algo
                MRKTA[MarketAgent]:::algo
            end

            subgraph LLM_LAYER["LLM Provider"]
                LLM_BASE[LLMProvider ABC]:::llm
                CLAUDE_P[ClaudeProvider]:::llm
                OPENAI_P[OpenAIProvider]:::llm
                OLLAMA_P[OllamaProvider]:::llm
            end

            subgraph REASON["Reasoning Agent"]
                REASON_A[ReasoningAgent]:::reason
            end
        end

        GRAPH_SVC[GraphService]:::db
    end

    subgraph DATA["Data Layer"]
        PG[(PostgreSQL\nUsers & Profiles)]:::db
        NEO4J[(Neo4j\nKnowledge Graph)]:::db
    end

    subgraph PROVIDERS["External AI"]
        CLAUDE_API[Anthropic API]:::ext
        OPENAI_API[OpenAI API]:::ext
        OLLAMA[Ollama Local]:::ext
    end

    subgraph DATASRC["Data Sources"]
        CSV[Kaggle CSV\n10k+ jobs]:::ingest
        ONET[O*NET / ESCO\nSkill Taxonomy]:::ingest
        SCRAPER[Scraper\noptional]:::ingest
    end

    CLIENT -->|REST + JWT| ROUTERS
    ROUTERS --> ORCH
    R_ADMIN --> ING
    ING --> NORM --> NEO4J
    ORCH --> ALGO_AGENTS & REASON_A
    REASON_A --> LLM_BASE
    LLM_BASE --> CLAUDE_P & OPENAI_P & OLLAMA_P
    CLAUDE_P --> CLAUDE_API
    OPENAI_P --> OPENAI_API
    OLLAMA_P --> OLLAMA
    ALGO_AGENTS --> GRAPH_SVC
    GRAPH_SVC --> NEO4J
    ROUTERS --> PG
    CSV & ONET & SCRAPER --> ING
```

---

## 4. Technology Stack

```mermaid
graph LR
    classDef front  fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef back   fill:#6366F1,stroke:#4338CA,color:#fff
    classDef engine fill:#10B981,stroke:#047857,color:#fff
    classDef llmpkg fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef db     fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef infra  fill:#6B7280,stroke:#374151,color:#fff

    subgraph FRONT["Frontend"]
        F1[React 18]:::front
        F2[TypeScript]:::front
        F3[Vite]:::front
        F4[TailwindCSS]:::front
        F5[shadcn/ui]:::front
        F6[React Query]:::front
        F7[React Router v6]:::front
    end

    subgraph BACK["Backend"]
        B1[Python 3.11]:::back
        B2[FastAPI]:::back
        B3[Uvicorn ASGI]:::back
        B4[Pydantic v2]:::back
        B5[SQLAlchemy + Alembic]:::back
        B6[python-jose JWT]:::back
        B7[neo4j-driver]:::back
        B8[pandas — ETL]:::back
        B9[rapidfuzz — skill matching]:::back
    end

    subgraph ENG["Intelligence Engine — Agents"]
        E1[IngestionAgent\nCSV + scraper parsing]:::engine
        E2[NormalizationAgent\nSynonym resolution]:::engine
        E3[SkillGapAgent\nWeighted readiness score]:::engine
        E4[RecommendationAgent\nJaccard + partial match]:::engine
        E5[PathFinderAgent\nBFS + topological sort]:::engine
        E6[MarketAgent\nDemand aggregation]:::engine
    end

    subgraph LLMPKG["LLM Providers"]
        L1[anthropic SDK\nClaude Sonnet]:::llmpkg
        L2[openai SDK\nGPT-4o]:::llmpkg
        L3[Ollama HTTP\nLocal models]:::llmpkg
    end

    subgraph DB["Databases"]
        D1[PostgreSQL 15\nUsers / Auth]:::db
        D2[Neo4j 5\nKnowledge Graph]:::db
    end

    subgraph INFRA["Infrastructure"]
        I1[Docker Compose]:::infra
        I2[Alembic Migrations]:::infra
        I3[python-dotenv]:::infra
    end
```

---

## 5. Frontend Architecture

```mermaid
graph TD
    classDef page   fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef comp   fill:#60A5FA,stroke:#2563EB,color:#fff
    classDef state  fill:#BFDBFE,stroke:#3B82F6,color:#1E3A5F
    classDef api    fill:#6366F1,stroke:#4338CA,color:#fff

    subgraph PAGES["Pages (React Router)"]
        P_LOGIN["/ — Login"]:::page
        P_DASH["/dashboard"]:::page
        P_PROF["/profile"]:::page
        P_EDIT["/profile/edit"]:::page
        P_JOBS["/jobs"]:::page
        P_SKILLS["/skills"]:::page
        P_REC["/recommendations"]:::page
    end

    subgraph COMPONENTS["Shared Components"]
        C_LAYOUT[AppLayout\nSidebar + Mobile Nav]:::comp
        C_STATCARD[StatCard]:::comp
        C_SKILLBAR[SkillBar]:::comp
        C_JOBCARD[JobCard]:::comp
    end

    subgraph STATE["State Management"]
        RQ[React Query\nServer State Cache]:::state
        LOCAL[useState\nLocal UI State]:::state
    end

    subgraph API_CLIENT["API Client Layer"]
        A_AUTH[authApi]:::api
        A_PROFILE[profileApi]:::api
        A_JOBS[jobsApi]:::api
        A_SKILLS[skillsApi]:::api
        A_REC[recApi]:::api
        A_GAP[gapApi]:::api
        A_MARKET[marketApi]:::api
    end

    P_LOGIN --> A_AUTH
    P_DASH --> A_MARKET & A_SKILLS
    P_PROF --> A_PROFILE
    P_EDIT --> A_PROFILE
    P_JOBS --> A_JOBS
    P_SKILLS --> A_GAP
    P_REC --> A_REC

    P_DASH --> C_STATCARD & C_SKILLBAR
    P_JOBS --> C_JOBCARD
    PAGES --> C_LAYOUT

    A_AUTH & A_PROFILE & A_JOBS & A_REC --> RQ
```

---

## 6. Backend Architecture

### File Structure

```
backend/
├── main.py                              # FastAPI app · CORS · routers
├── app/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── jobs.py
│   │   ├── skills.py
│   │   ├── recommendations.py
│   │   ├── gap_analysis.py
│   │   ├── market.py
│   │   ├── dashboard.py
│   │   └── admin.py                     # POST /admin/ingest/csv
│   │
│   ├── engine/                          # ← Intelligence Engine
│   │   ├── orchestrator.py              # Coordinates all agents
│   │   │
│   │   ├── ingestion/                   # Data ingestion pipeline
│   │   │   ├── ingestion_agent.py       # CSV / scraper → validated records
│   │   │   └── normalization_agent.py   # Skill synonym resolution
│   │   │
│   │   ├── algorithmic/                 # Pure Python — no LLM
│   │   │   ├── skill_gap_agent.py       # Weighted readiness scoring
│   │   │   ├── recommendation_agent.py  # Jaccard + partial skill match
│   │   │   ├── path_finder_agent.py     # BFS + topological sort
│   │   │   └── market_agent.py          # Skill demand aggregation
│   │   │
│   │   ├── llm/                         # Pluggable LLM abstraction
│   │   │   ├── base.py                  # LLMProvider ABC
│   │   │   ├── claude_provider.py
│   │   │   ├── openai_provider.py
│   │   │   └── ollama_provider.py
│   │   │
│   │   └── reasoning/                   # LLM-powered narrative layer
│   │       └── reasoning_agent.py       # Explains all algorithmic outputs
│   │
│   ├── services/
│   │   └── graph_service.py             # All Cypher queries
│   │
│   ├── models/
│   │   ├── user.py
│   │   └── profile.py
│   │
│   ├── schemas/
│   │   ├── auth.py · profile.py · job.py · skill.py
│   │   ├── recommendation.py · gap_analysis.py
│   │   ├── market.py · dashboard.py · ingest.py
│   │
│   └── database/
│       ├── postgres.py
│       └── neo4j.py
│
└── data/
    ├── kaggle_jobs.csv                  # 10k+ real job postings
    ├── onet_skills.csv                  # O*NET skill taxonomy
    └── synonyms.json                    # Skill synonym map
```

### Router → Engine Flow

```mermaid
graph TB
    classDef router  fill:#6366F1,stroke:#4338CA,color:#fff
    classDef admin   fill:#DC2626,stroke:#991B1B,color:#fff
    classDef orch    fill:#F59E0B,stroke:#B45309,color:#fff
    classDef ingest  fill:#6B7280,stroke:#374151,color:#fff
    classDef algo    fill:#10B981,stroke:#047857,color:#fff
    classDef reason  fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm     fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef svc     fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef db      fill:#0F766E,stroke:#064E3B,color:#fff

    subgraph ROUTERS["Student Routers"]
        R1[gap_analysis]:::router
        R2[recommendations]:::router
        R3[market]:::router
        R4[dashboard]:::router
    end

    R_ADM[admin/ingest]:::admin

    ORCH[EngineOrchestrator]:::orch

    subgraph INGEST["Ingestion Pipeline"]
        IA[IngestionAgent]:::ingest
        NA[NormalizationAgent]:::ingest
    end

    subgraph ALGO["Algorithmic Agents"]
        SGA[SkillGapAgent]:::algo
        RCA[RecommendationAgent]:::algo
        PFA[PathFinderAgent]:::algo
        MKA[MarketAgent]:::algo
    end

    RA[ReasoningAgent]:::reason
    LLM[LLMProvider]:::llm
    GS[GraphService]:::svc
    NEO[(Neo4j)]:::db

    ROUTERS --> ORCH
    R_ADM --> IA --> NA --> NEO
    ORCH --> SGA & RCA & PFA & MKA
    ORCH --> RA
    RA --> LLM
    SGA & RCA & PFA & MKA --> GS
    GS --> NEO
```

---

## 7. Database Design

### 7.1 PostgreSQL — Relational Schema

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string hashed_password
        string name
        timestamp created_at
        timestamp updated_at
    }

    student_profiles {
        uuid id PK
        uuid user_id FK
        string major
        int graduation_year
        json skills
        json target_roles
        json experience
        timestamp updated_at
    }

    users ||--|| student_profiles : "has one"
```

> **Why PostgreSQL for user data?** Auth and profile data is relational with strict uniqueness constraints and ACID requirements. Neo4j stores the *semantic* skill graph for traversal — both stores are synchronized on every profile update.

### 7.2 Neo4j — Knowledge Graph Schema

```mermaid
graph LR
    classDef student  fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef skill    fill:#10B981,stroke:#047857,color:#fff
    classDef job      fill:#F59E0B,stroke:#B45309,color:#fff
    classDef course   fill:#F97316,stroke:#C2410C,color:#fff
    classDef category fill:#8B5CF6,stroke:#6D28D9,color:#fff

    STUDENT((Student\nid · email · name\ntarget_roles)):::student
    SKILL((Skill\nid · name\ncategory · level\nnormalized_name)):::skill
    JOB((Job\nid · title · company\nlocation · salary\ntype · source)):::job
    COURSE((Course\nid · title · provider\nurl · duration · free)):::course
    CATEGORY((Category\nid · name\nparent_category)):::category

    STUDENT -->|HAS_SKILL\nproficiency: 0–10\nyears: float| SKILL
    STUDENT -->|TARGETS| JOB
    JOB -->|REQUIRES\nimportance: must/nice\nfrequency: int| SKILL
    SKILL -->|LEADS_TO\ndifficulty_jump: int| SKILL
    COURSE -->|TEACHES| SKILL
    JOB -->|IN_CATEGORY| CATEGORY
```

> **Key change from v2:** `(Course)-[:TEACHES]->(Skill)` is the natural subject-verb-object direction. A course *teaches* a skill, not the reverse.

> **NormalizationAgent** adds the `normalized_name` property to every Skill node and uses `rapidfuzz` fuzzy matching against the O*NET/ESCO skill taxonomy to resolve synonyms before graph insertion.

**Node counts:**
| Node | Demo Seed | Target (Kaggle) |
|------|-----------|-----------------|
| Student | 3 | — |
| Job | 50 | 10,000+ |
| Skill | 80 | 500+ (O*NET) |
| Course | 30 | 30 |
| Category | 7 | 20+ |

---

## 8. API Contract

```mermaid
graph LR
    classDef auth   fill:#EF4444,stroke:#B91C1C,color:#fff
    classDef prof   fill:#3B82F6,stroke:#1D4ED8,color:#fff
    classDef jobs   fill:#10B981,stroke:#047857,color:#fff
    classDef skills fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef rec    fill:#F59E0B,stroke:#B45309,color:#fff
    classDef gap    fill:#F97316,stroke:#C2410C,color:#fff
    classDef mkt    fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef dash   fill:#6366F1,stroke:#4338CA,color:#fff
    classDef admin  fill:#DC2626,stroke:#991B1B,color:#fff

    subgraph AUTH["Auth"]
        A1["POST /auth/register"]:::auth
        A2["POST /auth/login"]:::auth
    end

    subgraph PROFILE["Profile 🔒"]
        P1["GET /profile"]:::prof
        P2["PUT /profile"]:::prof
        P3["POST /profile/skills"]:::prof
    end

    subgraph JOBS["Jobs 🔒"]
        J1["GET /jobs\n?type= location= search= limit="]:::jobs
        J2["GET /jobs/:id"]:::jobs
    end

    subgraph SKILLS["Skills 🔒"]
        SK1["GET /skills/market"]:::skills
        SK2["GET /skills/gap"]:::skills
    end

    subgraph REC["Recommendations 🔒"]
        R1["GET /recommendations/jobs"]:::rec
        R2["GET /recommendations/skills"]:::rec
        R3["GET /recommendations/courses"]:::rec
    end

    subgraph GAP["Gap Analysis 🔒"]
        G1["POST /gap-analysis\nBody: target_job_id"]:::gap
    end

    subgraph MARKET["Market 🔒"]
        M1["GET /market/insights"]:::mkt
    end

    subgraph DASH["Dashboard 🔒"]
        D1["GET /dashboard"]:::dash
    end

    subgraph ADMIN["Admin 🔑"]
        AD1["POST /admin/ingest/csv\nBody: file upload\nTriggers IngestionAgent pipeline"]:::admin
        AD2["GET /admin/ingest/status\nReturns: last run stats"]:::admin
    end
```

**Envelope — all responses:**
```json
{ "success": true,  "data": { ... }, "message": "Optional message" }
{ "success": false, "error": "NOT_FOUND", "message": "Job xyz does not exist" }
```

---

## 9. Intelligence Engine — Agent Architecture

### 9.1 Agent Overview

The engine is composed of four types of agents. Each type has a single responsibility. The ReasoningAgent is optional — removing it never breaks the system.

```mermaid
graph TB
    classDef orch    fill:#F59E0B,stroke:#B45309,color:#fff
    classDef ingest  fill:#6B7280,stroke:#374151,color:#fff
    classDef algo    fill:#10B981,stroke:#047857,color:#fff
    classDef reason  fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm     fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef ext     fill:#EC4899,stroke:#BE185D,color:#fff

    ORCH["EngineOrchestrator\nRoutes requests to the correct agents\nHandles LLM unavailability gracefully"]:::orch

    subgraph TYPE1["Type 1 — Ingestion Pipeline"]
        IA[IngestionAgent\ningestion_agent.py]:::ingest
        NA[NormalizationAgent\nnormalization_agent.py]:::ingest
    end

    subgraph TYPE2["Type 2 — Algorithmic Agents (no LLM)"]
        SGA[SkillGapAgent\nskill_gap_agent.py]:::algo
        RCA[RecommendationAgent\nrecommendation_agent.py]:::algo
        PFA[PathFinderAgent\npath_finder_agent.py]:::algo
        MKA[MarketAgent\nmarket_agent.py]:::algo
    end

    subgraph TYPE3["Type 3 — LLM Provider Abstraction"]
        BASE[LLMProvider ABC]:::llm
        CP[ClaudeProvider]:::llm
        OP[OpenAIProvider]:::llm
        OL[OllamaProvider]:::llm
    end

    subgraph TYPE4["Type 4 — Reasoning Agent (optional)"]
        RA[ReasoningAgent\nreasoning_agent.py]:::reason
    end

    subgraph EXTAI["External AI Services"]
        C_API[Anthropic API]:::ext
        O_API[OpenAI API]:::ext
        LOC[Ollama Local]:::ext
    end

    ORCH --> TYPE1 & TYPE2 & TYPE4
    TYPE4 --> BASE
    BASE --> CP & OP & OL
    CP --> C_API
    OP --> O_API
    OL --> LOC
```

---

### 9.2 Ingestion Pipeline

The ingestion pipeline runs independently from the request cycle, triggered via `POST /admin/ingest/csv`.

```mermaid
graph TB
    classDef src    fill:#6B7280,stroke:#374151,color:#fff
    classDef agent  fill:#374151,stroke:#1F2937,color:#fff
    classDef norm   fill:#4B5563,stroke:#1F2937,color:#fff
    classDef db     fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef decide fill:#FEF9C3,stroke:#CA8A04,color:#1C1917

    subgraph SOURCES["Data Sources"]
        CSV["Kaggle CSV\n10k+ job postings"]:::src
        ONET["O*NET / ESCO\nSkill Taxonomy CSV"]:::src
        SCRAP["Scraper\nInternshala — optional"]:::src
    end

    subgraph IA["IngestionAgent — ingestion_agent.py"]
        IA1["Read + validate CSV schema\nDrop malformed rows"]:::agent
        IA2["Parse skills_required\ncomma-separated field"]:::agent
        IA3["Validate salary, location,\njob_type fields"]:::agent
        IA1 --> IA2 --> IA3
    end

    subgraph NA["NormalizationAgent — normalization_agent.py"]
        NA1["Load synonyms.json\n+ O*NET skill list"]:::norm
        NA2["For each raw skill name:\nExact match in synonym map?"]:::decide
        NA3["Use mapped name\ne.g. ReactJS → React"]:::norm
        NA4["Fuzzy match via rapidfuzz\nagainst O*NET taxonomy\nscore ≥ 90?"]:::decide
        NA5["Accept O*NET canonical name\nset normalized_name"]:::norm
        NA6["Keep original name\nflag for manual review"]:::norm
        NA1 --> NA2
        NA2 -- Yes --> NA3
        NA2 -- No  --> NA4
        NA4 -- Yes --> NA5
        NA4 -- No  --> NA6
    end

    subgraph NEO_WRITE["Neo4j Write"]
        NW1["MERGE Job node\nMERGE Skill node\non normalized_name"]:::db
        NW2["CREATE REQUIRES edge\nimportance by skill position"]:::db
        NW3["MERGE Category\nCREATE IN_CATEGORY"]:::db
    end

    SOURCES --> IA --> NA --> NW1 --> NW2 --> NW3
```

---

### 9.3 Algorithmic Agents

All four agents are pure Python — deterministic, unit-testable, zero network calls.

```mermaid
graph TB
    classDef agent fill:#10B981,stroke:#047857,color:#fff
    classDef input fill:#D1FAE5,stroke:#6EE7B7,color:#064E3B
    classDef out   fill:#A7F3D0,stroke:#34D399,color:#064E3B
    classDef graph fill:#14B8A6,stroke:#0F766E,color:#fff

    subgraph SGA["SkillGapAgent — skill_gap_agent.py"]
        SGA_IN["student_skills[]\nrequired_skills[]\nproficiency_map{}"]:::input
        SGA_CALC["readiness_score =\n  (must_matched / must_total) × 0.7\n+ (nice_matched / nice_total) × 0.3\n+ Σ proficiency_bonus"]:::agent
        SGA_OUT["readiness_score: 0–100\nmatched_skills[]\nmissing_skills[]"]:::out
        SGA_IN --> SGA_CALC --> SGA_OUT
    end

    subgraph RCA["RecommendationAgent — recommendation_agent.py"]
        RCA_IN["student_skills[]\nall_jobs[] from Neo4j"]:::input
        RCA_CALC["exact_score = |A ∩ B| / |A ∪ B|\npartial_score = graph proximity\n  via LEADS_TO within depth 2\nfinal_score = exact × 0.8 + partial × 0.2"]:::agent
        RCA_OUT["jobs[] ranked by\nfinal_score DESC"]:::out
        RCA_IN --> RCA_CALC --> RCA_OUT
    end

    subgraph PFA["PathFinderAgent — path_finder_agent.py"]
        PFA_IN["missing_skills[]\nLEADS_TO graph from Neo4j"]:::input
        PFA_CALC["BFS from each missing skill\nCollect prerequisite chains\nTopological sort → ordered path\nAttach TEACHES courses"]:::agent
        PFA_OUT["learning_path[]\nweeks_estimate per skill\ncourses per milestone"]:::out
        PFA_IN --> PFA_CALC --> PFA_OUT
    end

    subgraph MKA["MarketAgent — market_agent.py"]
        MKA_IN["All REQUIRES edges\nfrom Neo4j"]:::input
        MKA_CALC["demand_score =\n  REQUIRES count per Skill\n  normalized 0–100\ntrend = demand Δ over time"]:::agent
        MKA_OUT["skill_demand[]\ntrending_skills[]\ntop_categories[]"]:::out
        MKA_IN --> MKA_CALC --> MKA_OUT
    end

    NEO[(Neo4j)]:::graph
    NEO --> SGA_IN & RCA_IN & PFA_IN & MKA_IN
```

> **Partial skill matching in RecommendationAgent:** A student who knows Python gets partial credit toward a job requiring Machine Learning, because `Python → ML` exists as a `LEADS_TO` edge. Graph proximity within depth 2 is used as the partial match score.

---

### 9.4 LLM Provider Abstraction

```mermaid
graph TB
    classDef abc   fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef impl  fill:#A78BFA,stroke:#7C3AED,color:#fff
    classDef ext   fill:#EC4899,stroke:#BE185D,color:#fff
    classDef conf  fill:#FEF9C3,stroke:#CA8A04,color:#1C1917

    BASE["LLMProvider — base.py\n\ncomplete(system, user, schema: BaseModel) → BaseModel\nstream(system, user) → Generator\nget_model_info() → ModelInfo"]:::abc

    CP["ClaudeProvider\nclaude_provider.py\n\nanthropic.Anthropic()\nJSON via tool_use"]:::impl
    OP["OpenAIProvider\nopenai_provider.py\n\nopenai.OpenAI()\nJSON via response_format"]:::impl
    OL["OllamaProvider\nollama_provider.py\n\nrequests.post(OLLAMA_URL)\nJSON schema in system prompt"]:::impl

    CLAUDE["Anthropic API\nclaude-sonnet-4-6"]:::ext
    OPENAI["OpenAI API\ngpt-4o"]:::ext
    LOCAL["Ollama\nlocalhost:11434\nllama3 / mistral"]:::ext

    ENV[".env\nLLM_PROVIDER = claude | openai | ollama\nLLM_MODEL = claude-sonnet-4-6 | gpt-4o | llama3"]:::conf

    BASE <|-- CP
    BASE <|-- OP
    BASE <|-- OL
    CP --> CLAUDE
    OP --> OPENAI
    OL --> LOCAL
    ENV --> CP & OP & OL
```

**The `complete()` contract — every provider returns a validated Pydantic model:**
```python
class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: type[BaseModel],
        timeout: int = 30,
        retries: int = 2,
    ) -> BaseModel: ...
```

The ReasoningAgent never sees raw LLM output. The provider validates and parses into a schema before returning.

---

### 9.5 Reasoning Agent

The ReasoningAgent takes **algorithmic output** as input — it enriches, never replaces.

```mermaid
graph TB
    classDef agent  fill:#F97316,stroke:#C2410C,color:#fff
    classDef input  fill:#FED7AA,stroke:#FB923C,color:#7C2D12
    classDef out    fill:#FFEDD5,stroke:#F97316,color:#7C2D12
    classDef llm    fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef method fill:#F97316,stroke:#C2410C,color:#fff

    LLM[LLMProvider]:::llm

    RA["ReasoningAgent\nreasoning_agent.py"]:::agent

    subgraph METHODS["ReasoningAgent Methods"]
        M1["explain_gap(gap_result)\n\nInput: GapResult from SkillGapAgent\nOutput: explanation · encouragement\n  missing_skills with weeks_to_learn"]:::method

        M2["narrate_recommendations(ranked_jobs)\n\nInput: RankedJobs from RecommendationAgent\nOutput: why_recommended per job\n  re-ranked top 10"]:::method

        M3["write_roadmap(learning_path)\n\nInput: LearningPath from PathFinderAgent\nOutput: weekly_milestones[]\n  week ranges · goals · courses"]:::method

        M4["summarize_market(demand_data)\n\nInput: DemandData from MarketAgent\nOutput: trend_bullets[3]\n  market_summary · highlight_skills"]:::method
    end

    RA --> M1 & M2 & M3 & M4
    M1 & M2 & M3 & M4 --> LLM
```

---

### 9.6 Engine Orchestrator

```mermaid
flowchart TD
    classDef router  fill:#6366F1,stroke:#4338CA,color:#fff
    classDef orch    fill:#F59E0B,stroke:#B45309,color:#fff
    classDef algo    fill:#10B981,stroke:#047857,color:#fff
    classDef reason  fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm     fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef decide  fill:#FEF9C3,stroke:#CA8A04,color:#1C1917

    REQ(["API Request\ngap-analysis · recommendations\nroadmap · market"]):::router
    ORCH[EngineOrchestrator\norchestrator.py]:::orch

    STEP1["Run Algorithmic Agent\nSkillGapAgent / RecommendationAgent\nPathFinderAgent / MarketAgent"]:::algo
    RESULT["Structured scored result\nno natural language yet"]:::algo

    CHECK{"LLM_PROVIDER\nconfigured?"}:::decide

    STEP2["ReasoningAgent\nexplain · narrate · roadmap · summarize"]:::reason
    LLM_CALL["LLMProvider.complete()\nAlgorithmic result as context\nPydantic output schema"]:::llm

    FALLBACK["Return algorithmic result\nwith template narratives\n(no LLM call made)"]:::algo

    MERGE["Merge scores + narratives\ninto final response"]:::orch
    RESP(["Typed Pydantic Response"]):::router

    REQ --> ORCH --> STEP1 --> RESULT --> CHECK
    CHECK -- Yes --> STEP2 --> LLM_CALL --> MERGE --> RESP
    CHECK -- No  --> FALLBACK --> RESP
```

---

## 10. Data Sources

```mermaid
graph TB
    classDef primary fill:#10B981,stroke:#047857,color:#fff
    classDef secondary fill:#F59E0B,stroke:#B45309,color:#fff
    classDef optional fill:#6B7280,stroke:#374151,color:#fff

    subgraph PRIMARY["Primary Sources"]
        P1["Kaggle Job Dataset\n10,000+ real job postings\nfields: title · company · location\nskills_required · salary · type"]:::primary
        P2["O*NET / ESCO Skill Taxonomy\nCanonical skill names\nSkill categories + hierarchy\nUsed by NormalizationAgent"]:::primary
    end

    subgraph SECONDARY["Demo / Seed"]
        S1["Curated 50-job subset\nHand-verified skills\nUsed for local dev + demo"]:::secondary
        S2["30 courses (manual)\nmapped to skill nodes"]:::secondary
        S3["3 demo student profiles\njunior dev · career switcher\nbusiness analyst"]:::secondary
    end

    subgraph OPTIONAL["Optional"]
        O1["Internshala Scraper\n~500 Indian job market jobs\nActivated via ENV flag"]:::optional
    end

    P1 --> IA[IngestionAgent]
    P2 --> NA[NormalizationAgent]
    O1 --> IA
    S1 & S2 & S3 --> SEED[seed_demo_data.py]
```

---

## 11. Data Flow Diagrams

### 11.1 Authentication Flow

```mermaid
flowchart TD
    classDef step    fill:#6366F1,stroke:#4338CA,color:#fff
    classDef decide  fill:#FEF9C3,stroke:#CA8A04,color:#1C1917
    classDef success fill:#10B981,stroke:#047857,color:#fff
    classDef fail    fill:#EF4444,stroke:#B91C1C,color:#fff

    A(["Student enters\nemail + password"]):::step
    B["POST /auth/login"]:::step
    C{Email exists\nin PostgreSQL?}:::decide
    D["401 Unauthorized"]:::fail
    E{bcrypt verify\npassword hash}:::decide
    F["Generate JWT\nHS256 · 24h expiry\npayload: user_id · email"]:::success
    G["Return token + user profile"]:::success
    H["Store JWT in localStorage"]:::step
    I["All requests →\nAuthorization: Bearer token"]:::step
    J["FastAPI JWT middleware\ndecodes + validates"]:::step
    K{Token valid?}:::decide
    L["401 Unauthorized"]:::fail
    M["Inject current_user\ninto route handler"]:::success

    A --> B --> C
    C -- No  --> D
    C -- Yes --> E
    E -- Fail --> D
    E -- Pass --> F --> G --> H --> I --> J --> K
    K -- No  --> L
    K -- Yes --> M
```

### 11.2 Recommendation Flow

```mermaid
flowchart TD
    classDef api     fill:#6366F1,stroke:#4338CA,color:#fff
    classDef algo    fill:#10B981,stroke:#047857,color:#fff
    classDef reason  fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm     fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef db      fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef decide  fill:#FEF9C3,stroke:#CA8A04,color:#1C1917

    A(["GET /recommendations/jobs"]):::api
    B["Extract student_id from JWT"]:::api
    C["GraphService: student HAS_SKILL edges"]:::db
    D["GraphService: all Jobs + REQUIRES + LEADS_TO"]:::db
    E["RecommendationAgent:\nJaccard exact score per job\nPartial score via LEADS_TO depth-2\nfinal = exact×0.8 + partial×0.2"]:::algo
    F["Sort DESC · Top 20"]:::algo
    G{LLM configured?}:::decide
    H["ReasoningAgent.narrate_recommendations()\nTop 20 + student profile as context"]:::reason
    I["LLMProvider.complete()\nRe-rank by depth of fit\nGenerate why_recommended"]:::llm
    J["Merge scores + narratives"]:::algo
    K["Return top 10 raw\nwith template narratives"]:::algo
    L(["Return JobRecommendation[]"]):::api

    A --> B --> C & D --> E --> F --> G
    G -- Yes --> H --> I --> J --> L
    G -- No  --> K --> L
```

### 11.3 Skill Gap Analysis Flow

```mermaid
flowchart TD
    classDef api     fill:#6366F1,stroke:#4338CA,color:#fff
    classDef algo    fill:#10B981,stroke:#047857,color:#fff
    classDef reason  fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm     fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef db      fill:#14B8A6,stroke:#0F766E,color:#fff

    A(["POST /gap-analysis\ntarget_job_id"]):::api
    B["Extract student_id from JWT"]:::api
    C["GraphService:\nstudent HAS_SKILL + job REQUIRES"]:::db
    D["SkillGapAgent:\nreadiness_score · matched · missing\nweighted formula"]:::algo
    E["PathFinderAgent:\nBFS on LEADS_TO from missing skills\nTopological sort → ordered path\nGraphService: TEACHES courses"]:::algo
    F["ReasoningAgent.explain_gap()\ngap_result + learning_path as context"]:::reason
    G["LLMProvider.complete()\nGapAnalysisResponse schema\nexplanation · encouragement\nmissing with weeks"]:::llm
    H["ReasoningAgent.write_roadmap()\nordered path + courses"]:::reason
    I["LLMProvider.complete()\nWeekly milestone plan\nRoadmapResponse schema"]:::llm
    J["Merge algorithmic scores\n+ LLM narratives + roadmap"]:::algo
    K(["Return GapAnalysisResponse\n+ RoadmapResponse"]):::api

    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K
```

### 11.4 Ingestion Pipeline Flow

```mermaid
flowchart TD
    classDef src    fill:#6B7280,stroke:#374151,color:#fff
    classDef agent  fill:#374151,stroke:#111827,color:#fff
    classDef norm   fill:#4B5563,stroke:#1F2937,color:#fff
    classDef db     fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef decide fill:#FEF9C3,stroke:#CA8A04,color:#1C1917
    classDef admin  fill:#DC2626,stroke:#991B1B,color:#fff

    TRIG(["POST /admin/ingest/csv\nfile upload"]):::admin
    IA1["IngestionAgent:\nRead + validate schema\nDrop malformed rows"]:::agent
    IA2["Parse skills_required\nper row"]:::agent
    NA1["NormalizationAgent:\nLoad synonyms.json + O*NET list"]:::norm
    CHECK1{Exact synonym\nmatch?}:::decide
    MAP["Use mapped name\nReactJS → React"]:::norm
    CHECK2{Fuzzy match\n≥ 90 score?}:::decide
    ACCEPT["Accept O*NET canonical\nset normalized_name"]:::norm
    FLAG["Keep raw name\nflag for review"]:::norm
    MERGE_SK["MERGE Skill node\non normalized_name"]:::db
    MERGE_JOB["MERGE Job node\ntitle + company"]:::db
    CREATE_REL["CREATE REQUIRES edge\nimportance by skill rank"]:::db
    MERGE_CAT["MERGE Category\nCREATE IN_CATEGORY"]:::db
    DONE(["Ingestion complete\nReturn stats to admin"]):::admin

    TRIG --> IA1 --> IA2 --> NA1 --> CHECK1
    CHECK1 -- Yes --> MAP --> MERGE_SK
    CHECK1 -- No  --> CHECK2
    CHECK2 -- Yes --> ACCEPT --> MERGE_SK
    CHECK2 -- No  --> FLAG --> MERGE_SK
    MERGE_SK --> MERGE_JOB --> CREATE_REL --> MERGE_CAT --> DONE
```

---

## 12. Sequence Diagrams

### 12.1 User Login & Dashboard Load

```mermaid
sequenceDiagram
    actor U as Student
    participant FE as React Frontend
    participant API as FastAPI
    participant PG as PostgreSQL
    participant ENG as EngineOrchestrator
    participant NEO as Neo4j

    U->>FE: Enter email + password
    FE->>API: POST /auth/login
    API->>PG: SELECT user WHERE email = ?
    PG-->>API: User + hashed_password
    API->>API: bcrypt.verify(password, hash)
    API-->>FE: {token, user}
    FE->>FE: Store JWT

    FE->>API: GET /dashboard (Bearer)
    API->>API: JWT → user_id
    API->>ENG: get_dashboard(student_id)
    ENG->>NEO: student HAS_SKILL + target roles
    NEO-->>ENG: skill nodes + edges
    ENG->>NEO: skill demand across all jobs
    NEO-->>ENG: demand counts
    ENG->>ENG: SkillGapAgent.compute_readiness()
    ENG->>ENG: MarketAgent.aggregate_demand()
    ENG-->>API: DashboardStats
    API-->>FE: DashboardStats
    FE->>FE: Render Dashboard
```

### 12.2 Skill Gap Analysis Request

```mermaid
sequenceDiagram
    actor U as Student
    participant FE as React Frontend
    participant API as FastAPI
    participant ALGO as Algorithmic Agents
    participant RA as ReasoningAgent
    participant LLM as LLMProvider
    participant NEO as Neo4j

    U->>FE: Navigate to Skill Analysis
    FE->>API: GET /skills/gap (Bearer)
    API->>ALGO: SkillGapAgent.compute_gap(student_id, job_id)
    ALGO->>NEO: student HAS_SKILL + job REQUIRES
    NEO-->>ALGO: both skill sets
    ALGO->>ALGO: Compute readiness_score · matched · missing
    ALGO->>ALGO: PathFinderAgent.find_path(missing)
    ALGO->>NEO: BFS on LEADS_TO + TEACHES courses
    NEO-->>ALGO: ordered path + courses
    ALGO-->>API: GapResult (algorithmic)

    API->>RA: explain_gap(gap_result)
    RA->>LLM: complete(system, gap_context, GapSchema)
    Note over LLM: Claude / OpenAI / Ollama
    LLM-->>RA: explanation + encouragement + weeks
    RA->>LLM: complete(system, path_context, RoadmapSchema)
    LLM-->>RA: weekly milestones + courses
    RA-->>API: GapAnalysisResponse + RoadmapResponse
    API-->>FE: Full response
    FE->>FE: Render Skill Analysis
```

### 12.3 Job Recommendation Request

```mermaid
sequenceDiagram
    actor U as Student
    participant FE as React Frontend
    participant API as FastAPI
    participant ALGO as RecommendationAgent
    participant RA as ReasoningAgent
    participant LLM as LLMProvider
    participant NEO as Neo4j

    U->>FE: Navigate to Recommendations
    FE->>API: GET /recommendations/jobs?limit=10
    API->>ALGO: rank_jobs(student_id)
    ALGO->>NEO: all Jobs + REQUIRES + LEADS_TO
    NEO-->>ALGO: job + skill graph
    ALGO->>ALGO: Jaccard exact score per job
    ALGO->>ALGO: Partial score via LEADS_TO depth-2
    ALGO->>ALGO: final = exact×0.8 + partial×0.2 · sort DESC
    ALGO-->>API: Top 20 ranked jobs

    API->>RA: narrate_recommendations(top20, student)
    RA->>LLM: complete(system, candidates_context, NarratorSchema)
    Note over LLM: Re-rank by nuanced fit<br/>Generate why_recommended per job
    LLM-->>RA: top 10 + narratives
    RA-->>API: JobRecommendation[]
    API-->>FE: JobRecommendation[]
    FE->>FE: Render job cards
```

---

## 13. Component Diagram

```mermaid
graph TB
    classDef frontend fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef layout   fill:#60A5FA,stroke:#2563EB,color:#fff
    classDef router   fill:#6366F1,stroke:#4338CA,color:#fff
    classDef admin    fill:#DC2626,stroke:#991B1B,color:#fff
    classDef orch     fill:#F59E0B,stroke:#B45309,color:#fff
    classDef ingest   fill:#6B7280,stroke:#374151,color:#fff
    classDef algo     fill:#10B981,stroke:#047857,color:#fff
    classDef reason   fill:#F97316,stroke:#C2410C,color:#fff
    classDef llm      fill:#8B5CF6,stroke:#6D28D9,color:#fff
    classDef db       fill:#14B8A6,stroke:#0F766E,color:#fff

    subgraph FRONTEND["Frontend Application"]
        subgraph PAGES["Pages"]
            LOGIN[Login]:::frontend
            DASH[Dashboard]:::frontend
            PROF[Profile · Edit]:::frontend
            JOBS[Job Explorer]:::frontend
            SKILLS[Skill Analysis]:::frontend
            RECS[Recommendations]:::frontend
        end
        SIDEBAR[AppLayout Sidebar]:::layout
        CARDS[StatCard · SkillBar · JobCard]:::layout
    end

    subgraph BACKEND["Backend Application"]
        subgraph FAST["FastAPI Layer"]
            JWT_MW[JWT Middleware]:::router
            CORS_MW[CORS Middleware]:::router
        end

        subgraph ROUTES["Student Routers"]
            R_A[auth]:::router
            R_P[profile]:::router
            R_J[jobs]:::router
            R_REC[recommendations]:::router
            R_G[gap-analysis]:::router
            R_M[market]:::router
        end

        R_ADM[admin/ingest]:::admin
        ORCHESTR[EngineOrchestrator]:::orch

        subgraph ING["Ingestion Pipeline"]
            IAG[IngestionAgent]:::ingest
            NAG[NormalizationAgent]:::ingest
        end

        subgraph ALGOS["Algorithmic Agents"]
            SGA[SkillGapAgent]:::algo
            RCA[RecommendationAgent]:::algo
            PFA[PathFinderAgent]:::algo
            MKA[MarketAgent]:::algo
        end

        RAG[ReasoningAgent]:::reason

        subgraph LLMP["LLM Providers"]
            CLP[ClaudeProvider]:::llm
            OAP[OpenAIProvider]:::llm
            OLP[OllamaProvider]:::llm
        end

        GRS[GraphService]:::db
    end

    subgraph DATA["Data Stores"]
        PGS[(PostgreSQL)]:::db
        NEO[(Neo4j)]:::db
    end

    SIDEBAR --> PAGES --> JWT_MW
    JWT_MW --> ROUTES & R_ADM
    ROUTES --> ORCHESTR
    R_ADM --> IAG --> NAG --> NEO
    ORCHESTR --> ALGOS & RAG
    RAG --> CLP & OAP & OLP
    ALGOS --> GRS --> NEO
    R_A & R_P --> PGS
```

---

## 14. Deployment Architecture

```mermaid
graph TB
    classDef fe    fill:#3B82F6,stroke:#1E40AF,color:#fff
    classDef api   fill:#6366F1,stroke:#4338CA,color:#fff
    classDef db    fill:#14B8A6,stroke:#0F766E,color:#fff
    classDef env   fill:#FEF9C3,stroke:#CA8A04,color:#1C1917
    classDef ext   fill:#EC4899,stroke:#BE185D,color:#fff
    classDef local fill:#8B5CF6,stroke:#6D28D9,color:#fff

    subgraph LOCAL["Local Development — Docker Compose"]
        FE_DEV["React Dev Server\nlocalhost:5173"]:::fe
        API_DEV["FastAPI + Uvicorn\nlocalhost:8000 --reload"]:::api
        PG_DEV["PostgreSQL 15\nlocalhost:5432"]:::db
        NEO_DEV["Neo4j 5\nlocalhost:7474 HTTP\nlocalhost:7687 Bolt"]:::db
        OLLAMA_DEV["Ollama (optional)\nlocalhost:11434"]:::local
    end

    subgraph ENV[".env"]
        E1[DATABASE_URL]:::env
        E2[NEO4J_URI / USER / PASSWORD]:::env
        E3[ANTHROPIC_API_KEY]:::env
        E4[OPENAI_API_KEY]:::env
        E5[JWT_SECRET]:::env
        E6[LLM_PROVIDER / LLM_MODEL]:::env
        E7[FRONTEND_URL]:::env
    end

    subgraph CLOUD["External AI (optional)"]
        ANT["Anthropic API"]:::ext
        OAI["OpenAI API"]:::ext
    end

    FE_DEV -->|API calls| API_DEV
    API_DEV --> PG_DEV & NEO_DEV
    API_DEV -->|if claude| ANT
    API_DEV -->|if openai| OAI
    API_DEV -->|if ollama| OLLAMA_DEV
    ENV --> API_DEV
```

**Startup sequence:**
```
1. docker-compose up -d                        # PostgreSQL + Neo4j (+ Ollama optional)
2. alembic upgrade head                         # PG schema migrations
3. python -m app.engine.ingestion.ingestion_agent  # Load Kaggle CSV + O*NET
4. python -m app.etl.seed_demo_data             # Seed 3 demo students + 30 courses
5. uvicorn app.main:app --reload                # API on :8000
6. cd frontend && npm run dev                   # React on :5173
```

---

## 15. Security Design

```mermaid
graph LR
    classDef threat  fill:#EF4444,stroke:#B91C1C,color:#fff
    classDef control fill:#10B981,stroke:#047857,color:#fff

    subgraph THREATS["Threats"]
        T1[SQL Injection]:::threat
        T2[JWT Forgery]:::threat
        T3[Cross-Origin Requests]:::threat
        T4[Unauthorized Data Access]:::threat
        T5[Prompt Injection]:::threat
        T6[Cypher Injection]:::threat
    end

    subgraph CONTROLS["Controls"]
        C1[SQLAlchemy ORM\nparameterized queries]:::control
        C2[HS256 signed JWT · 24h expiry]:::control
        C3[FastAPI CORS · allowed origins from .env]:::control
        C4[JWT middleware on all protected routes\nstudent_id from token only — never from request]:::control
        C5[LLMProvider Pydantic schema enforcement\nfallback on parse failure\nno business logic inside LLM]:::control
        C6[neo4j-driver parameterized Cypher\n$param syntax only]:::control
    end

    T1 --> C1
    T2 --> C2
    T3 --> C3
    T4 --> C4
    T5 --> C5
    T6 --> C6
```

---

## 16. Data Models — API Contracts

```mermaid
classDiagram
    class StudentProfile {
        +str id
        +str name
        +str email
        +str major
        +int graduation_year
        +List~SkillEntry~ skills
        +List~str~ target_roles
        +List~ExperienceItem~ experience
    }

    class SkillEntry {
        +str name
        +int proficiency
        +float years
    }

    class ExperienceItem {
        +str title
        +str company
        +str duration
        +str description
    }

    class Job {
        +str id
        +str title
        +str company
        +str location
        +str type
        +List~str~ required_skills
        +float match_percentage
        +str description
        +str why_recommended
        +int salary_min
        +int salary_max
    }

    class GapAnalysisResponse {
        +int readiness_score
        +List~str~ matched_skills
        +List~MissingSkill~ missing_skills
        +str explanation
        +str encouragement
        +List~Milestone~ roadmap
    }

    class MissingSkill {
        +str skill_name
        +str importance
        +int estimated_learning_weeks
    }

    class Milestone {
        +str week_range
        +str skill_name
        +str course_title
        +str course_url
        +str goal
    }

    class DashboardStats {
        +int job_readiness_score
        +int skills_matched
        +int total_required_skills
        +List~str~ missing_high_demand_skills
        +List~SkillDemand~ market_demand
    }

    class MarketInsights {
        +List~SkillDemand~ top_skills
        +List~str~ trend_bullets
        +str summary
    }

    class LLMProvider {
        <<abstract>>
        +complete(system, user, schema) BaseModel
        +stream(system, user) Generator
        +get_model_info() ModelInfo
    }

    class ClaudeProvider {
        +model: str
        +complete(system, user, schema) BaseModel
    }

    class OpenAIProvider {
        +model: str
        +complete(system, user, schema) BaseModel
    }

    class OllamaProvider {
        +model: str
        +base_url: str
        +complete(system, user, schema) BaseModel
    }

    StudentProfile "1" --> "*" SkillEntry
    StudentProfile "1" --> "*" ExperienceItem
    GapAnalysisResponse "1" --> "*" MissingSkill
    GapAnalysisResponse "1" --> "*" Milestone
    DashboardStats "1" --> "*" SkillDemand
    MarketInsights "1" --> "*" SkillDemand
    LLMProvider <|-- ClaudeProvider
    LLMProvider <|-- OpenAIProvider
    LLMProvider <|-- OllamaProvider
```

---

*End of System Design Document — Version 3.0*
