# C3-IoC: A Career Guidance System for Assessing Student Skills Using Machine Learning and Network Visualisation

**Authors:** Adán José-García, Alison Sneyd, Ana Melro, Anaïs Ollagnier, Georgina Tarling, Haiyang Zhang, Mark Stevenson, Richard Everson, Rudy Arthur  
**Year:** 2022 (published online December 1, 2022)  
**Published in:** International Journal of Artificial Intelligence in Education, Volume 33, pp. 1094–1121 — DOI: 10.1007/s40593-022-00317-y (Funded by the UK Institute of Coding / Office for Students)

---

## Problem Statement

Computer Science graduates are struggling to connect their university training to the real IT job market. Existing career guidance tools — O*NET, ESCO, FOCUS-2, Myers-Briggs — are either too broad to be IT-specific, rely on occupational taxonomies that lag behind actual job market demand, underweight non-technical (soft) skills, or treat technical and non-technical competencies as entirely separate assessments that students must navigate independently. High unemployment rates among CS graduates are the result.

The core problem is that students don't know where they stand relative to the IT job market, and no existing tool shows them in a way that is simultaneously data-driven (based on live job postings), technically rigorous, and visually intuitive. C3-IoC is built to close this gap: a three-module deployed system that combines CV parsing, a soft-skills questionnaire, and network-based job role visualization to place students in an empirically grounded IT job space.

## Key Contributions & Objectives

1. A deployed, publicly accessible career guidance system at c3-ioc.co.uk targeting UK undergraduate and high school students for IT sector careers — not a prototype, but a live system used by real students.
2. A hybrid knowledge base combining 22,359 UK IT job advertisements (DWP "Find a Job," October 2018–December 2019) with the O*NET database (967 occupations, 231 skills), linked through a manually validated 25-skill non-technical crosswalk.
3. An IT skill dictionary of 195 unique skills across four categories (General Tech: 85, Tools & Platforms: 63, Programming Languages: 20, Non-technical: 25) extracted using Word2Vec trained on the job corpus.
4. An asymmetric similarity metric that penalizes skill gaps but not surpluses — correctly reflecting that having more skills than required is beneficial, while missing required skills is detrimental.
5. A "Most Informative Order" method using Frobenius norm minimization to identify that just 4 of 24 questionnaire items (attention to detail, management, self-control, teaching/guidance) provide sufficient signal for 80%+ community assignment accuracy — reducing student burden while maintaining placement quality.
6. Force-directed network visualization placing students in the IT role space with color-coded match scores, and radar chart skill profiles for both technical and non-technical competencies.

## Methodology / Theory / Framework

C3-IoC has three modules. Module 1 builds the knowledge base: the IT job corpus is scraped weekly from DWP's "Find a Job" portal, de-duplicated, and processed by Word2Vec to extract a 195-skill dictionary (seed list of 100 skills expanded via cosine similarity to 902 candidates, manually pruned). 26 IT job roles are identified from titles appearing more than 100 times (Software Developer: 2,374 ads; Software Engineer: 1,479; Data Scientist: 281, etc.). The O*NET database is filtered to 381 roles requiring at least a bachelor's degree, retaining 142 skills after correlation filtering.

Module 2 profiles the student: a CV upload (PDF) extracts technical skills via dictionary matching; a 24-item questionnaire (of which only 4 are mandatory) assesses non-technical skills. Results are displayed as interactive radar charts and can be manually adjusted.

Module 3 performs matching and visualization: the student's skill vector is compared against each job role using an asymmetric distance metric D(u,j) = √Σ_s max(j_s − u_s, 0)² that counts only deficits. Similarity Sim(u,j) = 1 − D(u,j)/D(∅,j) normalizes this to [0,1]. Job roles are clustered into communities via Louvain community detection, and a force-directed network layout positions the student in the job space with match scores color-coded by cluster membership.

## Software Tools / Setup Details

- Word2Vec (Mikolov et al., 2013) for skill entity extraction from job corpus
- Louvain community detection (Blondel et al., 2008) for job role clustering
- Revealed Comparative Advantage (RCA) index for identifying occupation-distinctive skills
- O*NET database version db_24 (2019): 967 occupations, 231 skills
- IT job corpus: 22,359 UK job advertisements from DWP "Find a Job" (October 2018–December 2019)
- Live deployment: c3-ioc.co.uk (built with IBM support)
- User trial: N=64 valid responses (October–December 2020, online due to COVID-19)

## Test / Experiment Analysis

The system was evaluated through two methods. First, dummy user experiments using O*NET occupational profiles to test placement accuracy: with 4 mandatory questions answered, community assignment accuracy ≈ 80% and SRP@10 ≈ 40%. With 6 questions, SRP@10 > 70%. With 24 questions answered, community assignment accuracy approaches 100% and SRP@10 ≈ 100%. Second, a user trial with 64 valid responses (36% Sheffield, 35% Exeter, 29% other UK students; 77% male, 72% aged 19–24; 60% CS/IT background): system usability showed 23 of 45 statement pairs with strong positive Spearman correlations, and 61 of 105 usefulness statement pairs with strong correlations (rs > 0.4). Two very strong correlations (rs > 0.7) were found for "would use to explore career options" combined with "can identify learning opportunities" and "value for career development" combined with "value for personal development."

## Test Data / Dataset Source

22,359 UK IT job advertisements from DWP "Find a Job" portal (October 2018–December 2019); O*NET database version db_24 (2019). User trial: 64 valid responses from UK university students. No external held-out test set for the matching algorithm — evaluation used synthetic O*NET profiles as proxies for real student data.

## Final Result

C3-IoC achieves 80% community assignment accuracy and SRP@10 > 70% with only 6 questionnaire responses, making it practically usable without placing a high burden on students. The force-directed network visualization, rated as the highest-usability component in the user trial, successfully communicates where a student sits in the IT job space — a form of explainability that text lists cannot provide. The deployed system at c3-ioc.co.uk demonstrates that the architecture is production-ready, not just academically viable.

**What works well here:** The asymmetric similarity metric is a theoretically sound and practically important design choice — penalizing only gaps, not surpluses, correctly reflects how hiring works. The Most Informative Order reduction from 24 to 4 mandatory questions is a genuine usability contribution, backed by formal minimization rather than intuition. The network visualization as the top-rated component in the user trial is a compelling empirical result: seeing yourself in a job space as a positioned node relative to role clusters conveys spatial context that a ranked list of match percentages cannot. The fact that this is deployed and used by real students rather than sitting as a prototype is a notable marker of practical viability.

## Limitations

The CV parser performs surface-level dictionary matching and cannot infer skills from contextual descriptions ("I led a team of 12" does not yield "leadership"). It also cannot assess proficiency level — basic Python and expert Python appear as the same skill node. The knowledge base is frozen at 2018–2019 job advertisements and O*NET 2019; it has not been updated and cannot reflect the GenAI, MLOps, or cloud-native skills that entered the IT market after that cutoff. The O*NET questionnaire wording is North American-centric and was flagged by UK students as awkward in the user trial. The system is limited to the UK IT sector and to students with at least bachelor's-level education; generalization to other sectors, countries, or vocational backgrounds requires substantial reconstruction. No learning path recommendations are included — C3-IoC places students in the job space and shows them where they stand, but does not tell them how to move.

**The missing half:** C3-IoC is a diagnostic tool, not a navigational one. It shows students their gap but not their path. A student who sees they are a poor match for Data Scientist is left to figure out on their own which skills to acquire and in what order.

## Final Summary

C3-IoC is the most practically grounded career guidance system in this review — it is live, has a real user base, and applies rigorous matching against a live job posting corpus. Its asymmetric similarity metric, Most Informative Order questionnaire, and network visualization are methodological contributions that other systems have not made. Its limitations are primarily temporal (stale knowledge base) and functional (no learning path generation).

**How CareerGraph does better:** CareerGraph solves the half of the problem C3-IoC leaves open. Where C3-IoC shows a student where they stand in the job space, CareerGraph's PathFinderAgent shows them how to move: our LEADS_TO edges produce an ordered skill acquisition path from the student's current position to their target role, not just a similarity score. Our knowledge base is not frozen — the IngestionAgent continuously re-ingests job postings, so skill demand signals stay current (the GenAI skills that are invisible in C3-IoC's 2019 corpus are live in ours). Our NormalizationAgent handles the contextual inference limitation that C3-IoC's dictionary matching cannot address, using fuzzy matching and synonym resolution to capture semantically equivalent skill descriptions regardless of surface form. And by representing students as persistent nodes in Neo4j with proficiency weights on HAS_SKILL edges, CareerGraph models skill level — not just skill presence — which C3-IoC explicitly cannot do.
