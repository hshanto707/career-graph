# CareerGraph — Current Status & Defense Roadmap

> Date: 2026-08-05. Supersedes `build-status.md` and the "Current state"
> section of `project-roadmap.md` (both dated 2026-07-16 and now stale in
> several places — noted inline below). Companion docs: `system-design.md`
> (architecture spec, still accurate), `gnn-model.md`/`gnn-defense-guide.md`
> (GNN training results), `gnn-training-guide.html` (a single self-contained
> page walking through the whole GNN — data, architecture, training,
> evaluation, and live integration — with code references, for anyone who
> wants the complete picture in one read), `algorithmic-agents-decisions.md`
> (documented product decisions). This is the honest scoreboard plus the
> sequenced plan to get from here to a defensible, demo-ready system.

## Update — 2026-08-11: Target Role Standardization & Skill Cluster Equivalence

- **Standardized Job Roles**: Target roles now use clean, company-agnostic titles with seniority levels (e.g. `Intern Software Engineer`, `Junior Software Engineer`, `Mid Software Engineer`, `Senior Software Engineer`). Seeded in `seed_demo_data.py` with curated core skills.
- **Skill Cluster Equivalence (`SkillGapAgent`)**: Registered standard technology stack clusters (`frontend_framework`, `backend_tech`, `database`, `devops_cloud`, `mobile`, `testing`, `ui_design`). When a job requires a skill in a cluster (e.g., `React`), if the student possesses *any* equivalent skill from that cluster (e.g. `Vue.js` or `Angular`), `SkillGapAgent` grants equivalence match credit. Competing alternative frameworks in that cluster are excluded from missing skills, giving junior candidates a realistic gap analysis.
- **Title Aggregation Filtering & Capping (`GraphService`)**:
  - `get_job_required_skills()` restricts title aggregation to `toLower(j.title) CONTAINS toLower($job_id)` (removing loose reverse containment matching that pulled in all 50 general company job postings).
  - Aggregated required skills for standard target roles are capped to top 10 core skills.
- **Frontend & Tests**: Target role dropdown on `EditProfile.tsx` uses clean title suggestions (`useJobTitleSuggestions`). All 196 backend tests and 85 frontend tests passing cleanly (`196 passed`, `85 passed`).

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

Milestone 1 is fully closed. **Milestone 2 (real LLM key) is deliberately
skipped by decision, not deferred for lack of time** — the LLM is optional
narration only, never scoring/ranking, and the template fallback is
already the app's real, tested, running behavior; see gap #2 below for the
full reasoning. *(Update: Milestones 3, 4, and 5 are also now done as of
later in this same day — see their own sections below for detail. Only
Milestone 6, defense prep, remains open.)*

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

## Test scoreboard (updated 2026-08-06, Milestone 4)

| Suite | Result |
|---|---|
| Backend (pytest) | **195 passed, 0 failed** — fully green |
| Frontend (vitest) | **85 passed, 0 failed**, 15 test files |
| ML (`ml/tests`, torch installed) | **29 passed, 0 failed** |
| Frontend typecheck | `tsc --noEmit` clean |

The formerly-failing CORS test (`test_cors_preflight_allows_configured_frontend_origin`
in `test_health.py`) is fixed — it now reads `settings.FRONTEND_URL`
instead of a hardcoded `localhost:5173` literal, so it's correct regardless
of which origin a given deployment is actually configured for.

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

### 2. ~~LLM has never been called for real~~ — DEFERRED BY DECISION, 2026-08-06 (not a gap)

`LLM_PROVIDER=none` in the live `.env` (no `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`
configured anywhere). Every explanation/narrative/roadmap the app has ever
shown a user is the template fallback, not `ReasoningAgent`. The provider
abstraction and fallback logic are well-tested with **mocks only**.

**Decision: skip Milestone 2 deliberately, not defer it for lack of time.**
The LLM is purely a decoupled, optional narration layer (`research-contribution.md`
Contribution 3) — it never scores, ranks, or predicts anything; it only
rewrites already-computed results (from the algorithmic agents / the GNN)
into sentences. The trained GNN is the actual "custom AI model" and is
fully live (Milestone 1). Running with `LLM_PROVIDER=none` is a real,
tested, intentionally-supported configuration, not a stub — the template
fallback is hand-written, non-empty copy that has been the app's actual
behavior throughout this entire build. Skipping this milestone leaves
nothing functionally incomplete. The only thing forgone is a defense-demo
talking point ("here's a real Claude-generated sentence"), and the
alternative framing — "the system runs LLM-free by design, which is itself
evidence the graceful-degradation architecture is real, not just claimed"
— is arguably the stronger thing to say in a defense. Revisit only if time
remains after Milestones 3–6.

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

### 6. ~~Smaller, real, lower-priority items~~ — ALL RESOLVED 2026-08-06 (Milestone 4)

- ~~`mockData.ts`/`job-card.tsx` dead code~~ — both deleted (only
  `job-card.tsx` imported the former; only a stale comment in `Jobs.tsx`
  referenced the latter, updated to explain the deletion instead).
- ~~No rate-limit/lockout on repeated failed logins~~ — added
  (`backend/app/core/login_lockout.py`, 5 attempts / 5-minute window per
  email, 429 `TOO_MANY_ATTEMPTS`). Explicitly documented as an in-process,
  non-distributed control — a real scope decision for a capstone demo, not
  an oversight; see that module's docstring.
- ~~No React error boundary~~ — added (`components/ErrorBoundary.tsx`,
  wraps the whole app in `App.tsx`).
- ~~`test_cors_preflight_allows_configured_frontend_origin` hardcoded an
  origin~~ — fixed to read `settings.FRONTEND_URL`. **The backend test
  suite is now 195/195 — fully green for the first time**, no more
  pre-existing-failure caveat needed anywhere in this doc.
- ~~Root README not re-verified~~ — actually run from a clean state (see
  below) and found two real, previously-unknown bugs in the process.

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

### Milestone 2 — Make the LLM layer real — SKIPPED BY DECISION (see gap #2 above)

Deliberately not pursued: the LLM is optional narration only, never scoring
or ranking, and the no-LLM template path is already the app's real, tested,
running behavior. Revisit only if time remains after Milestones 3–6 and a
live-LLM demo moment is specifically wanted. If picked back up later, the
original plan was:

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

### Milestone 3 — Data & LEADS_TO honesty pass — DONE 2026-08-06

**Decision: stay synthetic, documented clearly.** Given project timeline,
pursuing real Kaggle/O*NET data was deferred rather than attempted
partially — a fully-documented synthetic dataset is more defensible than a
half-migrated real one. The full Discussion-chapter limitations writeup is
done: see `docs/discussion-limitations.md` (five limitations — synthetic
dataset, `LEADS_TO` heuristic, GNN-vs-baseline result, single-region data,
LLM narration never exercised live — plus a Threats to Validity section
covering internal/external/construct validity and reproducibility). Also
fixed a related honesty gap this milestone surfaced: `system-design.md`'s
scope diagram claimed "Real jobmarket data" as an in-scope item — corrected
with a footnote pointing at the actual (synthetic) status and the new doc.
`docs/data-sources.md` also had a stale `onet_skills.csv` row count (~140,
actually 518) — fixed.

Original plan (kept for reference; superseded by the above):

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

### Milestone 4 — Polish & cleanup — DONE 2026-08-06

All five items done; see gap #6 above for the per-item detail. One item
(#5, README re-verification) surfaced two real, previously-unknown bugs
while actually running the flow from a clean state rather than assuming it
still worked:

1. **The root `docker-compose.yml` had a CORS-breaking default** —
   `FRONTEND_URL` defaulted to `http://localhost:5173`, but that stack's
   frontend is the nginx-served *built* container on port **80**, not a
   Vite dev server — every request from that frontend to the API would
   have failed CORS. Fixed to `http://localhost`. This is the exact same
   class of bug fixed earlier in `backend/docker-compose.yml` (port 8081
   vs. 8080) — evidently a recurring risk with this project's two parallel
   compose files, worth remembering when either changes.
2. **The root compose's `api` service was missing the `ml`/`backend/data`
   mounts** the GNN integration (Milestone 1) added to
   `backend/docker-compose.yml` — the GNN would have silently stayed
   unavailable (no checkpoint found) in that stack. Added the same two
   mounts for parity.
3. The README itself was badly stale: claimed an `/api/v1/` path prefix
   that has never existed, the wrong frontend port (5173 instead of 8080),
   `postgresql+asyncpg` instead of the actual `psycopg2`, a manual
   `alembic upgrade head` step that's now automatic in the
   `backend/docker-compose.yml` path, "87 tests" (now 195+85+29), and an
   orphaned, content-less thesis-chapter-outline fragment tacked onto the
   end that looked like an accidental paste, not intended README content
   (removed — flagged in case it was actually wanted somewhere else).
   Rewritten to document both the actual dev workflow
   (`backend/docker-compose.yml` + `make seed` + `npm run dev`) and the
   one-shot full-containerized alternative (root `docker-compose.yml`),
   with an explicit note that the two aren't meant to run simultaneously
   (same host ports). Verified both flows live: stopped the dev stack,
   brought the root stack up from nothing, ran the missing `alembic
   upgrade head`, confirmed register/login/CORS/the containerized frontend/
   the GNN all work, tore it down, and restored the original dev stack
   with its data intact (verified: 9,380 jobs still present, 195/195
   backend tests still passing afterward).

Original plan (kept for reference; superseded by the above):

1. Fix `test_cors_preflight_allows_configured_frontend_origin` to read
   `settings.FRONTEND_URL` instead of a hardcoded origin.
2. Delete `job-card.tsx` + `mockData.ts` (confirm nothing else references
   them first — currently only `Profile.test.tsx` and the guard test do).
3. Add a top-level React error boundary.
4. Basic login rate-limit/lockout (even a simple in-memory or DB-backed
   attempt counter is enough to demonstrate the control exists).
5. Re-verify the root README's docker-compose instructions from a clean
   clone.

### Milestone 5 — Thesis chapters — WRITTEN 2026-08-06, one manual step remains

All four chapters are drafted, grounded in this project's actual repo
content (real test counts, real evaluation numbers, real bugs found/fixed
during hardening — nothing fabricated for the occasion):

1. **`docs/implementation-chapter.md`** — stack, key engineering decisions
   (the retrieve-then-rerank GNN integration, the graceful-degradation
   pattern applied twice, the synthetic-data decision), and a dedicated
   section on the four real bugs found/fixed during hardening as concrete
   evidence of how the system was actually verified.
2. **`docs/evaluation-chapter.md`** — the GNN-vs-baseline table, plus two
   things the original plan didn't fully anticipate needing: a section
   proving the GNN is actually *used* live (not just evaluated offline —
   this was a real, closed gap, not always true during the build), and a
   section on what a green test suite does and doesn't prove, using the
   read-only-filesystem bug as the concrete example.
3. **`docs/discussion-limitations.md`** — now the full Discussion chapter:
   a new "Synthesis of findings" section up front (three separate verdicts:
   is the software correct, does the model add value, is this a fair test
   of the approach), followed by the limitations/threats-to-validity
   content from Milestone 3.
4. **`docs/conclusion-future-work.md`** — reconciles against
   `system-design.md` §2 and all six `research-contribution.md`
   contributions (delivered-as-verified, not just designed), plus a
   12-item Future Work list ordered from "directly closes a stated
   limitation" through `system-design.md`'s existing Post-Capstone Scope
   to infrastructure items this project's own hardening phase surfaced.

**One manual step remains, flagged rather than skipped:** the
Implementation chapter has a placeholder screenshots section — actual
screenshots of the running app need to be captured and inserted before
submission (no browser/screenshot tool was available to do this
automatically). Everything the screenshots would show has been verified
working live (see `docs/evaluation-chapter.md` §4), so this is a capture
task, not an open functional question.

### Milestone 6 — Defense prep

1. Rehearse a live demo path: register → build profile → Job Explorer →
   Skill Gap Analysis → Recommendations → point out the GNN-influenced
   result (`match_source: "gnn"`) from Milestone 1.
2. Prepare answers for the three hardest predictable questions: *"why does
   your trained model underperform a hand-tuned heuristic?"* (sparse
   positives, documented in the evaluation report), *"is this real
   data?"* (honest synthetic-data limitation from Milestone 3), and *"why
   isn't the LLM turned on?"* (deliberate design choice, not a gap — see
   gap #2 above; the graceful-degradation architecture being genuinely
   exercised, not just claimed, is itself the answer).
3. `demo/thesis-presentation.html` already exists and covers research
   contribution + GNN training/evaluation detail — update it once
   Milestone 1's live-integration story is ready to present (already true).

---

## Suggested immediate next step

Milestones 1, 3, 4, and 5 are done; Milestone 2 is deliberately skipped
(see above). All four thesis chapters are written
(`docs/implementation-chapter.md`, `docs/evaluation-chapter.md`,
`docs/discussion-limitations.md`, `docs/conclusion-future-work.md`).
**Milestone 6 (defense prep)** is next: rehearse the live demo path,
prepare the three hardest predictable Q&A answers, capture real
screenshots for the Implementation chapter's placeholder section, and fill
in `capstone-proposal.md`'s still-blank `[Your Name]`/`[Supervisor Name]`
fields (noticed while cross-referencing chapters for this milestone —
outside this doc's scope to fill in, but worth flagging before submission).
