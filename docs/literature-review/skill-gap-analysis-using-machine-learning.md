# Skill Gap Analysis Using Machine Learning

**Authors:** M. Sujitha, T.V. Ananthan, G. Lakshmi, A. Ramya Teja Sree, G. Sahithi  
**Year:** 2025  
**Published in:** International Journal of Scientific Research in Engineering and Management (IJSREM), Volume 9, Issue 3, March 2025 — DOI: 10.55041/IJSREM42529

---

## Problem Statement

The mismatch between what students and job seekers can do and what the labor market actually needs is a persistent and well-documented problem. Current tools that address this gap tend to fail in predictable ways: they rely on manual assessment by counselors who cannot scale, use static platforms built around keyword matching, or offer generic advice that does not adapt to how rapidly skill demands shift across industries. The result is that people receive guidance that feels impersonal at best and actively misleading at worst — "learn Python" applied equally to a fresh graduate targeting a data science role and a ten-year professional wanting to transition to machine learning management.

This paper proposes an automated, ML-powered skill gap analysis system that reads a user's resume, maps their current competencies against a target career's requirements, and generates a personalized learning roadmap with course suggestions, interview preparation materials, and progress tracking — tailored to the individual, not the average student.

## Key Contributions & Objectives

1. An automated resume analysis pipeline using NLP (spaCy, BERT-based NER) to extract both hard and soft skills from PDF, Word, and plaintext documents.
2. A career interest mapping module that uses supervised classification (Random Forest, SVM, Decision Trees) to match stated career goals to industry-validated skill profiles.
3. A skill gap identification engine combining cosine similarity and Jaccard similarity to compare the student's extracted skills against role requirements, with categorization by skill type (technical/soft, hard/domain-specific).
4. A personalized development roadmap generator that recommends courses from Coursera, LinkedIn Learning, and edX, links to practice problems and mock assessments, and generates targeted interview questions based on identified gaps.
5. A Skill Gap Index (SGI) and Proficiency Match Rate (PMR) as quantitative summary metrics: SGI = [(Required − Acquired) / Required] × 100, PMR = [Matched / Total Required] × 100.
6. A progress tracking mechanism using periodic re-assessments to update the student's skill profile and adapt recommendations over time.

## Methodology / Theory / Framework

The system operates in five stages. First, resume ingestion: PyPDF2 and python-docx extract raw text, which is then cleaned, tokenized, and processed for entity recognition. Second, skill extraction: pre-trained NER models identify both technical skills (programming languages, frameworks, tools) and soft skills (communication, leadership) from resume content. Third, career mapping: a classifier trained on industry skill databases assigns the user's interest statement to one or more occupation categories, then retrieves the required skill profile for that category. Fourth, gap analysis: cosine similarity and Jaccard similarity compare extracted skills to required skills, categorize gaps by type, and compute SGI and PMR. Fifth, roadmap generation: the gap list is matched against a course database (populated via Coursera, LinkedIn Learning, and edX APIs and web scraping) to produce prioritized learning suggestions, with interview question banks generated for identified deficiencies.

The system is designed as a web application with a Flask/Django backend, MySQL/PostgreSQL storage, and HTML/CSS/JavaScript frontend, deployable to AWS or Heroku.

## Software Tools / Setup Details

- NLP: spaCy, NLTK, Hugging Face Transformers (BERT for NER)
- ML frameworks: Scikit-learn (Random Forest, SVM, Decision Trees, K-Means clustering), TensorFlow
- Resume parsing: PyPDF2 (PDF), python-docx (Word)
- Database: MySQL or PostgreSQL
- Web scraping: BeautifulSoup, Scrapy
- External APIs: Coursera, LinkedIn Learning, edX
- Deployment: Flask/Django backend, AWS/Heroku cloud hosting
- Frontend: HTML, CSS, JavaScript

## Test / Experiment Analysis

The paper presents a system design and architectural proposal rather than a completed empirical study. No quantitative accuracy results, precision/recall metrics, or user study findings are reported. The described models (Random Forest, SVM, K-Means clustering) are standard approaches with well-understood performance characteristics, but no evaluation data — accuracy percentages, confusion matrices, or F1 scores — is provided for this specific system. The paper describes the architecture as designed and notes that it addresses limitations of existing manual and keyword-based tools, but this claim is not supported by any comparative measurement.

## Test Data / Dataset Source

No specific dataset is described or cited. The system is designed to ingest user-provided resumes and pull career skill data from job portals and industry databases, but no particular sources, sizes, or data compositions are specified. Course data comes from external APIs and scraping of online learning platforms.

## Final Result

The paper presents a complete architectural blueprint for an ML-powered skill gap analysis system covering the full student journey from resume parsing through personalized learning path generation and progress tracking. The SGI and PMR formulas provide clean quantitative abstractions of skill gap severity that can be surfaced to users. The integration with live learning platforms via APIs means recommendations are drawn from real, currently available courses rather than static lists.

**What works well here:** The architecture is sensible and covers all the right components — parsing, extraction, gap quantification, and roadmap generation. The decision to use both cosine similarity and Jaccard similarity for skill matching, rather than simple keyword overlap, is a reasonable methodological choice. The progress tracking mechanism — which updates the student's skill profile as they complete recommended activities and re-runs the gap analysis — addresses a gap in many static tools.

## Limitations

The paper makes no attempt to evaluate the system empirically. There are no test datasets, no accuracy metrics, no baseline comparisons, and no user studies. Every claim about system effectiveness is asserted rather than measured. Without knowing how accurately the NER extracts skills from real-world resumes — which can be highly heterogeneous in structure and language — it is impossible to assess the actual quality of the gap analysis that follows. A system that misidentifies skills in the parsing stage will produce confidently wrong readiness scores.

The career interest mapping module introduces a cold-start-adjacent problem: the classifier needs enough labeled training data for each occupation to work well, and the paper does not describe this training corpus. The course recommendation component raises a maintenance concern — scraped and API-fed data from Coursera and LinkedIn Learning goes stale as courses are added, removed, and revised.

**The deeper limitation:** This is a student-facing tool that treats all skills as equally weighted and does not account for which gaps are most critical for a specific target job posting. Knowing that you are missing three out of ten required skills is useful; knowing that the three missing skills are must-haves for 85% of job postings at your target salary band is actionable.

## Final Summary

This paper is an honest and practical contribution to the student-facing career guidance space — it describes a well-structured system that covers all the right components, from resume parsing to learning path generation. The SGI/PMR formulas are clean summary metrics that a student can understand and track over time.

**How CareerGraph does better:** CareerGraph implements and evaluates all of what this paper proposes, and adds three capabilities it does not address. First, our NormalizationAgent maps extracted skills to O*NET/ESCO with synonym resolution and fuzzy matching — handling the heterogeneity problem that NER-based extraction alone cannot solve. Second, our SkillGapAgent weights gaps by market demand frequency (from our MarketAgent's job posting analysis), not just by presence/absence — so a student knows not just *that* they are missing a skill but *how much that gap matters* for their target role in the real market. Third, our PathFinderAgent computes an ordered acquisition path using LEADS_TO prerequisite edges in Neo4j, turning an unordered list of missing skills into a navigable sequence — which this paper's roadmap generator cannot produce because it has no graph-based prerequisite structure.
