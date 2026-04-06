# AI-Powered Career Planning Using Multi-Agent Systems and Large Language Models

**Authors:** Sanat Nanasaheb Ladkat, Manisha Prakash Bharati  
**Year:** 2025  
**Published in:** International Journal for Multidisciplinary Research (IJFMR), Volume 7, Issue 3, May–June 2025 — E-ISSN: 2582-2160, Article ID: IJFMR250346587

---

## Problem Statement

Career planning tools have a long history of being either too generic to be useful or too rigid to be adaptable. Static aptitude tests offer one-time snapshots. Database-driven platforms match keywords without reasoning about context. Cloud-based AI tools require sending sensitive personal information to external servers and incur unpredictable API costs. What is missing is a system that can reason sequentially about a user's profile — understanding not just what skills they have, but which careers those skills enable, what skills each career requires, and how to build a realistic timeline to bridge the gap — while doing this locally, privately, and at low cost.

This paper builds exactly that system: a four-agent pipeline running on local LLMs via Ollama, orchestrated end-to-end from free-text user input to a downloadable, milestone-structured career roadmap.

## Key Contributions & Objectives

1. A modular four-agent architecture — Profile Agent, Career Agent, Skills Agent, and Roadmap Agent — where each agent has a role-specific prompt template and passes structured JSON outputs to the next.
2. Local LLM inference via Ollama (hosting DeepSeek or LLaMA models), eliminating cloud data-transfer costs and user data privacy risks inherent in OpenAI/Anthropic API-based tools.
3. A Streamlit-based interactive frontend with iterative exploration: users can revisit any stage, change career targets, and receive an updated roadmap without restarting the session.
4. Downloadable PDF career roadmap output as a concrete deliverable a student can keep and share.
5. An empirical evaluation with 20 volunteers showing 85% high relevance for career recommendations, 90% skill mapping precision, and 4.5/5 clarity rating — completed in under 20 seconds end-to-end.

## Methodology / Theory / Framework

The system operates as a sequential multi-agent pipeline. The Profile Agent receives free-text user input (education, experience, interests, goals) and structures it into a validated JSON schema. The Career Agent receives this structured profile and prompts the LLM to return 3–5 career options with demand outlook, pros/cons, and suitability rationale. The Skills Agent takes the user's chosen career and returns a prioritized list of hard skills, soft skills, and certifications alongside curated learning resources. The Roadmap Agent synthesizes all prior outputs into a monthly/quarterly milestone timeline. All four agents query the same locally hosted model via Ollama's REST interface. Session state persists throughout via Streamlit's `st.session_state`, so earlier profile decisions inform later roadmap steps.

The central design decision is locality: by running inference entirely on a 16GB RAM + GPU laptop, the system avoids the latency, cost variability, and data exposure risks of cloud APIs.

## Software Tools / Setup Details

- LLM inference: Ollama with DeepSeek or LLaMA models (open-source)
- Frontend: Streamlit (Python)
- Optional backend: FastAPI for scaled deployment
- Hardware requirement: 16 GB RAM + GPU
- Evaluation: 20 volunteers (10M/10F), ages 18–30, across Engineering, Arts, Commerce, Design, and Humanities — ~10 minutes per session

## Test / Experiment Analysis

20 volunteer users evaluated the system using a structured protocol: they provided their own career background and goals, went through the full four-agent pipeline, and rated outputs on a 5-point Likert scale covering clarity, usability, and trust. Career relevance was rated by the evaluators comparing system recommendations against their own career research. Skill mapping precision was assessed by comparison with industry job posting requirements.

Results: relevance accuracy 85% highly relevant (10% moderate), skill mapping precision 90%, average latency under 20 seconds total (Profile: 3.2s, Career: 5.8s, Skills: 6.1s, Roadmap: 4.4s). User satisfaction ratings: Clarity 4.5/5, Usability 4.3/5, Trust 4.1/5. Compared to cloud-based tools, the system was 30% faster end-to-end and scored 50% higher on perceived personalization.

## Test Data / Dataset Source

No external dataset. The 20-volunteer study used participants' own real career profiles as input. No public dataset or ground truth career taxonomy was used for validation.

## Final Result

The four-agent pipeline delivers a complete, personalized career plan in under 20 seconds with strong relevance and user satisfaction scores. The local LLM architecture achieves this without any external API dependency — a meaningful practical differentiator for institutions concerned about student data privacy.

**What works well here:** The four-agent modular design is clean and extensible — each agent has a single responsibility, and the structured JSON handoffs between agents prevent error propagation from unstructured text passing. The decision to run locally rather than via cloud APIs is well-motivated and distinguishes this system from tools like GPT-4-based assistants that expose user data and have unpredictable per-token costs. The user satisfaction scores (4.1–4.5 across all dimensions) from a heterogeneous background group (not just CS students) suggest the system's language is accessible.

## Limitations

The evaluation sample is very small (n=20) and the methodology — volunteer self-assessment of relevance — introduces significant subjectivity. There is no comparison against a rigorous baseline beyond broad characterizations of "cloud-based tools." Output quality is entirely contingent on the quality of the locally hosted model: a weaker DeepSeek variant will produce noticeably worse roadmaps than GPT-4, and the paper does not report model-specific benchmarks. The system has no connection to real job posting data — career demand outlooks and skill priority lists are drawn entirely from the LLM's training data, which has a knowledge cutoff. For fast-moving fields (AI engineering, GenAI tooling, cybersecurity), this means recommendations may already be outdated at deployment.

**The deeper limitation:** The system cannot tell a student whether their target career is actually achievable from their current position in a specific labor market. It produces a generic "what you need to do" roadmap, but not a "what the market in your city needs" gap analysis. LLM-generated timelines are plausible-sounding but not grounded in empirical data about how long workers actually take to transition between roles.

## Final Summary

This paper describes a practical and well-architected local multi-agent system for career planning. The local LLM approach, clean four-agent pipeline, and sub-20-second end-to-end response time are genuine engineering contributions. The user satisfaction results are encouraging for an early prototype.

**How CareerGraph does better:** CareerGraph's multi-agent architecture has the same modular separation of concerns — IngestionAgent, SkillGapAgent, MarketAgent, PathFinderAgent, ReasoningAgent — but grounds every agent's output in real data rather than LLM priors. Our MarketAgent queries an actual database of ingested job postings to compute skill demand frequencies; this paper's Career Agent generates demand outlooks from a language model's training memory. Our PathFinderAgent traverses LEADS_TO prerequisite edges derived from real co-occurrence patterns in job postings, producing an empirically ordered learning path; this paper's Roadmap Agent produces a timeline from prompt-engineered inference. The difference matters most in fast-moving domains: CareerGraph's market data can be re-ingested from new job postings, while a locally hosted LLM's knowledge is frozen at its training cutoff.
