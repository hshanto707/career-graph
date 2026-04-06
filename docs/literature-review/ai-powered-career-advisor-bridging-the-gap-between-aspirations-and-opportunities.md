# AI Powered Career Advisor: Bridging the Gap between the Aspirations and Opportunities

**Authors:** Harshul Gupta, Megha Gupta, Nimish Tomar, Tusha Gangwar  
**Year:** 2025  
**Published in:** International Journal for Research in Applied Science & Engineering Technology (IJRASET), Volume 13, Issue IV, April 2025

---

## Problem Statement

Getting good career advice is unevenly distributed. Students from well-resourced backgrounds have access to guidance counselors, alumni networks, and mentors who can help them match their skills and interests to viable career paths. Everyone else often has to figure it out alone. Traditional career guidance tools are too rigid — they offer generic job lists based on academic major without adapting to the real-time state of the labor market or the individual's actual skill profile.

This paper argues that an AI-powered career advisor can close this gap by combining machine learning, NLP, and data analytics to provide personalized career guidance at scale. The goal is a platform that analyzes a user's skills, interests, and qualifications, maps them to current job market demand, and delivers career path recommendations along with targeted skill-building advice.

## Key Contributions & Objectives

1. Proposes an end-to-end AI-powered career advisory web application with a multi-layered recommendation engine.
2. Implements collaborative filtering and content-based filtering in combination with deep learning models for personalized career matching.
3. Integrates NLP-based resume analysis to extract skills from uploaded resumes and identify skill gaps relative to career goals.
4. Provides a real-time job market dashboard showing salary trends, industry demand, and sector-specific insights.
5. Incorporates an iterative feedback loop allowing users to refine recommendations based on assessments and re-evaluation.
6. Addresses ethical AI concerns including algorithmic bias mitigation and GDPR-compliant data handling.

## Methodology / Theory / Framework

The platform follows a five-stage pipeline: user data collection → data processing and analysis → recommendation engine → interactive UI → feedback loop. Users provide structured input through a skill assessment questionnaire covering career goals, education, skills, and experience. Alternatively, they can upload a resume, which is parsed using NLP to extract skill entities and qualifications.

The recommendation engine uses three techniques in combination. Collaborative filtering surfaces career paths based on patterns from users with similar profiles. Content-based filtering matches job opportunities against the user's specific skills and qualifications. Deep learning models (neural networks via TensorFlow/Keras) identify non-obvious relationships between skills, experience, and job market demand. As the system accumulates user feedback, it iteratively improves its recommendations.

The frontend is built with React.js and Next.js for responsive, SEO-friendly interfaces. The backend uses Python with Scikit-learn for classical ML and TensorFlow/Keras for deep learning. NLP components use NLTK, SpaCy, and Hugging Face Transformers for resume parsing, POS tagging, and named entity recognition. Apache Spark and Hadoop handle large-scale data processing.

## Software Tools / Setup Details

- Frontend: React.js, Next.js
- ML/DL: Python, TensorFlow/Keras, Scikit-learn, Pandas
- NLP: NLTK, SpaCy, Hugging Face Transformers
- Big data processing: Apache Spark, Hadoop
- Cloud infrastructure for scalable deployment
- Ethical compliance: fairness algorithms, GDPR-aligned data policies

## Test / Experiment Analysis

This paper presents a prototype demonstration rather than a formal empirical evaluation. Results are shown through UI screenshots of the skill assessment questionnaire (Figure 3), resume upload and analysis interface (Figure 4), result analysis loading screen (Figure 5), career recommendation dashboard (Figure 6), and recommended action plan based on assessment (Figure 7). No quantitative accuracy metrics, precision/recall, or user study results are reported. The paper describes the system's goals and architecture and presents screenshots as evidence of functionality.

## Test Data / Dataset Source

No specific dataset is described or cited. The paper refers generically to "job boards, educational sources, and labor market data" as input sources for the recommendation engine, and mentions integration with "third-party APIs" for real-time job market data. No dataset size, composition, or source is specified.

## Final Result

The paper claims the platform successfully delivers personalized career recommendations, real-time job market trend insights, resume analysis with skill gap identification, and suggested improvement actions for closing the gap between a user's current profile and a target career. The recommendation engine improves over time through the feedback loop.

**What works well here:** The architecture described is sensible and comprehensive — combining collaborative filtering, content-based filtering, and deep learning for career matching is a standard but effective approach. The decision to include NLP-based resume analysis alongside the questionnaire gives users two entry points for profile creation. The ethical AI section, which explicitly addresses fairness, algorithmic bias, and GDPR, is a notable addition that many systems in this space ignore entirely. The UI screenshots show a clean, intuitive interface that would actually be usable by students without technical backgrounds.

## Limitations

This paper does not report a single quantitative result. There are no accuracy metrics, no baseline comparisons, no user study, and no dataset description. Every claim — "delivers personalized recommendations," "provides real-time insights" — is asserted rather than demonstrated. The recommendation engine design mentions TensorFlow/Keras and Scikit-learn but gives no details about model architecture, training data, or evaluation. Without this, it is impossible to assess how well the system actually performs versus any existing tool.

The collaboration filtering approach requires significant user interaction history to work well, which creates a cold-start problem for new users that is not addressed. Similarly, content-based filtering requires a well-structured job posting database whose source, quality, and coverage are never described. The paper acknowledges bias as a concern but does not explain what fairness constraints or debiasing techniques are actually applied.

**The deeper issue:** This reads as a proposal and prototype description, not a completed research contribution. It does not advance the technical state of the art, and the lack of any empirical evaluation makes it impossible to place alongside papers that report rigorous results.

## Final Summary

The AI Powered Career Advisor demonstrates a coherent and user-centered vision for AI-based career guidance. Its multi-layered recommendation architecture, resume analysis, real-time market dashboard, and feedback loop describe exactly the kind of system that students need. The ethical AI commitments are a genuine differentiator in this space.

**How CareerGraph does better:** CareerGraph is the implemented, evaluated version of what this paper proposes. Where this paper describes a recommendation engine without any measurement, CareerGraph's SkillGapAgent computes a mathematically grounded readiness score using a weighted formula across must-have and nice-to-have skills with proficiency bonuses. Our RecommendationAgent uses Jaccard similarity combined with LEADS_TO depth-2 proximity rather than collaborative filtering — which avoids the cold-start problem entirely since no user interaction history is required. Our MarketAgent delivers real job market demand signals from actual ingested job posting data rather than unspecified third-party APIs. Most importantly, every step in CareerGraph's pipeline is backed by real data (10k+ Kaggle job postings, O*NET/ESCO taxonomy) and a defined algorithmic process that can be explained to a student in plain language by the ReasoningAgent — not left as a black-box neural network output.
