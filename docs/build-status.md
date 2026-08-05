# CareerGraph — Build Status (Final Verification Pass)

> **Superseded by `docs/current-status.md` (2026-08-05, updated 2026-08-06)**
> — this snapshot is kept for history but several items below are now
> stale (live DB integration is done, self-registration UI exists, the GNN
> is now wired into a live request path). Read `current-status.md` first.
>
> Date: 2026-07-16. Companion to `features-todo.md` (per-item checklist) and
> `project-roadmap.md` (updated current-state section). This document is the
> honest scoreboard: what was built, what actually passes, and what remains
> before this is genuinely demo/thesis-ready.

## What was built

- **Backend** (`backend/app/`): FastAPI app with CORS + envelope error handling;
  Postgres (`users`, `student_profiles`) + Neo4j client layers behind a single
  `GraphService`; JWT auth (register/login, bcrypt, `get_current_user`);
  ingestion pipeline (`IngestionAgent` → `NormalizationAgent`, synonym +
  rapidfuzz matching, flag-for-review); four algorithmic agents (SkillGap,
  Recommendation, PathFinder, Market); a pluggable LLM provider layer
  (Claude/OpenAI/Ollama) + `ReasoningAgent` + `EngineOrchestrator` with a
  documented, tested no-LLM fallback; all 8 student routers + an admin
  ingestion endpoint gated by a fixed admin token.
- **Frontend** (`frontend/src/`): `apiClient` with envelope unwrapping and
  auth-header injection; `useAuth` context; React Query wired per page; all
  seven pages (Login, Dashboard, Profile, EditProfile, Jobs, SkillAnalysis,
  Recommendations) reading from the real API instead of `mockData.ts`; route
  protection; toast-based error surfacing.
- **GNN model** (`ml/`): a full export → split → train → evaluate pipeline
  (2-layer heterogeneous GraphSAGE, link prediction on `REQUIRES`/`LEADS_TO`),
  with a trained checkpoint and a real evaluation report comparing it against
  the algorithmic baseline on identical held-out edges.

## Test scoreboards (run fresh in this pass)

| Suite | Result | Command |
|---|---|---|
| Backend (pytest) | **173 passed, 0 failed** | `cd backend && .venv/bin/python -m pytest -q` |
| Frontend (vitest) | **69 passed, 0 failed, 13 test files** | `cd frontend && npm run test -- --run` |
| ML pipeline tests (pytest, torch installed) | **27 passed, 0 skipped** | `ml/.venv/bin/python -m pytest ml/tests -q` |

Backend breakdown by file: `test_health.py` 10, `test_auth.py` 25,
`test_data_layer.py` 13, `test_ingestion.py` 28, `test_algorithmic_agents.py`
29, `test_llm_reasoning.py` 25, `test_routers.py` 26, `test_gnn_recommendation_agent.py` 5.

Sanity checks also run in this pass:
- `import main` (backend FastAPI entrypoint, `backend/main.py`) — **succeeds**.
- `npm run build` (frontend) — **succeeds** (505 KB main bundle, single chunk —
  a real but minor perf note, not a blocker).
- `import torch` in the backend venv — still **fails** (`ModuleNotFoundError`),
  by design (`ml/requirements.txt` is deliberately kept separate from
  `backend/requirements.txt` so the API never needs torch to run). A
  dedicated `ml/.venv` was created and `pip install -r ml/requirements.txt`
  succeeded (torch 2.13.0, torch_geometric 2.8.0, scikit-learn 1.9.0), which
  is why `ml/tests` now runs all 27 tests instead of auto-skipping the
  torch-dependent ones.

## What remains before this is truly demo/thesis-ready

Ranked by priority:

1. **Real data acquisition.** `backend/data/kaggle_jobs.csv` is now a
   ~10,000-row synthetic dataset (up from the earlier 204-line placeholder),
   with `onet_skills.csv` at 518 skills and `synonyms.json` at 215 aliases —
   i.e. the dataset is now at realistic target *scale* (10k postings, a
   500+-skill taxonomy). It is still **synthetic, generated data**, not the
   real Kaggle job-postings dataset or the real O*NET/ESCO taxonomy the
   thesis and system-design describe — that claim is not resolved.
   What scale unlocks: ingestion/normalization was re-run end-to-end against
   the full file (not just tiny unit-test fixtures) — 10,000/10,000 rows
   read, 0 dropped, 55,428 skill edges written, 493 skill instances (17
   distinct skill strings) flagged for manual review by the fuzzy-matcher
   out of injected messy/typo'd skill names, all in well under a second of
   wall-clock time. That means ingestion-at-scale and GNN-at-scale testing
   against this fixture are now meaningful in a way they weren't at 204
   rows. The only remaining piece of this gap is swapping in genuinely
   real-world source data (an actual Kaggle job-postings export and the
   real O*NET/ESCO taxonomy) if/when that becomes available.
2. **Live database integration testing.** `docker-compose.yml` exists and
   defines Postgres 15 + Neo4j 5 + the API, but was not started in this pass
   — no test in either suite has run against a live Postgres or Neo4j
   instance; all DB-layer tests use SQLite (Postgres) or an in-memory fake
   (`FakeGraphService`, Neo4j). Alembic's `upgrade head`/`downgrade base`
   round-trip and the Neo4j constraint-bootstrap script are untested against
   real engines. Needs an actual `docker compose up -d` + a pass of the
   integration-style tests against the real containers.
3. **Real LLM API configuration.** The `LLMProvider` abstraction and
   orchestrator fallback are fully implemented and unit-tested, but only with
   mocked SDK calls. No `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` is configured
   anywhere in this repo (only `.env.example` exists) — the system has never
   actually produced a real Claude/GPT-generated explanation. A live demo
   needs a real key configured and at least a manual smoke test of
   `explain_gap`/`narrate_recommendations`/`write_roadmap`/`summarize_market`
   against the real API.
4. **GNN training on the real ingested graph — DONE 2026-07-18.** A dedicated
   `ml/.venv` was created (`torch` 2.13.0, `torch_geometric` 2.8.0,
   `scikit-learn` 1.9.0 all installed cleanly), and the full pipeline was
   re-run end-to-end against the 10,000-row `kaggle_jobs.csv` /
   518-skill `onet_skills.csv` graph: export (9,380 Job nodes, 434 Skill
   nodes, 54,288 REQUIRES edges, 388 synthetic LEADS_TO edges) → train
   (60 epochs, loss 1.3843 → 0.0310, ~30s wall-clock) → evaluate. The
   checkpoint (`ml/checkpoints/gnn_link_predictor.pt`) and evaluation report
   (`ml/results/evaluation_report.json`) are now current for the 10k-scale
   dataset, not the old 165-job fixture. Headline finding, reported honestly
   in `docs/gnn-model.md`/`docs/gnn-defense-guide.md`: the algorithmic
   baseline still wins on REQUIRES at this scale (AUC-ROC 0.961 vs 0.935,
   Hits@10 0.116 vs 0.018, MRR 0.067 vs 0.013, 5,429 test edges each) — the
   literature-precedent expectation that scale would flip this did not hold
   for this configuration. LEADS_TO's GNN AUC-ROC improved markedly with
   scale (0.306 → 0.685) though the relation is still synthetic placeholder
   data (now 39 test edges instead of 6). Remaining open item: `LEADS_TO`
   still has no real data source — it's synthesized by an alphabetical
   same-category heuristic in `ml/graph_build.py`, fine for pipeline
   correctness but not a real prerequisite-graph result.
5. **Smaller open items, lower priority but still real:** no self-registration
   UI exists (login-only — either build it or explicitly document seeded
   demo credentials as the intended demo path); no rate-limit/lockout policy
   on repeated failed logins; `mockData.ts` still exists solely because
   `job-card.tsx` imports its `Job` type (move the type, then delete the
   file); no dedicated React error boundary for unhandled render crashes
   (only per-query toast errors); root README's docker-compose startup
   sequence has not been re-verified end-to-end against a live run.

## Bottom line

The application is **functionally complete and internally consistent** — routers,
agents, orchestrator, frontend pages, and the GNN pipeline all exist, are
wired together correctly, and are covered by a genuinely green test suite
(173 + 69 + 19 tests passing, 1 skipped for a documented environment reason).
What's missing is **scale and realism of the inputs it's exercised against**:
real Kaggle/O*NET data, a live Postgres/Neo4j pair, a real LLM key, and a GNN
run against the real (not fixture) graph. None of those require new code —
they require running the existing, tested code against real infrastructure
and real data, which is exactly the honest gap to close before the demo/defense.
