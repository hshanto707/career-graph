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

Exported graph (from `backend/data/kaggle_jobs.csv`, the 10,000-row synthetic
dataset, `onet_skills.csv` at 518 skills, `synonyms.json` at 215 aliases —
retrained/re-evaluated 2026-07-18, actual `ml/export_graph.py` output):

| Node type | Count | Edge type | Count |
|---|---|---|---|
| Student | 3 | (Student)-HAS_SKILL->(Skill) | 11 |
| Skill | 434 | (Job)-REQUIRES->(Skill) | 54,288 |
| Job | 9,380 | (Skill)-LEADS_TO->(Skill) | 388 (synthetic) |
| Course | 30 | (Course)-TEACHES->(Skill) | 37 |
| Category | 14 | (Job)-IN_CATEGORY->(Category) | 9,380 |

(9,380 distinct Job nodes rather than the full 10,000 rows because some
posting ids collapse to the same normalized job identity — consistent with
the dedup behavior already exercised by the ingestion pipeline's own test
suite; 54,288 REQUIRES edges is in the same ballpark as the 55,428
skill-edge figure separately reported for raw ingestion in
`docs/build-status.md`, the small difference coming from this export path's
own node/edge bookkeeping rather than a discrepancy in the underlying data.)

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

## Actual results (10,000-row dataset, 60 epochs, seed=42, retrained 2026-07-18)

Training loss: `1.3843 → 0.0310` over 60 epochs (epoch 1 val_auc 0.7222,
peaking at 0.9367 at epoch 50, epoch 60 val_auc 0.9352 — a slight dip after
the peak, consistent with the model starting to overfit the train split by
epoch 60 rather than still under-fitting). Full 60-epoch run, including
graph export/build, took **~30 seconds wall-clock** on this machine
(full-batch training over a ~9.4k-Job graph is still cheap for this model
size).

Evaluation (`ml/evaluate.py` output, `ml/results/evaluation_report.json`):

| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |
|---|---|---|---|---|---|---|
| Job-REQUIRES->Skill | GNN (GraphSAGE) | 0.935 | 0.018 | 0.013 | 5,429 | 5,429 |
| Job-REQUIRES->Skill | Algorithmic baseline | 0.961 | 0.116 | 0.067 | 5,429 | 5,429 |
| Skill-LEADS_TO->Skill | GNN (GraphSAGE) | 0.685 | 0.538 | 0.427 | 39 | 39 |
| Skill-LEADS_TO->Skill | Algorithmic baseline | 0.500 | 1.000 | 1.000 | 39 | 39 |

Both models are scored via `evaluate.py` on **the identical `splits` object**
(built once, passed to both `evaluate_gnn` and `evaluate_baseline`) — the
correctness requirement test-plan.md #6 calls out explicitly.

### Honest read of these numbers

**At 10x+ the previous scale, the algorithmic baseline still wins on
REQUIRES, on all three metrics** — this is the honest result, not the
hoped-for one. AUC-ROC is close (0.961 baseline vs 0.935 GNN) but Hits@10
and MRR are not (0.116 vs 0.018, 0.067 vs 0.013). Two things matter for
reading this correctly, not just "the GNN lost again":
1. The much larger candidate pool (5,429 negatives vs 71 previously) makes
   Hits@10/MRR mechanically harder for *both* models — a top-10 hit out of
   ~5,400 candidates is a much stricter bar than out of 71 — so the raw
   Hits@10 numbers are not comparable to the old small-fixture run.
2. The Jaccard/co-occurrence baseline still directly reuses the
   ground-truth job-skill co-occurrence structure regardless of scale;
   scaling up the graph didn't erode that advantage the way the
   literature-review precedent (Node2Vec/GNN approaches overtaking
   baselines "at scale") predicted it might. With this architecture
   (60 epochs, hidden=64/out=32, full-batch, no richer input features than
   a learned embedding table) and this particular synthetic dataset, the
   GNN does **not** overtake the baseline on REQUIRES — that expectation
   from §9 of `docs/gnn-defense-guide.md` did not pan out and is corrected
   there.

On LEADS_TO, the picture changed with scale but is still not a clean win:
the GNN's AUC-ROC rose substantially (0.306 → 0.685), i.e. it now separates
real from fake LEADS_TO pairs meaningfully better than chance, likely
because 434 skills across 14 categories gives the encoder real neighborhood
structure to learn from instead of 75 skills in 8 categories. But the
baseline still wins Hits@10/MRR outright (1.000/1.000) because it directly
reconstructs the deterministic alphabetical-chain heuristic via depth-1/2
reachability over the train edges — that's tautological, not generalization,
and is expected given `LEADS_TO` is still synthetic placeholder data (see
above). The test-positive count for LEADS_TO grew from 6 to **39**, which is
a real improvement in statistical meaningfulness (still a modest sample, but
no longer "a single flipped comparison swings AUC by ~0.17").

**Bottom line:** the full pipeline (export → split → negative-sample →
train → checkpoint → evaluate → baseline-compare) has now been proven
correct and reproducible at the intended 10k-job/500+-skill thesis scale,
not just on the small fixture. The honest headline finding is that the
algorithmic baseline remains competitive-to-better than this GNN
configuration on REQUIRES even at scale, and LEADS_TO is more measurable
than before but still evaluates a synthetic, non-real relation.

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
  pydantic).
- `ml/tests/test_gnn_pipeline_requires_torch.py` — needs
  `ml/requirements.txt` installed; auto-skips (not fails) if torch/PyG/
  sklearn aren't importable, covering test-plan.md GNN #1–#4, #7, #8, plus
  reproducibility and mismatched-checkpoint edge cases.
- Full run, `ml/.venv` with torch/torch_geometric/scikit-learn actually
  installed (2026-07-18): **`ml/tests` — 27 passed, 0 skipped** (all
  torch-dependent tests actually executed, not skipped, in ~170s wall-clock
  — the previous report's "19 passed, 1 skipped"/"8 passed" figures were
  from an environment where torch import failed).
- `backend/tests/test_gnn_recommendation_agent.py` — runs in the plain
  backend suite (173 backend tests total, all passing), covering the
  fallback contract (test-plan.md GNN #8).

## Retraining cadence

Per `project-roadmap.md`'s locked-in decision: a fixed snapshot trained
once (this document's numbers) for defense reproducibility; a live
retrain-on-every-ingestion pipeline is Future Work.
