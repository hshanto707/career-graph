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

**Honest caveat #1 — data scale.** At the time this model was last trained, the graph was built from the *original small seed fixture* (165 jobs, 75 skills, 3 demo students, 30 courses), not the 10,000-row synthetic dataset generated afterward. **This is the single most important thing to say proactively in the defense**: the pipeline is fully built, tested, and proven correct, but the reported numbers below are from the small fixture and need to be re-run against the 10k-row dataset before being called final thesis numbers. (See §9 "What to do before defense.")

**Honest caveat #2 — `LEADS_TO` has no real data source.** Nothing in the ingestion pipeline ever produces genuine skill-prerequisite edges (no dataset defines "Python leads to Machine Learning" style progressions). `LEADS_TO` edges are **synthesized** by a placeholder heuristic (skills in the same O*NET category are chained alphabetically) purely so the link-prediction task has *something* to train/evaluate on for that edge type. This is explicitly documented as a stand-in, tracked as Future Work. If asked "where does your prerequisite graph come from," the honest answer is: it doesn't exist as real data yet — this is the model correctly learning to predict a synthetic, heuristic ordering, not a validated pedagogical curriculum.

Graph size actually exported and trained on:

| Node type | Count | Edge type | Count |
|---|---|---|---|
| Student | 3 | `HAS_SKILL` | 11 |
| Skill | 75 | `REQUIRES` | 714 |
| Job | 165 | `LEADS_TO` (synthetic) | 56 |
| Course | 30 | `TEACHES` | 37 |
| Category | 8 | `IN_CATEGORY` | 165 |

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

**What actually happened when trained:** loss went from **1.39 → 0.016** over 60 epochs — the model is clearly learning to separate real from fake edges on the training data (this is a "does it learn at all" sanity signal, not itself a generalization claim — that's what the held-out test metrics in §7 are for).

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

## 8. Actual results (small seed graph — see honest caveat in §4 and §9)

| Edge Type | Model | AUC-ROC | Hits@10 | MRR | #test_pos | #test_neg |
|---|---|---|---|---|---|---|
| Job→REQUIRES→Skill | GNN (GraphSAGE) | 0.927 | 0.873 | 0.651 | 71 | 71 |
| Job→REQUIRES→Skill | Algorithmic baseline | 0.975 | 1.000 | 0.765 | 71 | 71 |
| Skill→LEADS_TO→Skill | GNN (GraphSAGE) | 0.306 | 1.000 | 0.442 | 6 | 6 |
| Skill→LEADS_TO→Skill | Algorithmic baseline | 0.500 | 1.000 | 1.000 | 6 | 6 |

### How to talk about these numbers honestly (this is the actual defense answer)

**The baseline currently wins on REQUIRES, and both models are near-meaningless on LEADS_TO.** Do not hide this — state it proactively, then explain *why*, which is the more impressive part:

1. **Why the baseline wins at this scale:** 165 jobs / 75 skills is a small, dense graph. A Jaccard/co-occurrence baseline directly reuses the ground-truth structure (two jobs are "similar" precisely because they share required skills — that's almost the definition of the task). A learned encoder has to *discover* that pattern from noisy embeddings with only 60 epochs of training on ~570 training edges. At this scale, hand-crafted structural similarity is a very strong, hard-to-beat baseline — this is expected and is exactly what the literature review's precedents predict (Node2Vec/GNN approaches consistently show their advantage emerging at scale — thousands to hundreds of thousands of edges — not at n=165).
2. **Why LEADS_TO numbers are close to meaningless:** only **6 test positive edges** exist for that relation. Six data points cannot support a statistically reliable AUC-ROC estimate (a single flipped comparison swings AUC by ~0.17). This is a sample-size problem, not a model-quality problem, and is compounded by `LEADS_TO` being synthetic/heuristic data in the first place (§4).
3. **What this section of the pipeline *does* prove:** the full pipeline — graph export, leakage-safe splitting, negative sampling, training, checkpointing, evaluation, and a fair head-to-head comparison — is built correctly, runs end-to-end, and is reproducible (fixed seeds throughout). That is the defensible claim right now: **"the machinery is correct and proven; the current numbers are a pipeline-correctness demonstration on a small fixture, not yet the thesis's final scaled result."**

If an examiner pushes on "so does the GNN actually help or not" — the honest, prepared answer is: *"On this small fixture, no — the algorithmic baseline wins, which is itself an expected and informative result consistent with the literature. The full evaluation infrastructure is built to re-run unchanged against the real 10,000-job dataset, where the literature's precedents (and general link-prediction scaling behavior) predict the GNN should close or reverse this gap, because a learned encoder generalizes to unseen skill/job combinations in ways a purely lexical Jaccard-overlap score structurally cannot. That re-run is the next step, not yet done."*

---

## 9. What to do before defense (in priority order)

1. **Retrain and re-evaluate against the 10,000-row dataset** generated after this model was last trained (`backend/data/kaggle_jobs.csv`, 518-skill taxonomy). This requires no new code — `ml/graph_build.py`/`export_graph.py` need to point at the real ingested 10k-job graph instead of the small seed fixture, then `python ml/train_gnn.py && python ml/evaluate.py` re-run as-is. This is the single highest-value action: it turns "pipeline-correctness numbers" into "thesis-defense numbers," and per the literature precedent, is where the GNN has a real chance to outperform the baseline.
2. **Decide and document a real (even if simple) `LEADS_TO` data source** — e.g., derive prerequisite pairs from course curricula order, or from co-occurrence-plus-difficulty heuristics — rather than the current alphabetical-within-category placeholder, so that edge type's evaluation is meaningful rather than a small-sample artifact.
3. **Re-run with the environment properly installed** (`ml/requirements.txt`: torch, torch_geometric, scikit-learn) — confirmed installable and previously run successfully (torch 2.13.0, torch_geometric 2.8.0, scikit-learn 1.9.0), but must be re-verified in whatever machine will run the final numbers.
4. Optionally: run 2-3 different seeds and report mean ± spread for the metrics, to preempt "how do you know this isn't just luck on one random split" — the split/training code is already seed-parameterized, so this is a rerun, not new code.

---

## 10. How it's wired into the live system (graceful degradation)

**File:** `backend/app/engine/algorithmic/gnn_recommendation_agent.py`.

The GNN is **optional infrastructure**, following the exact same design pattern as the pluggable LLM providers:
- If no checkpoint file exists, or torch isn't installed, constructing the agent never raises an error — it just reports `is_available = False` with a human-readable `unavailable_reason`.
- Scoring methods return `None` (never crash) if unavailable, or if a candidate node wasn't seen during training (e.g., a brand-new skill added after training).
- A `score_requires_with_fallback()` helper lets any caller pass an algorithmic score to fall back to, and get back `(score, source)` where `source` tells you whether the number came from `"gnn"` or `"algorithmic"`.

**Why this matters for the defense:** it means the GNN is a genuine enhancement layer, not a single point of failure — the whole system (including its test suite) is designed to keep working correctly even if the model were deleted, un-trained, or simply not present in a given deployment. This mirrors the system's overall design philosophy (stated in `system-design.md`) that the LLM is also optional and the system degrades gracefully without it.

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
A: No — it means the baseline is strong at this data scale, which is an expected, literature-consistent result, and the comparison methodology (identical test edges, real production baseline logic, reproducible seeds) is exactly what makes that an honest, informative finding rather than a hidden failure. The pipeline is built to be re-run at 10x-plus the current scale, which is where a learned encoder is expected to start winning.

**Q: What's the biggest limitation of this work?**
A: Two, stated together: (1) the dataset it was evaluated on is small and (until retrained) synthetic-at-small-scale rather than the newly generated 10k-row synthetic dataset or real-world data, and (2) the `LEADS_TO` (skill-prerequisite) relation has no real data source at all yet — it's a documented placeholder heuristic. Both are explicitly tracked, not hidden, and neither requires new architecture to fix — just more/better data and a rerun.

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
| Live-system integration (graceful fallback) | `backend/app/engine/algorithmic/gnn_recommendation_agent.py` |
| Tests (pure-Python, run anywhere) | `ml/tests/test_graph_build.py`, `ml/tests/test_split.py` |
| Tests (need torch installed) | `ml/tests/test_gnn_pipeline_requires_torch.py` |
