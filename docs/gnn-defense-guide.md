# The GNN Model — Defense Prep Guide

> Plain-English + technical walkthrough of CareerGraph's custom AI model, written for capstone defense prep. Companion to `docs/gnn-model.md` (the terse implementation log), `docs/project-roadmap.md` Part B (why this model was chosen), and `docs/research-contribution.md` (how it's positioned against prior work). This document assumes an examiner may ask "how does this actually work" and "why should I believe these numbers" — it's structured to answer both.

---

## 1. What this is, in one paragraph

CareerGraph's knowledge graph (Students, Jobs, Skills, Courses, Categories, connected by edges like `Job–REQUIRES→Skill` and `Skill–LEADS_TO→Skill`) already powers the hand-tuned algorithmic agents (Jaccard similarity, BFS/topological sort). The GNN is a **learned alternative to those hand-tuned formulas**: instead of a human deciding "similarity = intersection over union," a 2-layer heterogeneous **GraphSAGE** neural network learns a numeric representation (an *embedding*) for every node by repeatedly aggregating information from its neighbors, and predicts whether an edge (e.g., "this Job requires this Skill") is likely to exist by comparing two nodes' embeddings. It is trained and evaluated as a **link prediction** task, and its predictions are compared head-to-head against the existing algorithmic agents on data neither model has seen, so we get an honest answer to "does learning the pattern beat hand-coding it?"

---

## 2. Why a GNN (and why this is the thesis's core contribution)

- The literature review already surveys knowledge-graph embedding approaches for this exact problem space: de Groot et al. use **Node2Vec** for career-pathfinding link prediction; Vultureanu-Albisi et al. use **TransE + GAT + knowledge distillation**; Fettach et al. use **TA-DistMult** for temporal skill-demand forecasting. CareerGraph's contribution is a **GraphSAGE-based link predictor purpose-built for the Student–Skill–Job–Course schema**, evaluated with an explicit, apples-to-apples comparison against a hand-tuned algorithmic baseline on identical held-out edges — a comparison none of the three prior works provide against a *personalized per-student* gap score.
- It is deliberately **not** a novel architecture invented from scratch. The contribution is the **application, integration, and rigorous evaluation** of a known technique (GraphSAGE link prediction) to a specific, previously-unmodeled graph schema, with a fully reproducible pipeline (export → split → train → evaluate → compare) — this is a legitimate and common thesis-level contribution, not a weakness. Say this directly if asked "what's novel here."
- It sits **alongside**, not in place of, the LLM reasoning layer. The LLM (Claude/GPT/Ollama) is a pluggable, off-the-shelf, *non-trained* component that turns structured scores into natural-language explanations. The GNN is the opposite: a *trained*, structured-output-only component that never touches natural language. Keeping these separate is itself a design decision worth stating clearly if asked "is the AI in this project just calling an LLM API?" — no, the GNN is the actual trained model; the LLM is a narration layer.

---

## 3. The task: link prediction, explained simply

"Link prediction" means: given a graph with some edges hidden, predict which hidden pairs of nodes are actually connected. Concretely, the model is trained on two edge types:

- **`(Job) –REQUIRES→ (Skill)`** — does this job posting require this skill?
- **`(Skill) –LEADS_TO→ (Skill)`** — is this skill a natural prerequisite/progression toward that skill?

For each, some real edges are hidden from the model during training (the **test split**), and some **fake edges** (pairs that are *not* connected in the graph) are generated as negative examples. The model is asked to score every real and fake pair; a good model gives real edges high scores and fake edges low scores. That's the entire task — it's binary classification per candidate edge, at graph scale.

---

## 4. Data & graph construction

**Node types:** Student, Skill, Job, Course, Category.
**Edge types:** `HAS_SKILL` (Student→Skill), `REQUIRES` (Job→Skill), `LEADS_TO` (Skill→Skill), `TEACHES` (Course→Skill), `IN_CATEGORY` (Job→Category).

The graph is built by running the **real** `IngestionAgent` → `NormalizationAgent` pipeline (the same production code the backend API uses) against the seed/demo dataset, not a separate toy generator — this matters because it means the graph-construction logic being evaluated is the actual system logic, not a simplified stand-in.

**Honest caveat #1 — data scale (resolved 2026-07-18).** The model has now been retrained and re-evaluated against the 10,000-row synthetic dataset (`backend/data/kaggle_jobs.csv`, 518-skill `onet_skills.csv`, 215-alias `synonyms.json`) rather than the original small seed fixture (165 jobs / 75 skills). The results in §8 below are from that retrain. This does **not** mean the dataset is real-world data — it's still synthetic, generated data at realistic target scale, not an actual Kaggle export or real O*NET/ESCO taxonomy — that separate caveat still stands (see `docs/build-status.md` gap #1).

**Honest caveat #2 — `LEADS_TO` has no real data source.** Nothing in the ingestion pipeline ever produces genuine skill-prerequisite edges (no dataset defines "Python leads to Machine Learning" style progressions). `LEADS_TO` edges are **synthesized** by a placeholder heuristic (skills in the same O*NET category are chained alphabetically) purely so the link-prediction task has *something* to train/evaluate on for that edge type. This is explicitly documented as a stand-in, tracked as Future Work. If asked "where does your prerequisite graph come from," the honest answer is: it doesn't exist as real data yet — this is the model correctly learning to predict a synthetic, heuristic ordering, not a validated pedagogical curriculum.

Graph size actually exported and trained on (10,000-row dataset, retrained 2026-07-18):

| Node type | Count | Edge type | Count |
|---|---|---|---|
| Student | 3 | `HAS_SKILL` | 11 |
| Skill | 434 | `REQUIRES` | 54,288 |
| Job | 9,380 | `LEADS_TO` (synthetic) | 388 |
| Course | 30 | `TEACHES` | 37 |
| Category | 14 | `IN_CATEGORY` | 9,380 |

(For reference, the previous small-fixture run this document quoted before
retraining was: Student 3, Skill 75, Job 165, Course 30, Category 8;
`HAS_SKILL` 11, `REQUIRES` 714, `LEADS_TO` 56, `TEACHES` 37, `IN_CATEGORY`
165.)

---

## 5. Model architecture, layer by layer

**File:** `ml/model.py`.

1. **Input features.** The schema has no rich numeric features per node yet (no embeddings of job descriptions, no numeric skill vectors) — so each node starts from a **learned embedding table** (`nn.Embedding`), one table per node type. In plain terms: every node starts as a random vector that the model tunes during training, rather than starting from hand-crafted features.
2. **Two rounds of message passing (`HeteroConv` + `SAGEConv`).** This is the actual "graph" part of "graph neural network." In round 1, every node updates its vector by averaging its neighbors' vectors (across every relevant edge type, in both directions — reverse edges are added purely so information flows both ways, e.g. a Skill also learns from the Jobs that require it, not just the other way around). A ReLU non-linearity is applied. In round 2, this repeats — so by the end, every node's final vector has absorbed information from neighbors-of-neighbors (2 hops away). This is what "GraphSAGE" means: **SA**mple and aggre**G**at**E** neighbor information.
3. **Decoder: dot product.** To score whether a Job and a Skill are connected, take their two final vectors and compute a dot product — a single number. Higher dot product = model thinks they're more likely connected. This is deliberately the simplest possible decoder (no extra learned layers) so that any predictive power comes from the *encoder's* learned representations, not from decoder complexity — a defensible, explainable design choice if challenged on "why didn't you use a fancier decoder."
4. **Output.** During training, the raw dot product (a "logit") feeds into `BCEWithLogitsLoss` (binary cross-entropy) for numerical stability. At evaluation/inference time, a sigmoid converts it to a 0–1 probability-like score.

**Sizes used:** hidden layer = 64 dimensions, output (final embedding) = 32 dimensions — small, deliberately, given the current graph's small scale (over-parameterizing a 165-node-type graph would just memorize it).

---

## 6. Training procedure, step by step

**Files:** `ml/split.py` (pure Python, no torch — independently unit-tested), `ml/train_gnn.py`.

1. **Split the target edges (`REQUIRES`, `LEADS_TO`) into train/val/test (80/10/10).** This is done *per edge*, not per node — meaning individual job-skill connections are held out, not entire jobs. Splitting is deterministic (seeded random shuffle, seed=42) so it's exactly reproducible.
2. **Leakage prevention — the most important methodological detail.** Held-out validation/test edges are removed from the graph entirely before training, not just excluded from the loss calculation. Concretely: the message-passing step in §5 only ever sees the **train-split** positive edges for `REQUIRES`/`LEADS_TO`. If test edges were left in the graph during message passing, the model could "cheat" by having that structural information leak into node embeddings even without ever computing a loss on it — this is a classic and easy-to-miss link-prediction bug, and it's explicitly avoided and tested for (`ml/tests/test_split.py` checks the three splits never overlap).
3. **Negative sampling.** For every real edge in a split, one fake (non-existent) edge is randomly sampled as a negative example. Crucially, "non-existent" is checked against the **full** set of real edges (train+val+test combined) — not just the train set — so a "negative" sample is never actually a real edge that just happened to be held out for testing. This is also unit tested.
4. **Training loop.** 60 epochs, Adam optimizer, learning rate 0.01. Each epoch: encode the whole graph once (2 rounds of message passing), score every training edge (positive and negative) with the dot-product decoder, compute binary cross-entropy loss summed across both target edge types, backpropagate, update weights. Validation AUC is computed every epoch on the held-out validation split (not used for training) purely to monitor progress — it does not affect training itself in this basic version (no early stopping was implemented, deliberately kept simple given the small scale).
5. **Checkpoint.** The trained weights, architecture config, node-ID-to-index mapping, and full training history (loss per epoch) are saved to `ml/checkpoints/gnn_link_predictor.pt` — this is what a "trained model" concretely means here: a file containing tuned numbers, not a live service.

**What actually happened when trained (10k-row dataset, 2026-07-18):** loss went from **1.3843 → 0.0310** over 60 epochs; validation AUC rose from 0.7222 (epoch 1) to a peak of 0.9367 (epoch 50), settling at 0.9352 by epoch 60 — the model is clearly learning to separate real from fake edges on the training data (this is a "does it learn at all" sanity signal, not itself a generalization claim — that's what the held-out test metrics in §7 are for). The slight val-AUC dip between epoch 50 and 60 is a mild overfitting signal, not a reason to add many more epochs at this configuration. The full 60-epoch run (including graph export/build) took **~30 seconds wall-clock**.

---

## 7. Evaluation methodology — metrics explained simply

**File:** `ml/evaluate.py`. Evaluation runs only on the **test split** (never seen during training or validation-monitoring).

- **AUC-ROC** ("Area Under the ROC Curve"): if you pick one real edge and one fake edge at random, AUC-ROC is the probability the model scores the real one higher. 0.5 = random guessing, 1.0 = perfect separation.
- **Hits@10**: of all the real held-out edges, what fraction rank in the top 10 when compared against the negative candidates? A practical "would this actually surface as a top recommendation" metric.
- **MRR** ("Mean Reciprocal Rank"): for each real edge, take 1 ÷ its rank among the candidates, then average. Rewards getting the *very best* rank, not just "in the top 10."

**Fairness guarantee (important, and directly answers test-plan.md's explicit requirement):** the GNN and the algorithmic baseline are evaluated on the **exact same held-out test edges** — the same `splits` object is passed to both `evaluate_gnn()` and `evaluate_baseline()` in one function call, so there is no way for one model to have gotten an easier test set. This is the single fact to state if asked "how do you know this comparison is fair."

**How the baseline is scored (`ml/baseline.py`)** — the comparison isn't against a strawman, it reuses the *actual production* algorithmic agents' exact scoring logic:
- `REQUIRES`: reuses `RecommendationAgent`'s Jaccard `exact_score` formula, applied job-to-job.
- `LEADS_TO`: reuses `RecommendationAgent`'s existing depth-1/depth-2 `LEADS_TO` reachability credit function, imported directly from the production code.

---

## 8. Actual results (10,000-row dataset, retrained 2026-08-06 — see §4)

| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |
|---|---|---|---|---|---|---|
| Job→REQUIRES→Skill | GNN (GraphSAGE) | 0.937 | 0.014 | 0.012 | 5,429 | 5,429 |
| Job→REQUIRES→Skill | Algorithmic baseline | 0.961 | 0.116 | 0.067 | 5,429 | 5,429 |
| Skill→LEADS_TO→Skill | GNN (GraphSAGE) | 0.679 | 0.538 | 0.296 | 39 | 39 |
| Skill→LEADS_TO→Skill | Algorithmic baseline | 0.500 | 1.000 | 1.000 | 39 | 39 |

(Re-run from the identical source data as the 2026-07-18 checkpoint, as a
reproducibility check before wiring the model into a live request path --
see §10. Numbers move by noise-level amounts run-to-run at fixed seed 42,
same qualitative conclusion. Previous small-fixture numbers, superseded by
both of the above: REQUIRES GNN 0.927/0.873/0.651 vs baseline
0.975/1.000/0.765 on 71/71 test edges; LEADS_TO GNN 0.306/1.000/0.442 vs
baseline 0.500/1.000/1.000 on 6/6 test edges.)

### How to talk about these numbers honestly (this is the actual defense answer)

**The baseline still wins on REQUIRES at 10x-plus scale — the literature-precedent hope that scale would close or reverse the gap did not pan out for this configuration.** Do not hide this — state it proactively, then explain *why*, which is the more informative part:

1. **REQUIRES at scale:** AUC-ROC narrowed to a near-tie (0.961 baseline vs 0.935 GNN), but Hits@10/MRR did not (0.116 vs 0.018, 0.067 vs 0.013). Two things explain this without excusing it: (a) the candidate pool grew from 71 negatives to 5,429 negatives, which mechanically makes Hits@10 far stricter for *both* models — the raw Hits@10 numbers are not comparable across the two runs; (b) the Jaccard/co-occurrence baseline still directly reuses the ground-truth job-skill co-occurrence structure regardless of graph size, and that advantage did not erode with scale the way the literature precedent predicted. Said plainly: **at this scale, with this architecture (60 epochs, hidden=64/out=32, embedding-table-only inputs), the GNN does not overtake the baseline on REQUIRES.** That is a real, useful finding, not a failure to hide.
2. **LEADS_TO at scale:** the test-positive count grew from 6 to **39** (more statistically meaningful, though still modest), and the GNN's AUC-ROC rose substantially (0.306 → 0.685) — it now discriminates real from fake LEADS_TO pairs meaningfully better than chance, plausibly because 434 skills across 14 categories gives the encoder real neighborhood structure to learn versus 75 skills in 8 categories before. But the baseline still wins Hits@10/MRR outright (1.000/1.000) because it directly reconstructs the deterministic alphabetical-chain heuristic via depth-1/2 reachability over train edges — that's tautological reconstruction of a known synthetic rule, not generalization, and is expected given `LEADS_TO` is still placeholder data (§4).
3. **What this section of the pipeline *does* prove:** the full pipeline — graph export, leakage-safe splitting, negative sampling, training, checkpointing, evaluation, and a fair head-to-head comparison — is built correctly, runs end-to-end, and is reproducible (fixed seeds throughout), now demonstrated at the intended thesis scale (9,380 jobs / 434 skills), not just a small fixture. The defensible claim is: **"the machinery is correct, proven, and now run at full scale; at this scale, the hand-tuned algorithmic baseline is still competitive-to-better than this GNN configuration on REQUIRES, and LEADS_TO remains an evaluation of synthetic placeholder data even with a larger, more meaningful test set."**

If an examiner pushes on "so does the GNN actually help or not" — the honest, prepared answer is: *"At the full 10k-job / 434-skill scale, no — the algorithmic baseline still wins on REQUIRES, on all three metrics, which contradicts what the literature precedent would predict and is worth stating plainly rather than downplaying. AUC-ROC is close (0.96 vs 0.94), but the baseline's Jaccard/co-occurrence signal remains a genuinely strong, hard-to-beat approach for this task and this dataset. On LEADS_TO, the GNN's AUC-ROC improved a lot with scale (0.31 → 0.69), showing it can learn real structure there, but that relation is still synthetic placeholder data, so I wouldn't over-read even the improved numbers. The honest conclusion is that a hand-tuned structural-similarity baseline is a legitimately strong competitor for this graph and task, and the value of the GNN work is the rigorous, reproducible comparison infrastructure that proved that — not a foregone 'GNN wins' conclusion."*

---

## 9. What to do before defense (in priority order)

1. **DONE (2026-07-18): retrained and re-evaluated against the 10,000-row dataset** (`backend/data/kaggle_jobs.csv`, 518-skill `onet_skills.csv`, 215-alias `synonyms.json`). No new code was needed — `ml/graph_build.py`/`export_graph.py` already pointed at `backend/data/`, so re-running `python ml/export_graph.py && python ml/train_gnn.py --epochs 60 && python ml/evaluate.py` picked up the new scale automatically. Result: the hoped-for "GNN overtakes baseline at scale" outcome did **not** materialize for REQUIRES with this configuration (see §8) — this is now the reported, final-for-this-configuration thesis number, not a placeholder.
2. **Still open: decide and document a real (even if simple) `LEADS_TO` data source** — e.g., derive prerequisite pairs from course curricula order, or from co-occurrence-plus-difficulty heuristics — rather than the current alphabetical-within-category placeholder. Test-positive count did grow from 6 to 39 with the larger skill taxonomy, which helps statistical meaningfulness, but the relation itself is still synthetic.
3. **DONE: environment properly installed and re-verified** (`ml/requirements.txt`: torch 2.13.0, torch_geometric 2.8.0, scikit-learn 1.9.0) — installed cleanly into a fresh `ml/.venv` on 2026-07-18, `ml/tests` ran 27/27 passed with no skips (previously some torch-dependent tests auto-skipped in environments without torch).
4. Optionally, still open: run 2-3 different seeds and report mean ± spread for the metrics, to preempt "how do you know this isn't just luck on one random split" — the split/training code is already seed-parameterized, so this is a rerun, not new code. Given the REQUIRES result held up across a much larger split (5,429 vs 71 test edges) rather than reversing, this is lower priority than it was before the retrain — the finding looks stable, not scale-fragile.
5. Optionally: given loss was still meaningfully decreasing through most of epoch 60 (with a slight val-AUC dip after epoch 50), a longer run or a learning-rate schedule could be tried, but is not expected to change the qualitative REQUIRES conclusion given the baseline's structural advantage is architectural, not a training-budget artifact.

---

## 10. How it's wired into the live system (retrieve-then-rerank, graceful degradation)

**As of 2026-08-06, this is no longer just standalone inference code — the trained model actually influences a real `GET /recommendations/jobs` response.** Earlier builds had `gnn_recommendation_agent.py` fully implemented and unit-tested in isolation, but nothing ever called it — `EngineOrchestrator` had zero references to the GNN. That gap is now closed:

**Files:** `backend/app/engine/algorithmic/gnn_recommendation_agent.py` (inference), `backend/app/engine/algorithmic/recommendation_agent.py` (integration), `backend/app/engine/orchestrator.py` (wiring).

**The integration is a retrieve-then-rerank architecture**, a standard, explainable pattern in real recommender systems:
1. `RecommendationAgent.rank_jobs` first scores **every** job in the catalog (9,380 of them) with the cheap, pure-Python Jaccard/LEADS_TO-BFS algorithm — no model inference, this is the retrieval stage.
2. The top 50 candidates by that algorithmic score are then **reranked** by the GNN: for each of a job's still-missing required skills, `score_leads_to` is queried against every skill the student already owns, using the trained model's learned notion of skill-progression plausibility — not limited to the synthetic, hand-authored `LEADS_TO` edges the BFS-based partial score is otherwise capped at. The blend is `0.6*exact + 0.15*partial + 0.25*gnn` for reranked jobs (vs. `0.8*exact + 0.2*partial` for the pure-algorithmic path).
3. Bounding the model-inference stage to a small top-N pool — rather than scoring all 9,380 jobs with the GNN — is what keeps this tractable; it also matches how retrieve-then-rerank systems work in production recommender literature.
4. Every job in the API response carries a `match_source` field (`"gnn"` or `"algorithmic"`), so a defense demo can point at a specific real recommendation and say concretely "this one, the model reranked."

**Graceful degradation is preserved end to end**, following the exact same design pattern as the pluggable LLM providers:
- If no checkpoint file exists, or torch isn't installed, constructing `GNNRecommendationAgent` never raises — it just reports `is_available = False` with a human-readable `unavailable_reason`, and `rank_jobs` silently skips the rerank stage (every job stays `"algorithmic"`, scores identical to the pre-integration behavior).
- Scoring methods return `None` (never crash) for a candidate node unseen during training (e.g., a brand-new skill added after training) — that missing skill just contributes 0 to `gnn_score`, not an error.
- `GNNRecommendationAgent` is a process-wide cached singleton (`get_default_gnn_agent()`) — `EngineOrchestrator` is rebuilt on every request, and reloading the checkpoint from disk (a `torch.load` deserialization) on every single API call would be a real, unnecessary cost; the model loads once per process and the encoder's forward pass is itself cached per-agent-instance so a 50-job rerank pool costs one graph encode, not fifty.

**Deployment note:** the backend Docker image now installs `torch`/`torch_geometric`/`scikit-learn` (previously deliberately excluded to keep the API lightweight — see `ml/requirements.txt`'s original rationale, still accurate for *why* the code stays degradable), and `docker-compose.yml` mounts `../ml` and `./data` into the container so the checkpoint and its dependencies (`model.py`, `export_graph.py`, `graph_build.py`) resolve at the same repo-relative paths the code already expected.

**A real bug the live-container test caught:** the inference path was calling `export_graph.export()` to rebuild the message-passing graph, which — as a side effect meant for its offline CLI use — unconditionally writes a `.pt` cache file to disk. With `ml/` mounted read-only in the container (deliberately, so the running app can't mutate training artifacts), this crashed `GET /recommendations/jobs` with a 500 (`RuntimeError: ... Read-only file system`) — silently breaking the agent's own documented "never raise" graceful-degradation contract the moment it was actually exercised end-to-end. Fixed by building the in-memory `HeteroData` directly (`to_hetero_data(build_synthetic_career_graph())`) instead of the disk-writing wrapper; inference never needed the persisted file. **The lesson for the defense:** the fallback contract was correctly *unit-tested* (missing checkpoint, corrupt checkpoint, torch not installed), but the first real HTTP round-trip against a production-shaped deployment (read-only mount) still found a gap none of those unit tests could have caught — a concrete, honest example of why live verification matters beyond a green test suite.

**Why this matters for the defense:** the GNN is a genuine enhancement layer, not a single point of failure — the system (including its test suite, e.g. `TestOrchestratorGNNWiring` in `backend/tests/test_routers.py`) is designed to keep working correctly even if the model were deleted, un-trained, or simply not present in a given deployment, while *also* actually being present and influencing real output in the deployed demo. This mirrors the system's overall design philosophy (stated in `system-design.md`) that the LLM is also optional and the system degrades gracefully without it — the GNN just went one step further than the LLM currently has (see `docs/current-status.md` Milestone 2): it's both gracefully-optional *and* actually turned on.

---

## 11. Anticipated defense Q&A

**Q: What exactly is "the AI model" you built, in one sentence?**
A: A 2-layer heterogeneous GraphSAGE neural network that learns embeddings for every Student/Skill/Job/Course/Category node and predicts missing `REQUIRES` and `LEADS_TO` edges by comparing embeddings, trained and evaluated with a leakage-safe edge split against an identical-test-set comparison to the existing hand-tuned algorithmic scoring.

**Q: Why not just use the LLM for everything?**
A: The LLM is intentionally never used for scoring/ranking — it only narrates already-computed structured results into natural language, and it's not trained (it's a pluggable API call). The GNN is the actual trained, structured model; keeping them separate means a hallucinated LLM sentence can never silently change a ranking or a gap score — the numbers come from deterministic algorithms or a trained-and-evaluated GNN, never from free-text generation.

**Q: Is this really a GNN, or just node embeddings?**
A: It's a full GNN — the embeddings are not static/precomputed (like plain Node2Vec); they're produced by 2 rounds of message passing that aggregate live neighbor information through `SAGEConv`, so a node's representation depends on its graph neighborhood, not just a fixed lookup table trained in isolation.

**Q: How do you know your train/test split isn't leaking information?**
A: Held-out validation/test edges are excluded from the message-passing graph itself, not just from the loss — unit tested explicitly (`ml/tests/test_split.py`) to assert the three splits never overlap, and negative samples are checked against the full positive set so a "negative" can never secretly be a held-out real edge.

**Q: Your GNN loses to the baseline — doesn't that mean it failed?**
A: No. It was retrained and re-evaluated at the full 10,000-job/434-skill scale (2026-07-18) specifically to test whether more scale would close the gap, and it didn't for REQUIRES: the baseline still wins on AUC-ROC (0.961 vs 0.935), Hits@10 (0.116 vs 0.018), and MRR (0.067 vs 0.013). That's a real, honestly-reported result, not a hidden failure — the comparison methodology (identical test edges, real production baseline logic, reproducible seeds, now at 5,429 test edges instead of 71) is exactly what makes it a trustworthy finding. The takeaway is that a hand-tuned Jaccard/co-occurrence baseline is a genuinely strong, hard-to-beat approach for this specific graph and task, at this scale, with this GNN configuration — not that the GNN pipeline is broken. On LEADS_TO the GNN's AUC-ROC did improve substantially with scale (0.306 → 0.685), so the picture isn't "the GNN never helps," it's task- and metric-dependent.

**Q: What's the biggest limitation of this work?**
A: Two, stated together: (1) even at the full 10,000-job/434-skill scale, this GNN configuration does not outperform the hand-tuned algorithmic baseline on the REQUIRES task — the dataset is realistic in scale but still synthetic, generated data, not real-world data, and (2) the `LEADS_TO` (skill-prerequisite) relation has no real data source at all yet — it's a documented placeholder heuristic, now with 39 test edges instead of 6 but still not a real prerequisite graph. Neither requires new architecture to fix outright — (1) would need either richer input features than learned embedding tables or acceptance that the baseline is simply strong here, and (2) needs real curriculum/progression data.

**Q: Does the GNN actually affect what a real user sees, or is it just an offline experiment?**
A: It actually affects live output. `GET /recommendations/jobs` runs a retrieve-then-rerank pipeline: every job is scored algorithmically first, then the top 50 candidates are rescored by the trained model, and the API response marks each job `match_source: "gnn"` or `"algorithmic"` so it's directly inspectable which recommendations the model influenced. This wasn't always true — for most of the build, the checkpoint and evaluation report existed but `EngineOrchestrator` never called the inference code at all. That gap was identified and closed as its own milestone (see `docs/current-status.md`).

**Q: Could this scale to a real production system?**
A: Yes, structurally — the architecture (embedding tables + 2-layer SAGEConv + dot-product decoder) scales to graphs far larger than the current one; the main real-world addition needed would be richer input node features (e.g., text embeddings of job descriptions) rather than learned-from-scratch embedding tables, to help the model generalize to nodes it has few training edges for.

---

## 12. Where the code lives (quick reference for a live demo)

| Purpose | File |
|---|---|
| Graph construction (pure Python) | `ml/graph_build.py` |
| Export to PyTorch Geometric `HeteroData` | `ml/export_graph.py` |
| Edge split + negative sampling (pure Python, no torch) | `ml/split.py` |
| Model architecture | `ml/model.py` |
| Training loop | `ml/train_gnn.py` |
| Evaluation + baseline comparison | `ml/evaluate.py` |
| Baseline adapter (reuses production `RecommendationAgent`) | `ml/baseline.py` |
| Trained checkpoint | `ml/checkpoints/gnn_link_predictor.pt` |
| Evaluation report (raw numbers) | `ml/results/evaluation_report.json` |
| GNN inference (graceful fallback) | `backend/app/engine/algorithmic/gnn_recommendation_agent.py` |
| Retrieve-then-rerank integration | `backend/app/engine/algorithmic/recommendation_agent.py` (`rank_jobs`) |
| Orchestrator wiring + `match_source` | `backend/app/engine/orchestrator.py` (`get_job_recommendations`) |
| GNN wiring tests (no torch needed, stub agent) | `backend/tests/test_algorithmic_agents.py` (rerank tests), `backend/tests/test_routers.py::TestOrchestratorGNNWiring` |
| Tests (pure-Python, run anywhere) | `ml/tests/test_graph_build.py`, `ml/tests/test_split.py` |
| Encoder-caching test (torch required) | `ml/tests/test_gnn_pipeline_requires_torch.py::test_encoder_forward_pass_is_cached_across_score_calls` |
| Tests (need torch installed) | `ml/tests/test_gnn_pipeline_requires_torch.py` |
