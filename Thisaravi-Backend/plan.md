# Project Plan: Self-Evolving Skill Gap Analyzer and Guidance System

## 1. Vision

A platform that helps candidates (students and professionals) understand the gap between their current skill set and a target career role, then provides personalized, actionable guidance -- capstone project recommendations, course suggestions, and skill prioritization -- that continuously improves through expert feedback and model self-evolution.

## 2. Problem Statement

Career guidance for technical roles is often generic, outdated, or disconnected from real job market data. Students completing their degrees lack visibility into:

- Which specific skills they are missing for their target role
- How important each missing skill is relative to actual job postings
- What projects would most efficiently close their skill gap
- How their existing projects and experience already align with the role

Existing tools either provide static skill checklists or rely on a single LLM prompt with no grounding in real job market data. There is no mechanism for systematic improvement of the guidance quality over time.

## 3. Approach

The system addresses this through a multi-service architecture that combines:

- **Knowledge Graph grounding** -- Real LinkedIn job data stored in Neo4j, with TF-IDF skill importance derived from actual job postings per role
- **Multi-evidence skill assessment** -- Candidates are assessed from multiple evidence sources (CV claims, project technologies, work experience, certifications) using a probabilistic model
- **GNN-based learnability prediction** -- A Graph Neural Network trained on the knowledge graph predicts which missing skills a candidate is most likely to acquire, based on their existing skill graph neighborhood
- **LLM-powered generation** -- Fine-tuned (Gemma 3 4B via LoRA) and cloud (Gemini) models generate personalized project recommendations and gap analyses
- **Self-evolving feedback loop** -- Expert feedback drives prompt evolution and model re-fine-tuning in a closed loop

## 4. System Components

| Component | Role | Port |
|-----------|------|------|
| **Thisaravi Frontend** | React SPA -- student analysis, expert feedback, evolution dashboard | 5173 |
| **Thisaravi Backend** | API gateway, LLM orchestration, feedback loop, profile/job management | 8010 |
| **Agent-Runtime** | CV processing pipeline, skill normalization, Neo4j graph writing, XAI | 8002 |
| **Advanced-Recommendation-System** | Skill gap analysis, course recommendations, GNN ranking, explainability | 8001 |
| **Neo4j AuraDB** | Knowledge graph (candidates, skills, roles, jobs, projects, courses) | Cloud |
| **GNN-Link-Prediction** | Trained GNN model artifacts (GraphSAGE, heterogeneous graph) | Offline |

## 5. What Has Been Built

### 5.1 Core Analysis Pipeline (Complete)

- [x] LLM-powered skill gap analysis and project generation with streaming output
- [x] Dual provider support: Google Gemini (cloud) and Ollama (local, fine-tuned Gemma 3 4B)
- [x] Structured JSON and markdown output parsing on the frontend
- [x] Manual input mode and "From Sources" mode (candidate + job pulled from services)

### 5.2 Knowledge Graph and Recommendation Engine (Complete)

- [x] Neo4j AuraDB with candidate, skill, role, job, project, course, and certification nodes
- [x] TF-IDF role skill importance computation from real job posting data
- [x] Evidence-weighted skill confidence (P_has) from 4 source types
- [x] Graded fuzzy skill matching (exact, cluster, high-similarity, medium-similarity)
- [x] Deficit-based ranking: `deficit = importance x (1 - match_strength)`
- [x] Course recommendations via greedy set cover optimization
- [x] Project-role relevance scoring
- [x] LinkedIn job data scraped and loaded into Neo4j

### 5.3 GNN Link Prediction (Complete)

- [x] Heterogeneous GraphSAGE model (person, skill, project, skill_category nodes)
- [x] 2-layer GNN, 128 hidden dimensions, trained on 51K+ person-skill edges
- [x] Hybrid multiplicative ranking: `score = gap x importance_norm x P_gnn`
- [x] New-candidate fallback (average P_gnn across training set)

### 5.4 Explainability (Complete)

- [x] 3-level SHAP explanations (formula-level, feature-level, graph-level)
- [x] XGBoost surrogate model for TreeExplainer-based explanations
- [x] Skill-level contribution analysis (Agent-Runtime)
- [x] ML model SHAP feature importance (Agent-Runtime)

### 5.5 Agent-Runtime CV Pipeline (Complete)

- [x] 4-step agentic pipeline: Extract -> Normalize -> KG Write -> Gap Analyze
- [x] PDF/DOCX CV parsing via Open Router and Gemini LLMs
- [x] Skill normalization via alias dictionary + LLM-assisted matching
- [x] Full Neo4j graph upsert with proper node/relationship management
- [x] AI explanation generation via fine-tuned Qwen 2.5 3B model

### 5.6 Self-Evolving Feedback Loop (Complete)

- [x] 5-dimension expert feedback collection (skill accuracy, project relevance, tech stack, implementation quality, overall)
- [x] Statistical + LLM-powered pattern analysis
- [x] Meta-prompting-based prompt evolution with diff preview
- [x] Training dataset regeneration with evolved prompts
- [x] HuggingFace Hub upload for re-fine-tuning

### 5.7 Frontend (Complete)

- [x] Role-based access (student / expert)
- [x] Real-time streaming markdown rendering
- [x] Structured results dashboard (match score, missing skills, project card)
- [x] Expert feedback portal with 5-dimension ratings
- [x] 4-phase evolution dashboard
- [x] Student analysis history with feedback cross-referencing
- [x] Profile management with backend sync
- [x] Job browsing by role from Neo4j

### 5.8 Model Fine-Tuning Pipeline (Complete)

- [x] Synthetic seed generation and real-session seed extraction
- [x] Smart guidance: deterministic domain-expert logic for tech stack and project naming
- [x] Teacher model (Gemini/Ollama) data generation pipeline
- [x] LoRA fine-tuning on Google Colab (Gemma 3 4B -> GGUF -> Ollama)
- [x] V1 (text) and V2 (JSON) generation modes

## 6. What Remains / Future Work

### 6.1 Evaluation and Validation

- [ ] Formal evaluation of LLM output quality across evolution cycles (tracking rating distributions per prompt version)
- [ ] A/B testing framework: serve both base and evolved models, compare expert ratings
- [ ] Quantitative comparison of GNN hybrid ranking vs. symbolic-only ranking on a held-out candidate set
- [ ] User study with actual students to validate end-to-end usefulness

### 6.2 System Improvements

- [ ] Authentication and authorization (currently localStorage-based, no real auth)
- [ ] Persistent user accounts with database backing instead of localStorage + JSONL
- [ ] Connection pooling and proper lifecycle management for Neo4j driver
- [ ] Service health monitoring and graceful degradation (circuit breakers for downstream services)
- [ ] Rate limiting and input validation hardening on all endpoints
- [ ] Containerization (Docker Compose for the full multi-service stack)

### 6.3 Feature Enhancements

- [ ] Job description upload via image/PDF directly from the frontend (Agent-Runtime `/job-gap/analyze` endpoint exists but not wired to the frontend)
- [ ] CV upload from the frontend (Agent-Runtime `/agent/run-from-pdf` exists but not exposed in the frontend)
- [ ] Domain-specific prompt evolution branches (e.g. separate prompts for ML vs. Finance vs. Healthcare roles)
- [ ] DPO (Direct Preference Optimization) integration using paired preferred/rejected feedback
- [ ] Real-time job market trend tracking (periodic re-scraping and knowledge graph updates)
- [ ] Multi-model evolution: evolve different prompts for different teacher models

### 6.4 Research Extensions

- [ ] Confidence-based auto-triggering of evolution phases (replace manual triggers with statistical confidence thresholds)
- [ ] Longitudinal tracking of student skill acquisition after following recommendations
- [ ] Cross-role transfer learning in the GNN (can skills learned for one role transfer learnability signals for another?)
- [ ] Comparison of self-evolution approach against RLHF and constitutional AI methods

## 7. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Microservice split** (Backend / Agent-Runtime / Recommendation) | Separation of concerns: LLM orchestration, CV pipeline, and graph analytics have different scaling and development needs |
| **Hybrid ranking (multiplicative)** over additive | Ensures skills must be simultaneously missing, important, AND learnable -- avoids recommending easy but unimportant skills |
| **Fine-tuned small model** (Gemma 3 4B) alongside cloud LLM | Offers offline/local inference with acceptable quality; cloud model provides baseline and comparison |
| **Expert feedback** rather than user self-assessment | Domain experts provide more reliable quality signals for model improvement than end-users |
| **Manual evolution triggers** | Researcher maintains control over each phase; avoids autonomous prompt drift |
| **JSONL storage** for feedback data | Simple, append-only, no additional database dependency; consistent with existing patterns |
| **Graded skill matching** over binary | Captures partial skill coverage (e.g., knowing Python3 partially covers Python) rather than treating skills as all-or-nothing |
