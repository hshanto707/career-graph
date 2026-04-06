# Skill-Pulse: An Intelligent Decision Support Architecture for Dynamic Workforce Allocation

**Authors:** S. Gnanapriya, Athira R  
**Year:** 2026  
**Published in:** International Journal of Scientific Research in Engineering and Management (IJSREM), Volume 10, Issue 2, February 2026 — DOI: 10.55041/IJSREM56372

---

## Problem Statement

Traditional labor market intelligence platforms are built around a batch-processing model that is fundamentally mismatched to how workforce planning actually works: they produce historical snapshots, disaggregate their analysis into siloed reports (a forecast tool here, a geospatial map there, a career path engine somewhere else), and offer no unified view of the interplay between demand trends, skill gaps, workforce risk, and individual career trajectories. Job seekers, enterprises, and policymakers all need answers from the same underlying data, but existing tools force each audience to navigate a different fragmented system.

This paper introduces Skill-Pulse AI — a unified Streamlit-based platform integrating predictive, diagnostic, and prescriptive analytics for workforce intelligence in a single interface, with persona-based views tailored to individual job seekers versus institutional stakeholders.

## Key Contributions & Objectives

1. A unified multi-analytics architecture integrating seasonality-aware demand forecasting, Isolation Forest-based anomaly detection, graph-based career path optimization, semantic resume parsing, and policy simulation in a single platform.
2. Multi-scenario demand forecasting (conservative, moderate, aggressive projections) with uncertainty bounds, decomposing labor demand signals into trend and seasonal components.
3. Isolation Forest-based unsupervised anomaly detection trained on multidimensional labor indicators (demand intensity, salary distribution, growth rate) to identify high-risk, volatile skill segments — a capability not present in any other system in this review.
4. Graph-based career path optimization using Dijkstra's algorithm on a weighted graph (edges weighted by salary variation and market gap), with NetworkX as the computation backend.
5. Semantic resume parsing using PyPDF2/Python-DOCX and pattern matching to compute a "market readiness score" for each uploaded resume against current demand data.
6. Policy simulation modules for grant-to-employment ROI estimation — enabling policymakers to test training investment scenarios before committing resources.

## Methodology / Theory / Framework

The system follows a layered modular architecture. The data ingestion layer normalizes labor market data, applies city-wise filtering, and resolves geographic coordinates via Geopy. The forecasting layer decomposes demand signals into trend and seasonal components, then generates three scenarios (conservative, moderate, aggressive) with uncertainty bounds. The anomaly detection layer trains an Isolation Forest on multidimensional indicators — demand intensity, salary distribution, and growth rate — and flags skill segments that score anomalously across multiple dimensions simultaneously. The skill gap analysis layer extracts skills from uploaded resumes via document parsing and semantic pattern matching, then computes a market readiness score by comparing extracted skills to current demand signals. The career path layer models skills and roles as a weighted directed graph, running Dijkstra's shortest path algorithm with edges weighted by salary variation and market gap to produce optimized career transition routes. The policy layer simulates grant-to-employment ROI under different investment assumptions.

The data is a hybrid of structured real labor market datasets and synthetic signal generation to fill coverage gaps — specifically for Indian metro context, with Mumbai used as the primary exemplar.

## Software Tools / Setup Details

- Python (core), Streamlit (UI/deployment)
- NumPy, Pandas (data processing)
- Scikit-learn (Isolation Forest anomaly detection)
- NetworkX (graph-based career path modeling)
- Geopy (geocoding and geospatial resolution)
- Plotly (interactive charts, geospatial maps, network visualizations)
- PyPDF2, Python-DOCX (resume parsing)
- Data: hybrid structured labor market datasets + synthetic data generation (Indian metro context, Mumbai modeled)

## Test / Experiment Analysis

The paper presents simulated results for 5 job roles in a Mumbai metro labor market. No benchmark comparisons against prior systems are reported; no holdout accuracy metrics (RMSE, F1-score) are provided. Results are primarily visualizations of the system's output for the modeled scenario.

Simulated demand figures for Mumbai IT roles:

| Role | Demand | Gap | Avg. Salary (INR) | Growth (%) |
|---|---|---|---|---|
| Software Engineer | 2,060 | 659 | ₹2,142,743 | 14.37% |
| Data Scientist | 1,666 | 533 | ₹2,020,006 | 4.10% |
| UI/UX Designer | 4,371 | 1,398 | ₹1,689,911 | 16.45% |
| Product Manager | 1,969 | 630 | ₹1,820,455 | 18.82% |
| Cloud Architect | 2,384 | 762 | ₹1,846,025 | 12.97% |

## Test Data / Dataset Source

Hybrid dataset: structured labor market data combined with synthetic signal generation for the Indian metro market context. No named public dataset, no dataset size specification, and no description of how the real-data and synthetic-data components are balanced or validated against each other.

## Final Result

Skill-Pulse AI demonstrates a unified platform that integrates capabilities typically spread across multiple separate tools — forecasting, anomaly detection, resume analysis, career path optimization, and policy simulation — in a single Streamlit interface with persona-based views. The Isolation Forest-based anomaly detection for identifying high-risk skill segments is an architecturally novel contribution in the labor market intelligence space.

**What works well here:** The breadth of the platform is genuinely impressive — combining demand forecasting, anomaly detection, resume analysis, career pathfinding, and policy simulation in one interface is an ambitious integration that most systems in this space avoid by narrowing their scope. The anomaly detection component for flagging volatile skill segments is not present in any other system in this review and addresses a real need for risk-aware workforce planning. The multi-scenario forecasting with uncertainty bounds is more epistemically honest than point-estimate demand projections, and the persona-based interface distinction between job seekers and institutional users reflects real-world deployment requirements.

## Limitations

The evaluation is built entirely on simulated or synthetic data, with no validation against real labor market outcomes. The demand, gap, salary, and growth figures are produced by a model trained on partially synthetic data — it is not possible to assess whether they reflect actual market conditions. Resume analysis uses pattern matching rather than semantic embeddings or NLP-based entity recognition, which limits its ability to handle the diverse ways skills are described in real resumes. The forecasting uses trend-seasonality decomposition rather than deep sequence models (LSTM, Transformer), which may underperform for labor markets with complex non-linear dynamics. There is no real-time job portal API integration, so the platform cannot be kept current without manual data updates. The city-level aggregation limits applicability to sub-city, neighborhood, or firm-level granularity — relevant for students choosing between employers rather than cities.

**The deeper limitation:** The platform is designed for workforce planners and HR departments, not for individual students. The career path optimization produces the shortest route between occupations, but it does not account for where a specific student is currently positioned or what their proficiency level is in each skill. A student with intermediate Python and no data science background would receive the same career path recommendation from Data Analyst to Data Scientist as a student with advanced Python and three years of analytics experience.

## Final Summary

Skill-Pulse AI is the most ambitions workforce intelligence platform in this review in terms of functional scope. The combination of anomaly detection, multi-scenario forecasting, and policy simulation under one roof, with persona-based views, represents a design vision that goes significantly beyond most academic prototypes in this space.

**How CareerGraph does better:** Skill-Pulse AI is designed for the institutional level — HR departments, policymakers, enterprise workforce planners. CareerGraph is designed for the individual student. Our SkillGapAgent computes a personalized readiness score for a specific student against a specific target job, incorporating their actual proficiency weights on each skill — something Skill-Pulse's market readiness score does not do. Our PathFinderAgent produces an ordered, prerequisite-aware learning path grounded in O*NET/ESCO taxonomy, not just a shortest Dijkstra path weighted by salary variation. And CareerGraph's market signals come from a real, re-ingestable job posting database — not synthetic data — which means the demand figures students see are backed by actual job posting evidence, not model-generated estimates. The anomaly detection capability Skill-Pulse introduces for high-risk skill segments is an idea worth incorporating into CareerGraph's MarketAgent as a future enhancement: surfacing which skills in a student's learning path are in volatile demand categories would be genuinely actionable guidance.
