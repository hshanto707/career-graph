# CareerGraph — Current Status & Defense Roadmap

> Date: 2026-08-05. Supersedes `build-status.md` and the "Current state"
> section of `project-roadmap.md` (both dated 2026-07-16 and now stale in
> several places — noted inline below). Companion docs: `system-design.md`
> (architecture spec, still accurate), `gnn-model.md`/`gnn-defense-guide.md`
> (GNN training results), `algorithmic-agents-decisions.md` (documented
> product decisions). This is the honest scoreboard plus the sequenced plan
> to get from here to a defensible, demo-ready system.

## Update — 2026-08-06: Milestone 1 (GNN integration) is done

Everything in this doc's original "Milestone 1" section is now implemented
and tested:

- Retrained the checkpoint against the current data (`ml/export_graph.py` →
  `ml/train_gnn.py` → `ml/evaluate.py`), confirming reproducibility (same
  numbers, noise-level differences, as the 2026-07-18 run).
- Fixed a real performance bug: `GNNRecommendationAgent` was recomputing a
  full encoder forward pass on *every single* `score_requires`/
  `score_leads_to` call — now cached, which is what makes reranking a pool
  of candidates per-request tractable instead of prohibitively slow.
- `RecommendationAgent.rank_jobs` now runs a retrieve-then-rerank pipeline:
  cheap algorithmic scoring over the full 9,380-job catalog, then the top
  50 candidates get rescored with a GNN-derived skill-progression signal,
  blended `0.6*exact + 0.15*partial + 0.25*gnn`. Every job's `match_source`
  (`"gnn"` or `"algorithmic"`) is now in the `GET /recommendations/jobs`
  response and shown as a small badge on the Recommendations page.
- `EngineOrchestrator` now actually constructs and passes a `GNNRecommendationAgent`
  (a process-wide cached singleton — `EngineOrchestrator` is rebuilt per
  request, so this avoids reloading the checkpoint from disk on every API call).
- The backend Docker image now installs torch/torch_geometric/scikit-learn,
  and `docker-compose.yml` mounts `ml/` and `backend/data` into the
  container so the checkpoint actually loads in the running deployment, not
  just in local/test environments.
- New tests: 5 in `test_algorithmic_agents.py` (rerank behavior via a stub
  GNN agent), 3 in `test_routers.py::TestOrchestratorGNNWiring` (orchestrator
  + real HTTP route wiring), 1 in `ml/tests/` (encoder caching). Full
  backend suite: 190/191 passing (same pre-existing unrelated CORS failure).
- Docs updated: `research-contribution.md` now has "Contribution 6",
  `gnn-defense-guide.md` §10 rewritten to describe the actual live
  integration (was previously describing dead code).

**Verified live, end to end, in the actual running container** (not just
tests): registered a real student via `POST /auth/register`, added skills
via `PUT /profile`, hit `GET /recommendations/jobs`, and confirmed
`match_source: "gnn"` on real returned jobs. This surfaced one more real
bug, now fixed: `GNNRecommendationAgent`'s inference path was calling
`export_graph.export()`, which unconditionally writes a `.pt` cache file to
disk — an unwanted side effect for a live inference call, and one that
crashed the whole request with a 500 once `ml/` was mounted read-only in
the container (`RuntimeError: ... Read-only file system`), *silently
violating the agent's own "never raise" graceful-degradation contract*.
Fixed by building the in-memory graph directly (`to_hetero_data(build_synthetic_career_graph())`)
instead of going through the disk-writing wrapper — correct regardless of
mount permissions, since inference never needed the persisted file at all.
First request after a cold start costs ~0.7s (building the graph + one
encoder forward pass, cached in the process-wide singleton after that);
warm requests are ~0.4s.

Milestone 1 is fully closed. Milestones 2–6 below are unchanged and still open.

## TL;DR (original, 2026-08-05 — see update above for what's changed)

The **software is functionally complete and live** — real Postgres + Neo4j
running via `docker compose`, seeded with the full 10k-job synthetic
dataset, every frontend page wired to the real API, 182/183 backend tests
and 80/80 frontend tests passing (the one backend failure is a pre-existing,
unrelated CORS test bug, not a real issue). ~~What's **not** done is the part
that actually makes this a "custom AI model" capstone rather than a CRUD
app: **the trained GNN has never been wired into a live request path.**~~
**(Resolved above.)** It previously trained, evaluated, and sat in
`ml/checkpoints/` unused — `RecommendationAgent`
never called it. The remaining gap that matters most for defense Q&A is a
never-exercised LLM key (Milestone 2, still open). Everything else below is
real but secondary.

---

## What's actually working right now (verified live this session)

- **Auth**: register/login real, JWT issuance/validation confirmed via live
  `curl` round-trips against the running containers, not just mocks.
- **Profile**: skills, major, graduation year, target role, experience —
  all persist and reload correctly.
- **Job Explorer** (`/jobs`): browses the live 9,380-job graph, filters by
  type/location/search, paginates. **Just fixed this session** — see bug #1
  below.
- **Skill Gap Analysis** (`/skills/gap`, Dashboard): readiness score,
  matched/missing skills, roadmap — all confirmed correct end-to-end with a
  real target job and real skills (readiness 18%, 1/7 matched, roadmap
  generated). **Fixed this session** — see bug #2 below; symptom is gone.
- **Recommendations**: jobs/skills/courses all rank and render from live
  data via the pure-algorithmic `RecommendationAgent`/`PathFinderAgent`.
- **Market demand**: `MarketAgent` aggregates real `REQUIRES` edge counts
  across all 9,380 jobs into normalized demand scores.
- **Dashboard**: readiness, matched-skill counts, "Skills You Have" vs.
  "Skills to Acquire" all correct now that ownership is computed from the
  student's actual `HAS_SKILL` edges (not inferred by exclusion).

## Bugs found and fixed this session

1. **Job Explorer showed one company at a time.** `GraphService.list_jobs`
   ordered results `ORDER BY j.id`, and `Job.id = slug(company)::slug(title)`
   — so results sorted alphabetically by *company* first, meaning page 1
   was all "Aegis Loop Technologies", page 2 all "Aequus Health Solutions",
   etc. This is exactly the "aren't working properly" symptom in the
   screenshot. Fixed: now `ORDER BY j.title, j.company, j.id`, and the list
   endpoint also now returns `source`/`salary_min`/`salary_max` (previously
   silently dropped from the list query, though not from `GET /jobs/{id}`).
2. **Target role was stored as free text, not a job id**, and the dashboard
   inferred "skills you have" by exclusion from an (often-empty) missing
   list — together these produced the "readiness 0%, 0/0 matched, phantom
   owned skills" bug reported earlier. Root cause + fix documented in this
   session's earlier turns (`EditProfile.tsx`'s target-role picker now
   selects a real `Job.id`; `orchestrator.get_dashboard` now returns
   `matched_market_skills` computed from real `HAS_SKILL` edges).
3. **`GET /dashboard` 500s on a job with zero required skills** — an
   `OPTIONAL MATCH` + `collect()` Cypher pattern produced a `{name: null}`
   placeholder instead of an empty list, crashing `MarketAgent._normalize_name`.
4. **`GET /jobs/{id}` never returned required skills** — the detail panel
   had nothing to show beyond title/company/location. Added
   `JobDetailOut.required_skills`, populated from `get_job_required_skills`.
5. **CORS preflight 400** — `backend/.env`'s `FRONTEND_URL` didn't match the
   frontend's actual Vite port (8080 vs. a stale 8081). Config, not code.

None of these were agent/engine logic bugs — they were data-shape and
wiring bugs in the FastAPI/Neo4j/React layers. **The base structure is
sound.** This is a genuine green light to move on to the agents/model work.

## Test scoreboard (run fresh this session)

| Suite | Result |
|---|---|
| Backend (pytest) | **182 passed, 1 failed** (pre-existing, unrelated CORS-origin test — see note below) |
| Frontend (vitest) | **80 passed, 0 failed**, 14 test files |
| Frontend typecheck | `tsc --noEmit` clean |

The CORS test failure (`test_cors_preflight_allows_configured_frontend_origin`
in `test_health.py`) asserts against the hardcoded origin `localhost:5173`;
the container's real `FRONTEND_URL` is now `8080` to match the actual
frontend. Either the test should read `settings.FRONTEND_URL` instead of a
hardcoded literal, or the test fixture needs its own override — trivial fix,
listed in Milestone 5.

ML pipeline tests weren't re-run this session (no `ml/.venv` active in this
environment) — last known-good run (2026-07-18): 27 passed.

---

## The real gaps — ranked by what actually matters for the thesis

### 1. ~~GNN is trained but never called~~ — RESOLVED 2026-08-06

`RecommendationAgent.rank_jobs` now runs a retrieve-then-rerank pipeline
that calls `GNNRecommendationAgent` for the top candidate pool, and
`EngineOrchestrator` wires it in via a process-wide cached singleton. See
the "Update — 2026-08-06" section at the top of this doc for the full
breakdown, and `gnn-defense-guide.md` §10 for the defense-facing writeup.
Verified live end to end against the actual running container, including
one real bug the live verification caught and fixed (see "Update —
2026-08-06" above).

### 2. LLM has never been called for real

`LLM_PROVIDER=none` in the live `.env` (no `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`
configured anywhere). Every explanation/narrative/roadmap the app has ever
shown a user is the template fallback, not `ReasoningAgent`. The provider
abstraction and fallback logic are well-tested with **mocks only**. Before
defense, this needs a real key and a manual smoke test capturing real
output for the Implementation/Evaluation chapters — a reviewer asking "show
me a real Claude-generated explanation" currently has nothing to point to.

### 3. Data is still synthetic

`backend/data/kaggle_jobs.csv` (10,000 rows) and `onet_skills.csv` (518
skills) are generated, not the real Kaggle dataset or real O*NET/ESCO
taxonomy. Ingestion/normalization/GNN training are all *proven correct* at
this scale and shape, but the "real-world data" claim in the thesis is not
literally true yet. This is lower priority than #1/#2 — the pipeline
correctness doesn't change if the underlying CSV is swapped later, and it's
plausible this stays synthetic-with-a-documented-limitation for defense
(see Milestone 6).

### 4. `LEADS_TO` (skill-prerequisite) edges are a heuristic, not real data

Synthesized by an alphabetical same-category rule in `ml/graph_build.py` —
fine for pipeline correctness, not a real prerequisite-graph result. The
GNN's `LEADS_TO` AUC-ROC (0.685) is the more GNN-favorable of the two
results in `evaluation_report.json`, but it's evaluated against synthetic
ground truth, which weakens how much weight that result can carry in the
Evaluation chapter without a caveat.

### 5. GNN checkpoint predates the current live graph

`ml/checkpoints/gnn_link_predictor.pt` was trained 2026-07-18. The graph has
been reseeded multiple times since (including this session's `make seed`)
and self-healed a `Skill.name` data bug that didn't exist at training time.
The node-id sets are very likely still consistent (same deterministic CSV →
same ids), but this should be **retrained after any data/ingestion change**,
and definitely as part of Milestone 1 (wiring), so the served model matches
the served graph.

### 6. Smaller, real, lower-priority items

- `mockData.ts` still exists solely because `components/ui/job-card.tsx`
  imports its `Job` type, and `job-card.tsx` itself is dead code (per a
  comment in `Jobs.tsx`) — the Job Explorer builds its own list item instead.
  Delete `job-card.tsx` + `mockData.ts` together, or keep both if
  `JobCard` is still planned for the Recommendations page redesign.
- No rate-limit/lockout policy on repeated failed logins.
- No dedicated React error boundary for unhandled render crashes (only
  per-query toast errors — a crash outside a query, e.g. a render bug,
  currently white-screens).
- `test_cors_preflight_allows_configured_frontend_origin` hardcodes an
  origin that no longer matches the real `.env` — fix the test to read
  `settings.FRONTEND_URL`.
- Root README's docker-compose startup sequence should be re-verified
  end-to-end (it likely still works — `make run` clearly does — but hasn't
  been walked from a completely clean clone this session).

---

## Milestone roadmap to defense-ready

Ordered by priority; each milestone is scoped to be independently
demoable/testable before moving to the next.

### Milestone 1 — Wire the GNN into a live request path

*This is the one that turns "we trained a model" into "the app uses the
model." Highest priority, do this first.*

1. Retrain the GNN against the current live graph (`ml/export_graph.py` →
   `ml/train_gnn.py` → `ml/evaluate.py`), confirm the checkpoint's node-id
   set matches what's in Neo4j today.
2. Decide the blend policy in `RecommendationAgent` (or a thin wrapper
   `EngineOrchestrator` calls): e.g. GNN score as a third signal alongside
   exact/partial match, or GNN-only for candidates the algorithmic path
   scores as weak partial matches (where a learned signal adds the most
   value). `score_requires_with_fallback()` already gives you the
   graceful-degradation contract — use it as designed.
3. Surface the source (`"gnn"` vs `"algorithmic"`) somewhere visible for
   defense purposes — even just a debug/admin field — so you can show a
   live example of the GNN actually influencing a real ranking.
4. Extend `test_gnn_recommendation_agent.py`/add an orchestrator-level
   integration test proving the blended path is exercised, not just the
   standalone agent.
5. Update `research-contribution.md`'s "Contribution 6" section to
   describe the *integrated* system, and `gnn-defense-guide.md` with the
   "why does the algorithmic baseline still win on REQUIRES" narrative —
   you'll be asked this in defense; have the honest answer ready (sparse
   per-skill positive examples relative to graph size, per the existing
   evaluation report, is the current best explanation).

### Milestone 2 — Make the LLM layer real

1. Get a real `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`), set
   `LLM_PROVIDER=claude` in `backend/.env`.
2. Manually smoke-test all four `ReasoningAgent` methods
   (`explain_gap`, `narrate_recommendations`, `write_roadmap`,
   `summarize_market`) against a real profile with real gaps — capture the
   actual output.
3. Confirm the documented no-LLM fallback still works by temporarily
   unsetting the key — this is a testable, defensible resilience claim,
   worth having a screenshot/log of for the defense.
4. Note any prompt-tuning needed once real output is visible (mocked tests
   only assert shape, not quality).

### Milestone 3 — Data & LEADS_TO honesty pass

1. Decide explicitly: real Kaggle/O*NET data, or ship synthetic-with-
   documented-limitation. Given time constraints, the second is defensible
   *if stated clearly* in the Discussion chapter — reviewers respect an
   honest limitation far more than an undisclosed one.
2. If staying synthetic: write the limitation paragraph now (data
   recency/realism, `LEADS_TO` heuristic) so it's ready for the Discussion
   chapter, not improvised during defense.
3. If real data is pursued: re-run ingestion → GNN pipeline end-to-end
   against it, update `evaluation_report.json`, and fold the new numbers
   into `gnn-model.md`.

### Milestone 4 — Polish & cleanup

1. Fix `test_cors_preflight_allows_configured_frontend_origin` to read
   `settings.FRONTEND_URL` instead of a hardcoded origin.
2. Delete `job-card.tsx` + `mockData.ts` (confirm nothing else references
   them first — currently only `Profile.test.tsx` and the guard test do).
3. Add a top-level React error boundary.
4. Basic login rate-limit/lockout (even a simple in-memory or DB-backed
   attempt counter is enough to demonstrate the control exists).
5. Re-verify the root README's docker-compose instructions from a clean
   clone.

### Milestone 5 — Thesis chapters (fed directly by Milestones 1–3)

1. **Implementation chapter** — stack, key engineering decisions
   (including the real bugs found/fixed this session as evidence of a
   rigorously tested system), screenshots of the working, GNN-integrated
   app.
2. **Evaluation chapter** — GNN vs. algorithmic-baseline table (already
   exists in `evaluation_report.json`/`gnn-model.md`), extended with the
   *integrated-system* result from Milestone 1 (e.g., does blending change
   any live recommendation's ranking in a demonstrable way).
3. **Discussion** — limitations: synthetic data, `LEADS_TO` heuristic,
   single-region jobs, GNN underperforming the algorithmic baseline on
   `REQUIRES` at this scale (with the sparse-positive-examples explanation).
4. **Conclusion & Future Work** — reconcile against `system-design.md` §2
   and `research-contribution.md`; real Kaggle/O*NET data and a temporal
   `LEADS_TO` model are natural "future work" items either way.

### Milestone 6 — Defense prep

1. Rehearse a live demo path: register → build profile → Job Explorer →
   Skill Gap Analysis → Recommendations → point out the GNN-influenced
   result from Milestone 1 → point out a real LLM-generated explanation
   from Milestone 2.
2. Prepare answers for the two hardest predictable questions: *"why does
   your trained model underperform a hand-tuned heuristic?"* (sparse
   positives, documented in the evaluation report) and *"is this real
   data?"* (honest synthetic-data limitation from Milestone 3).
3. `demo/thesis-presentation.html` already exists and covers research
   contribution + GNN training/evaluation detail — update it once
   Milestones 1–2 change the "is this integrated" answer from no to yes.

---

## Suggested immediate next step

Start Milestone 1, step 1 (retrain against the current live graph) and step
2 (decide + implement the blend policy in `RecommendationAgent`) — that's
the highest-leverage piece of remaining work and the one every other
GNN-related deliverable (thesis chapters, defense narrative, "Contribution
6") depends on.
