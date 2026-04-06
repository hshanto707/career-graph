# Skill Demand Forecasting Using Temporal Knowledge Graph Embeddings

**Authors:** Yousra Fettach, Adil Bahaj, Mounir Ghogho  
**Year:** 2025  
**Published in:** arXiv preprint arXiv:2504.07233 (submitted to Elsevier) — Ghent University / University Mohammed VI Polytechnic / University of Leeds

---

## Problem Statement

The labor market doesn't stay still. Skills that were highly demanded five years ago are declining; new skill requirements appear as industries evolve. Most existing skill recommendation and gap analysis systems treat the labor market as a static snapshot — they tell you what skills are in demand right now, based on current job postings. What they can't tell you is where demand is heading.

This paper asks a harder question: can we predict which skills will become more or less demanded in the future, for specific job titles, before that shift has fully materialized in the data? The authors reframe this as a temporal knowledge graph (TKG) link prediction problem — predicting future edges in a job-skill graph based on historical edge patterns — rather than a time series forecasting problem. This framing is important because time series methods require continuous quantitative demand signals, which are sparse for many skills. TKG forecasting is self-supervised and can reason about emerging skills that have no prior demand history.

## Key Contributions & Objectives

1. Introduces T-JobEdKG, a novel temporal knowledge graph constructed from 99,676 Moroccan job postings (Rekrute.com, 2005–2022) and 10,180 Coursera courses — claimed to be the only temporal KG on job-skill evolution in the literature.
2. Formalizes skill demand forecasting as temporal KG link prediction: given past quadruples `(job, requires, skill, timestamp)`, predict which job-skill links will form in the future.
3. Benchmarks five temporal KG embedding models (DE-TransE, DE-DistMult, TA-TransE, TA-DistMult, Tero) on the T-JobEdKG, with thorough hyperparameter search.
4. Publishes a case study showing temporal demand trajectories for specific skills like "data analysis" and "Java" across IT job titles, including forecasted demand through 2025.
5. Releases code as TempTorchKGE — an adaptation of TorchKGE for temporal KGs that uses bulk matrix operations for efficiency.

## Methodology / Theory / Framework

T-JobEdKG is built from the source JobEdKG (Fettach et al., 2024), extended to include timestamps. Each fact in the graph is a quadruple `(head, relation, tail, timestamp)` where the timestamp marks when the fact first appeared in job postings. The graph contains 55,718 nodes and 1,296,374 relations across 12 types (requires, co-occurs_with, provides, favors, belongs_to, etc.). Entity types include 9,736 job titles, 32,824 hard skills, 21 soft skills, 10,180 courses, 133 sectors, 2,714 recruiters.

The temporal link prediction task is: given historical facts before time `τ_k`, predict future facts at `τ_k`. Five models are compared — two families: diachronic embedding (DE), where temporal information is encoded in entity embeddings as a sinusoidal function of timestamp; and time-aware relation embedding (TA), where timestamps are embedded into a sequence fed to an LSTM to produce dynamic relation representations. TransE and DistMult scoring functions are tested for each family. Tero, which uses complex space rotation, is also evaluated.

The key finding: TA models significantly outperform DE models on this specific dataset, because job-skill demand is fundamentally about how *relationships* change over time (TA models), not about how the semantic meaning of skills themselves changes (DE models).

## Software Tools / Setup Details

- TorchKGE (adapted to TempTorchKGE) for temporal KG embedding on PyTorch
- Spacy rule-based matching for skill entity recognition in English (Jobzilla rules) and French (ESCO/ROME rules)
- TextAttack (RoBERTa-CoLA) for sentence completeness filtering of extracted skills
- Argos Translate + Helsinki-NLP/opus-mt-fr-en for French-to-English translation
- Adam optimizer, triplet loss with margin, grid search over lr, emb_dim, margin, n_neg
- 4× 12GB GPUs for training
- Code: https://github.com/team611/JobEd and https://github.com/BahajAdil/TempTorchKGE
- Dataset: Rekrute.com (99,676 job postings, 2005–2022, Morocco) + Coursera API (10,180 courses)

## Test / Experiment Analysis

Grid search over learning rate (0.01, 0.001, 0.0001), embedding dimension (50, 100, 150, 200), margin (1, 5, 10, 20), negatives per positive (10, 30, 40). Evaluation metrics: Hit@1, Hit@3, Hit@10, MRR, and Mean Rank on the filtered test split of T-JobEdKG. A case study shows temporal demand heatmaps for specific skills across job titles (Figures 4–7), with the model forecasting demand trends for 2023–2025.

## Test Data / Dataset Source

T-JobEdKG: constructed from Rekrute.com (Moroccan job portal), 99,676 job postings in English and French, spanning November 2005 to September 2022. Also includes 10,180 Coursera courses. Final graph: 55,718 nodes, 1,296,374 relations. Dataset is publicly available at: https://github.com/BahajAdil/JobEd.

## Final Result

TA-DistMult is the best-performing model with Hit@1 = **61.77%**, Hit@3 = **84.53%**, Hit@10 = **95.08%**, MRR = **74.20%**. TA-TransE is close behind (Hit@1 = 61.26%, MRR = 71.65%). DE and Tero models perform significantly worse — Tero achieves only Hit@1 = 48.15%, MRR = 49.17%. The paper's analysis of *why* TA beats DE is genuinely insightful: in this domain, relationships evolve over time (demand for a skill in a job role changes), but the semantics of the skill entity itself don't fundamentally change — "Java" means the same thing in 2010 and 2024. TA models capture this correctly. The case study shows a clear and interpretable declining demand for Java and a post-2023 plateau in data analysis demand for Consulting IT Engineer roles.

**What works well here:** Framing skill demand forecasting as temporal KG link prediction is a genuinely novel and well-motivated contribution. The result that TA-DistMult (LSTM-based temporal relation embedding + DistMult scoring) is the right model for this task — and the theoretical explanation for why — is a strong analytical contribution. The publicly released dataset and TempTorchKGE library make this reproducible. The temporal heatmaps in the case study are the most intuitive skill demand visualizations we've seen in this literature.

## Limitations

The dataset is geographically limited: 99,676 Moroccan job postings from a single job portal (Rekrute.com). Morocco is not a representative proxy for global labor markets, and the job-skill mix in the Moroccan IT sector may differ substantially from other regions. The dataset is in French and English but the French-language skills required translation with automated tools, introducing noise. The KG is closed-world: it can only forecast demand for skills and jobs already in the graph — it cannot handle entirely new skills that emerge after the training cutoff. The temporal resolution is limited by when job postings first appeared, not by actual market-wide demand volume. No comparison against non-graph-based baselines (traditional time series, XGBoost) is provided, which would help calibrate how much the KG structure actually adds.

**The harder limitation:** The paper focuses on job-skill link prediction (will this job require this skill in the future?) but does not connect this to student guidance. It tells educational institutions and companies something useful, but it doesn't tell a specific student what to learn next given their current skills. The skill demand signal it produces is global, not personalized.

## Final Summary

This is one of the most technically sophisticated papers in this review. The use of temporal knowledge graph embeddings for skill demand forecasting is a genuinely novel framing, the dataset is substantial, and the TA-DistMult result is clean and well-explained. The temporal case studies are immediately useful for understanding skill trajectory trends — the kind of market intelligence that career guidance systems should integrate.

**How CareerGraph does better:** CareerGraph's MarketAgent already computes present-tense demand frequency from job postings, which serves the current-market signal this paper's approach tries to model. Where this paper predicts future job-skill links, CareerGraph takes a different and more immediately actionable approach: it uses LEADS_TO edges to encode prerequisite chains derived from market co-occurrence, giving students not just a demand forecast but a navigable path through the skill graph. More importantly, T-JobEdKG's forecasts are at the aggregate market level — "data analysis demand is declining in Consulting IT Engineer roles in Morocco" — whereas CareerGraph's SkillGapAgent computes a personalized readiness score tied to a specific student's existing skills against a specific target job. The outputs of this paper's model could theoretically enrich CareerGraph's LEADS_TO edge weights by incorporating temporal demand trends, which is a clear path for future integration.
