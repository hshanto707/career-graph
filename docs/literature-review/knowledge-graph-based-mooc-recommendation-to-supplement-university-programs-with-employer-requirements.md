# Development of a Knowledge Graph-Based Model for Recommending MOOCs to Supplement University Educational Programs in Line With Employer Requirements

**Authors:** Valiya Ramazanova, Madina Sambetbayeva, Sandugash Serikbayeva, Zhanna Sadirmekova, Aigerim Yerimbetova  
**Year:** 2024 (published December 17, 2024)  
**Published in:** IEEE Access, Volume 12 — DOI: 10.1109/ACCESS.2024.3519263 (Funded by the Science Committee of Kazakhstan, Grant AP22783030)

---

## Problem Statement

The gap between what universities teach and what employers need is well-documented but structurally persistent — curriculum reform cycles operate on years-long timescales while skill requirements in the IT labor market evolve in months. Students who graduate with what their university considers a complete education discover that employers require skills their programs never mentioned. Existing attempts to close this gap typically operate in isolation: curriculum designers work from one knowledge source, MOOC platforms from another, and employers from a third. No system systematically connects all three — linking what a specific educational program covers to what specific job vacancies require and then to which specific online courses close the identified gap.

This paper builds exactly that three-domain knowledge graph in Neo4j, using a multilingual sentence transformer to handle Kazakhstan's bilingual (Russian-English) professional environment, and demonstrates six concrete recommendation scenarios via Cypher queries.

## Key Contributions & Objectives

1. A heterogeneous knowledge graph integrating three domains — university educational programs, job vacancies (hh.kz), and MOOC courses (Coursera) — with skills as the linking entity across all three.
2. A multilingual skill matching approach using the `paraphrase-multilingual-mpnet-base-v2` Sentence Transformer (768-dimensional dense vectors, trained on 50+ languages), achieving F1 = 0.8917 on skill paraphrase classification — significantly outperforming BERT (F1 = 0.6988) and Word2Vec (F1 = 0.7731).
3. Six operational recommendation scenarios implemented as Cypher queries in Neo4j: skill compatibility analysis, job recommendations, in-demand skill identification, skill gap identification, course recommendations by vacancy group, and course recommendations targeting underdeveloped skills.
4. A TF-IDF enrichment step that improves concept-to-skill linking from the educational program side, reducing false negatives from curriculum terminology not used in job postings.
5. Empirical evaluation by three domain experts using P@K (K=3 and K=5) across five recommendation scenarios, including a baseline comparison against BERT and Word2Vec.

## Methodology / Theory / Framework

The KG construction pipeline builds three separate ontological graphs, then integrates them through embedding-based similarity. The Educational Program (EP) graph encodes competency maps, learning outcomes, and discipline annotations for the "Information Systems" specialty at a Kazakh university. The Vacancy graph encodes 5,248 IT job postings from hh.kz across 25 IT professions collected February–March 2024. The MOOC graph encodes 953 free English-language computer science and IT courses from Coursera (May 2024) with their modules, lessons, and skill tags.

All text phrases in all three graphs are embedded using `paraphrase-multilingual-mpnet-base-v2`. Cosine similarity is computed pairwise across graphs: IS_SIMILAR_TO edges are created between EP and Vacancy nodes when cosine similarity ≥ 0.87; IS_SIMILAR_TO2 edges between Vacancy and MOOC nodes when similarity ≥ 0.81. These thresholds were empirically determined. The resulting meta-path is: Educational Program → Skill → Skill → Job Vacancy → Skill → Skill → MOOC Course.

All graphs are stored in Neo4j (graph database), and the six recommendation scenarios are implemented as Cypher queries. The model comparison (Table 5) is evaluated on a binary skill paraphrase classification task using an English benchmark.

## Software Tools / Setup Details

- Neo4j (graph database, Cypher query language)
- `paraphrase-multilingual-mpnet-base-v2` Sentence Transformer (HuggingFace, 768-dim embeddings)
- BeautifulSoup (Coursera web scraping)
- hh.kz API (https://api.hh.ru/vacancies) for vacancy collection
- TF-IDF (EP vocabulary enrichment)
- Scikit-learn, Python
- Datasets: 5,248 hh.kz job vacancies (25 IT professions, Kazakhstan, Feb–Mar 2024); 953 Coursera courses (May 2024); university EP data for "Information Systems" specialty (2022 intake)
- Model modeled per IEEE Standard 2807-2022

## Test / Experiment Analysis

The paper evaluates four components. First, a model comparison on skill paraphrase classification: `paraphrase-multilingual-mpnet-base-v2` achieves F1 = 0.8917 (Precision = 0.983, Recall = 0.8159), outperforming BERT (F1 = 0.6988, driven by very high recall but low precision at 0.5479) and Word2Vec (F1 = 0.7731, high precision at 0.991 but low recall at 0.6338). Second, recommendation P@K evaluation by three domain experts across five scenarios: Scenario 1 (skill similarity): P@3 ≈ 1.0 for most cases, P@5 satisfactory; Scenario 2 (vacancy recommendations): P@5 = 1.0 for top-5 vacancies; Scenario 4 (underdeveloped skills): P@5 ranges from 0.4 (System Administrator) to 1.0 (Project Engineer); Scenario 5 (courses for developer group): P@K = 1.0 for all top-5 courses with matching skill counts of 4–6; Scenario 6 (courses for gap skills): P@5 = 0.8–1.0 across roles.

Top skills for "Developer" vacancies by mention count: git (139), javascript (114), SQL (101), PHP (96), PostgreSQL (84), HTML (82), MySQL (75), OOP (61), CSS (58).

## Test Data / Dataset Source

5,248 IT job vacancies from hh.kz across 177 settlements in Kazakhstan (February–March 2024). 953 Coursera free courses in CS/IT/Data Science (May 2024). University EP data for "Information Systems" specialty, 2022 intake. Evaluation: three domain experts, P@K scoring.

## Final Result

The `paraphrase-multilingual-mpnet-base-v2` Sentence Transformer outperforms both BERT and Word2Vec for skill paraphrase matching at F1 = 0.8917, confirming it as the right model for multilingual labor market skill entity linking. The six Cypher-query recommendation scenarios demonstrate production-ready functionality: the system can answer curriculum alignment questions, identify skill gaps between EP and target jobs, and recommend specific Coursera courses to close each gap — all within a single Neo4j knowledge graph.

**What works well here:** The three-domain knowledge graph architecture — educational programs, job vacancies, and MOOC courses linked through skill embeddings — is architecturally the closest published antecedent to what CareerGraph is building. The multilingual embedding approach is a genuine methodological contribution for non-English-speaking markets where skill terminology appears in mixed-language job postings. The empirical model comparison is rigorous and honestly explains *why* `paraphrase-multilingual-mpnet-base-v2` outperforms BERT: BERT achieves high recall but low precision (lots of false positives) because it lacks sufficient multilingual domain adaptation. The six Cypher query scenarios are immediately reproducible by any practitioner with a Neo4j instance.

## Limitations

The evaluation relies on only three domain experts applying P@K — a small and potentially biased evaluation pool. For Scenario 4 (underdeveloped skill identification), P@5 drops to 0.4 for System Administrator, indicating real variability in recommendation quality across roles. The model was fine-tuned on IT job vacancies from hh.kz, which limits its applicability outside the IT sector and outside Kazakhstan without re-tuning. The MOOC dataset covers only free Coursera courses, excluding paid courses, other platforms (edX, Udemy, Coursera for Business), and non-English resources. Cosine similarity thresholds (0.87 and 0.81) were empirically set and not validated through ablation. The KG has no learner node — there is no student profile represented as a persistent entity in the graph, so the system cannot track individual progress or personalize recommendations beyond the EP-level.

**The persistent architecture gap:** The system models what a curriculum covers and what employers want, but not what a specific student knows. Skill gap identification is at the curriculum level, not the student level. Two students from the same program would receive identical recommendations regardless of their individual competency profiles.

## Final Summary

This paper is one of the most directly relevant antecedents to CareerGraph in the literature. Its three-domain knowledge graph (educational programs + job vacancies + MOOCs), multilingual sentence transformer embedding strategy, and Neo4j Cypher implementation are all directly transferable architectural elements. The skill paraphrase matching evaluation is rigorous, and the six recommendation scenarios demonstrate practical utility beyond academic proof-of-concept.

**How CareerGraph does better:** The most significant gap this paper leaves is the absence of student-level personalization. CareerGraph represents each student as a first-class node in Neo4j with persistent HAS_SKILL edges and proficiency weights — something this system does not do. Our SkillGapAgent computes a gap specific to a particular student's profile against a particular target job, not a curriculum-level gap that applies identically to all students in a program. Our PathFinderAgent adds the ordering dimension this system lacks: rather than returning an unordered list of gap skills and courses, we traverse LEADS_TO prerequisite edges to produce a sequenced learning path. And where this system relies on three domain experts for evaluation, our pipeline is evaluated against 10,000+ real job postings with quantitative readiness scoring — grounding the gap analysis in empirical market data rather than expert judgment.
