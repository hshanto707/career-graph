# Discussion

> Thesis Discussion chapter draft, per `docs/current-status.md` Milestones
> 3 and 5. Companion to `docs/evaluation-chapter.md` (the results this
> chapter interprets), `docs/data-sources.md` (data provenance detail),
> `docs/gnn-defense-guide.md` (GNN-specific honest results),
> `docs/research-contribution.md` (what the project *does* claim, for
> contrast). Every claim below is grounded in what's actually in this
> repo — no numbers here are invented for the occasion.
>
> **Framing for the defense:** every limitation below is disclosed
> proactively, not extracted under questioning. That's deliberate — a
> reviewer trusts a system more, not less, when its authors can state
> exactly where it's weak and why.

---

## Synthesis of findings

Three separate questions were evaluated (`docs/evaluation-chapter.md`),
and they warrant three separate verdicts rather than one blended
impression:

**Is the software correct and well-engineered?** Yes, with strong
evidence: 195 backend tests, 85 frontend tests, and 29 ML pipeline tests,
all passing, covering red/green cases and documented edge cases
per-module (`docs/test-plan.md`). More importantly, that test coverage was
proven to matter in practice, not just in principle — real bugs were found
and fixed throughout hardening (`docs/implementation-chapter.md` §4),
including one (the GNN's disk-write side effect crashing under a
read-only mount) that only a real, production-shaped deployment caught, no
unit test having constructed that scenario. The system's graceful-degradation
architecture — the LLM and the GNN both being individually optional
without breaking anything else — was exercised for real throughout the
build, not just designed for.

**Does the trained model add value?** The honest answer is *not on the
metric the thesis originally hoped it would* (`REQUIRES` link prediction,
where the hand-tuned Jaccard/co-occurrence baseline wins on all three
reported metrics), but *yes on a different, real one*: the model is
successfully integrated into a live request path via a retrieve-then-rerank
architecture, demonstrably influences real recommendations
(`match_source: "gnn"` verified against a real deployment, not a mock),
and shows a genuine, non-tautological learning signal on `LEADS_TO`
(AUC-ROC 0.679 vs. a random-chance 0.500 baseline) despite that relation's
ground truth itself being synthetic. The contribution is therefore best
framed as: *a correctly-built, rigorously-evaluated, honestly-reported
learned model that is actually in production* — not as "a model that beats
the baseline," which would overstate one metric and understate the
engineering result of the integration itself.

**Is this a fair test of what GNN-based career-graph link prediction can
do?** Only partially, and that partial-ness is the throughline connecting
every limitation below: the dataset is synthetic, the `LEADS_TO` ground
truth is a hand-authored heuristic, and the LLM narration layer — while a
deliberate scope choice, not an oversight — means one documented capability
of the architecture has never been exercised against a real provider. None
of these limitations required re-architecting anything to disclose or to
plan a fix for; each has a concrete, scoped path to being closed
(`docs/data-sources.md`, `docs/current-status.md`'s milestone plan), which
is itself part of the contribution: an honestly-scoped system with a
credible path forward, rather than a system whose limitations were
discovered only under defense questioning.

---

## Limitations

## 1. The dataset is synthetic, not real-world data

`backend/data/kaggle_jobs.csv` (10,000 rows), `onet_skills.csv` (518
skills), and `synonyms.json` (215+ aliases) are generated fixtures, not the
real Kaggle job-postings dataset or the real O*NET/ESCO skill taxonomy
originally scoped in `system-design.md` §10. This is a stated project
decision (`docs/current-status.md` Milestone 3, 2026-08-06), made under
project timeline constraints, not an oversight discovered late.

**What this does and doesn't undermine:**

- It does **not** undermine the correctness of the ingestion pipeline
  (`IngestionAgent` → `NormalizationAgent`), the knowledge-graph schema, the
  four algorithmic agents, or the GNN training/evaluation machinery — all of
  that is proven correct against data at the intended target *scale and
  shape* (10,000+ postings, 500+ skill taxonomy per `system-design.md`),
  which is exactly what those components need to be exercised meaningfully.
  Swapping in a real CSV of the same shape would not require touching any
  of that code.
- It **does** undermine any claim that the specific skill-demand numbers,
  job-title distributions, or salary ranges reported by `MarketAgent`
  reflect the actual current job market — they reflect a generated
  approximation of one. A student using this system today would be getting
  gap analysis against synthetic market signals, not real employer demand.
- The synthetic generation process (`backend/data/generators/*.py`, 10
  domain-specific scripts, fixed seeds, documented in
  `docs/data-sources.md`) was designed to be *realistically shaped* —
  plausible job titles, skill co-occurrence patterns, salary ranges — but
  "plausible" is not "real," and a domain expert would likely be able to
  tell the difference on close inspection.

**What real data would take:** `docs/data-sources.md` already documents
concrete next steps (a specific Kaggle job-postings dataset, O*NET's
`Technology Skills.txt`/`Skills.txt` flat files or the ESCO skills export,
and a skill-extraction pre-processing step most Kaggle job datasets need
since they don't ship a clean `skills_required` column). None of this is
hypothetical hand-waving — it's a scoped, described follow-up.

## 2. `LEADS_TO` (skill prerequisite) edges have no real data source

The `Skill-[:LEADS_TO]->Skill` relationship — which drives both
`PathFinderAgent`'s roadmap ordering and `RecommendationAgent`'s partial-credit
scoring — has never had a real data source, synthetic or otherwise, until
`ml/graph_build.py` synthesized one: skills within the same O*NET category,
chained alphabetically. This is clearly labeled in that module's own
docstring as a placeholder, not disguised as real.

This matters most for the GNN evaluation: the `LEADS_TO` link-prediction
task (`docs/gnn-model.md` §8) is being evaluated against ground truth that
is itself an arbitrary heuristic, not a real prerequisite relationship. The
algorithmic baseline's near-perfect Hits@10/MRR on this task (1.000/1.000)
is not evidence of a good prerequisite model — it's the baseline directly
reconstructing a deterministic alphabetical rule it has full visibility
into, which is tautological, not generalization. The GNN's improved AUC-ROC
with scale (0.306 → 0.679, see `gnn-defense-guide.md` §8) is a more
interesting result precisely because it demonstrates the model learning
*something* from graph structure despite the synthetic target, but neither
number should be read as "how good is this system at sequencing a real
learning path."

**What real data would take:** curriculum/course-sequencing order (e.g.
prerequisite chains already encoded in structured course catalogs), or
historical career-progression data (skill B commonly acquired after skill A
across real career trajectories) — both tracked as Future Work in
`system-design.md` §2 ("Advanced ranking models") and `project-roadmap.md`.

## 3. The trained GNN does not outperform the hand-tuned baseline on `REQUIRES`

At the full 10,000-job/434-skill scale, `RecommendationAgent`'s Jaccard/
co-occurrence heuristic beats the trained GraphSAGE model on all three
metrics for `Job-REQUIRES->Skill` link prediction (AUC-ROC 0.961 vs 0.937,
Hits@10 0.116 vs 0.014, MRR 0.067 vs 0.012 — `docs/gnn-model.md` §8). This
directly contradicts the literature-precedent hope (de Groot et al.,
Vultureanu-Albisi et al. — see `docs/literature-review.md`) that GNN-style
approaches would close or reverse this gap at scale.

The most likely explanation, consistent with that same literature: the
positive-edge density per skill is sparse relative to the size of the
candidate pool (5,429 test positives against 5,429 negatives, but each
individual skill has comparatively few REQUIRES edges to learn from), which
favors a heuristic that directly reuses ground-truth co-occurrence
structure over an embedding model trained from scratch with no richer input
features than a learned embedding table per node. This is disclosed as a
finding, not hidden — `docs/gnn-defense-guide.md` §8 walks through the
full reasoning and is the prepared answer for defense Q&A on this point.

**What would plausibly close the gap:** richer input node features (e.g.
text embeddings of job descriptions, rather than learned-from-scratch
embedding tables), more training epochs with a learning-rate schedule, or
simply more real (non-synthetic) positive examples per skill — none of
which were pursued in this phase given the milestone's actual point
(proving the pipeline is correct and reproducible at target scale), not
chasing a specific benchmark number.

## 4. Single-region, English-only job market

All synthetic job postings use US/Canada-style locations, English job
titles, and USD salary ranges. `system-design.md` §2 explicitly scopes
"Multi-region analysis" as Post-Capstone — this is a known, always-intended
limitation, not a surprise, but is stated here for completeness since it
compounds with limitation #1: even a real Kaggle dataset swapped in without
further work would likely still be single-region/English-dominant (most
public Kaggle job-postings datasets skew US-centric), so multi-region
support is a separate, larger effort from the "get real data" work in §1.

## 5. The LLM narration layer has never been exercised against a real provider

`ReasoningAgent`'s four narrative methods (`explain_gap`,
`narrate_recommendations`, `write_roadmap`, `summarize_market`) are fully
implemented and unit-tested, but only against mocked LLM responses —
`LLM_PROVIDER=none` in the live configuration, so every explanation a user
has ever seen is the deterministic template fallback, not real Claude/GPT
output. Unlike the other items in this section, this is a **deliberate
scope decision, not a resource constraint** (`docs/current-status.md`
Milestone 2): the LLM never scores, ranks, or predicts anything — it is a
strictly optional narration layer over results the algorithmic agents/GNN
have already computed, per `docs/research-contribution.md` Contribution 3.
Running LLM-free is itself evidence that the system's graceful-degradation
claim is real and exercised, not merely asserted. The limitation this
creates is narrow: no example exists yet of what a *real* LLM-generated
explanation reads like, only the template's.

## Threats to validity

- **Internal validity (does the system measure what it claims to?):** the
  GNN-vs-baseline comparison (`docs/gnn-model.md`) uses a leakage-safe edge
  split (`ml/tests/test_split.py` explicitly asserts train/val/test
  disjointness, and val/test positives are excluded from message passing,
  not just the loss) and identical held-out test edges for both models
  (`ml/evaluate.py` builds one `splits` object, passed to both evaluators) —
  this is a real, defensible internal-validity control, not asserted
  without evidence.
- **External validity (does it generalize beyond this dataset?):**
  weakened directly by limitations #1 and #4 above — results on a
  synthetic, single-region, English-only corpus may not transfer to a real,
  global, multi-language job market without re-validation.
- **Construct validity (is "skill demand" / "readiness score" measuring the
  right thing?):** `MarketAgent`'s demand score is a normalized REQUIRES-edge
  count, a reasonable proxy for demand but not validated against any
  external ground truth (e.g. real job-board posting volume, real salary
  correlation) — this is true independent of the synthetic-data question
  and would remain a construct-validity question even with real data,
  unless demand scores were separately validated against an authoritative
  source.
- **Reproducibility (is any of this a one-off, lucky result?):** every
  stochastic step in the pipeline (data generation, train/val/test split,
  negative sampling, model initialization) is seeded (`seed=42` used
  consistently throughout `ml/`), and the GNN checkpoint/evaluation report
  were independently reproduced at noise-level precision on a second run
  (`docs/gnn-model.md` §8, 2026-07-18 vs 2026-08-06) — this is a genuine
  strength, not a threat, and worth stating as such rather than only
  listing weaknesses in this section.

## Summary for defense

If asked to summarize this section in one breath: *the system's software
architecture, agent logic, and GNN training/evaluation methodology are all
correct and proven at the intended scale; what's not yet real is the
underlying data (synthetic job postings and skill taxonomy) and one
relationship (`LEADS_TO`) that has no real-world source at all. Both are
disclosed, both have a concrete documented path to being closed
(`docs/data-sources.md`), and neither requires re-architecting anything —
only re-running an already-correct pipeline against better inputs.*
