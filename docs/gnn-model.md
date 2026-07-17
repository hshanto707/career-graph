# CareerGraph — GNN Link-Prediction Model (Custom AI Model, Part B)

> Companion to `system-design.md`, `project-roadmap.md` Part B, `features-todo.md`'s
> GNN section, and `test-plan.md`'s "Custom AI Model (GNN)" section.

## Status

**Fully implemented and actually run in this sandbox** — torch 2.13.0,
torch_geometric 2.8.0, and scikit-learn 1.9.0 installed cleanly (no GPU, no
network issues encountered). All commands below were executed for real; the
numbers quoted are actual output, not placeholders.

## Data

No live Neo4j instance and no real Kaggle/O*NET dataset exist in this repo
(`backend/data/kaggle_jobs.csv`, `onet_skills.csv`, `synonyms.json` are
synthetic, hand-generated placeholders — see `docs/data-sources.md`, which
predates this phase). `ml/graph_build.py` builds the graph by running the
**real** `IngestionAgent` → `NormalizationAgent` pipeline against
`backend/tests/fakes.py::FakeGraphService` (in-memory, no Bolt connection
needed), then adds the curated demo students/courses from
`backend/app/etl/seed_demo_data.py`.

`LEADS_TO` (skill prerequisite) edges have **no data source at all** yet,
real or placeholder — nothing in the ingestion pipeline ever writes them.
`graph_build.py` synthesizes a small placeholder chain (skills within the
same O*NET category, alphabetically chained) so the LEADS_TO link-
prediction task has something to train/evaluate on. This is clearly marked
in the module docstring as a stand-in for real curriculum/prerequisite data
(tracked as Future Work).

Exported graph (from the current seed data):

| Node type | Count | Edge type | Count |
|---|---|---|---|
| Student | 3 | (Student)-HAS_SKILL->(Skill) | 11 |
| Skill | 75 | (Job)-REQUIRES->(Skill) | 714 |
| Job | 165 | (Skill)-LEADS_TO->(Skill) | 56 (synthetic) |
| Course | 30 | (Course)-TEACHES->(Skill) | 37 |
| Category | 8 | (Job)-IN_CATEGORY->(Category) | 165 |

## Architecture

- **Encoder**: 2-layer heterogeneous GraphSAGE (`torch_geometric.nn.HeteroConv`
  + `SAGEConv` per message-passing relation, forward and reverse). Each node
  type gets a learned embedding table as input (no rich numeric node
  features exist in the schema yet).
- **Decoder**: dot product between endpoint embeddings (a logit; sigmoid at
  eval/inference time).
- **Task**: link prediction on `(Job)-REQUIRES->(Skill)` and
  `(Skill)-LEADS_TO->(Skill)`.
- **Loss**: `BCEWithLogitsLoss`, summed across both target relations.

Files: `ml/model.py` (architecture), `ml/graph_build.py` (pure-Python graph
construction, no torch), `ml/export_graph.py` (→ PyG `HeteroData`),
`ml/split.py` (pure-Python edge split + negative sampling, no torch),
`ml/train_gnn.py` (training loop + checkpointing), `ml/evaluate.py`
(metrics + baseline comparison), `ml/baseline.py` (algorithmic baseline
adapters), `backend/app/engine/algorithmic/gnn_recommendation_agent.py`
(inference integration point).

## Leakage-safe split & negative sampling

`split_edges()` deterministically (seeded) partitions each target relation's
edges into disjoint train/val/test sets — no edge appears in more than one
split. **Only train-split positive edges are used for message passing**
during training/evaluation (val/test positives are held out of the graph
entirely, not just out of the loss). Negative edges are sampled by
rejection against the FULL positive set (train+val+test), so a "negative"
is never secretly a held-out positive.

## Install & run

```bash
# Separate from the core backend stack (backend/requirements.txt) —
# the API never needs torch installed to run.
python3 -m venv ml/.venv && source ml/.venv/bin/activate
pip install -r ml/requirements.txt
pip install -r backend/requirements.txt   # export_graph.py reuses backend/app's ingestion pipeline

python ml/export_graph.py                 # sanity-check the exported graph
python ml/train_gnn.py --epochs 60        # trains + saves ml/checkpoints/gnn_link_predictor.pt
python ml/evaluate.py                     # metrics + baseline comparison table
pytest ml/tests/                          # 27 tests, all executable with the above installed
```

## Actual results (this sandbox, seed data, 60 epochs, seed=42)

Training loss: `1.39 → 0.016` over 60 epochs (learns; not a full
convergence claim on this small synthetic dataset — see caveats below).

Evaluation (`ml/evaluate.py` output, `ml/results/evaluation_report.json`):

| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |
|---|---|---|---|---|---|---|
| Job-REQUIRES->Skill | GNN (GraphSAGE) | 0.927 | 0.873 | 0.651 | 71 | 71 |
| Job-REQUIRES->Skill | Algorithmic baseline | 0.975 | 1.000 | 0.765 | 71 | 71 |
| Skill-LEADS_TO->Skill | GNN (GraphSAGE) | 0.306 | 1.000 | 0.442 | 6 | 6 |
| Skill-LEADS_TO->Skill | Algorithmic baseline | 0.500 | 1.000 | 1.000 | 6 | 6 |

Both models are scored via `evaluate.py` on **the identical `splits` object**
(built once, passed to both `evaluate_gnn` and `evaluate_baseline`) — the
correctness requirement test-plan.md #6 calls out explicitly.

### Honest read of these numbers

On REQUIRES, the Jaccard/job-similarity baseline currently **beats** the
GNN on this seed dataset — expected and documented, not hidden: 165 jobs /
75 skills is far too small/dense for a learned encoder to out-generalize a
strong collaborative-filtering baseline, and the baseline directly reuses
the ground-truth co-occurrence structure. On LEADS_TO (only 56 synthetic
edges, 6 test positives), both models are noisy for the same reason —
6 test edges is not a statistically meaningful sample.

**These are pipeline-correctness numbers, not thesis-defense numbers.**
Per `test-plan.md`'s documented decision: "full-scale (10k-job) metrics are
the ones reported in the thesis, seed-data runs are for pipeline
correctness only." The full pipeline (export → split → negative-sample →
train → checkpoint → evaluate → baseline-compare) is proven correct and
reproducible end-to-end; re-running it unchanged against the real
10,000+-job Kaggle dataset once available (see `docs/data-sources.md`) is
the only remaining step for thesis-grade numbers, and would give the GNN
enough graph structure to plausibly out-generalize the baseline (the
literature-review precedents this project follows all show that pattern at
scale, not at n=165).

## Baseline comparison methodology (`ml/baseline.py`)

`RecommendationAgent`/`PathFinderAgent` weren't originally built to score a
single candidate edge in isolation, so the baseline adapts their exact
existing signal rather than inventing a new algorithm:

- **REQUIRES**: reuses `RecommendationAgent`'s Jaccard `exact_score`
  formula, applied job-to-job — score(job, skill) = best Jaccard overlap
  between `job`'s other required skills and any other job (in the
  train-split graph) that requires `skill`.
- **LEADS_TO**: reuses `RecommendationAgent`'s exact depth-1/depth-2
  LEADS_TO reachability credit function (`_build_leads_to_adjacency`,
  `_reachable_within_depth`, `DEPTH1_CREDIT`/`DEPTH2_CREDIT`), imported
  directly from `app.engine.algorithmic.recommendation_agent`.

## Inference integration (graceful fallback)

`GNNRecommendationAgent` (`backend/app/engine/algorithmic/gnn_recommendation_agent.py`)
mirrors the `LLMProvider` fallback pattern exactly:

- Constructing it never raises, even with torch not installed or no
  checkpoint on disk — `is_available` is `False` and `unavailable_reason`
  explains why.
- `score_requires()` / `score_leads_to()` return `None` (never raise) when
  unavailable, or when a candidate node id was never seen at training time.
- `score_requires_with_fallback()` is a ready-made helper for callers: pass
  an algorithmic score to fall back to, get back `(score, source)` where
  `source` is `"gnn"` or `"algorithmic"`.
- Verified in `backend/tests/test_gnn_recommendation_agent.py` (runs in the
  plain backend env, no torch) and
  `ml/tests/test_gnn_pipeline_requires_torch.py::test_gnn_agent_falls_back_gracefully_with_no_checkpoint`.

## Test coverage

- `ml/tests/test_graph_build.py`, `ml/tests/test_split.py` — pure Python,
  **runnable in any environment** (only need `pytest` + the same deps
  `backend/requirements.txt` already has: rapidfuzz, neo4j driver,
  pydantic). Actually run in this sandbox: **19 passed**.
- `ml/tests/test_gnn_pipeline_requires_torch.py` — needs
  `ml/requirements.txt` installed; auto-skips (not fails) if torch/PyG/
  sklearn aren't importable. Actually run in this sandbox (torch installed):
  **8 passed**, covering test-plan.md GNN #1–#4, #7, #8, plus
  reproducibility and mismatched-checkpoint edge cases.
- `backend/tests/test_gnn_recommendation_agent.py` — runs in the plain
  backend suite (173 backend tests total, all passing), covering the
  fallback contract (test-plan.md GNN #8).

## Retraining cadence

Per `project-roadmap.md`'s locked-in decision: a fixed snapshot trained
once (this document's numbers) for defense reproducibility; a live
retrain-on-every-ingestion pipeline is Future Work.
