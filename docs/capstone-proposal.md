# Capstone Project Proposal

**Project Title:** CareerGraph — Agent-Based Job Market Intelligence Platform for Student Career Guidance

**Student Name:** [Your Name]

**Supervisor Name:** [Supervisor Name]

**Date:** April 2026

---

## Introduction

University students frequently struggle to align their academic skillsets with the real demands of the jobmarket. Existing career guidance tools tend to offer generic advice disconnected from live job market data, leaving students without actionable direction when planning their careers. CareerGraph addresses this gap by building an intelligent, data-driven platform that ingests real job market data, models it as a knowledge graph, and delivers personalized, explainable career guidance to students.

The platform combines graph-based reasoning with a multi-agent intelligence engine to generate skill gap analyses, ordered learning roadmaps, and job recommendations — all grounded in real jobmarket demand. Rather than relying on opaque machine learning models, CareerGraph uses a transparent, algorithmic agent architecture augmented optionally with large language model (LLM) explanations, ensuring outputs are interpretable and actionable.

---

## Problem Statement

Students entering the job market often lack clarity on which specific skills are most valued by employers for their target roles, and how to prioritize skill acquisition efficiently. Generic career portals and university advising systems fail to connect individual skill profiles to real-time market demand. This disconnect results in misaligned expectations, skill gaps that go unaddressed until job rejection, and an inability to plan a concrete, ordered learning path toward a target role (Robst, 2007).

Furthermore, existing tools rarely explain _why_ a particular recommendation was made, reducing student trust and engagement. What is needed is a system that combines real jobmarket data, graph-based skill modeling, and explainable reasoning to provide students with personalized, transparent, and actionable career intelligence.

---

## Objectives

- **Skill Gap Analysis:** Enable students to receive a data-driven readiness score for their target roles by comparing their declared skills against real job market requirements using weighted graph intersection algorithms.
- **Ordered Learning Roadmap:** Generate a personalized, step-by-step skill acquisition roadmap by traversing a skill prerequisite graph using breadth-first search (BFS) and topological sort, guiding students from their current state to job readiness.
- **Explainable Recommendations:** Deliver job recommendations and plain-English explanations of skill gaps via a modular intelligence engine that pairs algorithmic agents with a pluggable LLM reasoning layer (supporting Claude, OpenAI, or local Ollama models).

---

## System Architecture

CareerGraph is structured as a full-stack web application composed of three primary layers: a React frontend, a FastAPI backend housing the Intelligence Engine, and a dual-database data layer (PostgreSQL + Neo4j).

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Frontend — React / TypeScript / Vite            │
│   Login · Dashboard · Profile · Job Explorer · Skill Analysis│
└────────────────────┬────────────────────────────────────────┘
                     │ REST + JWT
┌────────────────────▼────────────────────────────────────────┐
│                   Backend — FastAPI (Python 3.11)            │
│                                                              │
│   Student Routers: auth · profile · jobs · skills ·          │
│                    recommendations · gap-analysis ·           │
│                    market · dashboard                         │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐  │
│   │               Intelligence Engine                     │  │
│   │                                                       │  │
│   │   EngineOrchestrator                                  │  │
│   │        │                                              │  │
│   │   ┌────┴──────────────────────────────────────────┐  │  │
│   │   │  Ingestion Pipeline                           │  │  │
│   │   │  IngestionAgent → NormalizationAgent → Neo4j  │  │  │
│   │   └───────────────────────────────────────────────┘  │  │
│   │        │                                              │  │
│   │   ┌────┴──────────────────────────────────────────┐  │  │
│   │   │  Algorithmic Agents (no LLM dependency)       │  │  │
│   │   │  SkillGapAgent · RecommendationAgent          │  │  │
│   │   │  PathFinderAgent · MarketAgent                │  │  │
│   │   └───────────────────────────────────────────────┘  │  │
│   │        │                                              │  │
│   │   ┌────┴──────────────────────────────────────────┐  │  │
│   │   │  ReasoningAgent                               │  │  │
│   │   │  LLMProvider (Claude / OpenAI / Ollama)       │  │  │
│   │   └───────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────┘  │
│                                                              │
│   GraphService — Cypher query abstraction over Neo4j         │
└───────────┬──────────────────────────┬──────────────────────┘
            │                          │
┌───────────▼──────────┐  ┌────────────▼──────────────────────┐
│  PostgreSQL 15        │  │  Neo4j 5 — Knowledge Graph         │
│  Users & Auth Profiles│  │  Student · Skill · Job · Course    │
└──────────────────────┘  └────────────────────────────────────┘
```

### Intelligence Engine — Agent Roles

| Agent               | Type        | Responsibility                                                         |
| ------------------- | ----------- | ---------------------------------------------------------------------- |
| IngestionAgent      | Ingestion   | Parses the custom job postings CSV and validates schema                |
| NormalizationAgent  | Ingestion   | Resolves skill synonyms (`ReactJS → React`); deduplicates; feeds Neo4j |
| SkillGapAgent       | Algorithmic | Computes weighted readiness score via graph intersection               |
| RecommendationAgent | Algorithmic | Ranks job matches using Jaccard + partial skill overlap                |
| PathFinderAgent     | Algorithmic | Generates ordered learning roadmaps via BFS + topological sort         |
| MarketAgent         | Algorithmic | Aggregates market-wide skill demand trends                             |
| ReasoningAgent      | LLM-powered | Wraps algorithmic outputs in natural language explanations             |

### Knowledge Graph Schema (Neo4j)

The core data model is a property graph with five node types and five relationship types:

- **Nodes:** `Student`, `Skill`, `Job`, `Course`, `Category`
- **Relationships:**
  - `(Student)-[:HAS_SKILL {proficiency, years}]->(Skill)`
  - `(Student)-[:TARGETS]->(Job)`
  - `(Job)-[:REQUIRES {importance, frequency}]->(Skill)`
  - `(Skill)-[:LEADS_TO {difficulty_jump}]->(Skill)`
  - `(Course)-[:TEACHES]->(Skill)`

This structure enables graph traversal queries that would be expensive or impossible in a relational model — specifically the BFS prerequisite traversal used by PathFinderAgent and the skill intersection queries used by SkillGapAgent.

### Data Sources

- **Custom Job Postings Dataset** (`kaggle_jobs.csv`) — A hand-crafted dataset of 10,000 realistic job postings authored for this project. Each record includes job title, company, location, employment type, salary range, and a structured list of required skills. The dataset is designed to reflect realistic distributions of roles, industries, and skill demands across the software engineering and data science job market, ensuring the Intelligence Engine is grounded in representative, high-quality input data rather than noisy, uncontrolled scraped content.
- **Synonym Map** (`synonyms.json`) — A curated skill alias mapping (e.g., `ReactJS → React`, `Node → Node.js`) used by NormalizationAgent to canonicalize skill names before graph insertion, ensuring graph consistency across varied skill representations in the dataset.

### Technology Stack

| Layer               | Technologies                                                    |
| ------------------- | --------------------------------------------------------------- |
| Frontend            | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, React Query |
| Backend             | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy, Alembic |
| Intelligence Engine | Custom agent classes, rapidfuzz (skill matching), pandas (ETL)  |
| LLM Providers       | Anthropic SDK (Claude), OpenAI SDK (GPT-4o), Ollama (local)     |
| Databases           | PostgreSQL 15 (relational), Neo4j 5 (graph)                     |
| Infrastructure      | Docker Compose, python-dotenv, JWT authentication               |

---

## Expected Outcomes

Upon completion, CareerGraph will deliver:

1. A working full-stack web application deployable via Docker Compose, accessible to students through a browser-based interface.
2. A functional Intelligence Engine capable of producing skill gap scores, ranked job recommendations, ordered learning roadmaps, and market demand summaries — all derived from the custom-authored job postings dataset.
3. An LLM-augmented reasoning layer that generates plain-English explanations of all algorithmic outputs, with graceful degradation to structured results when no LLM provider is configured.
4. A Neo4j knowledge graph populated with 10,000+ job nodes, 500+ skill nodes, and their interconnecting relationships, queryable via the GraphService Cypher abstraction layer.
5. A demonstrated alignment between student skill profiles and real jobmarket demand, validated through end-to-end user journey testing across the platform's core flows: registration, skill gap analysis, roadmap generation, and job recommendation.

---

## References

Robst, J. (2007). Education and job match: The relatedness of college major and work. _Economics of Education Review_, _26_(4), 397–407. https://doi.org/10.1016/j.econedurev.2006.08.003

Robinson, I., Webber, J., & Eifrem, E. (2015). _Graph databases: New opportunities for connected data_ (2nd ed.). O'Reilly Media.

Amershi, S., Begel, A., Bird, C., DeLine, R., Gall, H., Kamar, E., Nagappan, N., Nushi, B., & Zimmermann, T. (2019). Software engineering for machine learning: A case study. _Proceedings of the 41st International Conference on Software Engineering: Software Engineering in Practice_, 291–300. https://doi.org/10.1109/ICSE-SEIP.2019.00042
