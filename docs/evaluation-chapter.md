# Evaluation

> Thesis Evaluation chapter draft, per `docs/current-status.md` Milestone
> 5. Companion to `docs/gnn-model.md` (full GNN training/evaluation detail)
> and `docs/gnn-defense-guide.md` (the same results, framed for defense
> Q&A). This chapter covers three separate things a capstone evaluation
> needs to answer: does the custom AI model actually work (§1), does it
> actually get *used* by the live system (§2), and is the software as a
> whole correct and tested (§3)? These are evaluated independently because
> a model can score well offline and still never influence a real
> recommendation — see §2 for why that distinction mattered here in
> practice, not just in principle.

---

## 1. GNN vs. algorithmic baseline

### 1.1 Method

Both models are scored by `ml/evaluate.py` against **the identical
`splits` object** — built once, passed unmodified to both `evaluate_gnn`
and `evaluate_baseline` — so a difference in the resulting metrics can only
reflect a difference in the models, never a difference in which edges were
held out. This is asserted, not just designed-for: `ml/tests/test_split.py`
explicitly checks train/val/test disjointness, and validation/test
positives are excluded from the message-passing graph itself during GNN
training/evaluation, not just from the loss — a leakage-safe split is a
precondition for any of the numbers below to mean anything.

The baseline is not a strawman: it directly reuses
`RecommendationAgent`'s real exact-match/partial-credit scoring logic
(`ml/baseline.py`), the same code a live user's `GET /recommendations/jobs`
request runs through — not a simplified reimplementation built only for
this comparison.

### 1.2 Results (10,000-job / 434-skill dataset, seed=42, retrained 2026-08-06)

| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |
|---|---|---|---|---|---|---|
| Job REQUIRES Skill | GNN (GraphSAGE) | 0.937 | 0.014 | 0.012 | 5,429 | 5,429 |
| Job REQUIRES Skill | Algorithmic baseline | 0.961 | 0.116 | 0.067 | 5,429 | 5,429 |
| Skill LEADS_TO Skill | GNN (GraphSAGE) | 0.679 | 0.538 | 0.296 | 39 | 39 |
| Skill LEADS_TO Skill | Algorithmic baseline | 0.500 | 1.000 | 1.000 | 39 | 39 |

Training: loss `1.3843 → 0.0310` over 60 epochs, validation AUC peaking at
0.9367 (epoch 50). Full pipeline (graph export + 60-epoch training) runs in
**~30 seconds wall-clock** on commodity CPU hardware — no GPU required at
this graph size, which matters for reproducibility (any examiner can
re-run this without special hardware).

### 1.3 Interpretation

**On `REQUIRES`, the algorithmic baseline wins on all three metrics.** This
is reported as the actual result, not softened — it directly contradicts
the literature-precedent expectation (de Groot et al.'s Node2Vec work,
Vultureanu-Albisi et al.'s TransE+GAT work — `docs/literature-review.md`)
that a learned approach would close or reverse this gap at scale. The most
defensible explanation available from this evaluation: per-skill positive
density is sparse relative to the size of the candidate pool (5,429
negatives per skill's few true positives), which favors a heuristic that
directly reuses ground-truth co-occurrence structure over an embedding
model with no richer input features than a learned-from-scratch embedding
table per node. This is a genuine, useful negative result, not a
methodology failure — the comparison infrastructure (identical splits,
identical metrics, real production baseline logic) is exactly what makes
it a trustworthy one.

**On `LEADS_TO`, the picture is mixed and the ground truth itself is
weaker evidence.** The GNN's AUC-ROC (0.679) meaningfully exceeds the
baseline's (0.500, i.e. no better than random) — the model has learned
*something* about which skill pairs are graph-structurally similar. But
the baseline's near-perfect Hits@10/MRR (1.000/1.000) is not a
counter-achievement — it's the baseline directly reconstructing a
deterministic alphabetical-same-category rule it has full visibility into
(`ml/graph_build.py`'s synthetic `LEADS_TO` heuristic — see
`docs/discussion-limitations.md` §2), which is tautological, not
generalization. Neither number should be read as "how good is this system
at ordering a real learning path," because the ground truth being
evaluated against is itself synthetic.

## 2. Does the trained model actually influence the live system?

This question is evaluated separately from §1 because — for a meaningful
period of this project's build — the answer was **no**: the checkpoint,
the evaluation report, and the "Contribution 6" narrative all existed and
were correct, but `EngineOrchestrator` had zero references to the GNN at
all. A model that is trained and evaluated but never called by any live
code path has proven something about the model, but nothing yet about the
*system*. Closing that gap was treated as its own milestone
(`docs/current-status.md` Milestone 1) precisely because it's a distinct
claim requiring distinct evidence.

**Evidence the gap is now closed:**

- `RecommendationAgent.rank_jobs` calls `GNNRecommendationAgent` directly
  for the top 50 algorithmically-ranked candidates per request (§3.3,
  Implementation chapter), not just in a standalone script.
- Verified against a real, running deployment — not just tests — by
  registering a real student, adding real skills, and hitting
  `GET /recommendations/jobs`:

  ```
  {
    "job_id": "silverlake-quantum-ventures::intern-data-analyst",
    "title": "Intern Data Analyst",
    "match_percentage": 65.0,
    "matched_skills": ["SQL", "Python"],
    "match_source": "gnn"
  }
  ```
  Confirmed live in the actual Docker container (torch installed,
  checkpoint mounted), not a mock — 2026-08-06.
- Live latency: first request after a cold start ~0.7s (building the
  in-memory graph + one encoder forward pass); subsequent requests ~0.4s
  (cached encoder output, process-wide singleton — §3.3, Implementation
  chapter). Both are well within an interactive request budget.
- Integration tests exist at the orchestrator level specifically to keep
  this claim true going forward, not just at the standalone-agent level:
  `backend/tests/test_routers.py::TestOrchestratorGNNWiring` asserts
  `match_source` actually varies based on GNN availability, through the
  real HTTP route, with a stubbed GNN agent (no torch dependency needed to
  run this check in CI).

## 3. Software correctness — test coverage

| Suite | Result | Breakdown |
|---|---|---|
| Backend (pytest) | **195 passed, 0 failed** | `test_routers.py` 51, `test_algorithmic_agents.py` 34, `test_auth.py` 29, `test_ingestion.py` 28, `test_llm_reasoning.py` 25, `test_data_layer.py` 13, `test_health.py` 10, `test_gnn_recommendation_agent.py` 5 |
| Frontend (vitest) | **85 passed, 0 failed** | 15 test files across every page, the API client, auth, routing, and the error boundary |
| ML pipeline (`ml/tests`, torch installed) | **29 passed, 0 failed** | `test_split.py` 11, `test_gnn_pipeline_requires_torch.py` 10, `test_graph_build.py` 8 |
| Frontend typecheck (`tsc --noEmit`) | Clean | — |
| Frontend production build (`npm run build`) | Succeeds | 575 KB main bundle (unsplit — a real, minor perf note, not a correctness issue) |

All three suites are fully green with **zero known failing or skipped
tests** as of 2026-08-06 — including a CORS-configuration test that had a
real, latent bug (hardcoded origin literal instead of reading actual
config) discovered and fixed during hardening
(`docs/current-status.md` Milestone 4).

### 3.1 What "green" does and doesn't prove

Stated plainly, because §4.3 of the Implementation chapter is direct
evidence for this: **a fully green test suite is necessary but not
sufficient evidence the system works.** The GNN's "never raise" contract
was correctly unit-tested (missing checkpoint, corrupt checkpoint, torch
absent) throughout the build, and every one of those tests passed the
entire time — but none of them constructed a read-only-filesystem,
production-shaped deployment scenario, which is exactly the condition that
crashed a real request the first time the integrated system was actually
deployed and driven end-to-end. This evaluation chapter's methodology
therefore deliberately includes both automated test results (this section)
and live, manually-verified system checks (§2, and the README
re-verification in `docs/current-status.md` Milestone 4) as two
independent forms of evidence, not one standing in for the other.

## 4. Usability / system-level notes

- **End-to-end flows verified live**, not just per-component: register →
  build a profile (skills, target role, major, graduation year) → browse
  the Job Explorer (with required-skills detail) → run a skill gap
  analysis against a real target job → view ranked recommendations
  (including GNN-influenced ones, §2) — all against the full 9,380-job
  seeded dataset.
- **Two deployment paths both verified working from a clean state**: the
  local dev workflow (`backend/docker-compose.yml` + `npm run dev`) and
  the one-shot full-containerized stack (root `docker-compose.yml`,
  nginx-served frontend). Both were found to have real CORS-configuration
  bugs before being fixed (`docs/current-status.md` Milestone 4) — a
  system-level usability failure mode (nothing loads, no data-correctness
  bug involved) that unit tests alone would not surface, since it depends
  on cross-service configuration agreement, not any single service's
  internal logic.
- **Graceful degradation confirmed for both optional subsystems**: the
  system runs correctly with the LLM off (its actual configuration
  throughout this build and the shipped defense build) and would run
  correctly with the GNN unavailable (verified via the stub-agent tests in
  §3, and previously true for the entire pre-Milestone-1 period of the
  build, during which the system functioned with the GNN wired to
  nothing).
