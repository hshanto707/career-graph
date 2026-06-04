# CareerGraph

**Agent-Based Labor Market Intelligence Platform for Student Career Guidance**

> Capstone Project — April 2026

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Start Databases (PostgreSQL + Neo4j)
```bash
docker-compose up -d
```
Wait ~10 seconds for databases to be healthy.

### 2. Run Database Migrations
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 3. Start the Backend API
```bash
# From backend/
uvicorn main:app --reload --port 8000
```
API docs available at: http://localhost:8000/api/docs

### 4. Start the Frontend
```bash
cd frontend
npm install   # first time only
npm run dev
```
App available at: http://localhost:5173

---

## Architecture

```
React Frontend (port 5173)
    ↓ REST + JWT (via Vite proxy to :8000)
FastAPI Backend (port 8000)
    ↓
Intelligence Engine (multi-agent)
    ├── IngestionAgent → NormalizationAgent → Neo4j
    ├── SkillGapAgent (weighted readiness scoring)
    ├── RecommendationAgent (Jaccard similarity)
    ├── PathFinderAgent (BFS + topological sort)
    ├── MarketAgent (demand aggregation)
    └── ReasoningAgent (optional LLM explanations)
    
Databases:
    ├── PostgreSQL (users & profiles)
    └── Neo4j (knowledge graph: jobs, skills, courses)
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | — | Register + receive JWT |
| POST | `/api/v1/auth/login` | — | Login + receive JWT |
| GET/PUT | `/api/v1/profile` | JWT | View/update student profile |
| POST | `/api/v1/profile/skills` | JWT | Add skill to Neo4j graph |
| GET | `/api/v1/jobs` | — | Browse jobs (search + filter) |
| GET | `/api/v1/skills/market` | — | Top demanded skills |
| POST | `/api/v1/gap-analysis` | JWT | Compute skill gap score |
| GET | `/api/v1/recommendations/jobs` | JWT | Ranked job matches |
| GET | `/api/v1/recommendations/skills` | JWT | Skills to learn next |
| GET | `/api/v1/market/insights` | — | Market trends |
| GET | `/api/v1/dashboard` | JWT | Personal KPI stats |
| POST | `/api/v1/admin/ingest/csv` | JWT | Upload job data CSV |
| GET | `/api/v1/health` | — | Health check |

## Running Tests (Backend)

```bash
cd backend
python3 -m pytest tests/ -v
# 87 tests, all passing
```

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```
DATABASE_URL=postgresql+asyncpg://careergraph:careergraph@localhost:5432/careergraph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=careergraph
JWT_SECRET=your-secret-key-here
LLM_PROVIDER=claude        # or openai, ollama
ANTHROPIC_API_KEY=...      # if using Claude
```

## Loading Job Data

After starting the API, use the admin endpoint to load the sample dataset:

```bash
curl -X POST http://localhost:8000/api/v1/admin/ingest/csv \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@backend/data/kaggle_jobs.csv"
```

Or use the Admin panel in the app (coming soon).

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, React Query, React Router v6 |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Intelligence Engine | Custom agent classes, rapidfuzz, pandas |
| LLM Providers | Anthropic Claude, OpenAI GPT-4o, Ollama (local) |
| Databases | PostgreSQL 15, Neo4j 5 |
| Infrastructure | Docker Compose, JWT authentication |






1. Methodology: Write an Introductory passage
  1.1. System Architecture
  1.2. Feasibility Study
    1.2.1. Economic Feasibility
    1.2.2. Technical Feasibility
    1.2.3. Operational Feasibility
  1.3. Requirement Analysis
    1.3.1. Functonal Requirements
    1.3.2. Non-Functional Requirements
    1.3.3. Tools & Technology 
  1.4. System Design
    1.4.1. Development Model
    1.4.2. Use Case Diagram
    1.4.3. Context Diagram
    1.4.4. Data Flow Diagram
    1.4.5. Entity-Relationship Diagram
    1.4.6. Database Schema Diagram
    1.4.7. System Flowchart
