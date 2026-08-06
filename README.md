# CareerGraph

**Agent-Based Job Market Intelligence Platform for Student Career Guidance**

> Capstone Project — April 2026. See `docs/current-status.md` for the
> up-to-date build status, honest gaps, and the milestone roadmap to
> defense-readiness — read that before this file for anything beyond
> "how do I run this."

---

## Quick Start (recommended: local dev workflow)

This is the path actually used and tested throughout development — real
Postgres + Neo4j in Docker, backend API in Docker with hot reload, frontend
via the Vite dev server for fast iteration.

### Prerequisites
- Docker & Docker Compose
- Node.js 18+

### 1. Start the databases + API
```bash
cd backend
make run       # docker compose up -- Postgres, Neo4j, and the FastAPI backend
```
Wait for all three containers to report healthy (Postgres/Neo4j have
healthchecks; the API waits on both). API docs at
http://localhost:8000/docs, health check at http://localhost:8000/health.

Database migrations run automatically as part of the API container's
startup — no separate `alembic upgrade head` step needed for this path.

### 2. Seed the knowledge graph
The Neo4j graph starts empty. Seed it with the full synthetic dataset
(~9,400 jobs, 434 skills — see `docs/data-sources.md` for what this data
actually is):
```bash
make seed
```
A smaller demo-only seed (`docker exec careergraph_backend_api python -m
app.etl.seed_demo_data`, ~50 jobs) also exists but most of the app's
autocomplete/search/market-demand features need the full seed to have
enough data to be useful.

### 3. Start the frontend
```bash
cd frontend
npm install   # first time only
npm run dev
```
App available at **http://localhost:8080** (the Vite dev server's actual
port — see `frontend/vite.config.ts`).

### Resetting the databases
```bash
cd backend
make db-clean   # wipe rows, keep schema/containers -- then `make seed` again
make db-nuke    # full teardown: drops volumes, recreates, reapplies migrations
```

---

## Alternative: one-shot full containerized stack

A second `docker-compose.yml` at the repo root builds and runs *everything*
as containers, including a production-built frontend served by nginx —
useful for a single "does the whole thing actually work end to end" check,
less convenient for active development (no frontend hot reload, and the
API's `--reload` still needs the bind-mounted `backend/` to pick up code
changes).

```bash
# From the repo root
docker compose up -d
docker exec careergraph_api alembic upgrade head   # not automatic in this compose file
```
Frontend at **http://localhost:80**, API at http://localhost:8000. This
stack uses *separate* Docker volumes/networks from `backend/docker-compose.yml`
(different container name prefixes) — the two are not meant to run
simultaneously (they'd fight over the same host ports for Postgres/Neo4j/the
API), and this one doesn't have a `make seed` equivalent yet — seed it the
same way as above, just via `careergraph_api` instead of
`careergraph_backend_api` as the container name.

---

## Architecture

```
React Frontend (Vite dev server :8080, or nginx-served :80 in the full-stack compose)
    ↓ REST + JWT
FastAPI Backend (port 8000, no path prefix -- routes are e.g. /auth/login, /jobs, not /api/v1/...)
    ↓
Intelligence Engine (multi-agent)
    ├── IngestionAgent → NormalizationAgent → Neo4j
    ├── SkillGapAgent (weighted readiness scoring)
    ├── RecommendationAgent (Jaccard/LEADS_TO similarity + GNN rerank)
    ├── GNNRecommendationAgent (trained GraphSAGE link predictor -- see docs/gnn-model.md)
    ├── PathFinderAgent (BFS + topological sort)
    ├── MarketAgent (demand aggregation)
    └── ReasoningAgent (optional LLM explanations -- off by default, see docs/current-status.md)

Databases:
    ├── PostgreSQL (users & profiles)
    └── Neo4j (knowledge graph: jobs, skills, courses)
```

## API Endpoints

All routes are unprefixed (no `/api/v1`). Selected routes — see
http://localhost:8000/docs for the full, always-current list:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Register + receive JWT |
| POST | `/auth/login` | — | Login + receive JWT (rate-limited after repeated failures, see below) |
| GET/PUT | `/profile` | JWT | View/update student profile |
| POST | `/profile/skills` | JWT | Add skill to Neo4j graph |
| GET | `/jobs` | JWT | Browse jobs (search + filter) |
| GET | `/jobs/{id}` | JWT | Job detail, including required skills |
| GET | `/skills/market` | JWT | Top demanded skills |
| GET | `/skills/gap` | JWT | Skill gap for the student's current target role |
| POST | `/gap-analysis` | JWT | Compute skill gap score for an explicit job |
| GET | `/recommendations/jobs` | JWT | Ranked job matches (`match_source: "gnn"`/`"algorithmic"` per job) |
| GET | `/recommendations/skills` | JWT | Skills to learn next |
| GET | `/recommendations/courses` | JWT | Courses to close a skill gap |
| GET | `/market/insights` | JWT | Market trends |
| GET | `/dashboard` | JWT | Personal KPI stats |
| POST | `/admin/ingest/csv` | Admin token | Upload job data CSV |
| GET | `/health` | — | Health check |

Failed logins lock out after 5 attempts within 5 minutes, per email (429
`TOO_MANY_ATTEMPTS`) — see `backend/app/core/login_lockout.py`.

## Running Tests

```bash
# Backend (from backend/, or docker exec careergraph_backend_api python -m pytest -q)
python3 -m pytest tests/ -v

# Frontend (from frontend/)
npm run test -- --run

# GNN / ML pipeline (needs ml/requirements.txt installed in a venv)
pytest ml/tests/ -v
```
Current counts (2026-08-06): backend 195/195, frontend 85/85, ml 29/29 —
see `docs/current-status.md` for the full scoreboard and what's still open.

## Environment Variables

`backend/.env.example` documents every variable; the two most likely to
need changing locally:

- `FRONTEND_URL` — must exactly match whatever origin the frontend is
  actually served from (CORS is an exact string match, not a wildcard) —
  `http://localhost:8080` for the Vite dev workflow above,
  `http://localhost` for the one-shot full-containerized stack.
- `LLM_PROVIDER` — `none` by default (deliberately — see
  `docs/current-status.md` Milestone 2 for why this is a supported,
  intentional configuration, not a gap). Set to `claude`/`openai`/`ollama`
  plus the matching API key to enable real LLM-generated explanations.

## Loading Job Data

Prefer `make seed` (from `backend/`, see Quick Start above) for the full
dataset. The admin CSV-upload endpoint also exists for uploading a
different/updated file against a running instance:

```bash
curl -X POST http://localhost:8000/admin/ingest/csv \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "file=@backend/data/kaggle_jobs.csv"
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, React Query, React Router v6 |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Intelligence Engine | Custom agent classes, rapidfuzz, pandas |
| Custom AI Model | 2-layer heterogeneous GraphSAGE (PyTorch Geometric) link predictor, trained + evaluated against the algorithmic baseline -- see `docs/gnn-model.md` |
| LLM Providers (optional) | Anthropic Claude, OpenAI, Ollama (local) |
| Databases | PostgreSQL 15, Neo4j 5 |
| Infrastructure | Docker Compose, JWT authentication |

## Where to go next

- `docs/current-status.md` — current build status, honest gaps, milestone roadmap to defense.
- `docs/system-design.md` — full architecture spec.
- `docs/gnn-model.md` / `docs/gnn-defense-guide.md` — the trained model, its evaluation, and how it's actually wired into live recommendations.
- `docs/gnn-training-guide.html` — open this in a browser for the full GNN walkthrough in one place: data prep, architecture, training, evaluation, and live integration, with code references throughout.
- `docs/data-sources.md` — what the shipped dataset actually is and isn't.
- **Thesis chapters:** `docs/implementation-chapter.md`, `docs/evaluation-chapter.md`, `docs/discussion-limitations.md`, `docs/conclusion-future-work.md`.
