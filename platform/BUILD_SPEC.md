# CareerGraph — Platform Build Specification

**Status:** Active development  
**Last updated:** 2026-05-19  
**Scope:** Complete platform — backend wiring, frontend pages, infrastructure, model layer

---

## Directory Structure

```
career-graph/
├── platform/
│   ├── backend/          ← FastAPI + Intelligence Engine
│   ├── frontend/         ← React 18 + TypeScript
│   └── BUILD_SPEC.md     ← this file
├── docs/                 ← Capstone documents
├── data/                 ← CSV datasets (kaggle_jobs.csv, onet_skills.csv)
├── docker-compose.yml    ← Orchestrates postgres + neo4j + api
└── README.md
```

---

## Current State Audit

### What is complete and tested

| Component | Status | Tests |
|---|---|---|
| `SkillGapAgent` | Complete | ✓ unit tested |
| `RecommendationAgent` | Complete | ✓ unit tested |
| `PathFinderAgent` | Complete | ✓ unit tested |
| `MarketAgent` | Complete | ✓ unit tested |
| `ReasoningAgent` | Built, **not wired to any router** | ✓ unit tested |
| `EngineOrchestrator` | Built, **bypassed by all routers** | ✓ unit tested |
| `IngestionAgent` | Complete | ✓ unit tested |
| `NormalizationAgent` | Complete | ✓ unit tested |
| `GraphService` | Complete | ✓ integration tested |
| `LLMProvider` (Claude/OpenAI/Ollama) | Built, **not instantiated at startup** | ✓ unit tested |
| `auth` router | Complete | ✓ |
| `profile` router | Complete | ✓ |
| `jobs` router | Complete | ✓ |
| `skills` router | Partial — gap endpoint missing PathFinder | ✓ partial |
| `gap_analysis` router | Partial — no PathFinder, no LLM | ✓ partial |
| `recommendations` router | Partial — no LLM narration | ✓ partial |
| `market` router | Complete | ✓ |
| `dashboard` router | Complete | ✓ |
| `admin` router | Complete | ✓ |
| Frontend: LoginPage | Complete | — |
| Frontend: RegisterPage | Complete | — |
| Frontend: DashboardPage | Complete | — |
| Frontend: ProfilePage | Complete | — |
| Frontend: ProfileEditPage | Complete | — |
| Frontend: JobsPage | Complete | — |
| Frontend: SkillsPage | Partial — no roadmap section | — |
| Frontend: RecommendationsPage | Partial — no courses tab | — |
| Frontend: JobDetailPage | **Missing** | — |
| Frontend: RoadmapPage | **Missing** | — |
| Frontend: MarketPage | **Missing** | — |
| Frontend: AppLayout nav | Partial — missing new pages | — |

### Key wiring gaps (highest priority)

1. **`gap_analysis` router** calls `SkillGapAgent` directly but ignores `PathFinderAgent` and `ReasoningAgent`. The `explain` flag in the request schema is read but discarded.
2. **`recommendations` router** calls `RecommendationAgent` directly but never calls `ReasoningAgent.narrate_recommendations()`.
3. **LLM provider factory** does not exist — no code reads `LLM_PROVIDER` env var and creates the right provider at startup. All routers instantiate agents without an LLM.
4. **`LEADS_TO` edges** are never seeded. `PathFinderAgent.build_learning_path()` always receives an empty `prereq_graph`, making the topological sort a no-op. Prerequisite data must be seeded.
5. **Routers bypass `EngineOrchestrator`** — the orchestrator is fully implemented but never used in production code paths.

---

## Complete API Contract

All endpoints prefixed `/api/v1`. Auth endpoints use Bearer JWT.

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Register with name, email, password |
| POST | `/auth/login` | No | Returns JWT access token |

### Profile

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/profile` | Yes | Full profile + skills from Neo4j |
| PUT | `/profile` | Yes | Update name, university, graduation_year, target_roles, bio |
| POST | `/profile/skills` | Yes | Add/update skill with proficiency (0–10) and years |
| DELETE | `/profile/skills/{skill_name}` | Yes | Remove skill |

### Jobs

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/jobs` | No | List with search, location, employment_type, skill filters. Paginated. |
| GET | `/jobs/{job_id}` | No | Single job with full skill requirements (importance: must/nice) |

### Skills & Gap

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/skills/market` | No | Top 50 skills by demand count + demand_score (0–100) |
| GET | `/skills/gap?target_job_id=` | Yes | Gap result + **learning roadmap** (PathFinder output) |

### Gap Analysis

| Method | Path | Auth | Body | Description |
|---|---|---|---|---|
| POST | `/gap-analysis` | Yes | `{target_job_id, explain?}` | Full gap + roadmap + optional LLM explanation |

### Recommendations

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/recommendations/jobs?top_n=` | Yes | Jaccard-ranked job matches + optional why_recommended |
| GET | `/recommendations/skills` | Yes | Top missing market skills |
| GET | `/recommendations/courses` | Yes | Courses for top missing skills |

### Market

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/market/insights` | No | total_jobs, top_skills (30), top_categories |

### Dashboard

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/dashboard` | Yes | skills_count, top_job_readiness, total_jobs_in_market, top_demanded_skill |

### Admin

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/admin/ingest/csv` | Admin JWT | Ingest job CSV into Neo4j via IngestionAgent + NormalizationAgent |
| POST | `/admin/seed/prerequisites` | Admin JWT | **[NEW]** Seed LEADS_TO edges from prerequisite JSON |
| GET | `/admin/stats` | Admin JWT | **[NEW]** Graph stats: node counts, edge counts, last ingest time |

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Status + version |

### Model (Future)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/model/infer` | Admin JWT | **[STUB]** Direct inference against custom fine-tuned model |
| GET | `/model/status` | Admin JWT | **[STUB]** Health + version of the hosted model |

---

## Task List

Tasks are sized for independent agent execution. Each task specifies its inputs, outputs, and acceptance criteria. Tasks within a group are independent unless a `depends_on` is listed.

---

### GROUP B — Backend Wiring (highest priority)

---

#### B-01 · LLM Provider Factory at Startup

**File:** `platform/backend/app/engine/llm/factory.py` (new) + `platform/backend/main.py`

**What to do:**
Create a `create_llm_provider(settings) -> LLMProvider | None` function that reads `settings.llm_provider` and returns the correct provider instance (ClaudeProvider, OpenAIProvider, OllamaProvider, or `None`). Store the instance on `app.state.llm_provider` during `lifespan`. All routers that need an LLM should retrieve it via `request.app.state.llm_provider`.

**Acceptance criteria:**
- Setting `LLM_PROVIDER=none` or missing API key → `app.state.llm_provider` is `None`.
- Setting `LLM_PROVIDER=claude` with valid `ANTHROPIC_API_KEY` → ClaudeProvider instance.
- Setting `LLM_PROVIDER=openai` → OpenAIProvider instance.
- Setting `LLM_PROVIDER=ollama` → OllamaProvider instance.
- Setting `LLM_PROVIDER=custom` → CustomModelProvider (stub, returns template).
- No routers break when `llm_provider` is `None`.
- Unit test: `test_llm_factory.py` — four cases.

**Notes:** `CustomModelProvider` is a stub for the future fine-tuned model. It should implement `LLMProvider` and hit `settings.custom_model_url` if set.

---

#### B-02 · Wire EngineOrchestrator into `gap_analysis` Router

**File:** `platform/backend/app/routers/gap_analysis.py`

**What to do:**
Replace the direct `SkillGapAgent` call with `EngineOrchestrator.analyze_gap()`. Pass `llm_provider` from `request.app.state`. When `body.explain=True`, pass through to the orchestrator which calls `ReasoningAgent.explain_gap()`. Also call `orchestrator.get_learning_path()` and include the full PathFinder roadmap in the response.

**Response shape (update `GapAnalysisResult` schema):**
```json
{
  "target_job_id": "...",
  "target_job_title": "...",
  "readiness_score": 72.5,
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["Spark", "Scala"],
  "must_matched": 4,
  "must_total": 6,
  "nice_matched": 1,
  "nice_total": 3,
  "roadmap": {
    "milestones": [
      {"week": 1, "skills": ["Spark"], "description": "Week 1: Learn Spark"},
      {"week": 2, "skills": ["Scala"], "description": "Week 2: Learn Scala"}
    ],
    "weeks_estimate": 2,
    "total_skills": 2,
    "summary": "..."
  },
  "explanation": "...",
  "encouragement": "...",
  "weeks_to_learn": 4
}
```

**Acceptance criteria:**
- `POST /api/v1/gap-analysis` returns both gap and roadmap in one call.
- `explain=false` → no LLM called, template fallback used.
- `explain=true` → LLM explanation included if provider configured.
- `roadmap.milestones` is ordered (prerequisite skills come before dependent skills).
- Tests: `test_gap_analysis_router.py` updated to assert roadmap field present.

**Depends on:** B-01

---

#### B-03 · Wire ReasoningAgent into `recommendations` Router

**File:** `platform/backend/app/routers/recommendations.py`

**What to do:**
In `recommend_jobs()`, after getting the ranked list, call `orchestrator.reasoning_agent.narrate_recommendations(result)` if `request.app.state.llm_provider` is set. This adds `why_recommended` to each job dict.

**Acceptance criteria:**
- When LLM is configured, each job in `/recommendations/jobs` response includes `why_recommended` string.
- When LLM not configured, `why_recommended` is a template string (already implemented in ReasoningAgent).
- No latency regression when LLM disabled.
- Test: `test_recommendations_router.py` updated.

**Depends on:** B-01

---

#### B-04 · Skill Prerequisite Seeding

**Files:**
- `platform/backend/data/prerequisites.json` (new data file)
- `platform/backend/app/routers/admin.py` (new endpoint)
- `platform/backend/app/services/graph_service.py` (new method)

**What to do:**
Create `prerequisites.json` with a meaningful set of `LEADS_TO` relationships for the skills in the dataset. Format:
```json
{
  "prerequisites": [
    {"from": "Machine Learning", "to": "Python", "difficulty_jump": 2},
    {"from": "Deep Learning", "to": "Machine Learning", "difficulty_jump": 3},
    {"from": "React", "to": "JavaScript", "difficulty_jump": 1},
    ...
  ]
}
```
Cover at minimum: Python stack, JavaScript/TypeScript stack, data science stack, cloud stack (AWS/GCP/Azure).

Add `POST /api/v1/admin/seed/prerequisites` endpoint that reads this file and creates `LEADS_TO` edges in Neo4j.

Add `GraphService.upsert_prereq_edges(edges: list[dict])` method using MERGE.

**Acceptance criteria:**
- After calling the endpoint, `GET /api/v1/skills/gap` returns a roadmap with skills in correct prerequisite order (e.g., Python before Machine Learning).
- The prerequisite file has at least 40 relationships.
- Test: `test_admin_router.py` - seeding creates LEADS_TO edges.

---

#### B-05 · Update `skills/gap` Endpoint to Return Roadmap

**File:** `platform/backend/app/routers/skills.py`

**What to do:**
The `GET /skills/gap` endpoint currently returns gap only. Update it to also call `PathFinderAgent` and return the full roadmap structure, matching the B-02 `gap_analysis` response shape (minus the LLM explanation fields — `skills/gap` stays algorithmic-only, no LLM).

**Acceptance criteria:**
- Response includes `roadmap` field with milestones, weeks_estimate, total_skills.
- Matches the subset of B-02 response that doesn't require LLM.

---

#### B-06 · Admin Stats Endpoint

**File:** `platform/backend/app/routers/admin.py`

**What to do:**
Add `GET /api/v1/admin/stats` that returns:
```json
{
  "node_counts": {"Job": 120, "Skill": 80, "Student": 5, "Course": 30, "Category": 7},
  "edge_counts": {"REQUIRES": 450, "HAS_SKILL": 23, "LEADS_TO": 40, "TEACHES": 60},
  "graph_density": 0.04
}
```
Add corresponding `GraphService.get_graph_stats()` method using `MATCH (n) RETURN labels(n), count(n)` and similar Cypher queries.

**Acceptance criteria:**
- Returns correct counts from a seeded Neo4j instance.
- Requires admin JWT.
- Test: mock Neo4j session, assert correct counts returned.

---

#### B-07 · Custom Model Provider Stub

**File:** `platform/backend/app/engine/llm/custom_provider.py` (new)

**What to do:**
Implement `CustomModelProvider(LLMProvider)` that:
1. Reads `CUSTOM_MODEL_URL` and `CUSTOM_MODEL_NAME` from settings.
2. On `complete(system, user)` — if `CUSTOM_MODEL_URL` is set, POST to `{url}/v1/chat/completions` with OpenAI-compatible request format (compatible with vLLM and HuggingFace TGI endpoints).
3. Falls back to template if URL not set or request fails.

This prepares the wiring for hosting your own fine-tuned model via vLLM or TGI without changing any other code.

**Acceptance criteria:**
- `LLM_PROVIDER=custom` + `CUSTOM_MODEL_URL=http://localhost:8080` → requests go to that URL.
- Failure degrades gracefully to template.
- `LLM_PROVIDER=custom` without URL → behaves like `None`.
- Test: mock httpx call, assert OpenAI-format payload sent.

**Depends on:** B-01

---

#### B-08 · Startup Data Validation

**File:** `platform/backend/main.py`

**What to do:**
In `lifespan()`, add a startup check that logs warnings if:
- Neo4j has 0 Job nodes (data not ingested yet).
- `JWT_SECRET` is still the default placeholder value.
- `LLM_PROVIDER` is set but the corresponding API key is missing.

Do not raise exceptions — log warnings only, so the server still starts.

**Acceptance criteria:**
- Starting with empty Neo4j logs: `WARNING: No jobs in graph. Run POST /api/v1/admin/ingest/csv`.
- Starting with default JWT secret logs: `WARNING: JWT_SECRET is using placeholder value`.
- No crash on any of these conditions.

---

### GROUP F — Frontend Pages & Wiring

---

#### F-01 · Job Detail Page

**File:** `platform/frontend/src/pages/JobDetailPage.tsx` (new)

**Route:** `/jobs/:jobId`

**What to do:**
Create a full job detail view. Fetch `GET /api/v1/jobs/:id`. Display:
- Job title, company, location, employment type, salary range
- Required skills as skill chips (must-have in red/orange, nice-to-have in gray)
- "Analyze My Gap" button → calls `POST /api/v1/gap-analysis` and shows result inline
- "Add to Profile Target" button → calls `PUT /api/v1/profile` to add job title to `target_roles`
- Back link to Jobs Explorer

**Key component:** Inline gap result section (readiness score ring, matched/missing chips, roadmap milestones timeline) — reuse logic from SkillsPage but as a self-contained component.

**Acceptance criteria:**
- Navigating to `/jobs/some-id` shows the job.
- 404 shows an EmptyState with back link.
- "Analyze My Gap" renders readiness score and roadmap milestones inline.
- "Add to Profile Target" updates the profile and shows a success toast.

**Depends on:** F-08 (toast system), F-09 (reusable GapResult component)

---

#### F-02 · Learning Roadmap Page

**File:** `platform/frontend/src/pages/RoadmapPage.tsx` (new)

**Route:** `/roadmap`

**What to do:**
Dedicated page for viewing the student's learning roadmap. Let the student pick a target job (searchable dropdown, same pattern as SkillsPage), then:
1. Call `POST /api/v1/gap-analysis` with `explain=true`.
2. Display readiness score prominently.
3. Display roadmap as a vertical timeline — each milestone is a card with week number, skill names, and course suggestions.
4. Show LLM summary (if present) as a highlighted block.
5. Show "Add this roadmap as my career goal" button.

**Milestone card layout:**
```
Week 1                    ┌──────────────────────────────┐
────●──────────────────── │ Python Fundamentals           │
                          │ ┌─────────────────────────┐   │
                          │ │ Course: Python Bootcamp  │   │
                          │ │ Provider: Coursera · Free│   │
                          │ └─────────────────────────┘   │
                          └──────────────────────────────┘
```

**Acceptance criteria:**
- Selecting a job and clicking "Build Roadmap" renders all milestones.
- Milestones are in topological order (prerequisites first).
- Each milestone shows attached courses where available (from `/recommendations/courses`).
- Empty state when no job selected.
- Works when LLM is not configured (no summary shown, roadmap still renders).

---

#### F-03 · Market Trends Page

**File:** `platform/frontend/src/pages/MarketPage.tsx` (new)

**Route:** `/market`

**What to do:**
Dedicated market intelligence page. Fetch `GET /api/v1/market/insights`. Display:
- Total jobs ingested (KPI card)
- Top 30 skills as a horizontal bar chart (use CSS bars, no chart library needed)
- Top categories as a donut-style breakdown or pie-style list
- "Skills you're missing from top 10" section — fetch student's skills, diff against top 10 market skills, highlight gaps

**Acceptance criteria:**
- Skills list shows demand_score as a bar (width = demand_score%).
- Category breakdown shows job_count and percentage.
- "Missing from top 10" section is correct (compares user skills vs top 10).
- Page works for unauthenticated users (except the "Missing from top 10" section, which requires auth).

---

#### F-04 · Update App Router

**File:** `platform/frontend/src/App.tsx`

**What to do:**
Add three new routes:
```tsx
<Route path="jobs/:jobId" element={<JobDetailPage />} />
<Route path="roadmap" element={<RoadmapPage />} />
<Route path="market" element={<MarketPage />} />
```
Import the new pages.

**Acceptance criteria:**
- All three routes render correctly.
- `/jobs/nonexistent` renders 404 state, not a crash.
- Unauthenticated users hitting `/roadmap` are redirected to `/login`.

---

#### F-05 · Update AppLayout Navigation

**File:** `platform/frontend/src/components/layout/AppLayout.tsx`

**What to do:**
Add three new nav items to the sidebar:
- "Roadmap" → `/roadmap` (icon: Map or Route from lucide-react)
- "Market" → `/market` (icon: BarChart2)
- "Jobs" already exists — ensure it links correctly

Review sidebar ordering — suggested order: Dashboard → Profile → Jobs → Roadmap → Recommendations → Skills → Market.

**Acceptance criteria:**
- All nav items appear and are highlighted when active.
- Sidebar works on mobile (if it currently does).

---

#### F-06 · Update JobCard to Link to Job Detail

**File:** `platform/frontend/src/components/ui/JobCard.tsx`

**What to do:**
Wrap the JobCard title/company area in a `<Link to={/jobs/${id}}>` using react-router-dom. The card should be clickable (cursor-pointer) with a hover state.

**Acceptance criteria:**
- Clicking a JobCard title navigates to `/jobs/:id`.
- Score badge and skill chips are still visible.
- "Analyze Gap" on JobCard (if present) still works independently.

---

#### F-07 · Extend SkillsPage — Roadmap Section

**File:** `platform/frontend/src/pages/SkillsPage.tsx`

**What to do:**
After gap analysis result renders, show a collapsible "Learning Roadmap" section below the matched/missing skills. This section maps to `gapMutation.data.roadmap.milestones`. Each milestone is a row: `Week N · SkillA, SkillB`. Collapse by default, expand with a "Show Learning Path" button.

**Acceptance criteria:**
- After running gap analysis, "Show Learning Path" button appears.
- Expanding shows milestones in week order.
- If `roadmap.milestones` is empty (no gap), section shows "You're fully ready for this role!".

**Depends on:** B-02 (backend must return roadmap in gap-analysis response)

---

#### F-08 · Toast Notification System

**File:** `platform/frontend/src/components/ui/Toast.tsx` (new) + `platform/frontend/src/contexts/ToastContext.tsx` (new)

**What to do:**
Lightweight toast system — no external library. A `ToastContext` that exposes `toast.success(msg)`, `toast.error(msg)`. Renders a fixed-position stack of toast cards (top-right). Auto-dismisses after 3 seconds.

**Usage in mutations:**
- Add skill success → `toast.success("Skill added")`
- Add skill error → `toast.error(error.message)`
- Profile update success → `toast.success("Profile updated")`
- "Add to target" success → `toast.success("Added to target roles")`

**Acceptance criteria:**
- Toast renders on `toast.success()` call.
- Auto-dismisses after 3s.
- Multiple toasts stack.
- Only CSS + React, no external library.

---

#### F-09 · Reusable GapResult Component

**File:** `platform/frontend/src/components/ui/GapResult.tsx` (new)

**What to do:**
Extract the gap result display from `SkillsPage` into a standalone component. Props:
```ts
interface GapResultProps {
  data: GapAnalysisResult
  showRoadmap?: boolean
}
```
Used by: SkillsPage (already shows it), JobDetailPage (F-01), RoadmapPage (F-02).

**Acceptance criteria:**
- `<GapResult data={...} showRoadmap />` renders score, matched skills, missing skills, and roadmap.
- `showRoadmap={false}` hides the roadmap section.
- Score ring is colored green/amber/red by threshold (≥70/≥40/<40).

---

#### F-10 · Add Courses Tab to RecommendationsPage

**File:** `platform/frontend/src/pages/RecommendationsPage.tsx`

**What to do:**
Add a third tab "Courses" next to "Job Matches" and "Skills to Learn". Fetch `GET /api/v1/recommendations/courses`. Display as a list of course cards:
- Course title, provider
- Skills it teaches (badges)
- Free/paid indicator
- Link (if `url` present)

**Acceptance criteria:**
- "Courses" tab appears and renders.
- Empty state when no courses in graph.
- Course cards show teaches_skills badges.

---

#### F-11 · Skeleton Loading Components

**File:** `platform/frontend/src/components/ui/Skeleton.tsx` (new)

**What to do:**
Replace `<LoadingSpinner />` on key pages with skeleton placeholders that match the page layout. Create skeleton variants: `SkeletonCard`, `SkeletonRow`, `SkeletonText`. Use CSS pulse animation (`animate-pulse` in Tailwind).

Apply to: DashboardPage (stats grid + job list), RecommendationsPage (job list), RoadmapPage (milestones).

**Acceptance criteria:**
- Dashboard skeleton matches the 4-KPI + job-list layout.
- No layout shift when real content loads.
- `LoadingSpinner` remains for small inline uses (mutations).

---

### GROUP I — Infrastructure

---

#### I-01 · Frontend Dockerfile

**File:** `platform/frontend/Dockerfile` (new)

**What to do:**
Multi-stage Dockerfile:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**File:** `platform/frontend/nginx.conf` (new)
Configure nginx to serve the React SPA:
- All routes fall back to `index.html` (for client-side routing).
- `/api` proxied to `http://api:8000`.

**Acceptance criteria:**
- `docker build -f platform/frontend/Dockerfile platform/frontend` succeeds.
- Built container serves the React app on port 80.
- SPA routes (e.g., `/dashboard`) work without nginx 404.

---

#### I-02 · Add Frontend Service to docker-compose

**File:** `docker-compose.yml`

**What to do:**
Add a `frontend` service using the Dockerfile from I-01:
```yaml
frontend:
  build:
    context: ./platform/frontend
    dockerfile: Dockerfile
  container_name: careergraph_frontend
  ports:
    - "80:80"
  depends_on:
    - api
  restart: unless-stopped
```

Update vite.config.ts proxy to use `VITE_API_URL` env var for flexibility.

**Acceptance criteria:**
- `docker compose up` starts all four services (postgres, neo4j, api, frontend).
- Frontend at `http://localhost:80` talks to api at `http://api:8000` via nginx proxy.

---

#### I-03 · Environment Template Files

**Files:** 
- `platform/backend/.env.example` (update)
- `platform/frontend/.env.example` (new)
- Root `.env.example` (new)

**What to do:**
`platform/backend/.env.example`:
```
DATABASE_URL=postgresql+asyncpg://careergraph:careergraph@localhost:5432/careergraph
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=careergraph
JWT_SECRET=change-me-256-bit-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
LLM_PROVIDER=none                   # none | claude | openai | ollama | custom
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
CUSTOM_MODEL_URL=                   # vLLM or TGI endpoint, e.g. http://localhost:8080
CUSTOM_MODEL_NAME=careergraph-v1
FRONTEND_URL=http://localhost:5173
```

`platform/frontend/.env.example`:
```
VITE_API_URL=http://localhost:8000
```

**Acceptance criteria:**
- Each `.env.example` has a comment on every non-obvious variable.
- `CUSTOM_MODEL_URL` is included with a comment pointing to the vLLM/TGI setup section in README.

---

#### I-04 · Backend Health + Readiness Endpoints

**File:** `platform/backend/main.py`

**What to do:**
Extend `GET /api/v1/health` to return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "databases": {
    "postgres": "connected",
    "neo4j": "connected"
  },
  "llm_provider": "claude",
  "jobs_in_graph": 120
}
```
Add a lightweight DB ping in the health check.

**Acceptance criteria:**
- Returns `databases.neo4j: "disconnected"` if Neo4j is unreachable, without crashing.
- Returns `llm_provider: "none"` when no provider configured.
- Useful for docker-compose healthcheck and monitoring.

---

### GROUP M — Model Hosting Roadmap

This group contains stubs and design decisions, not full implementations. Tasks here prepare the architecture for the future fine-tuning phase.

---

#### M-01 · Custom Model Provider (see B-07)

The `CustomModelProvider` from B-07 is the integration point. It speaks the OpenAI-compatible API, which means the following model servers work out of the box once deployed:
- **vLLM** (`pip install vllm`) — fastest, GPU required
- **HuggingFace TGI** (Text Generation Inference) — Docker-native, GPU optional
- **Ollama** — already supported, CPU-friendly

No additional code needed here. Set `CUSTOM_MODEL_URL` to the running server URL.

---

#### M-02 · Training Data Schema Design

**File:** `platform/backend/data/training_schema.md` (new documentation)

**What to do:**
Document the schema for collecting fine-tuning training data from the platform's usage. Each training example is a (prompt, completion) pair.

**Example training pairs:**
```jsonl
{"messages": [
  {"role": "system", "content": "You are a career coach..."},
  {"role": "user", "content": "I have Python and SQL. Target job: Data Scientist. Missing: Spark, ML. Readiness: 55%."},
  {"role": "assistant", "content": "Your Python and SQL foundation is strong. Focus on Spark first (2 weeks), then scikit-learn for ML basics (3 weeks). You're 4–5 weeks from job-ready."}
]}
```

Data collection strategy:
1. When users interact with gap analysis + LLM explanation, log the (gap context, LLM output) pair.
2. Human review / rating step.
3. Export as JSONL for fine-tuning on OpenAI, Anthropic, or open-source base model.

**Note:** Only collect data with user consent. No PII in training pairs — use anonymized skill names, not student names.

---

#### M-03 · Logging for Training Data Collection

**File:** `platform/backend/app/engine/reasoning/training_logger.py` (new stub)

**What to do:**
Create a `TrainingLogger` class with a single method: `log_pair(prompt: dict, completion: str, rating: int | None = None)`. For now, appends JSONL to `data/training_pairs.jsonl`. Future: could log to a database or message queue.

Wire it into `ReasoningAgent.explain_gap()` when the LLM is called and returns a successful response.

**Acceptance criteria:**
- When LLM is configured and explain=True, a JSONL line is appended to `data/training_pairs.jsonl`.
- The JSONL format matches the schema from M-02.
- File is created if it doesn't exist.
- Failure to log does not affect API response.

---

#### M-04 · Model Inference Endpoints (Stub)

**File:** `platform/backend/app/routers/model.py` (new stub)

**What to do:**
Create two admin-only endpoints:

`POST /api/v1/model/infer` — Direct prompt → completion, for testing the hosted model.
```json
Request:  {"system": "...", "user": "..."}
Response: {"completion": "...", "model": "careergraph-v1", "latency_ms": 120}
```

`GET /api/v1/model/status` — Returns health of custom model endpoint.
```json
{"status": "available", "model": "careergraph-v1", "url": "http://..."}
```

Return `{"status": "not_configured"}` when `CUSTOM_MODEL_URL` is not set. No mock needed — this is a live passthrough to whatever is at `CUSTOM_MODEL_URL`.

**Acceptance criteria:**
- Returns 200 with `status: "not_configured"` when no URL set.
- Returns 200 with `status: "available"` when URL is set and server responds.
- Returns 503 when URL is set but server is unreachable.

---

## Implementation Priority Order

Execute in this sequence for fastest path to a demo-ready system:

```
Phase 1 — Core Wiring (1–2 days)
  B-01  LLM Provider Factory
  B-02  Wire gap_analysis router (PathFinder + ReasoningAgent)
  B-04  Prerequisite seeding (data file + endpoint)
  F-04  Update App Router (add new routes)
  F-05  Update AppLayout navigation

Phase 2 — Missing Pages (1–2 days)
  F-09  GapResult reusable component
  F-08  Toast system
  F-01  Job Detail page
  F-02  Roadmap page
  F-07  SkillsPage roadmap section
  F-03  Market page

Phase 3 — Polish (1 day)
  B-03  Wire recommendations LLM narration
  B-05  skills/gap returns roadmap
  B-06  Admin stats endpoint
  F-06  JobCard links to detail
  F-10  Courses tab in Recommendations
  F-11  Skeleton loaders

Phase 4 — Infrastructure (1 day)
  I-01  Frontend Dockerfile + nginx
  I-02  docker-compose frontend service
  I-03  Environment templates
  B-08  Startup data validation
  I-04  Health endpoint enrichment

Phase 5 — Model Layer (ongoing)
  B-07  CustomModelProvider stub
  M-02  Training data schema
  M-03  Training logger
  M-04  Model inference endpoints
```

---

## Agent Execution Notes

When multiple sub-agents pick up tasks:

- **B-01 must run before B-02, B-03, B-07** (all depend on the LLM factory).
- **B-04 must run before B-02** (gap_analysis roadmap is only meaningful with LEADS_TO edges).
- **F-09 must run before F-01 and F-02** (both reuse GapResult component).
- **F-08 can run in parallel with everything** (toast is standalone).
- **F-04 and F-05 can run in parallel** (no shared file edits).
- **All Group M tasks are independent of each other and of Groups B/F/I**.
- All tasks in Group I are independent of each other.

Each agent should:
1. Read the relevant existing files before editing.
2. Run `python3 -m pytest tests/ -q` from `platform/backend/` after any backend change.
3. Run `npm run build` from `platform/frontend/` after any frontend change.
4. Never break the 87 existing passing tests.
