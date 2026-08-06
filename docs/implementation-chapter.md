# Implementation

> Thesis Implementation chapter draft, per `docs/current-status.md`
> Milestone 5. Companion to `docs/methodology.md` (Chapter 1 — architecture,
> feasibility, requirements, diagrams, drafted before the build) and
> `docs/system-design.md` (the full architecture spec this chapter reports
> against). Where Methodology described *what was planned*, this chapter
> reports *what was actually built, how, and what changed along the way* —
> including real engineering decisions made under real constraints, not a
> retrospectively tidied narrative.

---

## 1. Development approach

The system was built module-by-module against the sequencing in
`docs/project-roadmap.md` Part A: data layer and auth first (nothing else
can be tested without them), then the ingestion pipeline, then the four
algorithmic agents (the deterministic baseline every later component is
measured against), then the student-facing routers and frontend wiring in
parallel, then the LLM provider abstraction, and — as its own, later,
explicitly separated phase — the custom GNN model (Part B) and its
integration into the live recommendation path.

This ordering was a deliberate risk-management choice: the algorithmic
agents are pure Python with no external dependencies and are fast to get
right and test exhaustively (`test-plan.md` §B5's red/green tests), which
made them a stable foundation to build the GNN comparison against later,
rather than trying to develop both simultaneously and risk an unfair or
inconsistent baseline.

Testing was continuous, not a final pass: every module shipped with its own
red/green tests (per `test-plan.md`'s per-module breakdown, B1–B7 backend,
F1–F8 frontend, plus a dedicated GNN section) before the next module was
started, and the full suite was re-run after every change throughout the
build — including the hardening/bugfix work described in §4 below, which
happened well after the "feature-complete" milestone and depended entirely
on this habit to catch regressions immediately.

## 2. Technology stack (as built)

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, TanStack Query, React Router v6 | Vite dev server on port **8080** (not the framework default 5173 — a real source of a CORS bug, §4) |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic | No `/api/v1` path prefix — routes are flat (`/auth/login`, `/jobs`, etc.) |
| Auth | bcrypt password hashing, JWT (HS256, 24h expiry) | Login additionally rate-limited (§4) |
| Relational data | PostgreSQL 15 | `users`, `student_profiles` |
| Graph data | Neo4j 5 (+ APOC) | `Student`, `Skill`, `Job`, `Course`, `Category` nodes; 6 relationship types |
| Ingestion | Custom `IngestionAgent`/`NormalizationAgent` pipeline | rapidfuzz (≥90 threshold) fuzzy skill matching, synonym exact-match, flag-for-review fallback |
| Intelligence Engine | Four pure-Python algorithmic agents + `EngineOrchestrator` | No ML/LLM dependency for correctness — see §3 |
| Custom AI Model | PyTorch 2.13 / PyTorch Geometric 2.8 — 2-layer heterogeneous GraphSAGE | Trained offline (`ml/`), served inline in the backend process (§3.3) |
| LLM (optional) | Pluggable provider abstraction — Claude / OpenAI / Ollama | Off by default; a deliberate scope decision, not a gap (§3.4) |
| Infrastructure | Docker Compose (Postgres + Neo4j + API [+ frontend]) | Two parallel compose files — see §4.4 for why that duplication was a real source of bugs |

## 3. Key engineering decisions

### 3.1 Algorithmic agents as the baseline, not a placeholder

`SkillGapAgent`, `RecommendationAgent`, `PathFinderAgent`, and
`MarketAgent` (`backend/app/engine/algorithmic/`) are deterministic,
LLM-free, and torch-free. This was not a stopgap pending the "real" AI
model — it's the system's actual intelligence for gap scoring, job
ranking, roadmap ordering, and market demand, and it doubles as the
scientific control the GNN is evaluated against (§3.3, Evaluation
chapter). Building it as production logic rather than a throwaway baseline
meant the comparison in `ml/evaluate.py` is apples-to-apples: the same
`RecommendationAgent.rank_jobs` Jaccard/LEADS_TO logic a real user's
request runs through is exactly what `ml/baseline.py` wraps for offline
evaluation.

### 3.2 Graceful degradation as a first-class pattern, applied twice

The LLM provider abstraction (`backend/app/engine/llm/`) was built with an
explicit contract: any misconfiguration or provider failure falls back to
a template narrative rather than propagating an error
(`EngineOrchestrator._reasoning_agent()`). When the GNN model was added
later, `GNNRecommendationAgent` was deliberately built to mirror that exact
same contract — never raise, report `is_available`/`unavailable_reason`,
degrade to `None` and let the caller fall back. Having the pattern already
proven once (LLM) made the second implementation (GNN) faster and more
consistent, and meant reviewers only need to understand the pattern once
to evaluate both subsystems.

This pattern also turned out to have a real gap that only live testing
caught — see §4.3.

### 3.3 The GNN as a retrieve-then-rerank layer, not a replacement

The trained model (2-layer heterogeneous GraphSAGE, `ml/model.py`) does
not replace `RecommendationAgent`'s scoring — it augments the top of it.
`RecommendationAgent.rank_jobs` scores every job in the catalog
algorithmically first (cheap, no model inference), then reranks only the
top 50 candidates with a GNN-derived signal before re-sorting. This
retrieve-then-rerank shape is a deliberate systems decision, not just a
performance shortcut: scoring all ~9,400 jobs with the GNN on every
request would be both slow and unnecessary, since the algorithmic pass
already discards the vast majority of clearly-irrelevant jobs cheaply. Each
job in the API response carries `match_source` (`"gnn"`/`"algorithmic"`)
so which recommendations were actually model-influenced is inspectable,
not just claimed.

A related, easy-to-miss performance decision: `GNNRecommendationAgent`
caches the encoder's forward pass (`_get_z_dict()`) after the first score
call, and is itself a process-wide singleton
(`get_default_gnn_agent()`) rather than being reconstructed per request —
`EngineOrchestrator` is rebuilt fresh on every API call
(`app/core/deps.py::get_orchestrator`), so without this, the checkpoint
would reload from disk and the encoder would rerun a full forward pass on
every single request. This was caught and fixed before the GNN was wired
into the orchestrator at all, not after a performance regression was
observed in production.

### 3.4 The LLM stays off by default — a decision, not a gap

`LLM_PROVIDER=none` throughout the build. This was reconsidered explicitly
during Milestone 2 (`docs/current-status.md`) and kept: the LLM never
scores, ranks, or predicts anything in this system — it is strictly an
optional narration layer over results the algorithmic agents/GNN have
already computed (`docs/research-contribution.md` Contribution 3). Running
LLM-free throughout development and for the shipped defense build is
itself evidence the graceful-degradation architecture is real and
exercised, not merely asserted in a design doc.

### 3.5 Synthetic data, chosen deliberately over a partial real-data migration

`backend/data/` is a realistically-shaped but synthetic corpus (10,000 job
postings, 518-skill taxonomy), not the literal Kaggle/O*NET datasets
originally scoped. This was an explicit decision (Milestone 3,
`docs/discussion-limitations.md` §1) made under project timeline
constraints: a fully-documented synthetic dataset was judged more
defensible than a partially-migrated real one attempted late and left in
an inconsistent state.

## 4. Real bugs found and fixed during hardening

Software that has never been exercised against real, adversarial-ish usage
tends to look more correct than it is. The items below were found by
actually running the application — registering real users, clicking
through real flows, deploying to a real container — not by code review
alone, and are reported here because each one is evidence of *how* the
system was verified, which is itself part of an honest implementation
account.

### 4.1 A Cypher `MERGE` bug that produced nameless Skill nodes

`GraphService._ingest_job_posting_tx` used `ON CREATE SET sk.name = ...`
when merging `Skill` nodes by `normalized_name` — since `ON CREATE SET`
only fires the first time a node is created, a `Skill` node created by one
write path (e.g. course-seeding) before a job-ingestion write path ever
touched that same skill would keep a `NULL` (or stale/mis-cased) `name`
property permanently, making it invisible to name-based search despite
being fully connected in the graph. Fixed by always `SET`-ting `sk.name`
(self-healing on every write) instead of gating on node creation. Found
via a user report ("I can't find React or Node") that traced back through
direct Cypher inspection to the actual `NULL` property, not a passing test
that happened to miss the case.

### 4.2 An `OPTIONAL MATCH` + `collect()` Cypher pattern producing a phantom null entry

`get_all_jobs_with_requires()`'s `OPTIONAL MATCH` + `collect({name: sk.name, ...})`
produces a single placeholder item `{name: null}` for a job with zero
`REQUIRES` edges, instead of an empty list — a Cypher-specific behavior
that isn't obvious from reading the query in isolation. This crashed
`MarketAgent._normalize_name(None)` in production, a real 500 a live
student hit on `GET /dashboard`. Fixed at the query layer (filter nulls
out of the collected list) and defensively in `MarketAgent` (treat a
missing name as empty string, not a crash trigger) — both, since either
fix alone would have left the other call site fragile to the same class of
bug recurring elsewhere.

### 4.3 The GNN's "never raise" contract had an actual hole, found only by live deployment

`GNNRecommendationAgent`'s inference path called
`export_graph.export()`, which — as a side effect intended for its offline
CLI use — unconditionally writes a `.pt` cache file to disk. With `ml/`
correctly mounted **read-only** in the deployed container (deliberately,
so the running app can't mutate training artifacts), this crashed
`GET /recommendations/jobs` with a 500 the moment a real request exercised
it, silently violating the exact graceful-degradation contract §3.2
describes. Every unit test for this contract (missing checkpoint, corrupt
checkpoint, torch not installed) passed throughout — none of them
constructed the "read-only filesystem in a production-shaped deployment"
scenario. Fixed by building the in-memory graph directly
(`to_hetero_data(build_synthetic_career_graph())`) instead of the
disk-writing wrapper, and a regression test was added
(`ml/tests/test_gnn_pipeline_requires_torch.py::test_inference_never_writes_to_disk`)
that asserts `export_graph.export` is never called by the scoring path at
all. **This is the concrete example, not a hypothetical one, for why this
implementation treats "the test suite is green" and "the system works in
a real deployment" as two different claims that both need checking.**

### 4.4 Two parallel `docker-compose.yml` files drifting out of sync

The repo has both a root `docker-compose.yml` (a one-shot full
containerized stack, including a built/nginx-served frontend) and
`backend/docker-compose.yml` (the dev workflow actually used throughout
the build — Postgres/Neo4j/API only, frontend via `npm run dev`). Both
independently configure `FRONTEND_URL` for CORS, and both were found,
independently, to have a wrong default: `backend/docker-compose.yml` had
`FRONTEND_URL` pointing at a stale port (8081, when the frontend actually
runs on 8080), and the root compose defaulted to `5173` when its
containerized frontend is actually served on port 80. Both were only
caught by actually running each stack and hitting a real CORS failure, not
by inspecting the YAML. The root compose was also missing the `ml`/
`backend/data` volume mounts the GNN integration (§3.3) needs — added for
parity once found. **The general lesson, stated for what it's worth in an
implementation chapter:** two independently-maintained copies of the same
configuration will drift, and the drift is invisible until something
actually tries to use the stale copy.

## 5. Screenshots

*(Insert screenshots of the working application here before submission —
recommended set: Login/Register, Dashboard with a populated skill-gap
chart, Job Explorer with the required-skills detail panel open,
Recommendations page showing at least one `match_source: "gnn"`
"AI-ranked" badge, Skill Analysis / gap breakdown, and Edit Profile's
skill/target-role autocomplete. All of these are real, working flows as of
this chapter's writing — see `docs/current-status.md` for what's been
verified live.)*
