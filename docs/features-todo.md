# CareerGraph — Features & TODOs by Module

> Companion to `project-roadmap.md` (build order/phasing) and `system-design.md` (architecture spec). This document breaks each module down into concrete **features** (what it must do) and a **TODO checklist** (what's actually left to build), for both backend and frontend. Planning only — no code written yet.

> **Update (2026-07-16, final verification phase)**: the baseline paragraph below describes the *original, pre-build* state of the repo and is kept for history. It is no longer accurate — see the checked-off items throughout this document. Current verified state: backend exists (`backend/app/...`, 173 pytest tests passing), frontend is wired to the real API client (69 vitest tests passing across 13 files, no page imports `mockData.ts`), and a GNN model has been trained and evaluated once against synthetic seed data (see the "Custom AI Model" section below and `docs/build-status.md` for the full honest scoreboard and remaining gaps).

Original baseline (pre-build, kept for history): the frontend (`frontend/src/`) is a fully static UI wired to `lib/mockData.ts`. `Login.tsx` has input fields but `handleLogin()` just calls `navigate('/dashboard')` — no request is sent, no validation, no error states. `Dashboard.tsx` and other pages render directly from mock arrays/objects with no loading/error/empty states and no data-fetching hooks. There is no `backend/` directory at all.

---

## BACKEND

### B1. Backend Scaffold & Infra

**Features**
- FastAPI app entrypoint with CORS restricted to `FRONTEND_URL`.
- Central router registration (`auth`, `profile`, `jobs`, `skills`, `recommendations`, `gap-analysis`, `market`, `dashboard`, `admin`).
- Consistent response envelope helper: `{success, data, message}` / `{success: false, error, message}`.
- Global exception handler mapping known errors (validation, not-found, auth) to the envelope format.
- `.env`-driven config object (`DATABASE_URL`, `NEO4J_URI/USER/PASSWORD`, `JWT_SECRET`, `LLM_PROVIDER`, `LLM_MODEL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `FRONTEND_URL`).
- Docker Compose: PostgreSQL 15, Neo4j 5 (with Bolt + HTTP ports), optional Ollama service.
- Health check endpoint (`GET /health`) that pings both DBs.

**TODO**
- [x] Scaffold `backend/` package structure per `system-design.md` §6 file tree. *(verified: `app/{routers,engine,services,models,schemas,database,core}` all present, `backend/main.py` imports cleanly.)*
- [x] `main.py` with CORS + router mounting.
- [x] `app/core/config.py` (pydantic-settings) reading `.env`.
- [x] `docker-compose.yml` (postgres, neo4j, backend, optional ollama), with named volumes for data persistence. *(file exists and defines all services; not yet run/verified live — see B2/gaps below — only `.env.example` exists, no real `.env`.)*
- [x] `requirements.txt` / `pyproject.toml` pinning FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, Alembic, python-jose, neo4j-driver, pandas, rapidfuzz, anthropic, openai, python-dotenv.
- [x] Response envelope + exception-handler utilities in `app/core/responses.py`.
- [x] `GET /health` endpoint. *(`tests/test_health.py`, 10 tests passing.)*
- [x] README section: local dev startup sequence (docker compose up → migrate → seed → uvicorn → npm run dev). *(present in root `README.md` "Quick Start" — not yet re-verified against a live `docker-compose up`, see gaps.)*

---

### B2. Data Layer (PostgreSQL + Neo4j + GraphService)

**Features**
- PostgreSQL: `users` (id, email UK, hashed_password, name, timestamps), `student_profiles` (id, user_id FK, major, graduation_year, skills JSON, target_roles JSON, experience JSON, updated_at) — one-to-one.
- Alembic migration chain (init → any later schema changes).
- Neo4j constraints: uniqueness on `Skill.normalized_name`, `Job.id`, `Student.id`, `Course.id`, `Category.name`.
- Neo4j indexes on frequently-filtered properties (`Job.type`, `Job.location`, `Skill.category`).
- `GraphService`: one class, one method per query pattern used by the algorithmic agents — no ad-hoc Cypher scattered across routers/agents. Fully parameterized (`$param` syntax only, no string interpolation).
- Sync strategy note: profile updates write to Postgres (source of truth for account data) *and* update/MERGE the corresponding `Student` node + `HAS_SKILL`/`TARGETS` edges in Neo4j in the same request.

**TODO**
- [x] SQLAlchemy models: `User`, `StudentProfile`. *(`app/models/user.py`, `app/models/profile.py`.)*
- [x] Pydantic schemas: `UserCreate`, `UserOut`, `ProfileUpdate`, `ProfileOut`. *(`app/schemas/auth.py`, `app/schemas/profile.py`.)*
- [x] Alembic `env.py` + initial migration. *(`alembic/versions/0001_initial_schema.py` present; `alembic upgrade head`/`downgrade base` not re-verified against a live Postgres in this pass — see gaps, test suite runs against SQLite via `TESTING=1`.)*
- [x] `app/database/postgres.py` (engine, session dependency).
- [x] `app/database/neo4j.py` (driver singleton, session context manager).
- [x] Cypher constraint/index bootstrap script (run once at startup or via a management command). *(present in `app/database/neo4j.py`; only exercised against a fake/in-memory graph in tests — never against a live Neo4j 5 instance in this pass.)*
- [x] `GraphService` methods needed by agents — all listed methods exist in `app/services/graph_service.py` and are covered by `tests/test_data_layer.py` (13 tests) against a fake graph backend, not a live Neo4j instance.
- [x] Decide + document Postgres↔Neo4j sync approach (transactional boundary, what happens on partial failure). *(documented + tested at the fake-graph level; never validated against real concurrent Postgres+Neo4j failures — see gaps.)*

---

### B3. Auth Module

**Features**
- Register: email uniqueness check, bcrypt password hashing, creates `User` + empty `StudentProfile`.
- Login: email lookup, bcrypt verify, JWT issuance (HS256, 24h expiry, payload `{user_id, email}`).
- JWT middleware/dependency (`get_current_user`) — every protected route pulls `student_id` from the token only, never from the request body/query (per `system-design.md` §15 control C4).
- 401 responses for bad credentials, expired/invalid tokens, missing header.
- Frontend contract: `POST /auth/register`, `POST /auth/login` → `{token, user}`.

**TODO**
- [x] `app/routers/auth.py`: `POST /auth/register`, `POST /auth/login`.
- [x] `app/core/security.py`: bcrypt hash/verify, JWT encode/decode helpers.
- [x] `get_current_user` FastAPI dependency + reusable `Depends()` for all protected routers. *(`app/core/deps.py`.)*
- [x] Input validation: email format, password minimum strength (define a simple policy).
- [ ] Rate-limit / lockout policy decision for repeated failed logins — not implemented (no in-memory counter or lockout found in `app/routers/auth.py`); still open, scope it explicitly as deferred to Future Work if not building it.
- [x] Unit tests: duplicate email registration, wrong password, expired token, tampered token. *(`tests/test_auth.py`, 25 tests, all passing.)*

---

### B4. Ingestion Pipeline (IngestionAgent + NormalizationAgent)

**Features**
- `IngestionAgent`: reads Kaggle CSV, validates required columns exist, drops malformed rows (missing title/company/skills), parses comma-separated `skills_required` into a list, validates `salary`/`location`/`job_type` fields against expected shapes.
- `NormalizationAgent`: loads `synonyms.json` + O*NET/ESCO skill list once; per raw skill — exact synonym match → mapped canonical name; else rapidfuzz fuzzy match ≥90 against O*NET taxonomy → canonical name + `normalized_name` set; else keep raw name and flag for manual review.
- Neo4j write stage: `MERGE` Skill on `normalized_name`, `MERGE` Job on title+company, `CREATE REQUIRES` edge with `importance` (must/nice) derived from skill position/frequency in the posting, `MERGE Category` + `CREATE IN_CATEGORY`.
- Admin trigger: `POST /admin/ingest/csv` (file upload) runs the pipeline synchronously or as a background task; `GET /admin/ingest/status` returns last-run stats (rows read, rows dropped, skills flagged for review, nodes/edges created).
- `seed_demo_data.py`: 3 demo students, 30 courses (manually curated, mapped to skill nodes), curated 50-job subset for fast local dev/demo without needing the full 10k CSV.

**TODO**
- [x] `data/kaggle_jobs.csv` is now a ~10,000-row synthetic dataset (up from the earlier 204-line placeholder), `data/onet_skills.csv` has 518 skills, `data/synonyms.json` has 215 aliases — the fixture is now at realistic target **scale** (10k postings, 500+-skill taxonomy), verified by running `IngestionAgent`+`NormalizationAgent` end-to-end over the full file: 10,000/10,000 rows read, 0 dropped, 55,428 skill edges written, 493 skill instances (17 distinct strings) flagged for manual review, in well under a second.
- [ ] These files are still **synthetic, generated data**, not the real Kaggle job-postings dataset or real O*NET/ESCO taxonomy (confirmed by reading `docs/gnn-model.md` and the CSV contents directly). Acquiring and swapping in genuinely real-world sources is still outstanding — this is the only remaining piece of this item.
- [x] `app/engine/ingestion/ingestion_agent.py` — CSV read/validate/parse.
- [x] `app/engine/ingestion/normalization_agent.py` — synonym + fuzzy match + flag-for-review logic.
- [x] Neo4j write step using `GraphService`. *(exercised only against the fake/in-memory graph service in tests, never a live Neo4j 5 instance.)*
- [x] `app/routers/admin.py`: `POST /admin/ingest/csv`, `GET /admin/ingest/status` — admin auth implemented as a fixed shared-secret header (`X-Admin-Token` checked against `ADMIN_TOKEN` setting), the "fixed admin token for capstone scope" option from the open decisions list.
- [x] `app/etl/seed_demo_data.py`.
- [x] Decide + implement "flagged for review" storage — implemented, admin-only, not surfaced in student UI (per plan).
- [x] Unit tests: malformed CSV row dropped, known synonym mapped correctly, fuzzy match threshold boundary (89 vs 90), unmatched skill flagged not silently dropped. *(`tests/test_ingestion.py`, 28 tests, all passing.)*
- [x] Idempotency: re-running ingestion on the same CSV should not duplicate Job/Skill nodes. *(tested against the fake graph service; not re-verified against a live Neo4j `MERGE` in this pass.)*

---

### B5. Algorithmic Agents (SkillGapAgent, RecommendationAgent, PathFinderAgent, MarketAgent)

**Features**
- **SkillGapAgent**: given `student_skills[]`, `required_skills[]` (split must/nice), `proficiency_map{}` → `readiness_score = (must_matched/must_total)×0.7 + (nice_matched/nice_total)×0.3 + proficiency_bonus`, plus `matched_skills[]`/`missing_skills[]`.
- **RecommendationAgent**: `exact_score = |A∩B|/|A∪B|` (Jaccard) + `partial_score` via `LEADS_TO` graph proximity within depth 2 → `final_score = exact×0.8 + partial×0.2`; returns jobs ranked descending.
- **PathFinderAgent**: BFS from each missing skill over `LEADS_TO`, topological sort into an ordered learning path, attaches `TEACHES` courses per milestone, estimates weeks per skill.
- **MarketAgent**: aggregates `REQUIRES` edge counts per skill → `demand_score` (0–100 normalized), trend delta over time (requires either historical ingestion snapshots or a simple recency-weighted proxy for v1).
- All four are pure Python, deterministic, zero network calls, unit-testable in isolation from FastAPI/DB (take graph data as plain Python structures, `GraphService` fetches it separately).

**TODO**
- [x] `app/engine/algorithmic/skill_gap_agent.py` + unit tests (edge cases: 0 required skills, student has 0 skills, all matched).
- [x] `app/engine/algorithmic/recommendation_agent.py` + unit tests (identical skill sets, disjoint sets, partial-match depth-2 boundary).
- [x] `app/engine/algorithmic/path_finder_agent.py` + unit tests (cyclic `LEADS_TO` graph handling — must not infinite-loop; missing skill with no prerequisites).
- [x] `app/engine/algorithmic/market_agent.py` + unit tests; trend decision documented and implemented (recency-weighted v1 proxy per the file's own docstring, since no historical ingestion snapshots exist yet). *(All four agents covered by `tests/test_algorithmic_agents.py`, 29 tests, all passing.)*
- [x] Decide/document the exact "must vs. nice" classification rule for skills within a job posting. *(Documented in `skill_gap_agent.py`: first 60% of a posting's skill list = "must", remainder = "nice"; unclassified defaults conservatively to "nice".)*
- [x] Shared Pydantic result schemas (`GapResult`, `RankedJob`, `LearningPath`, `DemandData`) used by both the agents and the `ReasoningAgent` as typed input.

---

### B6. LLM Provider Abstraction + Reasoning Agent + Orchestrator

**Features**
- `LLMProvider` ABC: `complete(system_prompt, user_prompt, output_schema, timeout=30, retries=2) -> BaseModel`, `stream(...)`, `get_model_info()`.
- `ClaudeProvider` (anthropic SDK, JSON via tool_use), `OpenAIProvider` (openai SDK, `response_format`), `OllamaProvider` (HTTP to local Ollama, JSON schema embedded in system prompt).
- Every provider returns a **validated Pydantic model** — `ReasoningAgent` never touches raw LLM text.
- `ReasoningAgent` methods: `explain_gap(gap_result)`, `narrate_recommendations(ranked_jobs)`, `write_roadmap(learning_path)`, `summarize_market(demand_data)`.
- `EngineOrchestrator`: runs the relevant algorithmic agent(s) first → checks `LLM_PROVIDER` configured → if yes, calls `ReasoningAgent` → merges scores + narrative into the typed response; if no, returns algorithmic result with **template narratives** (not empty strings) so the frontend never breaks.
- Provider selection purely via `.env` (`LLM_PROVIDER=claude|openai|ollama`), swappable without code changes.

**TODO**
- [x] `app/engine/llm/base.py` (ABC + shared retry/timeout logic).
- [x] `app/engine/llm/claude_provider.py`, `openai_provider.py`, `ollama_provider.py` (+ a `factory.py` for provider selection).
- [x] `app/engine/reasoning/reasoning_agent.py` with the 4 methods + their Pydantic output schemas.
- [x] `app/engine/orchestrator.py` — routing + LLM-configured check + fallback template strings.
- [x] Prompt templates per method (system + user prompt construction).
- [x] Retry/backoff + schema-validation-failure fallback path.
- [x] Cost/latency guardrail: cap tokens, set sane `max_tokens`, log provider + latency per call.
- [x] Unit tests with a mocked `LLMProvider` verifying orchestrator fallback behavior when `LLM_PROVIDER` unset. *(`tests/test_llm_reasoning.py` — 25 tests — and `tests/test_routers.py`'s `TestOrchestratorLLMFallback` class, all passing, all mocked — no test in this suite calls a real Anthropic/OpenAI/Ollama API, and no real `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` is configured anywhere in this repo — see gaps for what a live LLM demo still needs.)*

---

### B7. Student-Facing Routers

**Features**
- `profile`: `GET /profile`, `PUT /profile`, `POST /profile/skills` — read/update profile, add/update individual skills (proficiency, years).
- `jobs`: `GET /jobs?type=&location=&search=&limit=`, `GET /jobs/:id` — browse/filter/detail.
- `skills`: `GET /skills/market` (aggregate demand), `GET /skills/gap` (current user vs. their stated target role).
- `recommendations`: `GET /recommendations/jobs`, `GET /recommendations/skills`, `GET /recommendations/courses`.
- `gap-analysis`: `POST /gap-analysis` with `target_job_id` body → `GapAnalysisResponse` + `RoadmapResponse`.
- `market`: `GET /market/insights` → top skills, trend bullets, summary.
- `dashboard`: `GET /dashboard` → `DashboardStats` (readiness score, skills matched/total, missing high-demand skills, market demand snapshot).
- All routes protected by JWT except `/auth/*`; all return the shared envelope.

**TODO**
- [x] One router file per resource per `system-design.md` §6 file tree, each a thin controller delegating to `EngineOrchestrator`/`GraphService`. *(`app/routers/{auth,profile,jobs,skills,recommendations,gap_analysis,market,dashboard,admin}.py` all present.)*
- [x] Pydantic request/response schemas per route.
- [x] Pagination + filtering params for `GET /jobs`.
- [x] Decide what "current target role" means for `/skills/gap` — resolved and documented in code/tests (both `/skills/gap` and `POST /gap-analysis` exist and are consistency-tested against each other).
- [x] Integration tests per route (happy path + 401 unauthenticated + 404 not-found + validation error). *(`tests/test_routers.py`, 26 tests, all passing — covers all 8 student routers plus the cross-endpoint consistency checks and the parameterized 401 sweep from `test-plan.md`.)*

---

## FRONTEND

### F1. API Client Layer & Auth Wiring (new — doesn't exist yet)

**Features**
- Typed API client modules mirroring backend resources: `authApi`, `profileApi`, `jobsApi`, `skillsApi`, `recApi`, `gapApi`, `marketApi`.
- Central `fetch`/`axios` wrapper: base URL from env, JSON parsing, envelope unwrapping (`{success, data, message}` → throw on `success: false`), automatic `Authorization: Bearer <token>` header injection.
- JWT storage (localStorage) + a small auth context/hook (`useAuth`) exposing `token`, `user`, `login()`, `logout()`.
- React Query setup: `QueryClientProvider` at app root, per-resource `useQuery`/`useMutation` hooks (`useJobs`, `useProfile`, `useDashboard`, etc.), sane `staleTime`/retry config.
- Route protection: redirect to `/` (login) if no valid token when hitting `/dashboard`, `/profile`, etc.
- 401 handling: on any API 401, clear token and redirect to login (session-expired UX).

**TODO**
- [x] `src/lib/apiClient.ts` — base fetch wrapper + envelope handling + auth header injection. *(`src/lib/apiClient.test.ts`, 7 tests, passing.)*
- [x] `src/lib/api/{auth,profile,jobs,skills,recommendations,gap,market,dashboard}.ts`. *(all present in `src/lib/api/`.)*
- [x] `src/hooks/useAuth.tsx` (context provider + hook), wrap `App.tsx`. *(`src/hooks/useAuth.test.tsx`, 5 tests, passing.)*
- [x] `src/main.tsx` / `App.tsx`: add `QueryClientProvider`.
- [x] `src/components/ProtectedRoute.tsx`. *(`src/components/ProtectedRoute.test.tsx`, 2 tests, passing.)*
- [x] Env config: `VITE_API_BASE_URL` in `.env`/`.env.example`.
- [ ] Remove reliance on `mockData.ts` — **partially done**: no page under `src/pages` imports from `lib/mockData` anymore (enforced by `src/test/noMockDataImports.test.ts`), but `src/components/ui/job-card.tsx` still imports the `Job` *type* from `lib/mockData.ts`, so the file itself has not been deleted yet. Final cleanup (move the `Job` type out of `mockData.ts`, then delete it) is still outstanding.

---

### F2. Login Page

**Current state**: static form, `handleLogin()` just navigates — no request, no validation, no errors.

**Features needed**
- Controlled inputs (currently uncontrolled — no `useState`/`value`/`onChange` at all).
- Client-side validation (email format, required fields) before submit.
- Call `authApi.login()`, store token via `useAuth`, navigate to `/dashboard` only on success.
- Error state: invalid credentials, network failure — inline message, not a silent failure.
- Loading state on the submit button while the request is in flight.
- (Optional, if register flow is in scope) a register form/toggle — currently there is none at all; decide if self-registration is needed for the demo or if seeded demo accounts are sufficient.

**TODO**
- [x] Add controlled form state.
- [x] Wire to `authApi.login`, handle success/error/loading.
- [x] Add form validation.
- [ ] Decide + implement register UI — **not done**: `Login.tsx`/`Login.test.tsx` cover login only; no register form/toggle found in `src/pages`. Scope this out explicitly (seeded demo credentials only) or build it before the demo — currently undecided/undocumented.

*(`src/pages/Login.test.tsx`, 10 tests, all passing — covers validation, loading, error, and success paths from the test plan.)*

---

### F3. Dashboard Page

**Current state**: reads `dashboardStats`, `mockSkills`, `marketSkillDemand` directly, no fetching/loading/error states.

**Features needed**
- Replace mock reads with `useDashboard()` (React Query) hitting `GET /dashboard`.
- Loading skeleton state (component `skeleton.tsx` already exists in the UI kit — reuse it).
- Empty/partial-data state (e.g., student has 0 skills yet — should prompt "complete your profile" rather than render broken bars).
- Error state (API failure / no LLM configured shouldn't break this page since dashboard is largely algorithmic per system design).
- Keep existing `StatCard`/`SkillBar` components as-is — they're presentation-only and don't need changes, just real props.

**TODO**
- [x] `useDashboard` hook → `GET /dashboard`. *(`src/hooks/useDashboard.ts`.)*
- [x] Add loading skeleton + empty-state branch before the main render.
- [x] Remove `mockData` imports once wired. *(`src/pages/Dashboard.test.tsx`, 5 tests, all passing — covers loading, success, empty-profile, and error states from the test plan.)*

---

### F4. Profile & Edit Profile Pages

**Current state**: not yet read in detail — assume same mock pattern as others (uses `mockStudent`). Needs verification during implementation, but plan for:

**Features needed**
- View mode: render profile from `GET /profile`.
- Edit mode: form for major, graduation year, skills (add/remove with proficiency + years), target roles, experience items (add/remove).
- Skill entry UX: autocomplete/typeahead against known O*NET skill names (nice-to-have; v1 can be free text with normalization happening server-side).
- Save → `PUT /profile` (+ `POST /profile/skills` if skills are managed as a separate sub-resource per the API contract).
- Validation: graduation year range, at least one target role before gap-analysis/recommendations can be meaningfully used (decide if this is enforced or just a UX nudge).

**TODO**
- [x] `Profile.tsx`/`EditProfile.tsx` wired to real data.
- [x] `useProfile` query + update/skills mutations. *(`src/hooks/useProfile.ts`.)*
- [x] Form (react-hook-form + zod schema matching backend `ProfileUpdate`).
- [x] Refetch-on-success / cache invalidation for the skill list. *(`src/pages/Profile.test.tsx` — 4 tests — and `src/pages/EditProfile.test.tsx` — 6 tests, including the "adds a skill... without a full reload, rejecting duplicates" case — all passing.)*

---

### F5. Job Explorer Page

**Current state**: renders `mockJobs` with `matchPercentage`/`whyRecommended` baked into mock data.

**Features needed**
- `GET /jobs` with filters (type, location, search) + pagination/"load more".
- Filter UI state (dropdowns/search box) driving query params.
- Job detail view/modal via `GET /jobs/:id` (check if current UI already has a detail view or just a list — verify during implementation).
- Distinguish plain job browsing (no personalized match score, since `/jobs` is generic) from the personalized `/recommendations/jobs` — current mock data conflates the two (`Job` interface has `matchPercentage`/`whyRecommended` even in the generic list). Decide: does the Job Explorer show match scores too (would require joining recommendation data) or is that exclusive to the Recommendations page?

**TODO**
- [x] Clarified: Job Explorer is a pure catalog browse via `jobsApi` (`GET /jobs`), no personalized match scoring — resolved.
- [x] `useJobs(filters)` query with debounced search input. *(`src/hooks/useJobs.ts`.)*
- [x] Filter controls wired to query params.
- [x] Loading/empty/error states + "Load more" pagination.
- [x] Reuse existing `JobCard` component with real props. *(`src/pages/Jobs.test.tsx`, 8 tests, all passing — including the debounced-search and pagination-append cases.)*

---

### F6. Skill Analysis Page

**Current state**: uses `mockSkills` for a static gap view.

**Features needed**
- Trigger gap analysis against a chosen target job (`POST /gap-analysis` with `target_job_id`) — needs a job-selection UI if the student has multiple target roles/jobs in mind (currently no such selector exists in mock version).
- Render `readiness_score`, `matched_skills`, `missing_skills` (with `estimated_learning_weeks`), LLM `explanation`/`encouragement` when present, and the roadmap (`Milestone[]`: week ranges, courses, goals).
- Graceful rendering when no LLM is configured (template narrative instead of blank explanation).

**TODO**
- [x] Add target-job selector.
- [x] `useGapAnalysis(targetJobId)` mutation/query → render `GapAnalysisResponse` + `RoadmapResponse`. *(`src/hooks/useGapAnalysis.ts`.)*
- [x] Distinct "analyzing..." loading state for the (potentially slower) gap-analysis call.
- [x] Roadmap timeline UI (week ranges → milestones → course links). *(`src/pages/SkillAnalysis.test.tsx`, 10 tests, all passing — covers the "already 100% ready" and "no target job selectable" edge cases from the test plan.)*

---

### F7. Recommendations Page

**Current state**: uses `mockJobs`/`mockCourses` with hardcoded scores/explanations.

**Features needed**
- Three data sources: `GET /recommendations/jobs`, `/skills`, `/courses` — likely tabs or sections.
- Job cards show `why_recommended` (LLM-narrated) with graceful fallback text when LLM absent.
- Course cards show `matchScore`/`explanation` tied to actual skill gaps, not static mock text.

**TODO**
- [x] Recommendation hooks for jobs/skills/courses. *(`src/hooks/useRecommendations.ts`.)*
- [x] Tab/section structure wired to the three endpoints.
- [x] Loading/empty/error states per section (independent per-section failure).
- [x] Reuse existing `JobCard` for the jobs section; course card presentation adjusted. *(`src/pages/Recommendations.test.tsx`, 5 tests, all passing — including the independent-section-failure case from the test plan.)*

---

### F8. Shared Infra / Cross-Cutting Frontend TODOs

- [x] `AppLayout` wired to `useAuth`'s real `user` (name/email), not hardcoded.
- [x] Toast wiring via `sonner`/`toaster` for API error surfacing (per-page, matches test-plan F8 item 3). Note: no dedicated React `ErrorBoundary`/`componentDidCatch` component was found for unhandled render-time crashes — only query/mutation-level error toasts. Fine for the tested scope, but a top-level crash boundary is not in place.
- [x] Logout action (clear token, redirect to `/`).
- [x] Expand `src/test/` (Vitest) — `apiClient.test.ts` (7 tests), `useAuth.test.tsx` (5 tests), and page-level tests for all 7 pages (Dashboard, Login, Profile, EditProfile, Jobs, SkillAnalysis, Recommendations) with mocked API responses. Full suite: **13 test files, 69 tests, all passing.**
- [x] Loading/empty/error UI consistency pass across all pages — confirmed present in every page's test file.
- [ ] Decide fate of `mockData.ts` — **not fully resolved**: no `VITE_USE_MOCKS` flag exists; the file is simply still present because `job-card.tsx` imports the `Job` type from it (see F1 note). Automated check (`noMockDataImports.test.ts`) only guards page-level imports, not the type import — final decision/cleanup still open before thesis submission.

---

## Custom AI Model — Feature/TODO Detail (see `project-roadmap.md` Part B for full context)

**Features**
- Export pipeline: Neo4j → PyTorch Geometric `HeteroData` (node/edge type mapping).
- Link-prediction training script: GraphSAGE/R-GCN encoder + dot-product/MLP decoder, edge-level train/val/test split, negative sampling.
- Evaluation script: AUC-ROC, Hits@10, MRR — run against both the GNN and the existing algorithmic baseline on the same held-out edges.
- Inference module: load trained model weights, score candidate `REQUIRES`/`LEADS_TO` edges on demand, exposed behind the same optional/swappable pattern as `LLMProvider`.

**TODO**
- [x] `ml/export_graph.py` — Neo4j → `HeteroData` exporter. *(Note: exports from the ingestion pipeline run against `backend/tests/fakes.py::FakeGraphService`, i.e. the synthetic seed data — not a live Neo4j instance, since none exists in this repo/environment.)*
- [x] `ml/train_gnn.py` — model definition + training loop + checkpointing. *(`ml/checkpoints/gnn_link_predictor.pt` exists — was actually trained and checkpointed, per `docs/gnn-model.md`.)*
- [x] `ml/evaluate.py` — metrics computation, baseline comparison table. *(`ml/results/evaluation_report.json` contains real computed AUC-ROC/Hits@10/MRR numbers for both the GNN and the algorithmic baseline on identical held-out edges — this is a genuine result, not a placeholder, though on a tiny synthetic graph: 165 jobs/75 skills, only 6 `LEADS_TO` test edges.)*
- [x] `app/engine/algorithmic/gnn_recommendation_agent.py` — inference integration point, with graceful fallback to the algorithmic path when no checkpoint is present (`tests/test_gnn_recommendation_agent.py`, 5 tests, passing).
- [x] Retraining cadence decided: fixed snapshot for defense reproducibility (documented in `docs/gnn-model.md`), re-training pipeline noted as Future Work.
- [x] `ml/requirements.txt` kept separate from `backend/requirements.txt` so the core API doesn't need PyTorch.

**Caveat carried into all the checkmarks above**: `torch`/`torch_geometric` are **not installed in this environment** (`ModuleNotFoundError: No module named 'torch'` when checked in this pass) — `ml/tests/test_gnn_pipeline_requires_torch.py` auto-skips without them (confirmed: 19 passed, 1 skipped when running `pytest ml/tests`). The checkpoint and evaluation numbers above are real outputs *from a prior session* that had the ML stack installed, not something re-verified live in this verification pass, and not yet run against a real ingested Kaggle/O*NET graph — only the synthetic seed data. `LEADS_TO` edges have no real data source at all (synthesized via an alphabetical same-category heuristic in `ml/graph_build.py`) — this is explicitly flagged as Future Work in `docs/gnn-model.md`.

---

## Open decisions to resolve before/while building (flagged throughout above, collected here for visibility)

1. Admin auth model for `/admin/ingest/*` — separate role vs. fixed token (capstone scope).
2. `/skills/gap` vs. `POST /gap-analysis` — reconcile into one clear contract.
3. Job Explorer: personalized match scores or pure catalog?
4. Self-registration UI vs. seeded demo accounts only.
5. Market trend calculation without historical ingestion snapshots (v1 approximation).
6. "Must vs. nice" skill classification rule — needs a concrete, documented formula.
7. `mockData.ts` retirement plan (flag-gated during transition vs. immediate deletion).
8. GNN retraining cadence (fixed snapshot vs. live pipeline).
