# Explainable Recommender Systems Through Reinforcement Learning and Knowledge Distillation on Knowledge Graphs

**Authors:** Alexandra Vultureanu-Albisi, Ionut Muraretu, Costin Badica  
**Year:** 2025  
**Published in:** Information (MDPI), Volume 16, Issue 4, Article 282 — DOI: 10.3390/info16040282 (Published March 30, 2025)

---

## Problem Statement

Job recruitment systems face a dual problem: they need to match candidates to positions accurately, and they need to be explainable — particularly in the context of data protection regulations (GDPR) and the growing awareness that automated hiring tools can encode and amplify bias. Most existing systems optimize for one dimension or the other. Deep learning models achieve high matching accuracy but operate as black boxes; simple rule-based systems are transparent but poor at reasoning over complex, heterogeneous candidate and job data.

This paper proposes XR²K²G — a framework that chains Knowledge Graphs, Knowledge Distillation, Reinforcement Learning, and post-hoc explainability tools (LIME and SHAP) into a single system designed to simultaneously achieve accurate job recommendations and provide attributable reasons for each recommendation.

## Key Contributions & Objectives

1. The XR²K²G framework — integrating KG construction, TransE embedding, Graph Attention Network (GAT) teacher model, Knowledge Distillation to a lightweight student model, Q-learning agent, and post-hoc explanation via LIME and SHAP.
2. A two-stage embedding pipeline that preserves relational structure: TransE for initial KG embeddings, GAT as teacher model to refine them via attention over graph neighborhoods, and a student model trained via Knowledge Distillation (MSE loss) to produce lightweight but high-quality embeddings.
3. A Q-learning agent that uses distilled embeddings as state representations, selecting skill-matched jobs by maximizing expected reward (cosine similarity between user and job embeddings, with bonus for occupation alignment).
4. Post-hoc explanations via LIME (local perturbation-based) and SHAP (Shapley value-based) applied to the Q-value output, identifying which features of the student's profile most influenced each recommendation.
5. Empirical evaluation on a real recruitment dataset with precision = 0.80 and NDCG = 1.00 for a representative test user.

## Methodology / Theory / Framework

The pipeline has five stages. First, a KG is constructed from JSON files encoding CVs, skills, and job vacancies, creating entities (users, jobs, skills, occupations) and relations (has_skill, requires_skill, has_occupation, requires_occupation). The resulting KG contains 15,259 nodes and 11,302 edges. Second, TransE is trained on the KG (50 dimensions, 100 epochs, batch size 64, lr 0.0001) to produce initial entity embeddings. Third, a 2-layer GAT with 4 attention heads refines these embeddings by attending over graph neighborhoods (MSE reconstruction loss, Adam, 50 epochs). Fourth, a student MLP (2 FC layers, 64 hidden units, ReLU) is distilled from the GAT teacher, learning to replicate its output embeddings with 100 epochs of MSE training. Fifth, a Q-learning agent (2 FC layers, 128 hidden units, epsilon-greedy policy with ε=0.1, γ=0.9) uses the distilled embeddings as states and recommends the top K=5 jobs by Q-value. LIME and SHAP are then applied to the Q-network's output to attribute each recommendation to specific input features.

## Software Tools / Setup Details

- PyKEEN (TransE training)
- PyTorch 2.3.1, PyTorch Geometric 2.6.0 (GAT, student MLP)
- NetworkX (KG construction), Pandas, NumPy
- LIME, SHAP (post-hoc explainability)
- Matplotlib (visualization)
- Dataset: CVs, skills, and job vacancy JSON files sourced from Kostis et al. (PCI 2022); skills per user centered around 17–19 (some exceeding 50); top user skills: English, Greek, French, Python, C++; top job-demanded skills: computer technology, think creatively, communication
- Train/test split: 85%/15% via PyKEEN's TriplesFactory

## Test / Experiment Analysis

Evaluation is conducted on a single representative user profile ("user_User_99"), which is an acknowledged limitation. For this user, the top-5 recommended jobs (ranked by Q-value) are: System Engineer Athens (Q=8.78), DevOps Architect (1.63), Senior .NET Software Engineer (1.42), Care Assistant (1.27), Localities Social Worker (1.25). Metrics: Precision = 0.80 (4 of 5 recommendations relevant), Recall = 0.01 (expected given K=5 is small relative to total relevant jobs), F1 = 0.02, NDCG = 1.00. The optimal hyperparameter configuration (embedding dim=50, lr=0.001, Adam, batch size=64, L2 decay=0.0001) achieves test loss of 113.5095. SHAP attribution identifies "alter management" as the top positive contributor (+0.51) and "soldering techniques" as the strongest negative contributor (−0.38) for one explained recommendation.

## Test Data / Dataset Source

Recruitment dataset from Kostis et al. (PCI 2022): CVs, skills, and job vacancy JSON files. Skills per user peak around 17–19, with some users exceeding 50 skills. Top user skills include English, Greek, French, Python, C++. Job-demanded skills include computer technology, creativity, communication. Dataset is not publicly released independently but is derived from prior published work.

## Final Result

XR²K²G achieves precision = 0.80 on the test user's top-5 recommendations with NDCG = 1.00, indicating excellent ranking quality for relevant items. The Q-learning agent successfully integrates relational knowledge from the KG via distilled embeddings, and SHAP/LIME correctly attribute recommendations to specific skill features.

**What works well here:** The five-stage pipeline is methodologically ambitious and technically coherent — each stage has a clear motivation. Knowledge Distillation is an underused technique in recruitment AI, and its application here achieves the practical goal of lightweight deployable embeddings without sacrificing the relational reasoning capacity of the GAT teacher. The NDCG = 1.00 result, while from a single user, indicates the top-K ranking is well-ordered when relevant items are retrieved. The SHAP attribution example ("alter management" at +0.51) is concrete and readable — the kind of output a recruiter could act on.

## Limitations

The evaluation is conducted on a single user, which makes it impossible to draw general conclusions about system performance. No average metrics across a held-out test set of multiple users are reported. Recall is structurally low (0.01) because K=5 is small relative to the full job space, but this is not a meaningful limitation in practice — users do not expect to see all relevant jobs. The explainability pipeline spans multiple decision layers (TransE → GAT → student → Q-network → LIME/SHAP), creating a fragmented chain where an explanation at the Q-network level may not accurately reflect the original KG structure. The reward signal is simulated from static profiles rather than real user feedback, and the cold-start problem for new users is not addressed. Ethical concerns (gender/age bias in automated hiring) are acknowledged but not quantitatively addressed.

**The chain-of-explanation problem:** LIME and SHAP explain the Q-network's output given the distilled student embeddings — but these embeddings are themselves a compressed approximation of the GAT's output, which was trained on TransE's output. Each compression step potentially degrades how faithfully the explanation reflects the original knowledge graph structure.

## Final Summary

XR²K²G demonstrates a technically sophisticated integration of KG reasoning, Knowledge Distillation, and RL-based recommendation with post-hoc explainability. The five-stage architecture is more complex than most recruitment AI systems, and the SHAP/LIME attribution results show the explainability mechanism functioning as intended.

**How CareerGraph does better:** CareerGraph achieves interpretable recommendations without the complexity overhead of this five-stage pipeline. Our PathFinderAgent traverses LEADS_TO edges in Neo4j using BFS and topological sort — the recommendation sequence is directly readable as a path through the graph, not an attribution score over compressed embeddings. This means our explanations are structurally transparent at the graph level, not explained after the fact by a post-hoc approximator. Our ReasoningAgent then translates these graph paths into plain English using real market demand data from our MarketAgent — producing the same kind of skill-attribution explanation this paper uses SHAP to compute, but grounded in empirically observed job posting frequencies rather than Q-value sensitivities. And unlike XR²K²G's single-user evaluation, CareerGraph's SkillGapAgent computes a calibrated readiness score for any student against any job in the database using a consistent weighted formula.
