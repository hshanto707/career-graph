🚀 PROJECT: SkillGraph

Agentic Labor Market Intelligence Platform for Student Career Guidance

🎯 1. Core Goal

Build a system that:

Analyzes a student’s skills → compares with real labor market demand → identifies gaps → recommends jobs, skills, and courses with clear explanations.

🧠 2. Problem Statement

Students:

Don’t know what skills actually matter in the market
Apply blindly to jobs
Don’t understand why they’re getting rejected

Recruiters:

Want candidates aligned with real skill requirements
💡 3. Solution

SkillGraph uses:

Real job data (CSV + scraper)
Knowledge graph (Neo4j)
Agent-based backend
Explainable recommendation logic

To deliver:

Job recommendations
Skill gap analysis
Learning roadmap
🧩 4. Core Features
👤 Student Side
Create profile (skills, target roles)
View dashboard (readiness score, gaps)
Get:
Job recommendations
Skill recommendations
Course suggestions
View skill gap analysis
Explore job market
🏢 System Intelligence
CSV + scraper-based data ingestion
Skill normalization (ReactJS → React)
Knowledge graph relationships
Graph-based matching & scoring
Explainable recommendations
🧪 Optional (Post-Capstone)
RAG-based “Market Insights Assistant”
🏗 5. System Architecture
High-Level Flow
Scraper / CSV
      ↓
Ingestion Agent
      ↓
Normalization Agent
      ↓
Knowledge Graph (Neo4j)
      ↓
Skill Gap Agent
      ↓
Recommendation Agent
      ↓
Reasoning Agent (LLM - optional)
      ↓
Frontend UI
🧠 Backend Stack
FastAPI (core API)
PostgreSQL / SQLite (optional structured storage)
Neo4j (knowledge graph)
LangChain (optional, for agent orchestration)
Ollama / GPT (optional, for explanations)
🎨 Frontend Stack
Next.js (App Router)
React
Tailwind CSS
shadcn/ui
🤖 6. Agents (Core Logic)
1. Ingestion Agent
Reads CSV / scraper data
Validates schema
Sends to normalization
2. Normalization Agent
Cleans skill names
Deduplicates
Resolves synonyms
3. Skill Gap Agent
Compares:
Student skills
Job-required skills
Outputs:
Matched skills
Missing skills
Gap %
4. Recommendation Agent
Recommends:
Jobs (based on match score)
Skills (based on demand)
Courses (based on gaps)
5. Reasoning Agent (Optional)
Converts structured outputs into explanations
No business logic inside LLM
🧱 7. Knowledge Graph Design
Nodes
Student
Job
Skill
Course
Relationships
(Job) → REQUIRES → (Skill)
(Course) → TEACHES → (Skill)
(Student) → HAS_SKILL → (Skill)
(Student) → TARGETS → (Job)
📊 8. Scoring System

Simple, explainable:

Match Score = (Matched Skills / Required Skills) × 100

Enhancements:

Skill importance weight (frequency in jobs)
Partial match for related skills
📡 9. APIs
Student
POST /students
GET /students/{id}
Recommendations
GET /recommendations/jobs/{id}
GET /recommendations/skills/{id}
GET /recommendations/courses/{id}
Admin
POST /admin/ingest/csv
🗂 10. Data Sources
Primary
Kaggle job datasets (10k+ rows)
O*NET / ESCO skill datasets
Secondary
Internshala scraper (limit ~500 jobs)
🎨 11. Frontend Pages
Login / Landing
Dashboard (core insights)
Profile (view)
Edit Profile
Job Explorer
Skill Gap Analysis
Recommendations
🔥 12. Key Strengths (Highlight These)
Graph-based reasoning (not black-box AI)
Explainable recommendations
Real labor market data
Modular agent architecture
Scalable ingestion pipeline
🚫 13. What This Project Is NOT
Not a chatbot
Not a resume builder
Not social media
Not over-engineered ML system
🧪 14. Future Scope (Post-Capstone)
RAG-based market insights assistant
Real-time job ingestion
Resume parsing
Advanced ranking models
Multi-region job market analysis
💼 15. Resume Positioning

Built a graph-based labor market intelligence platform that ingests real-world job data, models skill-job relationships using Neo4j, and delivers explainable career recommendations via an agent-based architecture.

🎤 16. One-Line Pitch

“SkillGraph helps students understand what skills they need to get hired by aligning their profiles with real labor market demand using a knowledge graph.”

🧭 17. Strategic Positioning

This project demonstrates:

Backend system design
Data modeling (graph)
API architecture
Real-world problem solving
AI-assisted reasoning (optional)