# Market-aware Long-term Job Skill Recommendation with Explainable Deep Reinforcement Learning

**Authors:** Ying Sun, Yang Ji, Hengshu Zhu, Fuzhen Zhuang, Qing He, Hui Xiong  
**Year:** 2025  
**Published in:** ACM Transactions on Information Systems, Volume 43, Issue 2 — ACM

---

## Problem Statement

Most skill recommendation systems have a narrow view of the problem: they look at which skills are relevant to your current job, recommend those, and stop. They don't ask what happens to your career six months or two years later if you follow that advice. They also ignore how hard it is to actually learn each skill — recommending "learn machine learning" as casually as "learn basic Excel" is not useful guidance.

This paper reframes skill recommendation as a sequential decision-making problem: given a worker's current skill set, what is the optimal sequence of skills to acquire over time to maximize long-term salary while minimizing the total learning difficulty? This is a fundamentally harder problem, and it requires an architecture that can reason about multi-step futures — which is why the authors reach for Deep Reinforcement Learning.

There is also an explainability problem: even if a Deep Q-network finds the optimal skill path, workers won't follow advice they can't understand. The paper introduces SeSRDQN, which makes the Q-value estimation interpretable through prototype-based decomposition.

## Key Contributions & Objectives

1. Formulates sustainable skill recommendation as a multi-objective sequential decision-making problem with salary increase and learning difficulty as separate reward signals.
2. Designs a skill-learning environment with two components: a salary estimator (soft job qualification probabilities over 805,182 job postings) and a difficulty estimator (FPGrowth frequent itemset mining for co-occurrence-based learning cost).
3. Proposes SRDQN — a Deep Q-network with a dual-head architecture (separate Q-value estimators for salary and difficulty) and a skill co-occurrence graph for candidate selection.
4. Proposes SeSRDQN — a self-explaining extension where Q-values are decomposed as weighted similarities to learnable prototype skill sets, making recommendations interpretable.
5. Introduces a frequent subset-guided prototyping method ensuring prototypes resemble real market skill clusters.
6. Introduces an MCTS-based optimization-decoding procedure to project prototype embeddings into concrete, human-understandable skill sets.
7. User study with 48 participants demonstrating significantly improved understanding and trust over non-explainable baselines.

## Methodology / Theory / Framework

The environment models the student's state as their current skill set `O^t`. At each step, the agent picks a new skill `s^t` to add. The salary reward is computed by checking how many jobs the updated skill set qualifies for and averaging their salaries. The difficulty reward is the negative of the conditional learning probability (how surprising the new skill is given what the student already knows, derived from frequent itemset mining with FPGrowth).

SRDQN uses a dual MLP head to estimate Q values for salary and difficulty separately, combined as `Q_sal - α × Q_dif`. A co-occurrence skill graph reduces the action space from all 987 skills to the top-100 co-occurring candidates at each step.

SeSRDQN replaces the standard Q-value with a prototype-weighted sum: `Q = Σ Sim(O, p_i) × Q_u(s, p_i)`, where `p_i` are learnable prototype skill sets. Each recommendation is explained by showing which prototype(s) the student's current skill set most resembles. MCTS projects the learned prototype embeddings back into real skill sets for human readability.

## Software Tools / Setup Details

- FPGrowth for frequent itemset mining (support threshold 0.005)
- Three-layer MLP with 256 hidden units and 256-dimensional skill embeddings
- RMSProp optimizer with Glorot normal initialization
- MCTS-based prototype projection with UCB action selection
- Gated fusion network for testing BERT/GPT embedding integration
- Code publicly released: https://github.com/yangji721/SeSRDQN
- User study: 48 postgraduate students/staff across 3 universities

## Test / Experiment Analysis

Five research questions covering performance (5,000 test samples, 20-step horizon), ablation, parameter sensitivity (γ, α, N_c, k), prototype quality (tSNE visualization, global influence analysis), explainability (case studies + user study with 48 participants on 5-point Likert scale for Understanding, Trust, and Usability), and pre-trained model integration.

## Test Data / Dataset Source

Proprietary Chinese IT job posting dataset: 805,182 job postings, 987 distinct IT skills, 374,616 frequent skill sets (FPGrowth, support > 0.005). Training set: 145,000 samples. Test set: 5,000. Preprocessed with Jieba Chinese segmenter and n-gram filtering. Not publicly released.

## Final Result

SRDQN achieves an average salary of 38.24K RMB at the 20-step horizon with difficulty 0.66. SeSRDQN matches this (38.25K, 0.65) while being interpretable. Both significantly outperform the best greedy baseline (35.09K) and dramatically outperform GPT-4 (13.66K). User study results for SeSRDQN: Understanding = 3.85/5, Trust = 4.19/5, Usability = 4.57/5 — substantially better than SRDQN (3.28/3.14/3.57) and Reward DNN (2.78/2.95/2.28). Pre-trained LLM embeddings (BERT, GPT) did not improve recommendation quality over task-specific training.

**What works well here:** The two-reward formulation (salary + difficulty) is the right way to think about long-term career optimization — it matches how people actually think about career development. The finding that task-specific training dramatically outperforms general LLM embeddings for skill recommendation is an important and honest result. The user study is rigorous (48 participants, Likert scale, statistical testing) and shows that explainability genuinely improves trust — not just as a post-hoc claim but as a measured outcome.

## Limitations

The entire experiment is built on Chinese IT job postings. There is no evidence the approach generalizes to other languages, other industries (healthcare, finance), or Western job markets. The RL training and MCTS prototype projection add significant computational complexity — 61.9 seconds per prototype projection cycle is not compatible with real-time recommendations. The model optimizes salary and difficulty but ignores equally important factors like geographic preferences, work-life balance, and personal interests. The skill vocabulary (987 skills) was partially manually curated, introducing subjective decisions about which skills matter.

**The deeper issue:** The RL infrastructure (replay buffer, dual-head Q-network, MCTS projection) is heavyweight for what is fundamentally a sequential recommendation problem. A well-designed graph traversal over a skill prerequisite graph can produce similar ordered recommendations with far less engineering complexity and far more transparency.

## Final Summary

SeSRDQN is a methodologically sophisticated paper that genuinely advances the state of the art in long-term skill recommendation. Its multi-objective RL formulation is the most rigorous treatment of the "what skills should I learn next?" problem in the literature. The user study result — that explainability increases trust by measurable margins — is a valuable empirical finding for any career guidance system.

**How CareerGraph does better:** CareerGraph solves the same sequential recommendation problem (which skills to acquire next) using graph traversal rather than RL. Our PathFinder performs BFS on LEADS_TO edges in Neo4j, followed by a topological sort, to produce an ordered learning path that is fully transparent: every step is a graph edge you can inspect. This achieves the same ordered sequence quality without the training complexity, data requirements, or MCTS overhead. More importantly, our path is grounded in explicit prerequisite semantics (this skill leads to that one because the market data says so), not in a black-box Q-value. Our ReasoningAgent then explains each step in plain English using real market demand data from our MarketAgent — producing the SeSRDQN-style prototype explanations without needing prototype training at all.
