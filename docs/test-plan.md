# CareerGraph — Red/Green Test Plan & Edge Cases

> Companion to `features-todo.md`. For every feature listed there, this document defines the test(s) to write **first** (red — fails because the feature doesn't exist yet), the condition that makes them **green** (passes once the feature is correctly implemented), and the edge cases each test suite must cover. This is the acceptance bar: **the module is not "done" until every test below is green and every edge case is covered**, not just the happy path.

Format per feature:
- **Red/Green tests** — plain-English test cases, written TDD-style (test exists and fails before the code exists; passes once the code is correct).
- **Edge cases** — boundary/failure conditions the happy-path tests won't catch.

No code or test files are written yet — this is the test specification to implement alongside each module.

---

## BACKEND

### B1. Backend Scaffold & Infra

**Red/Green tests**
1. `GET /health` — Red: route doesn't exist, 404. Green: returns 200 with `{success: true, data: {postgres: "ok", neo4j: "ok"}}` when both DBs are reachable.
2. CORS preflight from `FRONTEND_URL` — Red: no CORS middleware, browser blocks the request (or test client sees missing `Access-Control-Allow-Origin`). Green: `OPTIONS` request from the configured origin gets the correct CORS headers; a request from an unlisted origin does not.
3. Unhandled exception in a route — Red: raises raw traceback / default FastAPI 500 HTML. Green: global exception handler returns the JSON envelope `{success: false, error, message}` with an appropriate status code.
4. Config loads from `.env` — Red: `Settings()` throws or falls back silently to wrong defaults when a required var is missing. Green: missing required env var fails fast at startup with a clear error; all required vars present → `Settings()` populates correctly.

**Edge cases**
- `GET /health` when Postgres is up but Neo4j is down (and vice versa) — must report per-service status, not a single boolean, and use 200 with partial failure detail (or 503 — decide and test consistently).
- A validation error (e.g., malformed JSON body) must still return the standard envelope, not FastAPI's default 422 shape, unless the team decides to keep FastAPI's default 422 and document that exception — this must be a **decided, tested** behavior either way.
- CORS with credentials (cookies) vs. bearer-token-only — confirm we don't need `allow_credentials=True` since auth is header-based, not cookie-based.

---

### B2. Data Layer (PostgreSQL + Neo4j + GraphService)

**Red/Green tests**
1. `User` uniqueness on email — Red: model/constraint doesn't exist, duplicate insert silently succeeds. Green: second insert with same email raises an integrity error the API layer converts to a 409/400.
2. `StudentProfile` one-to-one with `User` — Red: FK/relationship not defined. Green: creating two profiles for the same `user_id` is rejected (unique constraint on `user_id`).
3. Alembic migration round-trip — Red: no migration exists. Green: `alembic upgrade head` then `alembic downgrade base` both succeed cleanly on a fresh DB.
4. Neo4j uniqueness constraint on `Skill.normalized_name` — Red: constraint not created, two `MERGE`-independent inserts create duplicate skill nodes with the same normalized name. Green: constraint exists; duplicate `normalized_name` MERGEs to the same node.
5. `GraphService.get_student_skills(student_id)` — Red: method doesn't exist. Green: returns the correct skill list (name, proficiency, years) for a seeded student, empty list for a student with no `HAS_SKILL` edges.
6. `GraphService` uses parameterized Cypher — Red/Green isn't a runtime assertion so much as a code-review gate, but add a test that a skill name containing Cypher-special characters (e.g. `"Skill' MATCH (n) DETACH DELETE n //"`) round-trips as literal data and does **not** execute as Cypher (Cypher-injection regression test).

**Edge cases**
- Postgres transaction rollback: profile update fails mid-way (e.g., Neo4j write succeeds but Postgres commit fails, or vice versa) — define and test the actual consistency guarantee (full rollback vs. eventual consistency with a retry/reconciliation job); do not leave this undefined.
- `get_student_skills` for a student that doesn't exist in Neo4j at all (registered in Postgres but never synced) — should return empty, not throw.
- Concurrent registration with the same email (race condition) — both requests hit the uniqueness check near-simultaneously; only one should succeed.
- Neo4j constraint creation running twice (idempotent bootstrap) — must not error on second run.

---

### B3. Auth Module

**Red/Green tests**
1. Register with new email — Red: route missing. Green: 201, user + empty profile created, password stored hashed (never plaintext — assert the stored value is not equal to the submitted password and looks like a bcrypt hash).
2. Register with existing email — Red: not handled. Green: 409/400 with clear error, no duplicate row created.
3. Login with correct credentials — Red: no login route. Green: 200, returns `{token, user}`; token decodes to the correct `user_id`/`email` and expires ~24h from issuance.
4. Login with wrong password — Green: 401, no token returned, and importantly the response does not leak whether the email exists (generic "invalid credentials" message for both "no such user" and "wrong password").
5. Access a protected route with no `Authorization` header — Green: 401.
6. Access a protected route with an expired token — Green: 401 (requires a test that mints a token with a past expiry or freezes time).
7. Access a protected route with a token signed with the wrong secret — Green: 401 (tamper/forgery test).
8. `current_user` injection never trusts client-supplied `student_id` — Green: a request that includes a `student_id` field in the body/query different from the token's subject is ignored/rejected; the route always acts on the token's `user_id`.

**Edge cases**
- Empty-string or whitespace-only password/email on register.
- Extremely long email/password inputs (define and enforce max length, avoid unbounded bcrypt input).
- Case sensitivity of email at login (`User@Example.com` vs `user@example.com`) — decide normalization and test it.
- Password containing special/unicode characters — bcrypt hash/verify round-trips correctly.
- Replay of an old, previously-valid-but-now-expired token immediately after expiry boundary (off-by-one on the expiry check).
- Registering, then logging in before any profile fields are set — should not 500 on an "empty" profile.

---

### B4. Ingestion Pipeline (IngestionAgent + NormalizationAgent)

**Red/Green tests**
1. Valid CSV row → parsed record — Red: parser doesn't exist. Green: a well-formed row produces a record with correctly split `skills_required` list and validated `salary`/`location`/`job_type`.
2. Malformed row (missing title) → dropped, not crashed — Green: pipeline continues, dropped-row count increments, no exception propagates.
3. Exact synonym match (`ReactJS` → `React`) — Green: normalized name equals the canonical mapped name exactly.
4. Fuzzy match at/above threshold (score ≥ 90) — Green: unmapped-but-close skill name (e.g., a minor typo of an O*NET term) resolves to the canonical O*NET name.
5. Fuzzy match below threshold — Green: skill keeps its raw name and is flagged for manual review (assert the flag is actually recorded, not just "not normalized").
6. Neo4j MERGE idempotency — Red: re-running ingestion on the same CSV creates duplicate Job/Skill nodes. Green: running the pipeline twice on identical input results in the same node/edge counts as running it once.
7. `POST /admin/ingest/csv` end-to-end — Green: uploading a small fixture CSV returns stats matching what direct pipeline unit tests predict (rows read, dropped, skills flagged).
8. `GET /admin/ingest/status` — Green: reflects the most recent run's stats after a completed ingestion, and a sensible "no runs yet" state before any ingestion.

**Edge cases**
- CSV with a `skills_required` field containing a trailing/leading comma, extra whitespace, or empty entries (`"Python, , SQL"`).
- Duplicate skills within a single job posting (`"Python, Python, SQL"`) — should dedupe, not create duplicate `REQUIRES` edges.
- Skill name matching two different O*NET entries with a tied fuzzy score — define and test a deterministic tie-breaker (not "whatever the library returns first").
- Empty CSV file / CSV with only a header row.
- CSV with a BOM, different encoding, or Windows line endings — parser shouldn't choke.
- Extremely large `skills_required` list on one row (e.g., 50 skills) — performance/correctness sanity check, not just 2-3 skills.
- Ingestion admin endpoint called without admin credentials — must be rejected (401/403), tested explicitly since this is a common capstone-grade oversight.
- Re-ingesting after `synonyms.json` has been updated (a previously-flagged skill now has a mapping) — should re-resolve on next run, not stay stuck with the old flag forever (decide if this requires a re-normalization pass and test that decision).

---

### B5. Algorithmic Agents

**Red/Green tests — SkillGapAgent**
1. Full match — student has all must + nice skills → `readiness_score == 100` (or the defined max, plus proficiency bonus capped correctly).
2. Zero match — student has none of the required skills → low/zero score, `missing_skills` equals full required list.
3. Must-only weighting — student matches all "must" skills but none "nice" → score reflects the 0.7 weight exactly (assert the arithmetic, not just "score went up").
4. Proficiency bonus — two students with identical skill sets but different proficiency levels → the higher-proficiency student scores strictly higher.

**Red/Green tests — RecommendationAgent**
5. Identical skill sets (student == job requirements) → Jaccard exact_score == 1.0.
6. Disjoint skill sets, no `LEADS_TO` path within depth 2 → final_score == 0.
7. Disjoint exact match but a depth-1 `LEADS_TO` path exists (e.g., Python → ML) → partial_score contributes a nonzero, correctly-weighted amount to final_score.
8. Ranking order — given 3+ jobs with known expected scores, the returned list is sorted strictly descending by final_score.

**Red/Green tests — PathFinderAgent**
9. Simple linear prerequisite chain (A→B→C, missing C) → BFS + topological sort returns `[A, B, C]` in that order.
10. Missing skill with no prerequisites → path is just that single skill, no crash.
11. `LEADS_TO` graph containing a cycle → algorithm terminates (does not infinite-loop) and produces a defined, tested result (e.g., breaks the cycle deterministically or raises a handled error — decide and test the decision).
12. Courses attached — each milestone in the path that has a `TEACHES` course linked shows it; a skill with no course shows an empty/handled state, not a crash.

**Red/Green tests — MarketAgent**
13. Demand aggregation — a skill appearing in N job postings' `REQUIRES` edges has a `demand_score` proportional to N relative to the max in the dataset (0–100 normalized correctly, not just "some number").
14. Trending skills — given two ingestion snapshots (or the agreed v1 proxy), the trend calculation matches the documented formula exactly.

**Edge cases (all algorithmic agents)**
- Zero jobs / zero skills in the graph at all (empty database) — every agent must return an empty/zero-value result, not throw.
- A job with zero required skills (bad data slipped through ingestion) — Jaccard/gap math must not divide by zero.
- A student with zero skills — gap score is 0/well-defined, not NaN.
- Very large skill sets (stress case) — confirm no accidental O(n²) blowup that would matter at 10k-jobs scale (at least a rough perf sanity test, not full load testing).
- Duplicate skill entries in the input arrays (already deduped upstream, but agents should be defensive here too) — test they don't double-count.

---

### B6. LLM Provider Abstraction + Reasoning Agent + Orchestrator

**Red/Green tests**
1. `LLMProvider.complete()` contract — for each of Claude/OpenAI/Ollama, a mocked underlying SDK call returns valid JSON matching the given Pydantic schema → provider returns a correctly parsed/validated model instance (not raw dict/text).
2. Malformed LLM JSON response — Green: provider retries up to the configured `retries` count, and if all retries fail, raises a specific, catchable exception type (not a generic crash) that the orchestrator knows how to handle.
3. `ReasoningAgent.explain_gap()` — given a fixed `GapResult` fixture, mocked LLM returns a fixed schema-valid response → method returns that response unmodified (i.e., the agent adds no unvalidated business logic on top of the LLM output, per the "no business logic inside LLM, but also no logic *outside* corrupting it" design intent — actually test that the agent passes structured input in and structured output out faithfully).
4. Orchestrator with `LLM_PROVIDER` unset — Green: returns the algorithmic result wrapped in the defined **template narrative strings** (not `None`, not empty string) — assert the exact fallback text is present and non-empty.
5. Orchestrator with `LLM_PROVIDER` set but the provider raises after exhausting retries — Green: orchestrator catches it and falls back to the same template-narrative path as #4, request still returns 200 with algorithmic data (never a 500 just because the LLM is down).
6. Provider switch via env var — Green: setting `LLM_PROVIDER=ollama` vs `=claude` routes through the correct provider class without any other code change (a construction/factory test, not a live API call).

**Edge cases**
- LLM response schema-valid but semantically nonsensical (e.g., negative `estimated_learning_weeks`) — decide whether Pydantic field validators catch this (e.g., `ge=0`) and test that they do.
- Timeout mid-request — provider must respect the configured `timeout` and fail into the same retry/fallback path as a malformed response, not hang indefinitely (test with a mocked slow call).
- Concurrent requests hitting the LLM provider — confirm no shared mutable state between calls causes cross-request contamination (relevant if the provider client isn't safely reusable).
- API key missing/invalid for the configured provider — should fail at startup or first call with a clear error, and the orchestrator fallback should still kick in rather than propagating a raw auth error to the frontend.

---

### B7. Student-Facing Routers

**Red/Green tests**
1. `GET /profile` (authenticated) — Green: returns the current user's profile only; a second user's token returns their own (different) profile, never another user's data.
2. `PUT /profile` — Green: updates persist (re-fetch confirms change) and Neo4j `Student` node/edges are updated consistently with Postgres (cross-check both stores in the test).
3. `POST /profile/skills` — Green: adding a skill appears in a subsequent `GET /profile` and in `GraphService.get_student_skills`.
4. `GET /jobs` with filters — Green: `type=Internship` returns only internships; `location=` filter and `search=` filter each narrow results correctly; unfiltered call returns the full (paginated) set.
5. `GET /jobs/:id` — Green: correct job for a valid id; 404 envelope for a nonexistent id.
6. `GET /skills/market` — Green: matches `MarketAgent` output for the same seeded data (cross-check against the agent unit test fixture).
7. `GET /skills/gap` and `POST /gap-analysis` — Green: both produce internally consistent readiness scores for the same student+job (this test also forces resolution of the open contract-overlap decision from `features-todo.md`).
8. `GET /recommendations/jobs|skills|courses` — Green: each returns data shaped per the documented schema, sorted as the underlying agent guarantees.
9. `GET /market/insights` — Green: matches `MarketAgent` aggregate output.
10. `GET /dashboard` — Green: `job_readiness_score`, `skills_matched`, `missing_high_demand_skills` are internally consistent with what `/skills/gap` and `/skills/market` return independently for the same student (a cross-endpoint consistency test, not just "route returns 200").
11. Every protected route rejects an unauthenticated request with 401 (parameterized test across all routes in this module, not one-off).

**Edge cases**
- A brand-new student (empty profile, no skills, no target roles) hitting every one of these routes — none should 500; each should return a sensible empty/zero state.
- `GET /jobs` with a filter combination that matches zero results — returns an empty array with 200, not a 404.
- Pagination boundary — requesting a page past the last available result — empty array, not an error.
- `POST /gap-analysis` with a `target_job_id` that doesn't exist — 404/400 with a clear error, not a crash inside the agent chain.
- Search filter with special characters (SQL/Cypher-injection-style payloads in the `search` query param) — must be treated as literal search text (ties back to the B2 Cypher-injection test).

---

## FRONTEND

### F1. API Client Layer & Auth Wiring

**Red/Green tests**
1. `apiClient` unwraps `{success: true, data}` — Green: returns `data` directly to the caller.
2. `apiClient` on `{success: false, error, message}` — Green: throws/rejects with an error object containing `error` and `message`, which calling code can catch.
3. Auth header injection — Green: when a token exists in storage, every outgoing request via `apiClient` includes `Authorization: Bearer <token>`; when no token exists, it's omitted (not sent as `Bearer null`/`Bearer undefined`).
4. `useAuth` login flow — Green: after `login()` resolves, `token`/`user` are populated and persisted (survive a simulated page reload — re-reading from storage restores the same state).
5. `useAuth` logout — Green: clears token/user from state and storage.
6. Global 401 handling — Green: any API call resolving with a 401 triggers logout + redirect to `/`, tested via a mocked API returning 401 on a protected-route call.
7. `ProtectedRoute`/route guard — Green: navigating to `/dashboard` with no token redirects to `/`; with a valid token, renders the child route.

**Edge cases**
- Token present but expired (client doesn't know without a server round trip) — first API call fails 401 → must still trigger the logout/redirect path (don't rely on client-side expiry parsing as the only mechanism).
- Rapid double-submit of login (double-click) — should not fire two overlapping login requests that race and leave inconsistent auth state.
- API completely unreachable (network error, not a 4xx/5xx) — `apiClient` must surface a distinct "network error" state, not crash the calling component.
- Storage unavailable/blocked (e.g., private browsing edge cases) — decide graceful degradation and test it, or explicitly document as out of scope.

---

### F2. Login Page

**Red/Green tests**
1. Empty submit — Red: currently no validation exists at all. Green: submitting with empty email/password shows inline validation errors and does not call the API.
2. Invalid email format — Green: shows a validation error, no API call made.
3. Valid credentials submit — Green: calls `authApi.login`, on success navigates to `/dashboard`, token stored.
4. Invalid credentials submit — Green: shows an error message from the API response, stays on `/`, no navigation, no token stored.
5. Loading state — Green: submit button shows a loading/disabled state while the request is in flight, re-enables after success or failure.
6. Network failure during login — Green: shows a generic "couldn't reach server" message, not a raw exception or blank screen.

**Edge cases**
- Whitespace-only input in email/password fields — treated as empty (trim before validating).
- Pressing Enter in the password field submits the form (keyboard-only flow), not just clicking the button.
- Already-authenticated user navigating back to `/` — should redirect straight to `/dashboard` rather than showing the login form again.

---

### F3. Dashboard Page

**Red/Green tests**
1. Loading state — Green: on initial mount, before data resolves, renders the skeleton (not the mock-shaped layout, not a blank page).
2. Success state — Green: with a mocked `GET /dashboard` response, renders `StatCard`/`SkillBar` values that match the mocked payload exactly (regression-proofs prop wiring).
3. Empty-profile state — Green: a student with zero skills/zero required skills renders a "complete your profile" prompt instead of divide-by-zero-looking bars (0/0 skills matched) or broken percentage bars.
4. Error state — Green: a failed `GET /dashboard` (500 or network error) shows an inline error/retry affordance, not a blank or crashed page.

**Edge cases**
- `missingHighDemandSkills` empty array — the "Missing High-Demand Skills" card must render a sensible "none — you're covered" state rather than an empty list with a "0" that looks like an error.
- Extremely long skill names / many skills — layout doesn't overflow/break (basic responsive sanity, not full visual regression testing).

---

### F4. Profile & Edit Profile Pages

**Red/Green tests**
1. View mode renders `GET /profile` data (once implementation confirmed) — Green: matches fetched data exactly, no leftover mock data visible anywhere on the page.
2. Edit form pre-fills with current profile data — Green: opening edit mode shows the same values as view mode, not blank/default fields.
3. Add a skill — Green: submitting the add-skill form calls the skills endpoint, and on success the new skill appears in the list without a full page reload (cache invalidation/refetch works).
4. Remove a skill — Green: removing updates both the UI list and, on refetch, the backend no longer returns it.
5. Save profile changes — Green: `PUT /profile` is called with exactly the changed fields (or full object, per the decided contract), success shows a confirmation, and view mode reflects the change.
6. Validation errors (e.g., invalid graduation year) — Green: shown inline, save button blocked/disabled, no API call made with invalid data.

**Edge cases**
- Saving with zero skills and zero target roles — must be allowed (not forced to have data) but should surface the same "dashboard will be limited" guidance noted in F3.
- Duplicate skill entry (adding "Python" when it's already in the list) — should be prevented or merged, not create two entries.
- Concurrent edit — user has the edit form open in two tabs, saves in one, then saves stale data in the other — decide and test the conflict behavior (last-write-wins is acceptable for capstone scope, but it must be a decided, tested behavior, not undefined).

---

### F5. Job Explorer Page

**Red/Green tests**
1. Initial load — Green: fetches and renders jobs from `GET /jobs` with no filters applied.
2. Filter by type — Green: selecting "Internship" re-queries/re-filters and only internship cards render.
3. Search — Green: typing a query (debounced) narrows results to matching titles/companies/skills per the documented search behavior.
4. Empty results — Green: a filter combination with zero matches shows an explicit "no jobs match your filters" state, not a blank area.
5. Pagination/"load more" — Green: triggers the next page and appends (or replaces, per design) results correctly, and disables/hides the control when no more pages remain.

**Edge cases**
- Rapid filter changes (user clicks through 3 filters quickly) — only the latest request's results should render (guard against out-of-order response race conditions).
- Search input cleared after typing — reverts to the unfiltered/default list.
- Very long job description/company name — card layout doesn't break.

---

### F6. Skill Analysis Page

**Red/Green tests**
1. Target job selector — Green: renders available options (from the student's target roles or job list, per the decided UX), and selecting one triggers gap analysis.
2. Gap analysis result render — Green: `readiness_score`, `matched_skills`, `missing_skills` (with weeks) render exactly per a mocked `GapAnalysisResponse`.
3. Roadmap render — Green: milestones render in week-range order with correct course links.
4. LLM-narrative present — Green: `explanation`/`encouragement` text shown when present in the response.
5. LLM-narrative absent (no LLM configured) — Green: template/fallback text (from B6's orchestrator fallback) still renders something meaningful, not a blank section.
6. Loading state specific to this page — Green: distinguishable "analyzing..." state while the (potentially slower, LLM-backed) request is pending.

**Edge cases**
- Selecting a target job the student is already 100%-ready for — `missing_skills` empty, roadmap empty — page shows a positive "you're ready" state, not an empty broken-looking section.
- No target job selectable at all (student hasn't set any target roles) — page prompts to set one in Profile rather than showing an error.
- Very long roadmap (many milestones) — scrollable/paginated rendering, not an unbounded page.

---

### F7. Recommendations Page

**Red/Green tests**
1. Three independent sections load — Green: jobs/skills/courses each render from their respective endpoint responses.
2. Independent failure — Green: if `GET /recommendations/courses` fails but jobs/skills succeed, only the courses section shows an error state; the other two still render normally.
3. `why_recommended` text render — Green: shown per job card, falls back to template text when LLM narrative absent (same pattern as F6).
4. Empty recommendations — Green: e.g., zero course recommendations because the student has no skill gaps — shows a positive/explicit empty state, not a blank section.

**Edge cases**
- All three sections empty simultaneously (brand-new student) — page as a whole should still make sense (e.g., point back to Profile setup), not look broken.
- Recommendation list longer than a reasonable render count — confirm pagination/truncation behavior is intentional, not accidental.

---

### F8. Shared Infra / Cross-Cutting

**Red/Green tests**
1. Logout action — Green: available from `AppLayout`/nav, clears auth state, redirects to `/`.
2. `AppLayout` user display — Green: shows the real authenticated user's name/email (from `useAuth`), not a hardcoded string.
3. Global error toast — Green: an API error anywhere in the app (simulated) surfaces a toast/notification via the existing `sonner`/`toaster` components rather than failing silently.
4. `mockData.ts` retirement — Green: a repo-wide check (grep in CI, or a simple test asserting no page module imports from `lib/mockData`) passes once all pages are wired — this is the literal, automatable "confirm the mock-to-real transition is complete" test.

**Edge cases**
- Multiple simultaneous errors (e.g., two failed queries on the same page) — toasts stack/queue sensibly rather than overlapping illegibly.
- Logout while a request is in flight — in-flight request completing after logout should not resurrect stale authenticated UI state.

---

## Custom AI Model (GNN)

**Red/Green tests**
1. `export_graph.py` produces a `HeteroData` object — Green: node/edge counts in the exported object match direct Neo4j `COUNT` queries for each type on a fixed seeded dataset.
2. Train/val/test edge split — Green: splits are disjoint (no edge appears in more than one split) and each split is non-empty for a dataset above a minimum size.
3. Training loop runs to completion — Green: loss decreases over a fixed small number of epochs on a fixed seed (sanity check, not full convergence proof) — a "does it learn at all" smoke test.
4. Negative sampling — Green: sampled negative edges are verified to not exist as real edges in the full graph (no false negatives contaminating training).
5. Evaluation metrics computed — Green: `evaluate.py` produces AUC-ROC/Hits@10/MRR values in valid ranges (AUC in [0,1], Hits@k in [0,1]) on the held-out test split.
6. Baseline comparison — Green: the same evaluation harness, run against the algorithmic `RecommendationAgent`/`PathFinderAgent` scores on the identical held-out edges, produces a directly comparable metrics table — this is the thesis result, so the test must assert both models were scored on the exact same edge set (a correctness requirement for the comparison to be valid at all).
7. Inference module — Green: given a trained checkpoint, scoring a known held-out positive edge ranks it above a batch of known negatives (a sanity ranking test, independent of the full metrics pipeline).
8. Graceful-degradation integration — Green: with no trained GNN checkpoint present, `RecommendationAgent`/the GNN variant falls back to the pure algorithmic path without error (mirrors the B6 LLM-fallback pattern — same design principle, same test shape).

**Edge cases**
- A node with zero edges of a given type (e.g., a Skill that's in no job's `REQUIRES`) — export doesn't crash, and it's handled as an isolated node in training (or filtered, per a documented decision).
- Extremely sparse graph (small seed dataset) — training/eval scripts must not crash on small N even if metrics are noisy; document that full-scale (10k-job) metrics are the ones reported in the thesis, seed-data runs are for pipeline correctness only.
- Reproducibility — same random seed produces the same split and same (or near-identical, accounting for any nondeterministic GPU ops) metrics across two runs — needed so thesis results are defensible/reproducible.
- Checkpoint loading with a mismatched model architecture (e.g., after a code change to the encoder) — fails with a clear error rather than silently loading garbage weights.

---

## "Application complete" acceptance gate

The system is considered complete only when, across the suites above:
- **100% of the listed red/green tests are green.**
- **Every edge case has an explicit test**, not just a mental note — if an edge case is intentionally out of scope (e.g., storage-blocked browsers in F1), it must be documented as such in `features-todo.md`'s "Open decisions" section rather than silently skipped.
- Backend test suite runs green in CI against a fresh, migrated, seeded test database (not against production/dev data).
- Frontend test suite runs green with all backend calls mocked (no live backend dependency for frontend CI).
- The GNN evaluation comparison table (Part B, test #6) exists and is reproducible — this is both a test-suite gate and a thesis-evaluation deliverable.
