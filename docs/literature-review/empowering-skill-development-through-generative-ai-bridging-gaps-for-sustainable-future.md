# Empowering Skill Development Through Generative AI: Bridging Gaps for a Sustainable Future

**Authors:** Partha Majumdar  
**Year:** 2025  
**Published in:** The Scientific Temper, Volume 16, Special Issue 1, pp. 104–120 — DOI: 10.58414/SCIENTIFICTEMPER.2025.16.spl-1.14 (Published May 21, 2025)

---

## Problem Statement

Traditional career guidance systems are built around two structural constraints that limit their usefulness: they rely on static, historical data that does not reflect current skill demand, and they generate one-size-fits-all recommendations that do not adapt to the nuances of individual profiles. A freshly hired developer whose resume reads similarly to a five-year veteran's will receive the same generic advice — "learn leadership" or "get a PMP certification" — regardless of their actual experience, career stage, or the specific path they want to follow.

This paper proposes a generative AI pipeline that closes this gap by combining NLP-based explicit skill extraction (what a resume says the person can do) with GPT-4o's contextual inference of implicit skills (what the resume implies about deeper capabilities), then using that richer profile to drive role recommendations, research-based skill gap analysis, and a personalized development roadmap. The paper also situates this work within the UN Sustainable Development Goals, arguing that democratizing access to quality career guidance is a concrete contribution to reducing inequality (SDG 10) and improving access to education (SDG 4).

## Key Contributions & Objectives

1. A hybrid skill extraction approach combining spaCy NLP (explicit skills from explicit mentions) and GPT-4o inference (implicit skills inferred from contextual phrases like "managed a cross-functional team" → leadership, stakeholder management).
2. A multi-stage pipeline: resume parsing → hybrid skill extraction → GPT-4o role recommendation → ResearchGate scraping for research-trend mapping → GPT-4o skill gap analysis → personalized development report.
3. A Research Mapping step that scrapes ResearchGate to identify emerging skill trends for each recommended role — connecting current academic and industry research to individual learning priorities.
4. A retrospective validation methodology: 20 historical resumes (submitted 5 years prior) were run through the system, and predictions were compared against the individuals' actual 2025 career positions.
5. Alignment of the framework's design goals with SDGs 4, 8, 9, and 10 — making the case that AI-powered career guidance is a social equity intervention, not just a productivity tool.

## Methodology / Theory / Framework

The pipeline operates in four stages. Stage 1 (Skill Extraction): the user uploads a CV in DOCX or PDF format. spaCy tokenizes, POS-tags, and frequency-analyzes the text to extract explicit skill mentions (nouns and proper nouns). GPT-4o then reads the same text to infer implicit skills that explicit NLP cannot surface — for example, a phrase like "coordinated cross-departmental projects" becomes "project management, cross-functional communication." No data is stored; all processing is real-time. LinkedIn is deliberately excluded due to privacy, data inconsistency, and API restriction concerns.

Stage 2 (Role Recommendation): the combined explicit + implicit skill profile is submitted to GPT-4o with an engineered prompt that requests 3–5 role recommendations with justifications linking specific skills to role requirements. GPT-4o's broad training data enables it to reason across seniority levels from junior to executive.

Stage 3 (Research Mapping): for each recommended role, the system scrapes ResearchGate to identify current publications and research trends in the target domain — bridging the gap between what the candidate currently knows and what is actively emerging in their target field.

Stage 4 (Skill Gap Analysis and Report): GPT-4o compares the extracted skills to those required for the recommended role, distinguishes foundational knowledge from advanced proficiency, and produces a prioritized skill gap list with specific closing recommendations (certifications, courses, bootcamps). The full output is delivered as a user report.

## Software Tools / Setup Details

- OpenAI GPT-4o API (role recommendation, implicit skill extraction, gap analysis)
- spaCy (explicit skill extraction via NLP)
- ResearchGate (web scraping for research trend mapping)
- Test dataset: 20 historical resumes (no public benchmark dataset)

## Test / Experiment Analysis

The validation study used 20 real resumes submitted 5 years prior to the study date. The system's role recommendations for each resume were compared against the person's actual 2025 career position. Accuracy is reported per case and ranges from 50% to 95%, with a mode at 90–95%. Individual examples: Senior System Engineer → Senior Project Manager (95%), Tester → QA Manager (95%), Network Analyst → Technical Architect (80%), Database Administrator → Database Administrator (50%), Team Lead Information Security → Senior Manager Cyber Security (60%). The scatter plot shows a "sweet spot" at 8–15 years of experience where accuracy consistently exceeds 90%; accuracy degrades for profiles with more than 15 years of experience, falling to approximately 75% at 35 years.

## Test Data / Dataset Source

20 historical resumes obtained from individuals 5 years prior to the validation study. No named public benchmark dataset. No inter-rater reliability measurement for the accuracy scores.

## Final Result

The system correctly predicts career trajectories at 90%+ accuracy for most test cases, with performance peaking for mid-career professionals (8–15 years of experience). The hybrid NLP + GPT-4o skill extraction captures both what resumes say and what they imply, and the Research Mapping step connects the gap analysis to live academic research trends rather than static skill databases.

**What works well here:** The hybrid skill extraction approach is a genuine methodological contribution — combining spaCy's surface-level extraction with GPT-4o's contextual inference captures skills that keyword-matching systems systematically miss. The retrospective validation methodology is creative: by running old resumes through the system and checking against known outcomes, the study tests predictive validity without requiring a longitudinal prospective study. The 90–95% accuracy for mid-career professionals is a strong result, and the honest reporting of degraded performance at high experience levels adds credibility. The SDG framing, while sometimes stylistic in academic papers, here connects to a real argument about equitable access to personalized career advice.

## Limitations

The validation sample of 20 cases is far too small to draw statistically meaningful conclusions. The accuracy metric itself is not formally defined — it appears to reflect the research team's subjective judgment of how well the predicted role aligns with the actual outcome, not a computed similarity score against a ground truth taxonomy. No inter-rater reliability is reported, and with a single author, there is no check on scoring consistency. GPT-4o's role recommendations are drawn from its training data, which has a knowledge cutoff and reflects predominantly English-language, Western labor market norms — the paper does not address how well the system performs for non-Western career contexts or non-English resumes. The ResearchGate scraping for research mapping introduces a bias toward academic publications over practitioner skill development, which may not be aligned with what most job seekers actually need.

**The structural limitation:** The system recommends roles and produces skill gap reports, but it does not connect these to specific job postings in the actual current market. A student cannot see "these are the 47 jobs in your target city that match this skill profile" — they receive a generic, non-market-grounded roadmap.

## Final Summary

This paper demonstrates an effective generative AI pipeline for personalized career guidance that meaningfully advances beyond keyword-matching approaches by incorporating GPT-4o's contextual inference for implicit skill extraction. The retrospective validation study is a practical evaluation method for career guidance systems that other researchers in this space rarely employ.

**How CareerGraph does better:** CareerGraph grounds every step of the pipeline that this paper builds on generative AI inference in real market data. Our SkillGapAgent does not ask a language model which skills are needed — it computes the gap between a student's HAS_SKILL edges and the actual skills required by a specific target job in our database of real job postings. Our MarketAgent provides demand frequency for each missing skill based on current ingested data, not GPT-4o's training memory. Our NormalizationAgent maps extracted skills to O*NET/ESCO using fuzzy matching, not NLP inference — so when a student lists "managed cloud deployments," the skill is normalized to a taxonomy-aligned entity rather than an LLM-generated label. And our PathFinderAgent delivers an ordered learning path with LEADS_TO prerequisite semantics, whereas this paper's pipeline stops at a prioritized skill gap list without explaining what order the student should address it.
