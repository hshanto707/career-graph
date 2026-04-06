# Automatic Skill-Oriented Question Generation and Recommendation for Intelligent Job Interviews

**Authors:** Chuan Qin, Hengshu Zhu, Dazhong Shen, Ying Sun, Kaichun Yao, Peng Wang, Hui Xiong  
**Year:** 2023  
**Published in:** ACM Transactions on Information Systems, Volume 42, Issue 1 — ACM

---

## Problem Statement

Building a high-quality interview question bank for technical roles is expensive, slow, and fragile. It requires domain experts, takes considerable time, and becomes outdated every time a new skill or framework enters the market. At the same time, interviewers often struggle to ask the right depth of questions for a given candidate's skill profile — they either over-challenge or under-challenge.

This paper attacks both problems at once: it wants to automatically generate skill-oriented interview questions without heavy human annotation, and then recommend the right questions to an interviewer given any queried set of skills. The key challenge is that skill entities are ambiguous in text (the word "React" appears in many contexts), and question quality is hard to define without human judgment.

## Key Contributions & Objectives

1. Proposes DuerQues — an end-to-end intelligent system for skill-oriented interview question generation and recommendation, built on top of real click-through data from a major Chinese search engine.
2. DuerQues-SER: a distantly supervised skill entity recognition component using vocabulary annotation, Aho-Corasick pattern matching, and a Partial CRF neural NER model (F1 = 0.93 on query data).
3. DuerQues-IQG: a neural question generation model using an encoder-decoder with attention, copy, and coverage mechanisms — conditioned on a style token to produce interrogative outputs.
4. DuerQues-IQR: a graph-enhanced recommendation module that builds a skill co-occurrence graph and a word graph from click-through data, then uses Relational Graph Convolutional Networks (RGCN) to recommend the best questions for a queried skill set.
5. DuerQues-SES: an RGCN-based link prediction module for suggesting related skills an interviewer might not have considered, improving coverage.
6. Constructed a question bank of 53,998 skill-oriented interview questions from real user behavior data.

## Methodology / Theory / Framework

The system is split into two pipelines. The generation pipeline (SER + IQG) extracts skills from search queries and web page titles using distantly supervised NER, then trains a question generator on subgraphs formed by Louvain community detection on a query-page bipartite click graph. Each detected community corresponds to a skill topic, and the best query-page pair in each community becomes a training triple.

The recommendation pipeline (SES + IQR) builds a heterogeneous skill graph from three types of co-occurrence edges (query-query, title-title, and cross-query-title). RGCN propagates information across this graph to produce embeddings that capture both semantic and structural skill relationships. When an interviewer queries a set of skills, the RGCN-enriched embeddings are fed into a two-layer MLP that ranks the most relevant questions.

The whole thing is trained on proprietary Chinese search engine click-through logs — 10 million+ data points with real user behavior driving quality signals.

## Software Tools / Setup Details

- BERT-WWM (Chinese pretrained transformer) for character embeddings
- Partial CRF layer for handling unlabeled NER training positions
- Louvain community detection on query-URL bipartite graph
- RGCN (Relational Graph Convolutional Network) with 2 layers
- BiLSTM encoder-decoder with attention + copy mechanism
- Adam optimizer across all components
- Beam search (size 4) at inference for question generation

## Test / Experiment Analysis

Four independent evaluations, one per component. NER tested on query and KSC title datasets with 1,000 test instances each. Question generation tested on 200 test triples with human expert scoring (fluency and validity on a 1–5 scale). Skill suggestion evaluated with MRR and Hit@K on a split of the skill co-occurrence graph. Question recommendation evaluated on 88,272 user-skill-question interactions using AUC, F1, and Hit@5/10, with a case study where two interviewers evaluated output relevance and validity on 30 random skills.

## Test Data / Dataset Source

Proprietary click-through logs from a major Chinese search engine (July–September 2020). The final usable data covers 253,589 unique queries and 132,959 Knowledge Sharing Community (KSC) web pages. The public Weibo NER dataset was used as a secondary NER benchmark. No dataset is publicly released.

## Final Result

DuerQues-SER achieves F1 = 0.93 on query data and F1 = 0.89 on KSC title data — outperforming both baselines. Question generation achieves ROUGE-1 = 0.59 and human validity score of 3.42/5. Question recommendation achieves AUC = 0.93 and Hit@10 = 0.84 — strongly outperforming LSTM-MLP baselines. In the human case study, top-5 recommendations scored Relevancy = 0.99 and Validity = 0.87.

**What works well here:** The use of click-through data as a natural quality signal for question relevance is clever — it avoids expensive human annotation by leveraging real user behavior. The RGCN-based recommendation system that propagates graph context through heterogeneous skill co-occurrence edges is architecturally elegant and produces genuinely strong results. The skill suggestion module (SES) is a particularly useful addition that helps interviewers discover blind spots in their skill coverage.

## Limitations

The dataset is entirely Chinese-language and technology-domain specific. The system does not support personalization based on individual interviewer history or candidate profile. Because question generation relies on web page titles rather than full document content, the generated questions lack the depth of a subject matter expert's assessment. Rare or niche skills are poorly served due to sparse click-through data.

**The structural limitation:** This system is designed entirely around interviewers asking questions — it does not directly model the student or job seeker's skill gap, career fit, or learning trajectory. The skill graph it builds is valuable, but the output (interview questions) is orthogonal to what career guidance systems need (gap analysis, job matching, learning paths).

## Final Summary

DuerQues is a technically impressive system that solves a well-defined problem exceptionally well. Its NER results and recommendation quality are among the strongest in skill-related NLP literature. The graph-enhanced architecture for skill co-occurrence modeling is directly relevant to any system that needs to understand how skills relate to each other.

**How CareerGraph can do better:** CareerGraph doesn't generate interview questions — that's not our goal — but we can directly adopt DuerQues's insight about building skill co-occurrence graphs from real job posting data. Where DuerQues builds its graph from query logs, CareerGraph builds it from Kaggle job postings, with LEADS_TO edges capturing skill prerequisite relationships rather than just co-occurrence. This gives CareerGraph's PathFinder a more semantically meaningful graph to traverse. We also support multi-language normalization through our NormalizationAgent + ESCO integration, which DuerQues's Chinese-only approach cannot provide. The gap is in the career dimension: CareerGraph connects the skill graph to student profiles, job requirements, and learning roadmaps — a dimension DuerQues never addresses.
