# Explainable Person-Job Recommendations: Challenges, Approaches, and Comparative Analysis

**Authors:** Fang Tang, Renqi Zhu, Feng Yao, Junzhi Wang, Lailong Luo, Bo Li  
**Year:** 2025  
**Published in:** Frontiers in Artificial Intelligence — DOI: 10.3389/frai.2025.1660548 (Published October 9, 2025)

---

## Problem Statement

Person-job recommendation systems (PJRS) now mediate a growing fraction of all hiring decisions, yet most operate as black boxes: they match candidates to jobs without being able to say why a match was made or why a candidate was ranked below another. For jobseekers, this creates a trust problem — the system's outputs feel arbitrary and unexplainable when they need to be actionable. For recruiters, it creates a liability problem — bias in screening algorithms (gender, race, age) cannot be identified or corrected if the decision process is opaque. For system developers, it creates a regulatory problem — EU AI Act transparency requirements are now bearing directly on hiring tools.

Person-job matching has specific complexities that set it apart from generic recommendation (movie ratings, product suggestions): it is bilateral (both the candidate and the recruiter have preferences and requirements), the inputs are long-form documents (resumes, job descriptions) rather than ratings, and the consequences of an unexplained decision are high-stakes in ways that a missed movie recommendation is not. Existing XAI reviews cover general recommender systems; none systematically addresses PJRS-specific explainability challenges and methods.

## Key Contributions & Objectives

1. The first systematic review of explainability methods in person-job recommendation systems — 85 papers, January 2019–August 2025, following PRISMA 2020 guidelines with inter-rater agreement Krippendorff's α = 0.87.
2. A six-type taxonomy of "black box issues" in PJRS: invisibility of feature extraction, lack of transparency in weight assignment, invisibility of model decisions, uncertainty in parameter adjustments, data bias/discrimination, and inexplicability of prediction results.
3. A three-layer integrated framework organizing explainability methods by where in the pipeline they operate: data layer (feature transparency), model layer (decision visibility), and output layer (result explanation).
4. Quantitative benchmarking of six representative explainability method families — SHAP, LIME, attention-based, KG-enhanced GNNs, counterfactual explanations, and Explainable Boosting Machines (EBM) — on four metrics: HR@10, fidelity, sparsity, and user trust, combined into a composite E-P (Explainability-Performance) score.
5. Evidence-based context-specific guidance: which method to use for which deployment scenario, given the accuracy-interpretability tradeoffs in each.
6. Seven priority future directions: multimodal data integration, causal inference, dynamic preference modeling, computational efficiency, data sparsity handling, user feedback loops, and visualization tooling.

## Methodology / Theory / Framework

The systematic review followed PRISMA 2020 guidelines. Three databases were searched (Google Scholar, Web of Science, CNKI) using precision Boolean queries requiring presence of explainability/XAI terms combined with PJRS-specific terms, with explicit exclusion of e-commerce and movie recommendation papers to reduce noise. Two independent coders performed open and axial coding on the 85 included studies; an expert panel of three domain specialists validated the three-layer taxonomy. The benchmarking table (Table 4) compiles performance data from the reviewed literature rather than running new experiments — it synthesizes reported metrics into a standardized comparison.

The three-layer framework distinguishes: (1) data layer methods that make feature extraction transparent (attention heatmaps, causal attribution, neural visualization); (2) model layer methods that make the decision process visible (KG path reasoning, KG embedding, RL-based path selection, fairness-aware training); (3) output layer methods that explain results to end users (SHAP, LIME, natural language generation, counterfactual "what-if" explanations). Cross-layer hybrids — combining, for example, KG-enhanced GNNs with SHAP output explanations — achieve the best overall performance.

## Software Tools / Setup Details

Methods surveyed include: LIME, SHAP, attention mechanisms, KG-enhanced GNNs, RL with policy-guided paths, EBMs, causal inference pipelines, GANs (for fairness), NLG for explanation generation. Datasets appearing in reviewed papers include Zhaopin.com (100k+ Chinese job postings), CareerBuilder, LinkedIn-style datasets, and FairRec (fairness benchmark). No new software or datasets were created for this review.

## Test / Experiment Analysis

The benchmarking table synthesizes reported metrics from the 85 reviewed papers into a standardized comparison across six method families on four dimensions. The composite E-P scores are computed by the review authors, not drawn from a single study.

| Method | HR@10 | Fidelity | Sparsity | User Trust | E-P Score |
|---|---|---|---|---|---|
| SHAP | 0.95 | 1.00 | 0.50 | 0.70 | 0.79 |
| LIME | 0.95 | 0.80 | 0.90 | 1.00 | 0.91 |
| Attention-based | 0.90 | 0.85 | 0.80 | 0.80 | 0.84 |
| KG-enhanced GNN | 1.00 | 0.90 | 0.80 | 0.90 | 0.90 |
| Counterfactual | 0.95 | 0.95 | 1.00 | 0.90 | **0.95** |
| EBM | 0.85 | 1.00 | 0.70 | 0.95 | 0.88 |

Additional findings: KG-enhanced methods improve rating prediction accuracy by 12% but drop 20-30% in coverage with incomplete graphs. Attention mechanisms show unstable weight distributions across independent runs. Causal methods improve equity scores by 15% on FairRec but carry 2-3× runtime overhead. Deep models sacrifice 20-30% user trust in sparse data settings.

## Test Data / Dataset Source

Systematic review meta-analysis: 85 papers from 150 screened, across Google Scholar, Web of Science, and CNKI. Timeframe: January 2019–August 2025. No new dataset collected.

## Final Result

Counterfactual explanations achieve the highest composite E-P score (0.95), outperforming all other methods by balancing prediction quality (HR@10 = 0.95), fidelity to the underlying model (0.95), explanation sparsity/parsimony (1.00), and user trust (0.90). LIME achieves the highest user trust (1.00) but at the cost of lower fidelity (0.80). KG-enhanced GNNs achieve the highest HR@10 (1.00) and strong trust (0.90) but require high-quality structured data. The key cross-cutting finding is that hybrid cross-layer methods can achieve ≥20% explainability gains at ≤10% accuracy loss — so the accuracy-interpretability tradeoff is not as sharp as commonly assumed, if the right architecture is chosen.

**What works well here:** This is the most comprehensive synthesis of explainability methods for hiring AI in the current literature. The three-layer taxonomy is a clean organizing principle that forces distinctions between transparency at the data ingestion stage, the model reasoning stage, and the output presentation stage — three very different kinds of explainability that are often conflated. The finding that attention mechanisms are unreliable as explanations (unstable weight distributions across runs, tendency to overweight frequent but uninformative terms) is an important and honest warning for systems that depend on attention visualization. The counterfactual result — that "what would need to change for this decision to be different?" is the most trusted and informative explanation type — has direct implications for career guidance systems.

## Limitations

The protocol was not pre-registered before the review began, which introduces a risk of unintentional selection bias toward positive results. The temporal cutoff (2019–August 2025) excludes foundational pre-2019 work on recommendation explainability. The review covers English and Chinese literature (via CNKI) but likely misses contributions from Portuguese, Arabic, and other language academic communities. The benchmarking table synthesizes metrics reported across heterogeneous studies using different datasets and evaluation protocols — the composite E-P score is a useful heuristic but should not be interpreted as a definitive head-to-head comparison. Attention mechanisms are critiqued but their limitations in PJRS-specific long-document contexts are not distinguished from their behavior in other tasks.

**The structural gap:** This review covers explainability of matching between an existing candidate profile and existing job posting — it does not address career development guidance: explaining to a student which skills to acquire, in what order, to improve their match to a future job they do not yet qualify for. The gap analysis and learning path recommendation side of career guidance is outside the scope.

## Final Summary

This systematic review is the most thorough available map of explainability methods for person-job recommendation systems. Its three-layer taxonomy, benchmarking table, and context-specific method guidance provide a clear decision framework for any developer building hiring AI that needs to explain itself — whether for user trust, regulatory compliance, or bias auditing.

**How CareerGraph does better:** CareerGraph's explainability strategy is informed by exactly the lesson this review identifies — that the highest-trust explanation type is counterfactual ("what needs to change?"), not attention heatmaps or SHAP waterfall charts. Our ReasoningAgent generates natural language explanations grounded in real job market data: "You are missing LangChain, which appears in 43% of GenAI engineer postings in our dataset. Adding it would increase your readiness score from 0.62 to 0.74." That is a counterfactual-style explanation — specific, verifiable, and actionable — without the runtime overhead this review documents for LIME and formal counterfactual methods. Our PathFinderAgent's LEADS_TO traversal also implements the KG-path reasoning that this review identifies as the highest HR@10 approach, but grounds it in prerequisite semantics rather than user-interaction history, which avoids the data sparsity problem that KG-enhanced GNNs struggle with in cold-start scenarios.
