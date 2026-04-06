# An AI-Based Open Recommender System for Personalized Labor Market Driven Education

**Authors:** Mohammadreza Tavakoli, Abdolali Faraji, Jarno Vrolijk, Mohammadreza Molavi, Stefan T. Mol, Gábor Kismihók  
**Year:** 2022  
**Published in:** Advanced Engineering Informatics, Volume 52, Article 101508 — Elsevier (Available online: 24 February 2022)

---

## Problem Statement

Open Educational Resources (OER) have made high-quality learning material widely accessible, but abundance has created a new problem: learners cannot identify which resources are actually good, relevant to their goals, or aligned with what the labor market wants. A data science student browsing YouTube and Coursera for "machine learning" content faces thousands of results with no reliable way to prioritize them. Meanwhile, educators and workforce programs lack tools that connect real-time skill demand from job postings to specific educational resources that close those gaps.

This paper builds eDoer — an open, AI-driven recommender system that does three things at once: extracts skill demand from real job postings, filters the OER landscape for quality, and delivers personalized content recommendations to learners based on their stated preferences and learning history.

## Key Contributions & Objectives

1. A full end-to-end design methodology from user requirements gathering (47 learners, 23 subject matter experts) through implementation and experimental validation with 156 participants.
2. A Labor Market Intelligence component that analyzes 21,937 English job vacancies from Monster.com to identify the six highest-demand skills for three data science roles (Data Scientist, Data Analyst, Business Analyst): Python, R, Statistics, Machine Learning, Data Visualization, and Text Mining.
3. An LDA-based topic decomposition that breaks each of the six skills into granular learning topics — 132 topics total — providing more navigable learning objectives than skill-level labels alone.
4. A three-tier filtering pipeline (topic-based → metadata-based → quality-based) that distills 3,228 collected resources down to 764 high-quality OER, with a quality prediction model achieving 79.2% F1-score.
5. A dot-product-based personalization engine using 15-dimensional learner preference vectors (content length, detail level, learning strategy, format, classroom preference) to rank resources for each user.
6. A randomized controlled experiment (156 participants, 3 groups) demonstrating that eDoer significantly improves learning outcomes over self-directed search — and honestly reporting the null result on personalization.

## Methodology / Theory / Framework

The system pipeline has three major phases. Phase 1 extracts labor market intelligence: job vacancies from Monster.com (via Kaggle) are analyzed for skill occurrence frequencies, and the top six data science skills are identified. Phase 2 decomposes those skills into learnable topics using LDA applied to YouTube video transcripts, then collects educational resources through Google and YouTube searches on skill-topic keyword combinations. The three-tier filter applies: (1) topic relevance filtering removes resources not matching search keywords; (2) metadata quality filtering removes resources predicted as low-quality by an ML classifier trained on structural metadata; (3) content quality filtering applies a quality scoring model based on transcript similarity and popularity signals.

Phase 3 is the recommendation engine: learner profiles are represented as 15-dimensional preference vectors capturing length preferences (short/medium/long), detail level, learning strategy (theory/example/mixed), content format (video/book/slides/web page), and classroom preference. Recommendations are computed as dot products between learner preference vectors and resource feature vectors. Vectors are updated monthly based on feedback, with both long-term (all history) and short-term (1-month window) components. The eDoer platform delivers goal setting, personalized content, job skill requirements, and progress monitoring in a web interface.

## Software Tools / Setup Details

- Pafy (Python-YouTube library) for video resource collection
- LDA for topic extraction from educational video transcripts
- Prolific platform for participant recruitment (156 completions, compensated at £15.76 each)
- Qualtrics for survey and assessment administration
- ML quality prediction: binary classifier for metadata quality + content similarity model
- Dataset: 21,937 Monster.com job vacancies (Kaggle); 3,228 collected OER; 764 final high-quality resources
- 132 learning topics across 6 skills (Python: 26, Statistics: 27, Machine Learning: 35, R: 12, Data Viz: 14, Text Mining: 18)

## Test / Experiment Analysis

A randomized controlled experiment with three groups: Group 1 (n=53, self-directed learning), Group 2 (n=50, eDoer without personalization), Group 3 (n=53, eDoer with personalization). All groups had a 105-minute learning session on Basic Statistics for Engineers (7 topics), bookended by pretest and posttest assessments. One-way ANCOVA controlled for pretest scores.

Pretest scores were comparable across groups (0.20–0.24). Posttest scores: Group 1 = 0.34, Group 2 = 0.42, Group 3 = 0.42. ANCOVA: F(1,152) = 11.202, p < 0.001. Both eDoer groups significantly outperformed self-directed learning (p < 0.05). Critically, Group 3 (personalized) showed no significant advantage over Group 2 (non-personalized): t(152) = 0.137, p = 0.892. User satisfaction with content quality: Group 1 = 0.64, Group 2 = 0.75, Group 3 = 0.82. Willingness to recommend eDoer: 75% of combined eDoer users.

## Test Data / Dataset Source

Monster.com job vacancies dataset (21,937 English vacancies, from Kaggle) for labor market skill extraction. Educational resources: 3,228 collected from Google/YouTube searches, filtered to 764 high-quality OER. Experiment participants: 156 completed (from 175 recruited via Prolific), 14 excluded for insufficient effort, 5 for technical issues. Basic Statistics assessment bank: multiple-choice questions for 7 topics, validated by 3 domain experts.

## Final Result

eDoer significantly improves learning outcomes over self-directed search — a concrete, measured demonstration that AI-curated, labor-market-aligned OER delivery works better than leaving learners to navigate the open web alone. The effect held even without personalization, which is an important and honest finding: the quality filtering pipeline alone (reducing 3,228 resources to 764 high-quality items) is the primary driver of value, not the personalization layer.

**What works well here:** The randomized controlled experiment is genuinely rigorous — 156 participants, pre-registered controls, monetary compensation reducing selection bias, and honest reporting of the null personalization result. The LDA-based topic decomposition is a thoughtful middle layer between raw skill labels and individual resources: rather than recommending "learn machine learning," the system points to specific topics like "gradient boosted trees" or "cross-validation." The three-tier filtering pipeline is a clean and replicable approach to OER quality control at scale. The finding that quality filtering outperforms personalization is practically important for any system builder in this space.

## Limitations

The null result on personalization is the most significant finding and also the biggest limitation: a 15-dimensional preference vector based on content length and format doesn't appear to capture enough signal about how individuals actually learn best. The experiment ran for only 105 minutes — long enough to show effects of quality content delivery but too short to detect personalization benefits that might emerge over a longer learning arc. Generalizing from Basic Statistics to other subject domains or to non-academic skill development contexts is questionable. The job vacancy dataset covers only three data science roles from a single platform, limiting the labor market signal to a narrow slice of the skill landscape.

**The harder methodological issue:** The eDoer system recommends resources but does not model the student's learning trajectory or adapt recommendations based on demonstrated competency changes. A student who scores 0.42 on the posttest has moved their knowledge, but the next round of recommendations is still based on their static preference vector, not on what they actually know now.

## Final Summary

eDoer is the most rigorously evaluated labor-market-driven educational recommender in this review. Its core insight — that quality-filtered, skill-demand-aligned OER improves learning outcomes over self-directed search — is now empirically supported, not just asserted. The three-tier filtering pipeline and LDA topic decomposition are reusable architectural components for any system tackling the OER quality problem.

**How CareerGraph does better:** CareerGraph addresses the exact limitation that eDoer's null personalization result points toward: our recommendations are not preference-based but need-based. Our SkillGapAgent computes which skills each student is actually missing for their target role using their HAS_SKILL graph edges and proficiency weights — not inferred content length preferences. This means the personalization is grounded in the gap between current competence and target requirement, which is the signal that actually changes what you should learn. Our PathFinderAgent then produces an ordered sequence using LEADS_TO prerequisite chains, so a student is never sent to "learn machine learning" before completing "learn statistics" — the ordering is semantically correct, not random. And unlike eDoer's three data science roles, CareerGraph operates across O*NET's full occupation taxonomy, making the labor market intelligence signal far broader.
