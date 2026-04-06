# Job Posting-Enriched Knowledge Graph for Skills-Based Matching

**Authors:** Maurits de Groot, Jelle Schutte, David Graus  
**Year:** 2021  
**Published in:** RecSys in HR 2021 (Workshop on Recommender Systems for Human Resources, ACM RecSys), October 1, 2021, Amsterdam

---

## Problem Statement

ESCO and ISCO provide structured, authoritative representations of occupations and skills — but they are static. They reflect what skills occupations required at the time the taxonomy was last curated, not what the live labor market is currently demanding. A software engineering role in 2021 requires skills that did not exist in ESCO's last major update. Digitization and globalization constantly reshape which competencies are associated with which roles, and taxonomy maintenance cannot keep pace.

This paper asks whether enriching ESCO/ISCO taxonomies with co-occurrence statistics from real job postings can produce a dynamic, market-responsive Knowledge Graph that improves skills-based candidate-to-job matching, enables career pathfinding between roles, and identifies which skills are most distinctive for each occupation group.

## Key Contributions & Objectives

1. Constructs a custom Skills & Occupation Knowledge Graph (KG) by combining ISCO (occupation hierarchy) and ESCO (skills taxonomy) and enriching both with co-occurrence patterns extracted from 600,000 Dutch job postings via Textkernel Extract.
2. Evaluates link prediction for KG completion — discovering novel skill-to-occupation edges not in the original taxonomy — comparing Preferential Attachment (PA) and Node2Vec (N2V), finding N2V superior at realistic deployment ratios.
3. Applies skills-based Jaccard distance between occupations as edge weights for Dijkstra's shortest-path career pathfinding.
4. Adapts TF-IDF from document-term weighting to skill-occupation weighting across all four ISCO granularity levels to identify occupation-distinctive skills.
5. Demonstrates all three applications qualitatively on Dutch labor market data and characterizes the KG's structural properties.

## Methodology / Theory / Framework

The KG is built in three layers. First, the structural backbone: ISCO occupations (four granularity levels, 10 major groups) are linked to ESCO occupations and skills via the existing ISCO-to-ESCO cross-walk. Second, the market enrichment: 600,000 Dutch job postings are processed by Textkernel Extract (an industry-standard NLP parser), and extracted skill surface forms are matched to ESCO skill names using character n-gram Jaccard similarity with a threshold of 0.66 (tuned on 39.7 million Textkernel-to-ESCO mappings). Co-occurrence counts between occupations and skills become edge weights. Third, the resulting KG covers 1,220 nodes (983 ESCO skills, 237 ISCO occupations) and 3,910 edges.

For link prediction, the KG edges are split 55%/15%/30% train/validation/test. PA uses the product of node degrees; N2V trains embeddings with 1024 dimensions, walk length 4, 2500 walks per node. Career pathfinding computes pairwise Jaccard distances between occupation skill sets (distance threshold 0.8), then runs Dijkstra. TF-IDF treats skills as terms and ISCO occupation groups as documents, applied across all four hierarchy levels.

## Software Tools / Setup Details

- 600,000 Dutch job postings from Jobdigger (Burning Glass/Jobdigger), uniformly sampled across ISCO level-1 groups
- ISCO-08 taxonomy (International Labour Organization)
- ESCO v1 taxonomy (European Commission): 13,485 skills, 2,942 occupations
- Textkernel Extract (industry-standard NLP skill parser) for skill extraction
- Node2Vec (Grover & Leskovec, 2016) for graph embedding-based link prediction

## Test / Experiment Analysis

Link prediction was evaluated at equal positive/negative split and at increasing negative:positive ratios. At the equal split: PA achieves F1 = 0.78 (positive class), N2V achieves F1 = 0.65. However, at realistic negative-to-positive ratios ≥ 3:1, N2V consistently outperforms PA — and this advantage is stable through a 10:1 ratio. This is the operationally relevant result: in real KG completion settings where negative examples vastly outnumber positives, N2V is the better choice.

Career pathfinding results are qualitative: Dijkstra from "Cook" correctly identifies "Bakers, pastry-cooks and confectionery makers" as the nearest feasible transition. Jaccard distance statistics confirm the KG's occupation profiles are highly distinctive (mean = 0.938 for occupations, std = 0.070). Minimum distance = 0 for near-identical roles ("Food service counter attendants" / "Hotel receptionists"), maximum = 0.993 for entirely unrelated roles ("Electronics engineers" / "Policy administration professionals").

## Test Data / Dataset Source

600,000 Dutch job postings from Jobdigger, uniformly sampled across ISCO level-1 occupation groups, each labeled with a level-4 ISCO code. ESCO v1 and ISCO-08 taxonomies. No explicit train/test temporal split — the KG reflects aggregated co-occurrence across the full dataset.

## Final Result

Node2Vec outperforms Preferential Attachment for link prediction at realistic deployment ratios, making it the recommended approach for discovering novel skill-to-occupation edges in a market-enriched KG. The career pathfinding application demonstrates that Jaccard-distance-based shortest paths produce intuitively correct and operationally useful career transition routes. TF-IDF skill importance correctly identifies occupation-distinctive skills that generic co-occurrence counts would miss by weighting common cross-industry skills (like "project management") down.

**What works well here:** The core idea — that ESCO/ISCO taxonomies should be enriched with real market co-occurrence data rather than treated as authoritative ground truth — is both practically motivated and technically well-executed. The N2V link prediction result at realistic negative ratios is an important methodological finding for anyone building KG completion systems in the hiring domain. The TF-IDF adaptation to skill-occupation weighting is elegant and directly applicable to any system that needs to identify which skills are actually distinctive for a given role rather than just common across all roles.

## Limitations

The KG covers only 237 of 436 ISCO occupations and 983 of 13,485 ESCO skills due to vacancy coverage gaps and n-gram matching failures — less than 55% of the occupation taxonomy and 7% of the skill taxonomy are represented. The Jaccard distance threshold for career pathfinding (0.8) was set by visual inspection rather than optimization. The career pathfinding and TF-IDF applications lack any empirical validation — no ground truth for career transitions or expert-annotated skill relevance was collected. The paper is explicitly a workshop paper and positions itself as exploratory; end-user studies are out of scope. The character n-gram Jaccard matching for skill extraction is a naive approach that will produce both false positives (similar-sounding but unrelated terms) and false negatives (semantically equivalent skills with different surface forms).

**The structural gap:** The system models what the market currently requires but does not connect this to individual students or workers. The KG enables occupation-level career pathfinding, but it cannot tell a specific person — given their unique current skill set — which path is most realistic for them.

## Final Summary

This workshop paper lays out the foundational components of a market-enriched skills knowledge graph: co-occurrence-based enrichment of ESCO/ISCO, link prediction for KG completion, and Jaccard-distance career pathfinding. The Node2Vec link prediction result at realistic deployment ratios is its most transferable empirical finding.

**How CareerGraph does better:** CareerGraph extends this architecture in two critical directions. First, we represent students as first-class nodes in the graph with persistent HAS_SKILL edges and proficiency weights — the de Groot KG has no learner nodes at all, only occupations and skills. Second, our LEADS_TO edges encode directional prerequisite relationships between skills (skill A leads to skill B because the market data shows workers typically acquire them in that order), whereas this paper's KG uses only undirected co-occurrence edges between skills and occupations. This means CareerGraph's PathFinderAgent can produce an ordered learning sequence — "learn A before B before C" — while de Groot's Dijkstra pathfinding can only tell you which occupation is nearest, not which skills to acquire first to get there. Our NormalizationAgent also handles the entity linking gap this paper identifies (only 7% of ESCO skills covered) through fuzzy matching and synonym resolution against the full O*NET taxonomy.
