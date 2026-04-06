# An LLM-Powered Agent for Real-Time Analysis of the Vietnamese IT Job Market

**Authors:** Nguyen Minh Duc, Vo-Thanh Minh Nguyen, Dinh Hoang Long, Phan Xuan Vinh, Mai Thanh Nhan, Lê Hoàng Hiệp  
**Year:** 2025  
**Published in:** arXiv preprint arXiv:2511.14767v1 (26 September 2025)

---

## Problem Statement

Understanding the real-time state of a labor market requires dealing with two compounding problems at once: the data is moving (job postings appear and expire daily), and the questions people want answered are diverse and unpredictable (What skills are most in demand? How is seniority distributed across companies? Which combinations of skills appear together most often?). Static dashboards and fixed SQL reports cannot handle this — they answer the questions their authors thought to ask, and nothing else.

This paper argues that a ReAct-based LLM agent, equipped with a suite of database and analysis tools, can answer arbitrary natural language questions about a live job market dataset — and do it better than a non-agentic LLM that only has text generation capabilities. The authors demonstrate this on the Vietnamese IT job market, which is underrepresented in existing labor market research despite being a fast-growing technology sector.

## Key Contributions & Objectives

1. Builds a complete job market analysis system for the Vietnamese IT sector: a Playwright-based crawler, an LLM-based parser (Gemini 2.5), a PostgreSQL + pgvector storage layer, a ReAct agent with four specialized tools, and a Streamlit frontend.
2. Collects and structures 3,745 Vietnamese IT job postings across 755 companies and 288 unique skills (July 1–August 8, 2025) — the largest structured Vietnamese IT job market dataset described in recent work.
3. Demonstrates that a ReAct agentic approach outperforms vanilla LLM responses across four key dimensions: data source (real-time database vs. static training data), verifiability (citable counts vs. unverifiable claims), analytical capability (SQL aggregation + visualization vs. text generation), and knowledge currency (live 2025 data vs. training cutoff).
4. Identifies the top demanded skills in the Vietnamese IT market: Requirements Analysis (1,583 postings), Business Analysis (1,571), English (1,538), Leadership (1,365), and Agile/Scrum (1,358).
5. Surfaces a seniority structure dominated by mid-level roles (Senior 36.3%, Mid-level 25.0%) with relatively few entry-level positions — a finding with direct implications for recent graduates.

## Methodology / Theory / Framework

The pipeline has three stages. In Stage 1, a Python crawler built on Playwright scrapes job listings from TopCV (a major Vietnamese job portal), handling JavaScript-rendered pages and pagination. In Stage 2, a structured LLM parser using Gemini 2.5 extracts key fields — job title, company, required skills, experience level, salary range — from raw HTML content and stores them as normalized records in PostgreSQL, with skill embeddings stored in pgvector for semantic search.

In Stage 3, a ReAct (Reasoning + Acting) agent answers user questions through iterative Thought → Action → Observation cycles. The agent has four tools available: a SQL execution tool for structured aggregate queries, a semantic search tool (pgvector cosine similarity for skill-related retrieval), a visualization tool (matplotlib/seaborn chart generation), and a career advisor tool (RAG-based guidance generation from retrieved context). The agent selects which tool to invoke at each step based on the question type, reads the observation, and either completes the answer or continues the reasoning loop.

The non-agentic baseline is a vanilla Gemini 2.5 prompt without tool access — the comparison illustrates concretely where tool-augmented agents add value.

## Software Tools / Setup Details

- Playwright (Python) for JavaScript-rendered page crawling
- Gemini 2.5 Flash as the LLM backbone for both parsing and agent reasoning
- PostgreSQL for structured job data storage; pgvector extension for skill embeddings
- LangGraph for ReAct agent orchestration
- Matplotlib and Seaborn for visualization generation
- Streamlit for the user-facing analysis interface
- Dataset: 3,745 job postings, 755 companies, 288 unique skills, July 1–August 8, 2025

## Test / Experiment Analysis

The paper does not report formal quantitative evaluation metrics (no precision, recall, or user study). Evaluation is qualitative: the authors compare agentic vs. non-agentic responses to the same natural language questions side by side. A four-dimension comparison table distinguishes the approaches: data source, verifiability, analytical capability, and knowledge currency. Example queries shown include "What are the top demanded skills?" and "Which seniority level has the highest demand?" — the agent produces SQL results with bar charts; the vanilla LLM produces plausible but unverifiable text.

Case study findings: top-5 demanded skills are Requirements Analysis, Business Analysis, English, Leadership, and Agile/Scrum. Seniority distribution: Senior (36.3%), Mid-level (25.0%), Junior (15.6%), Fresher (8.2%), Intern (14.9%). The agent can answer follow-up questions about specific companies or skill co-occurrences that the vanilla LLM cannot.

## Test Data / Dataset Source

3,745 IT job postings scraped from TopCV (topcv.vn), covering July 1–August 8, 2025. 755 distinct companies, 288 unique skill entities extracted by Gemini 2.5. Data is Vietnam-specific and not publicly released.

## Final Result

The ReAct agent successfully answers a range of market analysis questions with SQL-backed, visualized, and verifiable responses that vanilla LLM cannot produce. The crawl-to-insight pipeline is fully automated: new job postings can be re-crawled and re-analyzed without manual intervention.

**What works well here:** The ReAct framework applied to labor market analysis is a clean and compelling architectural choice. Giving the agent distinct tools — SQL for aggregation, semantic search for concept-based retrieval, visualization for output rendering, and RAG for career advice — mirrors how a human analyst would approach these questions, and the tool separation prevents the agent from hallucinating numbers it can't support. The seniority distribution finding (Senior-dominated, few entry-level) is a practically significant insight for fresh graduates that most static dashboards miss because they don't ask the question. The paper is also honest that this is a proof of concept — it does not overclaim.

## Limitations

The 3,745-job dataset covers only 39 days from a single Vietnamese job portal (TopCV), which limits both the temporal depth and market coverage. Skill extraction is done purely by an LLM (Gemini 2.5) without validation against a standardized taxonomy like ESCO or O*NET — meaning "Requirements Analysis" and "Business Analysis" appear as separate skills despite substantial overlap, and skills with different surface forms may be double-counted. There is no formal accuracy evaluation of the agent's answers: the comparison to vanilla LLM is qualitative and cherry-picked. The career advisor tool is RAG-based but the quality of its guidance depends entirely on retrieval quality, which is not measured.

**The deeper limitation:** The system answers population-level questions about the market ("what are the top skills demanded?") but cannot answer student-level questions ("given that I already know Python and SQL, what should I learn next to qualify for a Senior Data Engineer role?"). It is a market observatory, not a student navigator.

## Final Summary

This paper demonstrates that a ReAct-based LLM agent with database tools can turn a live job posting dataset into a responsive, queryable market intelligence platform — a significant practical contribution for markets like Vietnam that lack structured labor data infrastructure. The four-tool architecture (SQL, semantic search, visualization, RAG advisor) is a clean reference design for AI-augmented market analysis.

**How CareerGraph does better:** CareerGraph addresses both halves of the problem this paper tackles — and the half it leaves unaddressed. Our IngestionAgent and MarketAgent do what this paper's crawler and ReAct agent do: ingest real job postings and answer demand-level questions about which skills are most required. But CareerGraph goes further by connecting that market data directly to individual students: our SkillGapAgent computes a personalized readiness score against a specific target job using the student's own HAS_SKILL edges in Neo4j, and our PathFinderAgent produces an ordered skill acquisition path using LEADS_TO prerequisite chains. The Vietnamese paper can tell a student that "Requirements Analysis is the top demanded skill" — CareerGraph tells them whether they're already on track to develop it, how many prerequisite skills they still need, and which course to take first.
