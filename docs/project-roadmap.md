# CareerGraph — Project Roadmap (Implementation, Custom AI Model, Thesis)

> **For current state and the remaining path to defense, see
> `docs/current-status.md` (2026-08-05, updated 2026-08-06)** — the
> "Context / current state" section below is dated 2026-07-16 and now
> stale in several places. This doc's Part A/B/C breakdown and phasing
> table remain useful as historical planning context.
>
> Companion to `system-design.md` (architecture spec), `methodology.md` / `capstone-proposal.md` / `research-contribution.md` / `literature-review.md` (thesis chapters already drafted). This document is the **execution plan** — what still needs to be built, module by module, and how it maps to the thesis and to a custom-trained AI model. Nothing here overrides the existing thesis docs; it sequences the work needed to make them true.

---

## Context / current state

> **Updated 2026-07-16 — final verification phase.** The paragraphs immediately below (marked "original") describe the state at the *start* of the build; they are kept for history but are no longer accurate. Current, verified state follows.

### Current state (verified this pass)

- **Backend** (`backend/`): fully built per `system-design.md` §6–§9 — FastAPI app, all 8 student routers + admin, data layer (Postgres + Neo4j client code, `GraphService`), auth (bcrypt + JWT), ingestion pipeline (`IngestionAgent`/`NormalizationAgent`), all 4 algorithmic agents, LLM provider abstraction (Claude/OpenAI/Ollama) + `ReasoningAgent` + `EngineOrchestrator`. `backend/main.py` imports cleanly. **173 pytest tests pass, 0 failures.** All DB-layer and LLM tests run against fakes/mocks/SQLite — **no live Postgres or Neo4j has been exercised** (docker-compose exists but was not started in this pass; only `.env.example` exists, no real `.env` with credentials).
- **Frontend** (`frontend/`): fully wired to the real API client — `apiClient.ts`, per-resource API modules, `useAuth`, React Query hooks per page, `ProtectedRoute`. No page under `src/pages` imports `lib/mockData.ts` any longer (only a leftover `Job` type import in `job-card.tsx`). **69 vitest tests pass across 13 files, 0 failures.** `npm run build` succeeds (505 KB main bundle, unsplit — a real but minor perf note, not a correctness issue).
- **Data**: `backend/data/{kaggle_jobs.csv, onet_skills.csv, synonyms.json}` exist but are **synthetic, hand-generated placeholders** (204/139/50 lines), not the real Kaggle 10k+ job dataset or the real O*NET/ESCO taxonomy. Ingestion pipeline correctness is proven against these fixtures, not against real-scale data.
- **GNN model** (`ml/`): built and actually trained once — `ml/checkpoints/gnn_link_predictor.pt` and `ml/results/evaluation_report.json` contain real (not placeholder) AUC-ROC/Hits@10/MRR numbers for the GNN vs. the algorithmic baseline, computed on identical held-out edges. This was done in a prior session that had `torch`/`torch_geometric` installed; **this environment does not have them installed** (`ml/tests/test_gnn_pipeline_requires_torch.py` auto-skips — confirmed 19 passed/1 skipped this pass). The graph trained on is the tiny synthetic seed dataset (165 jobs, 75 skills, 3 students), not a real ingested Kaggle/O*NET graph, and `LEADS_TO` edges are a synthesized placeholder heuristic (no real prerequisite data source exists yet).
- **LLM**: provider abstraction and orchestrator fallback are fully implemented and unit-tested with **mocked** providers only. No real `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` is configured anywhere in this repo — the system has never actually called a live LLM API end-to-end.
- **Thesis**: literature review, methodology, capstone proposal, and research-contribution chapters are already substantially drafted. Implementation chapter can now draw on a real, tested system; Evaluation chapter has a real (if small-scale) GNN-vs-baseline table to start from, but should be re-run against a larger real dataset before being called final.

### Original context (pre-build, kept for history)

- **Frontend** (`frontend/`): fully scaffolded React/Vite/TS app (Login, Dashboard, Profile, EditProfile, Jobs, SkillAnalysis, Recommendations pages; shadcn/ui components). Currently reads from `frontend/src/lib/mockData.ts` — no API client layer, no auth, no real data flow.
- **Backend**: does not exist yet. Everything in `system-design.md` §6–§9 (FastAPI app, routers, Intelligence Engine agents, LLM provider abstraction, GraphService) is a spec, not code.
- **Data layer**: no PostgreSQL/Neo4j instances or schemas stood up yet.
- **Thesis**: literature review, methodology, capstone proposal, and research-contribution chapters are already substantially drafted (`docs/methodology.md`, `docs/capstone-proposal.md`, `docs/research-contribution.md`, `docs/literature-review.md`, `docs/reference.md`, `docs/Capstone Report.pdf`). This roadmap does not redo those — it feeds the still-missing **Implementation** and **Evaluation** chapters.

## Decisions locked in

- **Custom AI model = Knowledge-Graph Embedding / GNN link-prediction model**, trained on the Neo4j schema, to predict `REQUIRES` (job↔skill) and `LEADS_TO` (skill↔skill) edges — evaluated against the existing hand-tuned Jaccard/BFS algorithmic agents as baseline. This sits alongside (not replacing) the pluggable, non-trained LLM reasoning layer already specified in `system-design.md` §9.4–9.5.
  - Precedent already covered in `literature-review.md`: de Groot et al. (Node2Vec for link prediction), Vultureanu-Albisi et al. (TransE + GAT + distillation), Fettach et al. (TA-DistMult, temporal KG). CareerGraph's GNN model should be positioned in `research-contribution.md` as a "Contribution 6" once trained and evaluated — a static (non-temporal), single-region link-prediction model purpose-built for the Student–Skill–Job–Course graph, simpler than TA-DistMult but with an explicit algorithmic baseline comparison none of the three prior works provide against a personalized per-student gap score.
- **Timeline: ~2–3 months** → MVP-first ordering; one well-executed GNN model + one clean ablation beats multiple experimental models.

---

## Part A — Software Modules (build order)

1. **Backend scaffold** — FastAPI app (`backend/main.py`, CORS, router registration), Docker Compose (PostgreSQL 15 + Neo4j 5 + optional Ollama), `.env` config, Alembic setup. (§6)
2. **Data layer** — PostgreSQL `users`/`student_profiles` tables; Neo4j constraints/indexes for `Student`, `Skill`, `Job`, `Course`, `Category` + 6 relationship types; `GraphService` as the single parameterized-Cypher access point. (§7)
3. **Auth module** — register/login, bcrypt, JWT (HS256, 24h), `current_user` middleware. (§11.1)
4. **Ingestion pipeline** — `IngestionAgent` (Kaggle CSV + O*NET/ESCO parsing, schema validation) → `NormalizationAgent` (synonym exact-match → rapidfuzz ≥90 fuzzy match → flag-for-review) → Neo4j MERGE writes; `POST /admin/ingest/csv`; `seed_demo_data.py`. (§9.2)
5. **Algorithmic agents** (pure Python, no LLM) — `SkillGapAgent`, `RecommendationAgent`, `PathFinderAgent`, `MarketAgent`. These are the baseline the GNN model is evaluated against. (§9.3)
6. **LLM provider + Reasoning agent** — `LLMProvider` ABC + `ClaudeProvider`/`OpenAIProvider`/`OllamaProvider`; `ReasoningAgent` (`explain_gap`, `narrate_recommendations`, `write_roadmap`, `summarize_market`); `EngineOrchestrator` with graceful no-LLM fallback. (§9.4–9.6)
7. **Student-facing routers** — `profile`, `jobs`, `skills`, `recommendations`, `gap-analysis`, `market`, `dashboard`, returning the `{success, data, message}` envelope. (§8)
8. **Frontend integration** — API client layer (`authApi`, `profileApi`, `jobsApi`, `skillsApi`, `recApi`, `gapApi`, `marketApi`) via React Query; JWT storage/interceptor; replace `mockData.ts` page-by-page. Existing UI components stay as-is. (§5)
9. **Testing & quality** — pytest for algorithmic agents + router integration tests; expand existing Vitest setup (`frontend/src/test/`); security pass against `system-design.md` §15 threat/control table.
10. **Deployment** — Docker Compose full-stack per §14; local demo is sufficient for defense, cloud deploy only if time remains.

---

## Part B — Custom AI Model (GNN / Knowledge-Graph Embedding)

1. **Data prep**: export populated Neo4j graph into a PyTorch Geometric `HeteroData` object (node types: Student, Skill, Job, Course, Category; edge types: HAS_SKILL, REQUIRES, LEADS_TO, TEACHES, IN_CATEGORY).
2. **Task**: link prediction on held-out `REQUIRES` and `LEADS_TO` edges, with negative sampling.
3. **Model**: 2-layer GraphSAGE or R-GCN encoder + dot-product/MLP decoder — simple and defensible, not a from-scratch novel architecture.
4. **Training**: edge-level train/val/test split (avoid node leakage); BCE loss; track AUC-ROC, Hits@10, MRR.
5. **Baseline comparison** (key Evaluation-chapter result): GNN scores vs. existing Jaccard/BFS algorithmic scores, same held-out edges, same metrics.
6. **Integration**: expose trained model behind a swappable inference module callable from `RecommendationAgent`/a new `GNNRecommendationAgent` variant — optional and gracefully degradable, consistent with the LLM provider pattern.
7. **Scope guard**: defer temporal/dynamic graph modeling and multi-region analysis to Future Work (already listed in `system-design.md` §2 and `capstone-proposal.md`).

---

## Part C — Thesis (remaining chapters)

Already drafted: Literature Review, Methodology (architecture, feasibility, requirements, diagrams), Capstone Proposal, Research Contribution, References.

Still needed, fed directly by Parts A & B above:
- **Implementation chapter** — stack, key engineering decisions, screenshots of the working (non-mocked) frontend, once Part A is built.
- **Evaluation chapter** — GNN vs. algorithmic-baseline metrics (AUC, Hits@k, MRR) from Part B, plus system-level performance/usability notes.
- **Discussion** — limitations (data recency, synthetic proficiency data, single-region jobs), threats to validity.
- **Conclusion & Future Work update** — confirm against `system-design.md` §2 "Post-Capstone Scope" and `research-contribution.md`.
- **Research Contribution update** — add the GNN model as a distinct, evaluated contribution once Part B results exist.

---

## Suggested phasing (~2–3 month deadline)

| Weeks | Focus |
|---|---|
| 1–2 | Backend scaffold + DB layer + auth + ingestion pipeline (Modules 1–4) |
| 3–4 | Algorithmic agents + student routers + frontend wiring starts (Modules 5, 7, 8) |
| 5 | LLM provider + ReasoningAgent + orchestrator (Module 6) |
| 6–7 | GNN data prep, training, baseline comparison (Part B) — start early, highest-risk item |
| 8 | Finish frontend integration + testing pass (Modules 8–9) |
| 9 | Evaluation chapter, polish deployment/demo, remaining thesis chapters |
| 10+ (buffer) | Revisions, defense prep |

## Working agreement

- No code until explicitly requested — this roadmap is planning only.
- Work proceeds module-by-module ("dive deeper on each") in the order above unless redirected.
- Suggested starting point: **Backend scaffold + Data layer** (Modules 1–2), since every other module depends on it.
