# Algorithmic Agents (B5) — Concrete Decisions

Companion to `system-design.md` §9.3 and `features-todo.md` B5. This
document resolves the open decisions flagged for this module with concrete,
implemented, tested rules. Source of truth for the "why" behind each
formula lives in the module docstrings in
`backend/app/engine/algorithmic/*.py`; this file is the human-readable
index.

## Open decision #6 — "must vs. nice" skill classification rule

**Where it's decided:** at ingestion time (B4 `NormalizationAgent` /
Neo4j write stage), not inside the algorithmic agents. By the time
`SkillGapAgent` runs, every `REQUIRES` edge already carries an explicit
`importance: "must" | "nice"` property — the agent is a pure consumer of
that label, never a re-deriver of it.

**The rule (to be applied by ingestion):**
1. A skill is `must` if it appears within the **first 60%** of the
   `skills_required` list for that job posting (position in the listing is
   treated as a proxy for the poster's stated priority — skills are almost
   always listed most-important-first in real postings), **or**
2. its `frequency` (how often it appears across postings for the same job
   title in the corpus) exceeds a configured threshold, signalling it's a
   baseline expectation for the role regardless of where any one posting
   happens to list it.
3. Otherwise: `nice`.

**Defensive default in `SkillGapAgent`:** if a required-skill dict is
missing the `importance` field entirely (malformed upstream data slipping
through), it is treated as `nice`, never `must` — this is a conservative
default so unclassified data can't silently inflate the higher-weighted
bucket. Covered by `test_defensive_default_missing_importance_treated_as_nice`.

## Open decision #7 — Skill Cluster Equivalence & Category Equivalence Matching

**Where it's decided:** inside `SkillGapAgent` (`backend/app/engine/algorithmic/skill_gap_agent.py`) and `GraphService` (`backend/app/services/graph_service.py`).

**The Problem:** Entry-level candidates for roles like *"Intern Software Engineer"* or *"Junior Software Engineer"* should not be penalized for not mastering every competing framework or language (e.g. needing React AND Angular AND Vue AND Svelte for frontend; or Node.js AND Python AND Go AND Spring for backend). Dumping dozens of competing framework requirements onto a junior candidate distorts the readiness score and missing skills analysis.

**The Rule & Implemented Architecture:**
1. **Skill Cluster Equivalence (`SkillGapAgent`)**: Common technology stack clusters (`frontend_framework`, `backend_tech`, `database`, `devops_cloud`, `mobile`, `testing`, `ui_design`) are registered in `SKILL_CLUSTERS`. When a job requires a skill in a cluster (e.g., `React`), if the candidate possesses *any* equivalent skill from that cluster (e.g. `Vue.js` or `Angular`), `SkillGapAgent` grants **equivalence match credit**. The requirement is marked satisfied (e.g., `"React (satisfied by Vue.js)"`) and competing alternative frameworks in that cluster are excluded from `missing_skills`.
2. **Title Aggregation Filtering & Skill Capping (`GraphService`)**:
   - `get_job_required_skills()` restricts title aggregation to `toLower(j.title) CONTAINS toLower($job_id)` (avoiding loose reverse containment matching that pulled in all generic 50 company postings).
   - Aggregated required skills for standard target roles are capped to a clean, realistic set (top 10 core skills) so junior candidates receive a focused skill gap analysis.

## SkillGapAgent — readiness_score arithmetic

```
readiness_score = (must_matched / must_total) * 0.7
                 + (nice_matched / nice_total) * 0.3    ... as a 0-100 base
                 + proficiency_bonus                     ... small additive bonus
```

- Each ratio term is zero-division safe: an empty must/nice bucket
  contributes `0` for that term instead of raising.
- `proficiency_bonus`: for every *matched* required skill, contributes
  `(proficiency / 10) * 2.0` points, summed and divided by
  `must_total + nice_total`, so two students with identical skill sets are
  still strictly ordered by how well they know those skills — without
  proficiency alone being able to dominate the 0.7/0.3 weighting. The final
  score is capped at 100.
- Duplicate skill names (student side and required side) are deduped
  case-insensitively before any ratio is computed — the student side keeps
  the *highest* proficiency seen for a repeated name; the required side
  keeps the first occurrence.

## RecommendationAgent — Jaccard + partial credit

```
exact_score   = |student ∩ job| / |student ∪ job|                (Jaccard)
partial_score = per-skill LEADS_TO credit, depth-capped at 2, / |job_skills|
final_score   = exact_score * 0.8 + partial_score * 0.2
```

- Partial credit is **asymmetric by depth**: a direct (depth-1) `LEADS_TO`
  edge from a known skill contributes full credit (`1.0`); a depth-2 path
  (one intermediate skill) contributes half credit (`0.5`). This keeps a
  depth-1 path strictly more valuable than an equivalent depth-2-only path,
  as required by the test plan.
- Only required skills **not already an exact match** receive partial
  credit — no double-counting.
- Ranking ties (identical `final_score`) are broken deterministically by
  ascending `job_id` so output ordering is reproducible.

## PathFinderAgent — BFS + topological sort, cycle handling

- `LEADS_TO` points prerequisite → advanced skill. The agent walks the
  graph **backward** from each missing skill (advanced → prerequisite) to
  discover the full ancestor set, then performs a forward topological sort
  (Kahn's algorithm) over the induced subgraph to produce a
  prerequisite-first ordered path.
- **Cycle handling:** if Kahn's algorithm ever finds no zero-in-degree node
  remaining (i.e. it's stuck inside a cycle), it deterministically
  force-selects the lexicographically smallest remaining skill name,
  emits it, and continues. This guarantees termination (the candidate set
  strictly shrinks every step) and a fully defined, reproducible output —
  chosen over raising, since a malformed cyclic graph shouldn't take down
  the whole gap-analysis request.
- `weeks_estimate` (v1 proxy, no historical learning-time data exists yet):
  `BASE_WEEKS (2) + max(difficulty_jump of any LEADS_TO edge landing on
  this skill from an already-included prerequisite)`. A skill with no
  known prerequisite edge just gets `BASE_WEEKS`.

## MarketAgent — demand aggregation + trend (open decision #5)

- `demand_score(skill) = (skill's REQUIRES count / max REQUIRES count in
  the dataset) * 100` — normalized against the corpus max so the score is
  meaningful at any dataset size (50-job seed vs. 10k-job Kaggle corpus).
- **Trend, v1:** no time-series/snapshot storage exists yet in the Neo4j
  schema. Decision: `MarketAgent.aggregate_demand()` accepts an *optional*
  `previous_demand_counts` snapshot; if supplied, `trend = current -
  previous` per skill and `trending_skills` are those with positive trend,
  sorted descending. If **not** supplied (the common v1 case — only one
  ingestion run exists), `trend` is explicitly `None` (not a fabricated
  `0`) and `trending_skills` is empty — "unknown" is preserved as distinct
  from "no growth". Once multiple ingestion snapshots exist, this can
  switch to a genuine recency-weighted calculation without changing the
  method's public contract.

## Cross-cutting defensiveness (all four agents)

- Empty graph / zero jobs / zero skills → every agent returns an
  empty/zero-value result, never raises or divides by zero.
- Duplicate skill entries (within a job's required list, within a
  student's skill list, within a missing-skills list) are deduped
  case-insensitively before any scoring math runs.
- All agents are pure functions of plain `list`/`dict` input — no Neo4j
  driver, no HTTP, no filesystem access — so they are fully unit-testable
  in isolation, per `backend/tests/test_algorithmic_agents.py`.

---

# B6/B7 — Engine Orchestrator, Fallback Narratives, and Router Contracts

Added in the phase that built `app/engine/orchestrator.py` and the
student-facing routers (`app/routers/{profile,jobs,skills,recommendations,
gap_analysis,market,dashboard}.py`). Resolves the remaining open decision
flagged in `features-todo.md`.

## Open decision #2 — `GET /skills/gap` vs. `POST /gap-analysis`

Both routes compute a skill gap for a student against a job, and
`system-design.md` §8/§11.3 documented them slightly inconsistently (one a
GET with no params, the other a POST with `target_job_id`). Resolution,
now implemented in `app/routers/skills.py` and `app/routers/gap_analysis.py`:

- **`POST /gap-analysis`** is the explicit entry point: the caller supplies
  `target_job_id` in the body (used from Job Explorer / Recommendations,
  where the student picked a specific job). An unknown `target_job_id` is a
  client error → `404 NOT_FOUND`.
- **`GET /skills/gap`** is the implicit, "just show me where I stand right
  now" entry point (used on first load of the Skill Analysis page, before
  any specific job has been picked):
  - It accepts an *optional* `?target_job_id=` query override, validated
    exactly like `POST /gap-analysis` (404 if the id doesn't exist) — for
    callers that already know which job they mean but prefer a GET.
  - Without the override, it resolves the target job automatically via
    `app/routers/_shared.py:resolve_target_job_id()` — the student's
    Postgres `student_profiles.target_roles` list, **last entry wins**
    (append-ordered = most-recently-added = "current" target role). This
    resolution is intentionally *not* validated against the graph (a
    profile can reference a `target_roles` job id that hasn't been synced
    into Neo4j yet, or ever) — `GraphService.get_job_required_skills()` on
    an unknown id simply returns `[]`, which flows into a well-defined
    (if unhelpful) zero-ish gap result rather than a crash. This keeps
    `GET /skills/gap` safe to call unconditionally from the moment a
    student logs in.
  - If the student has **no** target roles set at all (and no query
    override), the route returns a defined empty state — `readiness_score:
    0`, empty `matched_skills`/`missing_skills`/`roadmap`, plus an
    `explanation`/`encouragement` pair telling the student to set a target
    role — with `200`, never a `404`/`500`.
- **The contract-unifying guarantee:** both routes, once a `target_job_id`
  is known, call the exact same `EngineOrchestrator.compute_gap_analysis()`
  method. There is only one code path that computes a readiness score for a
  (student, job) pair — the two routes are just two different ways of
  arriving at the `target_job_id` argument. This is what test-plan.md B7#7
  ("both produce internally consistent readiness scores for the same
  student+job") and B7#10 (dashboard cross-consistency, below) actually
  test against.

## `GET /dashboard` ↔ `GET /skills/gap` ↔ `GET /skills/market` consistency

`GET /dashboard`'s router resolves `target_job_id` with the *same*
`resolve_target_job_id()` helper `GET /skills/gap` uses (both live in
`app/routers/_shared.py`), then calls
`EngineOrchestrator._compute_gap_result()` — the same `SkillGapAgent.compute_gap()`
call that `compute_gap_analysis()` (used by both gap routes) wraps with a
narrative. `job_readiness_score`/`skills_matched`/`total_required_skills` on
the dashboard are therefore numerically identical to `GET /skills/gap`'s
`readiness_score`/matched-missing counts for the same student, by
construction rather than by coincidence. Similarly, `market_demand` on the
dashboard and `GET /skills/market`'s response are both thin wrappers over
`EngineOrchestrator.get_skill_demand()` — same `MarketAgent.aggregate_demand()`
call, so the two are always in lockstep.

`GET /dashboard` deliberately never calls the `ReasoningAgent` at all (see
`system-design.md` §9.1: "dashboard is largely algorithmic") — this means a
missing/misconfigured/failing LLM provider can *never* affect the dashboard
route, by construction, not just by a try/except.

## `EngineOrchestrator` LLM-fallback contract (B6, wired into B7)

Every route that could show an LLM narrative (`gap-analysis`/`skills/gap`'s
`explanation`/`encouragement`/roadmap, `recommendations/jobs`'s
`why_recommended`, `market/insights`'s `trend_bullets`/`summary`) follows the
identical shape in `EngineOrchestrator`:

1. `_reasoning_agent()` returns a `ReasoningAgent` only if `Settings.LLM_PROVIDER`
   is a recognized, non-`"none"` value *and* the concrete provider
   constructs without error (e.g. a missing API key raises inside
   `create_llm_provider`, which is caught and treated identically to "no
   LLM configured"). Any other outcome returns `None`.
2. If a `ReasoningAgent` is available, the relevant narrative method
   (`explain_gap`/`write_roadmap`/`narrate_recommendations`/`summarize_market`)
   is called inside a broad `try/except Exception` — deliberately broad,
   not narrowed to `LLMProviderError`, because the orchestrator's job here
   is "never let this subsystem's failure reach the caller as a 500",
   not "handle only the failure modes we've already enumerated".
3. On any exception, or when no `ReasoningAgent` is available at all, the
   orchestrator falls back to a **written-out, non-empty template
   narrative** (e.g. `"Based on your skills, you match {pct}% of required
   skills for this role. You currently have {n} of {total} required
   skills..."`) — never `None`, never an empty string. The frontend
   contract is unconditionally satisfiable regardless of LLM
   configuration/availability.

This is exercised directly (no HTTP, no mocked network) in
`backend/tests/test_routers.py`'s `TestOrchestratorLLMFallback` class,
which covers test-plan.md B6 #4 (`LLM_PROVIDER` unset → template narrative
present and non-empty) and #5 (configured provider raises after exhausting
retries → same template fallback, no exception propagates).

---

## Open decision #3 — Job Explorer: personalized match scores or pure catalog?

**Decision: pure catalog. The Job Explorer (`frontend/src/pages/Jobs.tsx`)
never shows a personalized match score, "why recommended" text, or a
per-job skill-gap breakdown.** Personalized scoring/narrative is exclusive
to the Recommendations page (`GET /recommendations/jobs`).

**Why:**
1. `GET /jobs` returns `JobOut`
   (`backend/app/schemas/job.py`: `id/title/company/location/type/source/
   salary_min/salary_max`) — there is no student-skill-overlap data in this
   response at all, by design (`system-design.md` §8 documents `/jobs` as
   the plain catalog/filter route, separate from `/recommendations/jobs`
   which is where `RecommendationAgent` + `ReasoningAgent.narrate_recommendations()`
   actually run).
2. Making the catalog page personalized would mean calling
   `RecommendationAgent`/the LLM-backed narrator for every row of a
   browse-and-filter list (including every page of "Load more" and every
   keystroke of a debounced search) — that is a materially different,
   heavier request shape than a catalog page needs, and duplicates work
   the Recommendations page already does deliberately once.
3. It keeps the mental model clean for the thesis narrative: **`/jobs` is
   "what's out there"; `/recommendations/jobs` is "what's out there, for
   you."** Conflating them (as the original mock data did, by baking
   `matchPercentage`/`whyRecommended` onto every `Job` regardless of which
   page rendered it) was itself the bug the mock UI shipped with.

**Consequence for `components/ui/job-card.tsx`:** that component's props
are still the mock `Job` shape (`matchPercentage`/`requiredSkills`/
`whyRecommended` required, non-optional fields), which fits the
Recommendations page's genuinely personalized cards. The Job Explorer does
**not** force-fit `JobOut` into that shape (no fabricated `matchPercentage`,
no empty-array `requiredSkills` masquerading as real data) — it renders its
own catalog-only list item using only fields `JobOut` actually has. This is
a known, intentional divergence from the two pages sharing one card
component; unifying them is flagged as follow-up work for whichever phase
wires the Recommendations page to its real endpoints, at which point
`JobCard`'s props can be reconsidered (e.g. an optional
`matchPercentage`/`whyRecommended` so a single component serves both a
catalog and a personalized rendering), rather than solved by improvising a
new coupling from the Jobs-page side alone.

Covered by `frontend/src/pages/Jobs.test.tsx`'s "does not show a
personalized match score anywhere on the catalog page" test, and by
`frontend/src/hooks/useJobs.ts`'s docstring, per test-plan.md F5.
