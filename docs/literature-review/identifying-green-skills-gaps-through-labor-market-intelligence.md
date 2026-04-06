# Identifying Green Skills Gaps through Labor Market Intelligence

**Authors:** Dimitar Nikoloski, Adam Sulich, Letycja Sołoducho-Pelc, Gjorgi Mancheski, Marjan Angelski, Marija Midovska Petkoska  
**Year:** 2024  
**Published in:** Journal of Infrastructure, Policy and Development, Vol. 8, Issue 6 — EnPress Publisher

---

## Problem Statement

The world is going green faster than the workforce can keep up. Industries undergoing eco-friendly transitions are demanding workers with specialized green competencies — skills like carbon accounting, sustainable materials management, and clean energy systems — but educational institutions and training programs haven't adapted fast enough to produce them. The result is a widening green skills gap that existing analytical methods are poorly equipped to measure.

Traditional survey-based approaches to labor market analysis are too slow and too narrow for this problem. They fail to capture how rapidly skill demand evolves in green sectors, and they tend to exclude developing and underdeveloped economies where the gap is arguably most damaging. This paper sets out to solve the measurement problem: how do you identify and quantify a green skills mismatch at scale, across geographies and occupations, before it becomes a crisis?

## Key Contributions & Objectives

1. Introduces a conceptual research framework for identifying green skills gaps using Labor Market Intelligence (LMI) — an AI and ML-driven approach applied to live job vacancy and candidate profile data from online portals.
2. Categorizes green skill mismatches into three precise types: green skill shortages (demand exceeds supply at current wages), green skill deficits (below-benchmark competency), and green skill obsolescence (skills no longer required).
3. Proposes a three-phase data pipeline: ingestion (web scraping + API access), processing (deduplication + ontology-based classification), and analysis (ML/NLP-driven mismatch detection).
4. Uses the ESCO taxonomy (13,890 skills, 571 labeled as green) as a classification backbone.
5. Proposes an online platform for labor market matching based on green skills, with reskilling and upskilling functions built in.
6. Produces policy recommendations for curriculum adaptation and active labor market interventions.

## Methodology / Theory / Framework

The paper lays out a conceptual framework rather than running experiments — it is planning future empirical work. The proposed pipeline works in three stages. First, data is collected by scraping job portals and job-seeker profile databases, then ranked by how representative they are of green sectors. Second, the raw text is cleaned, deduplicated (to catch the same job posted across multiple portals), and classified using the ESCO taxonomy augmented with NACE sector codes, NUTS geographic codes, and ISCED education levels. Third, ML classification and clustering algorithms extract patterns: which green skills are demanded, which are supplied, and where the gap lies.

The framework distinguishes between external mismatch (comparing what employers want to what job seekers offer) and internal mismatch (skill gaps within already-employed workers). This paper focuses exclusively on the external dimension, which is more visible and more tractable given online data.

## Software Tools / Setup Details

This is a conceptual framework paper — no implementation is presented. The framework conceptually references:
- Web crawlers and APIs for job portal data collection
- ESCO database for ontological skill classification
- NLP tools and ML classifiers for gap detection
- Multidimensional databases and interactive dashboards for results dissemination

## Test / Experiment Analysis

No experiments are conducted. The paper does not report any empirical results — it is a blueprint, not a system evaluation. It supports its argument with secondary references to similar applied work in the UK, Germany, and South Korea.

## Test Data / Dataset Source

No primary dataset is used. Secondary examples are drawn from published studies on labor market data in Germany (Bauer et al., 2022) and South Korea (Song et al., 2021) to illustrate what the proposed approach could find.

## Final Result

There are no quantitative results. The conceptual outcomes include a structured blueprint for a green skills matching platform, a set of measurable supply/demand indicators by occupation, industry, region, and education level, and concrete policy signals for hard-to-fill green vacancies.

**What works well here:** The ESCO-based classification framework is genuinely useful and directly applicable to any skill gap system. The three-type mismatch taxonomy (shortage, deficit, obsolescence) is a clean analytical contribution that helps separate different policy responses. The paper's acknowledgment of coverage bias in online job data is intellectually honest and shows methodological awareness.

## Limitations

The paper openly acknowledges that online job vacancy data does not represent the whole labor market — many positions are filled through internal promotions, referrals, or informal channels, and these are invisible to the scraper. Companies also sometimes over-post vacancies to build candidate pipelines, which inflates demand estimates.

**The harder limitation:** There are no results. At all. This is a proposal for future research, not a completed study. The green skills mismatch it describes is real and urgent, but without empirical validation, we can't know whether the proposed pipeline actually works, scales, or produces actionable insights. The framework is also restricted to the "external" mismatch — it cannot say anything about the skill gaps of people who are already employed and quietly falling behind.

## Final Summary

This paper is best understood as a research agenda rather than a research contribution. It articulates the problem clearly, structures it well, and proposes a principled framework for addressing it. But it stops short of implementation, validation, or any concrete finding.

**How CareerGraph does better:** CareerGraph actually builds the pipeline this paper proposes. We ingest real job posting data (Kaggle, 10k+ postings), classify skills using the O*NET/ESCO taxonomy through our NormalizationAgent, store the structured results in a Neo4j knowledge graph, and compute explicit mismatch scores via our SkillGapAgent. The mismatch types this paper describes — shortages, deficits, and obsolescence — map directly onto what our MarketAgent surfaces through demand frequency analysis and what our SkillGapAgent computes per student profile. Where this paper stops at conceptualization, CareerGraph delivers measurable, student-facing outputs with explainable rationales from the ReasoningAgent.
