# Efficient Resume-Based Re-Education for Career Recommendation in Rapidly Evolving Job Markets

**Authors:** Saeed Ashrafi, Babak Majidi, Ehsan Akhtarkavan, Seyed Hossein Razavi Hajiagha  
**Year:** 2023 (published November 2, 2023)  
**Published in:** IEEE Access, Volume 11, pp. 124350–124367 — DOI: 10.1109/ACCESS.2023.3329576

---

## Problem Statement

Displacement events — the COVID-19 pandemic forced US unemployment to 14.7% in April 2020, with comparable figures in Canada (13%) and Australia (11%) — create a population of workers who need to transition careers quickly but cannot access traditional university re-education due to financial constraints and time pressure. Most existing job recommender systems compound this problem by recommending similar jobs rather than better ones: they match resumes to positions that look like the applicant's current role, rather than identifying what skills are missing, which higher-paying positions those skills would unlock, and what learning resources could close that gap.

Career-gAIde is built to answer the question displaced workers actually have: "Given where I am today, what career move would improve my salary, and what do I need to learn to make it?" This combines salary estimation, career-advancement-oriented job recommendation, skill gap identification, and learning path recommendation in a single end-to-end pipeline.

## Key Contributions & Objectives

1. Career-gAIde: an end-to-end pipeline that combines salary estimation from resume text, career-advancement job recommendation (finding higher-paying positions, not just similar ones), skill gap identification, and book-based learning path recommendation.
2. A CNN-based salary classification model that estimates annual salary into 10 income levels from resume/job advertisement text — achieving 70.70% accuracy via k-fold cross-validation, best using randomly initialized embeddings with bag-of-words and stemming.
3. A multi-field weighted similarity function combining concept overlap (via φ coefficient), experience level gap, education level gap, and salary differential — where the salary component actively rewards jobs above the applicant's current level and penalizes overqualification.
4. DBpedia Spotlight entity tagging for concept extraction from job titles and descriptions, enabling domain-agnostic skill matching without a predefined skills dictionary.
5. An automated book recommendation module using Google Books API combined with Amazon review-based quality scoring (K-means clustering of descriptions + review helpfulness weighting).

## Methodology / Theory / Framework

The pipeline has five modules. Module 1 crawls 8,870 job advertisements from jobserve.com, applies NLP preprocessing (stemming, stop word removal, tokenization), uses DBpedia Spotlight for concept extraction, normalizes salaries to annual USD, and classifies them into 10 income levels. Module 2 applies the same pipeline to the user's uploaded resume, including professional level extraction and DBpedia concept tagging. Module 3 estimates the user's current salary using a 1D CNN (embedding → convolution → global max pooling → dense + dropout → 10-class softmax), since salaries are rarely stated directly on resumes.

Module 4 computes career-advancement job similarity using a weighted function across five fields: title concept overlap (φ coefficient), description concept overlap, experience level gap (penalizing both over-qualification and large gaps), education gap, and salary differential (1/k reward for jobs k salary levels above current, negative penalty for jobs below). The top 10 advancement jobs are returned. Module 5 extracts skill gaps by comparing job concept vectors against resume concept vectors, queries Google Books per missing skill, clusters the results using K-means on TF-IDF of book descriptions, and ranks candidates using a review helpfulness score: Score = Σ(rating × helpful_votes) / total_reviews.

## Software Tools / Setup Details

- Python, NLTK (NLP), Keras + TensorFlow (CNN), Flask (web UI)
- DBpedia Spotlight (entity tagging / concept extraction)
- GloVe word embeddings (100-dimensional, 400k English Wikipedia vocabulary)
- Google Books API (book retrieval per skill gap)
- Amazon book and review dataset (offline quality ranking)
- Job dataset: 8,870 English job advertisements scraped from jobserve.com
- Evaluation: 30 human participants providing real resumes

## Test / Experiment Analysis

The salary classification CNN was evaluated via k-fold cross-validation on 8,870 job ads. The best model — CNN-Random with bag-of-words + stemming — achieved 70.70% accuracy. Counterintuitively, randomly initialized embeddings outperformed trainable GloVe (68.51%) and frozen GloVe (55.08%), likely because the job advertisement domain is sufficiently distinct from general Wikipedia text that pre-trained embeddings provide little advantage.

Job offer recommendation was evaluated by 30 human participants using real resumes against the job advertisement corpus. The φ coefficient similarity function achieved precision = 0.67, narrowly outperforming Jaccard similarity (0.65). Compared to the CapaR baseline (precision = 0.73), Career-gAIde's precision is lower — but CapaR is restricted to IT jobs and ignores salary and experience level, making it inappropriate for cross-domain or salary-aware career transitions.

Required skills identification: precision = 0.82, recall = 0.84, F1 = 0.83 (φ coefficient variant). Skill deficiency identification: precision = 0.77, recall = 0.79, F1 = 0.78. Both outperform CapaR on recall (CapaR skill deficiency recall = 0.65), which is the operationally critical metric — missing a needed skill gap is more harmful to career transition than a small number of false positives.

## Test Data / Dataset Source

8,870 English job advertisements scraped from jobserve.com (software engineering domain). 30 human participant resumes for recommendation evaluation. Amazon book and user review datasets for learning path quality ranking. No public benchmark dataset.

## Final Result

Career-gAIde demonstrates that salary estimation, advancement-oriented job matching, skill gap identification, and learning path recommendation can be integrated into a single pipeline and evaluated with real users. Its recall-focused design for skill identification (84% for required skills, 79% for deficiencies) correctly prioritizes completeness over precision in a career transition context — a missed gap is more damaging than a spurious recommendation.

**What works well here:** The salary-aware recommendation function is the standout contribution. By explicitly penalizing jobs below the user's current salary level and rewarding those above it, the system operationalizes what a displaced worker actually wants — not just "find me a job like my old one" but "find me a better job I can qualify for." The DBpedia Spotlight-based concept extraction avoids the predefined skills dictionary limitation that most comparable systems suffer from, making the approach at least nominally generalizable across domains. The CNN salary classification result — that randomly initialized domain-specific embeddings outperform general-purpose GloVe — is a practically useful finding for anyone building small-scale domain-specific NLP classifiers.

## Limitations

The 30-participant evaluation is very small, and all participants were likely recruited from the same institution, limiting representativeness. The system is currently validated only on software engineering jobs; the domain-agnosticism claimed by the DBpedia approach is not empirically tested outside this domain. The salary estimation accuracy of 70.70% across 10 income levels means approximately 3 in 10 users receive incorrectly estimated salary tiers, which corrupts the downstream advancement calculation. The learning path relies exclusively on books, which is a significant coverage gap: most workers seeking re-education in technical fields today expect online courses, video tutorials, and certifications, not just reading lists. The book recommendation quality depends on Amazon review availability, which is sparse for niche technical subjects. No bias analysis is conducted — the salary model trained on jobserve.com data will inherit whatever salary disparities exist in that dataset (gender pay gaps, geographic variation), and these biases will propagate into which jobs are recommended as "advancement" opportunities.

**The temporal limitation:** The system matches resumes against a fixed scraped corpus of job advertisements. In rapidly evolving markets — exactly the scenario the paper is designed for — a corpus scraped months ago may already be out of date. The paper acknowledges this but offers no mechanism for continuous re-ingestion.

## Final Summary

Career-gAIde is the most career-transition-focused system in this review. Its salary-aware job recommendation function addresses the actual economic question displaced workers care about, and its recall-optimized skill gap identification is well-motivated for the career transition context. The book-based learning path is an understandable starting point but limits practical utility compared to course-based alternatives.

**How CareerGraph does better:** CareerGraph's approach to all three of Career-gAIde's core modules is empirically grounded and continuously updatable in ways this system is not. Our MarketAgent computes skill demand from a re-ingestable job posting database — not a static scraped corpus — so the demand signals students receive reflect the current market, not a snapshot from months ago. Our SkillGapAgent computes weighted readiness scores using the student's proficiency-weighted HAS_SKILL edges against the target job's actual requirements, producing a more nuanced gap measurement than concept-vector subtraction. Most importantly, our PathFinderAgent converts the gap list into an ordered learning sequence using LEADS_TO prerequisite edges — addressing exactly the weakness this paper's book recommendation module has: it identifies what to learn, but provides no guidance on what order to learn it in. And CareerGraph's ReasoningAgent communicates all of this in plain language with market demand evidence, serving the exact displaced-worker audience Career-gAIde targets but with a significantly more actionable output.
