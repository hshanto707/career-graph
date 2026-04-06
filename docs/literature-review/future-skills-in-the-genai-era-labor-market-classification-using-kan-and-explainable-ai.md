# Future Skills in the GenAI Era: A Labor Market Classification System Using Kolmogorov–Arnold Networks and Explainable AI

**Authors:** Dimitrios Christos Kavargyris, Konstantinos Georgiou, Eleanna Papaioannou, Theodoros Moysiadis, Nikolaos Mittas, Lefteris Angelis  
**Year:** 2025  
**Published in:** Algorithms, Volume 18, Issue 9, Article 554 — MDPI (Horizon Europe SKILLAB Project)

---

## Problem Statement

Generative AI has fractured what used to be a single labor market category — "AI roles" — into two meaningfully different populations: roles that require traditional machine learning and statistical skills, and roles that require GenAI-specific competencies like prompt engineering, LLM integration, and RAG pipelines. Hiring managers, educators, and workforce planners urgently need to understand which skills belong to which category, and how fast this divide is widening.

The problem is that existing skill taxonomies like ESCO are too slow to update. By the time a new skill enters the official taxonomy, the market has moved on. Manual classification is impractical at scale. And most classification models are black boxes that cannot explain *why* a job is classified as GenAI-facing — which matters when you are using the output to redesign university curricula or national reskilling programs.

This paper introduces KANVAS (Kolmogorov–Arnold Network Versatile Algorithmic Solution), a framework that does three things simultaneously: classifies job postings as traditional AI or GenAI-facing, achieves approximately 80% accuracy doing so, and makes every classification decision interpretable through SHAP-based attribution of individual skill contributions.

## Key Contributions & Objectives

1. Introduces KANVAS — the first application of Kolmogorov–Arnold Networks (KANs) as an explanatory tool for labor market classification, combining B-spline-based neural units with SHAP for per-skill interpretability.
2. Collects 9,357 Online Job Advertisements (OJA) from LinkedIn and Kariera (EU countries, January 2023–May 2025) covering both traditional AI and GenAI-oriented roles.
3. Uses llama3:8b as an LLM-based labeling agent to annotate job postings as "modern" (GenAI-related) or "traditional" — achieving 83% agreement with a human gold standard.
4. Identifies the key discriminating skills: GenAI roles prioritize prompt engineering, LangChain, AI Agents, and Language Models; traditional roles anchor on SAS, DevOps, statistics, and Python.
5. Builds the KANVAS Job Analyzer — a Gradio-powered interactive HR tool that explains individual job classifications using SHAP radar plots and skill gap diagnostics.
6. Highlights that the traditional-to-GenAI transition does not require radical skill replacement: foundational skills like Machine Learning and scientific computing serve as bridges.

## Methodology / Theory / Framework

KANVAS runs a four-phase pipeline. Phase I collects OJA using a custom Python crawler, with skills extracted via two parallel tools: ESCOX (ESCO-aligned skill extractor for traditional roles) and a manually curated 226-skill Lightcast GenAI lexicon. Phase II uses llama3:8b with a carefully engineered prompt to label each job as "modern" or "traditional" — validated against 100 human-annotated examples from three independent annotators (unanimity required). Phase III trains a KAN on multi-hot encoded skill vectors. KANs replace static MLP activation functions with learnable univariate B-spline functions along edges, making each skill's contribution to the classification output mathematically tractable. Phase IV applies SHAP (Shapley Additive Explanations) to produce global and local skill attribution — summarizing which competencies most strongly push a classification toward modern or traditional.

An 80/20 stratified train-test split was applied. Weighted random sampling handled the class imbalance (58.49% traditional, 41.51% modern).

## Software Tools / Setup Details

- KANs implementation via PyKAN, adapted in Google Colab Pro with NVIDIA A100 GPU (83 GB RAM)
- ESCOX tool for ESCO-aligned skill extraction from traditional AI job postings
- llama3:8b (Ollama) for LLM-based role labeling (compared against deepseek-r1, mistral:instruct)
- deep_translator (GoogleTranslator) for multilingual OJA translation to English
- SHAP library for Shapley-based feature attribution
- Gradio frontend for KANVAS Job Analyzer interactive interface
- Code: https://github.com/dkavargy/KANVAS
- Dataset: 9,357 OJA from LinkedIn and Kariera (EU, Jan 2023–May 2025); 5,473 traditional, 3,884 modern

## Test / Experiment Analysis

Two validation stages. First, llama3:8b was evaluated against a 100-job human gold standard (three annotators, unanimous agreement required): 83% accuracy, outperforming all other LLMs tested (deepseek-r1:latest at 82%, mistral:instruct at 78%). Second, the KAN was benchmarked against seven classical classifiers (Logistic Regression, Decision Tree, Random Forest, Naive Bayes, KNN, SVM, Gradient Boosting) on accuracy, F1, precision, recall, and ROC AUC. SHAP stability was tested across five random seeds and bootstrap resampling — top 10 skills were 100% consistent across seeds.

## Test Data / Dataset Source

9,357 OJA collected from LinkedIn and Kariera (Greece-based international job portal), covering EU countries, January 2023–May 2025. No personally identifiable information; GDPR-compliant. Human gold standard: 100 unanimously annotated job descriptions.

## Final Result

The KAN model achieves **79% accuracy** (test set of 1,872 samples), **ROC AUC = 0.86**, macro F1 = 0.78. KANs marginally outperform all seven classical baselines including SVM (0.79 accuracy, 0.84 AUC) and Random Forest (0.79 accuracy, 0.89 AUC). The llama3:8b labeler achieves 83% accuracy against human annotations — outperforming larger models including deepseek-r1 variants.

SHAP analysis reveals: the top modern-role signal skills are Machine Learning, Deep Learning, AI Agents, Language Models, and LangChain. The strongest traditional-role signals are SAS Certified ModelOps Specialist, Qdrant, DevOps, and statistics. Notably, Machine Learning and scientific computing appear in both groups — acting as bridges for traditional-to-GenAI career transitions rather than as barriers.

**What works well here:** KANVAS is the cleanest demonstration in the literature that ESCO-aligned skills and GenAI-specific skills are now meaningfully separable by a classifier — and that this separation is interpretable enough to be actionable. The human annotation validation with inter-annotator unanimity is methodologically rigorous. The finding that LangChain, AI Agents, and prompt engineering are the key discriminators of GenAI roles in the EU labor market is an empirical result that curriculum designers can act on immediately. The KANVAS Job Analyzer is a practical HR tool, not just an academic exercise.

## Limitations

The 9,357-job dataset is drawn entirely from two platforms focused on data science and AI-heavy roles, with limited representation from healthcare, education, manufacturing, or the humanities. The findings may not generalize to sectors where GenAI adoption is at an earlier stage. The GenAI lexicon was manually curated by the authors, introducing subjective bias — and it may already be outdated given how fast GenAI tooling evolves (the 226-skill list may miss current skills like Cursor, Claude Agents, or Gemini Flash). The 17% LLM annotation noise is acknowledged but not corrected — it propagates into the KAN's training signal. The KAN's marginal performance advantage over SVM and Random Forest raises a real question: is the interpretability gain worth the additional complexity of KAN training?

**The deeper limitation:** KANVAS identifies skill profiles of job postings — it does not model individual workers. It can tell an employer that their job posting is "traditional" and should add prompt engineering, but it cannot tell a student with a specific current skill set which skills they personally need to close the gap to a modern role. The classification is job-centric, not student-centric.

## Final Summary

KANVAS is a methodologically sophisticated and practically oriented contribution to labor market intelligence. The combination of KANs and SHAP for explainable job role classification is novel, the EU job posting dataset is substantial, and the practical HR tool demonstrates real deployment intent. The skill-level findings — that prompt engineering, LangChain, and AI Agents are the key markers of GenAI roles — are immediately useful for curriculum and reskilling program design.

**How CareerGraph does better:** KANVAS classifies jobs and explains which skills distinguish role types. CareerGraph goes further by connecting this market intelligence directly to individual students. Our SkillGapAgent computes a personalized readiness score against a specific target job — using the student's current HAS_SKILL edges and proficiency weights, not just a population-level classification. Our NormalizationAgent would handle the GenAI taxonomy coverage gap KANVAS identifies: since we map all skills to O*NET/ESCO with fallback synonym resolution, emerging skills like LangChain and prompt engineering are normalized as they appear in job postings without requiring manual lexicon updates. And our MarketAgent already surfaces demand frequency signals equivalent to KANVAS's SHAP feature importance — telling students which skills in their gap have the highest market demand at the population level, while our SkillGapAgent tells them what it means for *their specific profile*.
