# CareerGraph — Research Contribution and Differentiation

**Document Purpose:** This document presents CareerGraph's original research contributions by comparing the system against three closely related prior works. It is intended to support the supervisor's assessment of novelty and the academic contribution of this capstone project.

---

## Selected Prior Works

Three papers were selected from the literature review as the closest comparators to CareerGraph. Each overlaps with one of the system's three core design pillars:

| Paper | Core Overlap |
|---|---|
| Weichselbraun et al. (2022) — *CareerCoach* | Knowledge graph construction + skill gap recommender |
| Ladkat & Bharati (2025) — *AI-Powered Career Planning with MAS and LLMs* | Multi-agent pipeline + LLM-driven career planning |
| José-García et al. (2022) — *C3-IoC* | Student-targeted skill assessment + labor market matching |

---

## Paper 1: Weichselbraun et al. (2022) — CareerCoach

**Citation:** Weichselbraun, A., Waldvogel, R., Fraefel, A., van Schie, A., & Kuntschik, P. (2022). Building knowledge graphs and recommender systems for suggesting reskilling and upskilling options from the web. *Information, 13*(11). MDPI.

### What They Do

CareerCoach builds a knowledge graph from 488 Swiss and German education provider websites (97,142 course descriptions, 73,969 nodes, 734,447 edges) and uses it to recommend career paths and upskilling courses. The skill gap is computed as the ratio of missing skills to total target skills: `|target \ user| / |target|`. Courses are scored by a weighted combination of skill specificity (IDF-style uniqueness) and total gap coverage. A fine-tuned DistilBERT model handles entity recognition. The system was deployed in production by three commercial companies.

### What CareerGraph Does Differently

| Dimension | CareerCoach (Weichselbraun et al.) | CareerGraph |
|---|---|---|
| **Student representation** | No student node in the graph. User profiles are computed on-the-fly from free-text input and are not persisted across sessions. | Students are first-class graph nodes in Neo4j with persistent `HAS_SKILL {proficiency: 0–10, years: float}` edges. Skills, proficiency levels, and career history are part of the graph and evolve over time. |
| **Skill gap formula** | Binary: skill is present or absent. No proficiency weighting. | Weighted readiness score: `must_score × 0.7 + nice_score × 0.3 + proficiency_bonus`. Distinguishes must-have from nice-to-have skills and rewards deeper proficiency. |
| **Learning path generation** | Recommends courses but cannot order them. No mechanism to say "learn A before B." | PathFinderAgent traverses `LEADS_TO {difficulty_jump}` prerequisite edges via BFS and applies topological sort, producing an ordered skill acquisition sequence from the student's current state to the target role. |
| **Skill normalization** | Entity linking has ~45% miss rate for skills not in the knowledge base, requiring NER fallback and manual review. | NormalizationAgent combines a curated synonym map (e.g., `ReactJS → React`) with rapidfuzz fuzzy matching at a ≥90 similarity threshold, resolving surface-form variation without manual correction. |
| **Explainability** | Ranked lists of careers and courses with scoring rationale. No natural language explanation. | All algorithmic outputs optionally pass through a ReasoningAgent that generates a plain-English explanation via Claude, GPT-4o, or Ollama — with graceful degradation to structured template responses when no LLM is configured. |
| **Market coverage** | German-speaking Swiss labor market only. Domain-specific DistilBERT model required. | Designed around O*NET skill taxonomy and a Kaggle job postings dataset, with an architecture that accepts any CSV-formatted job corpus without model fine-tuning. |

### Original Contribution Over This Work

CareerGraph extends CareerCoach's core concept (KG + skill-gap recommender) by solving what the authors identified as their primary limitation: the absence of a persistent student model. Where CareerCoach treats each session as stateless, CareerGraph models the student as a live node in the knowledge graph, enabling proficiency-aware gap scoring, time-tracked skill growth, and a graph-traversal learning path that CareerCoach's recommender cannot produce. The ordered prerequisite roadmap — enabled by `LEADS_TO` edges and topological sort — is a structural capability that CareerCoach does not have.

---

## Paper 2: Ladkat & Bharati (2025) — AI-Powered Career Planning with MAS and LLMs

**Citation:** Ladkat, S. N., & Bharati, M. P. (2025). AI-powered career planning using multi-agent systems and large language models. *International Journal for Multidisciplinary Research (IJFMR), 7*(3). E-ISSN: 2582-2160.

### What They Do

This paper builds a four-agent pipeline (Profile Agent → Career Agent → Skills Agent → Roadmap Agent) that runs on locally hosted LLMs via Ollama. Each agent receives structured JSON from the previous agent and queries the language model for the next output. The entire career plan — from profile structuring to milestone roadmap — is generated purely by LLM inference on the user's free-text input. The system runs on a local 16 GB RAM + GPU machine and produces a complete career plan in under 20 seconds. A 20-volunteer study reported 85% career relevance, 90% skill mapping precision, and 4.5/5 clarity.

### What CareerGraph Does Differently

| Dimension | Ladkat & Bharati (2025) | CareerGraph |
|---|---|---|
| **Grounding of recommendations** | All career demand signals, skill priorities, and roadmap timelines are drawn from LLM training data. No connection to real job posting data. | Every agent output is grounded in an ingested corpus of real job postings. Skill demand frequencies are computed from actual `REQUIRES` edge counts across 10,000+ job nodes — not inferred from model weights. |
| **Staleness** | Recommendations can only be as current as the LLM's training cutoff. Skills that emerged after the cutoff (e.g., GenAI tooling, MLOps) are absent or underweighted. | The IngestionAgent re-ingests new job posting data on demand. Skill demand reflects the current corpus, not a frozen snapshot. |
| **Algorithmic transparency** | No deterministic computation. Outputs are LLM generations — plausible-sounding but non-reproducible and non-auditable. | Four pure algorithmic agents (SkillGapAgent, RecommendationAgent, PathFinderAgent, MarketAgent) produce deterministic, unit-testable outputs using Jaccard similarity, BFS, and Kahn's topological sort. The LLM layer is strictly optional and sits on top of these results as an explanation wrapper. |
| **LLM dependency** | LLM is the core logic. The system cannot function without a running Ollama instance. Hardware requirement: 16 GB RAM + GPU. | LLM is optional. All intelligence functions (gap analysis, recommendations, roadmap, market trends) return structured, actionable responses when no LLM provider is configured. Graceful degradation is a design requirement (NFR-02), not an afterthought. |
| **Skill profile representation** | User profile is a free-text description processed by the Profile Agent. No persistent storage or proficiency model. | Student profile is stored relationally in PostgreSQL (auth/profile) and as a graph node in Neo4j with typed, proficiency-weighted `HAS_SKILL` edges. Profile persists across sessions. |
| **Labor market specificity** | The Career Agent generates demand outlooks from LLM priors. It cannot say whether a given role is in demand in a student's city or sector. | MarketAgent aggregates `REQUIRES` edge counts per skill across all ingested jobs. Market trend output reflects what the actual dataset says, not what the model guesses. |
| **Evaluation rigor** | n=20 volunteers, self-assessed relevance. No ground-truth baseline. | 87 unit and integration tests covering all agents, routers, and services — TDD from the first line of code. Reproducible, deterministic outputs enable systematic testing that LLM-only systems cannot support. |

### Original Contribution Over This Work

Ladkat & Bharati demonstrate the UX value of LLM-fluent career guidance, but their system cannot answer whether a career path is achievable from a given starting point in a specific labor market — it only tells students what to do, not whether those steps are grounded in real demand. CareerGraph separates the reasoning concern (LLM) from the evidence concern (graph algorithms on real data). This architecture means that LLM explanations in CareerGraph are always describing a result that has already been computed deterministically — the LLM cannot hallucinate a missing skill or fabricate a roadmap step. The result is a system where explainability and correctness are independent guarantees: the algorithm is correct by construction, and the explanation is clear by design.

---

## Paper 3: José-García et al. (2022) — C3-IoC Career Guidance System

**Citation:** José-García, A., Sneyd, A., Melro, A., Ollagnier, A., Tarling, G., Zhang, H., Stevenson, M., Everson, R., & Arthur, R. (2022). C3-IoC: A career guidance system for assessing student skills using machine learning and network visualisation. *International Journal of Artificial Intelligence in Education, 33*, 1094–1121.

### What They Do

C3-IoC is a deployed career guidance system for UK IT students (c3-ioc.co.uk). It combines a CV parser (dictionary matching over 195 IT skills), a 24-item soft-skills questionnaire, and a force-directed network visualization that places the student in an IT job space. The asymmetric similarity metric `D(u,j) = √Σ max(j_s − u_s, 0)²` correctly penalizes only skill deficits, not surpluses. Louvain community detection clusters 26 IT job roles. A key contribution is the Most Informative Order method, which identifies that just 4 of 24 questionnaire items are sufficient for 80% community assignment accuracy. The system was evaluated with 64 UK university students.

### What CareerGraph Does Differently

| Dimension | C3-IoC (José-García et al.) | CareerGraph |
|---|---|---|
| **Actionable output** | Diagnostic only. Shows the student where they stand in the job space and which skills are missing. Does not generate a path to close the gap. | Full end-to-end guidance: SkillGapAgent identifies the gap, PathFinderAgent generates an ordered sequence of skills to acquire (via BFS + topological sort on `LEADS_TO` edges), and courses are attached via `TEACHES` edges. The student receives not just a gap score but a week-by-week learning roadmap. |
| **Skill proficiency** | Binary: skill is present or absent. Advanced Python and beginner Python are the same node. | `HAS_SKILL` edges carry `{proficiency: 0–10, years: float}`. The readiness score rewards deeper proficiency. The gap analysis distinguishes between a skill the student lacks entirely and one they have at a low level. |
| **Knowledge base currency** | Frozen at 2018–2019 UK job advertisements and O*NET 2019. Cannot reflect skills that emerged after this cutoff (GenAI, MLOps, cloud-native stacks). | IngestionAgent re-ingests from any CSV-formatted job corpus on demand. Skill demand in CareerGraph reflects the current ingested dataset, not a historical snapshot. |
| **Skill representation** | Surface-form dictionary matching. "I led a team of 12" does not yield "leadership." Contextual and synonymous skill descriptions are missed. | NormalizationAgent applies synonym resolution and rapidfuzz fuzzy matching (threshold ≥ 90) to canonicalize skill names before inserting them into the graph, capturing semantically equivalent forms that exact string matching misses. |
| **Student persistence** | Stateless. Each session requires re-upload of CV and re-completion of the questionnaire. | Student node persists in Neo4j across sessions. Skills, proficiency levels, and target roles are stored and updated incrementally. |
| **Geographic and domain scope** | UK IT sector only. Requires reconstruction for other sectors, countries, or education levels. | O*NET taxonomy integration and CSV-based ingestion allow CareerGraph to be adapted to any job market corpus without architectural changes. |
| **Natural language output** | No explanation layer. Outputs are visualizations (radar charts, network graphs) and match scores. | ReasoningAgent generates natural language explanations of all algorithmic outputs — readable by a student with no data background — while the underlying algorithmic result remains independently available and inspectable. |

### Original Contribution Over This Work

C3-IoC solves the placement problem — "where am I in the job space?" — but leaves the navigation problem unsolved: "how do I move to where I want to be?" CareerGraph is designed to solve both. The `LEADS_TO` prerequisite graph and PathFinderAgent's BFS traversal provide the navigational layer that C3-IoC explicitly does not attempt. CareerGraph also closes C3-IoC's two most significant limitations: the frozen knowledge base (addressed by the IngestionAgent pipeline) and the binary skill model (addressed by proficiency-weighted `HAS_SKILL` edges and a composite readiness score).

---

## Summary: CareerGraph's Unified Research Contribution

The three papers above each solve a subset of the career guidance problem. CareerCoach builds a knowledge graph and recommender but has no persistent student model and no ordered learning paths. Ladkat & Bharati build a multi-agent pipeline but ground all reasoning in LLM priors with no connection to real job data. C3-IoC provides rigorous market-grounded placement but cannot generate a path from that placement to the student's target.

CareerGraph's contribution is the integration of all three capabilities in a single, coherent architecture:

### Contribution 1 — Persistent, Proficiency-Weighted Student Graph Node
Students are modeled as first-class nodes in the Neo4j knowledge graph with `HAS_SKILL {proficiency, years}` edges. No prior system in this review persists student profiles at the graph level with typed proficiency attributes. This enables gap scores and roadmaps that are sensitive to skill depth, not just skill presence — a meaningful distinction for a student who knows Python at a beginner level versus an expert.

### Contribution 2 — Ordered Learning Roadmap via Prerequisite Graph Traversal
The `LEADS_TO {difficulty_jump}` relationship encodes skill prerequisites directly in the graph. PathFinderAgent applies BFS from the student's missing skills and topological sort to produce an ordered acquisition sequence. Courses are attached via `TEACHES` edges. This gives students an actionable, step-by-step path — not just a list of gaps — and is structurally absent from all three comparator systems.

### Contribution 3 — LLM as a Decoupled, Optional Explainability Layer
Unlike Ladkat & Bharati (where LLM is the core reasoning engine), CareerGraph's four algorithmic agents operate without any LLM dependency. The ReasoningAgent wraps deterministic algorithmic outputs in natural language after the fact. This means:
- The system functions fully with no LLM configured (NFR-02 — graceful degradation).
- LLM explanations describe a result that has already been proven correct by the algorithm — the model cannot hallucinate a gap score or fabricate a prerequisite.
- The LLM provider is hot-swappable (Claude / OpenAI / Ollama) with no change to the intelligence logic.

### Contribution 4 — Continuous Skill Normalization Pipeline
The NormalizationAgent combines a curated synonym map with rapidfuzz fuzzy matching (threshold ≥ 90) to canonicalize skill names before graph insertion. This directly addresses the ~45% entity linking gap reported by Weichselbraun et al. and the surface-form matching limitation of C3-IoC, without requiring a fine-tuned NLP model.

### Contribution 5 — Live, Re-Ingestible Knowledge Base
The IngestionAgent accepts any CSV-formatted job corpus via a single admin endpoint. Unlike C3-IoC (frozen at 2019) and Ladkat & Bharati (frozen at LLM training cutoff), CareerGraph's market intelligence reflects whatever dataset has been most recently ingested. Emerging skill signals (GenAI, MLOps, cloud-native infrastructure) appear as soon as a corpus containing them is ingested.

---

## Contribution Matrix

| Capability | CareerCoach (2022) | Ladkat & Bharati (2025) | C3-IoC (2022) | **CareerGraph** |
|---|:---:|:---:|:---:|:---:|
| Knowledge graph for skill modeling | ✓ | ✗ | Partial | **✓** |
| Persistent student graph node | ✗ | ✗ | ✗ | **✓** |
| Skill proficiency weighting | ✗ | ✗ | ✗ | **✓** |
| Ordered learning roadmap | ✗ | ✓ (LLM-generated) | ✗ | **✓ (graph-derived)** |
| Market-grounded recommendations | ✓ (courses) | ✗ | ✓ (job matching) | **✓ (jobs + market trends)** |
| Multi-agent architecture | ✗ | ✓ | ✗ | **✓** |
| LLM-optional (graceful degradation) | N/A | ✗ | N/A | **✓** |
| Natural language explanations | ✗ | ✓ | ✗ | **✓** |
| Fuzzy skill normalization | Partial (45% miss rate) | ✗ | ✗ | **✓** |
| Live re-ingestible knowledge base | ✗ | ✗ | ✗ | **✓** |
| Student-facing web application | Production (B2B) | Streamlit prototype | Production (students) | **✓ Full-stack** |

---

## References

José-García, A., Sneyd, A., Melro, A., Ollagnier, A., Tarling, G., Zhang, H., Stevenson, M., Everson, R., & Arthur, R. (2022). C3-IoC: A career guidance system for assessing student skills using machine learning and network visualisation. *International Journal of Artificial Intelligence in Education, 33*, 1094–1121. https://doi.org/10.1007/s40593-022-00317-y

Ladkat, S. N., & Bharati, M. P. (2025). AI-powered career planning using multi-agent systems and large language models. *International Journal for Multidisciplinary Research (IJFMR), 7*(3). E-ISSN: 2582-2160.

Weichselbraun, A., Waldvogel, R., Fraefel, A., van Schie, A., & Kuntschik, P. (2022). Building knowledge graphs and recommender systems for suggesting reskilling and upskilling options from the web. *Information, 13*(11). MDPI. https://doi.org/10.3390/info13110534
