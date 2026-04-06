# Development Plan

> Self-Evolving Skill Gap Analyzer and Guidance System

## Table of Contents

- [Project Proposal](#project-proposal)
- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [Research Contributions](#research-contributions)
- [System Components](#system-components)
- [Development Roadmap](#development-roadmap)
  - [Phase 1: Foundation](#phase-1-foundation)
  - [Phase 2: Intelligent Analysis](#phase-2-intelligent-analysis)
  - [Phase 3: Self-Evolving Feedback Loop](#phase-3-self-evolving-feedback-loop)
  - [Phase 4: Fine-Tuned Model Training](#phase-4-fine-tuned-model-training)
  - [Phase 5: Frontend and User Experience](#phase-5-frontend-and-user-experience)
  - [Phase 6: Evaluation and Refinement](#phase-6-evaluation-and-refinement)
  - [Phase 7: Advanced Features](#phase-7-advanced-features)
- [Current Status](#current-status)
- [Upcoming Work](#upcoming-work)
- [Technical Decisions](#technical-decisions)

---

## Project Proposal

### Problem Statement

Students and career-changers face a persistent challenge: the gap between their current skills and the demands of their target career roles is difficult to assess objectively, and the guidance available to bridge that gap is generic, static, and disconnected from the realities of the job market. Existing career guidance tools typically:

- Provide binary "have it / don't have it" skill assessments, ignoring partial knowledge and transferable skills
- Offer generic advice that doesn't account for individual backgrounds, interests, or personality
- Remain static -- they never improve from feedback on the quality of their recommendations
- Lack transparency about *why* certain skills or projects are recommended

### Proposed Solution

A multi-service platform that combines **graph-based skill analytics**, **machine learning** (GNN link prediction, TF-IDF importance scoring, SHAP explainability), and **fine-tuned large language models** to deliver personalized, evidence-based career guidance. The system:

1. **Builds a knowledge graph** of candidates, skills, jobs, roles, courses, and projects from real CV data and job market scraping
2. **Analyzes skill gaps** using graded fuzzy matching, probabilistic confidence scoring, and TF-IDF role importance -- not binary matching
3. **Predicts skill acquisition paths** using a heterogeneous GNN (SAGEConv) trained on 51K+ person-skill edges to identify which skills a candidate is most likely to acquire next
4. **Generates personalized recommendations** via fine-tuned Gemma 3 4B models that produce gap analyses, capstone project proposals, and implementation plans tailored to a candidate's background
5. **Continuously improves** through a self-evolving feedback loop where expert review drives prompt evolution, dataset regeneration, and model re-training -- creating a system that gets better over time without manual intervention

### Research Contributions

1. **Self-evolving LLM guidance**: A closed-loop system where expert feedback is statistically analyzed, system prompts are autonomously evolved by an LLM acting as a Prompt Engineer, and training data is regenerated to re-fine-tune the model
2. **Hybrid neuro-symbolic skill ranking**: Combining graph neural network predictions with symbolic TF-IDF importance and evidence-weighted confidence for explainable skill recommendations
3. **Domain-aware synthetic data generation**: Expert-knowledge-guided data generation using a smart generator that maps student backgrounds to curated skill gaps and project recommendations, enriching teacher-model outputs
4. **Multi-evidence skill confidence**: Probabilistic skill assessment using noisy-OR aggregation across CV claims, work experience, project evidence, and certifications

---

## System Components

| Component | Description | Status |
|-----------|-------------|--------|
| **Backend** (this repo) | API gateway, LLM generation, feedback loop, data pipeline | Active development |
| **Frontend** | React 19 UI for students and experts | Functional |
| **Agent-Runtime** | CV parsing, skill normalization, KG writing, XAI | Functional |
| **Advanced-Recommendation-System** | TF-IDF, deficit analysis, course recs, GNN ranking, SHAP | Functional |
| **GNN-Link-Prediction** | HeteroGNN training pipeline for skill prediction | Trained model available |
| **Neo4j Aura** | Shared knowledge graph | Deployed |

---

## Development Roadmap

### Phase 1: Foundation

Establish the core infrastructure and data layer.

- [x] Set up Neo4j knowledge graph schema (Person, Skill, Job, Role, Course, Project nodes)
- [x] Build the Agent-Runtime agentic pipeline (Extract -> Normalize -> KG Write -> Gap Analyze)
- [x] Implement 200+ skill alias normalization dictionary with category assignment
- [x] Create the KG writer with MERGE-based idempotent writes and UNWIND batch operations
- [x] Set up the Backend as the central API gateway with FastAPI
- [x] Implement HTTP client wrappers for Agent-Runtime and Recommendation System
- [x] Set up Vite proxy configuration for frontend-backend communication
- [x] Implement JSONL-based persistence for profiles, feedback, and outputs
- [x] Integrate Neo4j Aura for job data queries (browse by role, full-text search)

### Phase 2: Intelligent Analysis

Implement the core skill analysis and recommendation algorithms.

- [x] Build evidence-weighted skill confidence scoring (noisy-OR formula)
- [x] Implement TF-IDF role-skill importance scoring
- [x] Create 4-tier graded skill matching (exact=1.0, cluster=0.7, high-sim=0.6, mid-sim=0.4)
- [x] Build deficit computation and ranking service
- [x] Train HeteroGNN (SAGEConv, 2 layers, 128-dim) on 51K+ person-skill edges
- [x] Implement GNN inference service with fallback for unseen candidates
- [x] Create hybrid ranking formula: `gap * importance_norm * P_gnn`
- [x] Build additive ranking alternative: `0.3*(1-P_has) + 0.4*importance + 0.3*P_gnn`
- [x] Implement greedy set-cover course recommendation with diversity optimization
- [x] Build project-role relevance scoring
- [x] Add SHAP explainability (3 levels: formula, feature, graph)
- [x] Train XGBoost surrogate model for SHAP-based explanations
- [x] Create evaluation framework comparing hybrid vs symbolic rankers
- [x] Implement skill-level XAI with contribution percentages
- [x] Add SHAP-based model-level predictions with user-friendly explanations

### Phase 3: Self-Evolving Feedback Loop

The core research contribution -- a system that improves itself through expert feedback.

- [x] Design feedback schema (5-dimension ratings: skill_gap_accuracy, project_relevance, tech_stack_appropriateness, implementation_step_quality, overall_quality)
- [x] Implement model output logging with `logging_wrapper()` for every generation
- [x] Build expert feedback collection API (ratings + free-text comments)
- [x] Implement Phase 2: Pattern Analysis -- statistical dimension analysis (mean/median/stddev, WEAK/NEUTRAL/STRONG classification)
- [x] Implement Phase 2: LLM-powered theme extraction from expert comments
- [x] Build PatternReport generation with criticisms, praises, and actionable insights
- [x] Implement Phase 3: Prompt Evolution -- LLM as Prompt Engineer
- [x] Add rules engine for prompt evolution (preserve schema, measurable instructions, <800 words)
- [x] Create unified diff preview before committing prompt changes
- [x] Implement prompt version tracking (`v2_base` -> `v2_evolved_N`)
- [x] Build Phase 4: Dataset regeneration with evolved prompts
- [x] Create pipeline orchestration (analysis -> evolution -> regeneration)
- [x] Integrate HuggingFace Hub upload for regenerated datasets
- [x] Build real seed extraction from user interaction logs (SHA-256 dedup)

### Phase 4: Fine-Tuned Model Training

Build the training data pipeline and fine-tune domain-specific models.

- [x] Create seed generation across 50+ role archetypes
- [x] Build smart_generator.py with domain-expert mappings (finance, medical, creative, engineering, security, etc.)
- [x] Implement augment_dataset.py with teacher model generation (Gemini / Ollama)
- [x] Support V1 (structured text) and V2 (structured JSON) output formats
- [x] Build V1 fine-tuning notebook (Gemma 3 4B + LoRA, r=64, 2.7% trainable)
- [x] Build V2 fine-tuning notebook (JSON output format)
- [x] Implement `train_on_responses_only` masking for SFT
- [x] Export to Q4_K_M GGUF (~2.49 GB) for Ollama deployment
- [x] Upload models to HuggingFace Hub (Hashinika/gemma-3-4b-student-advisor-*)
- [x] Create Ollama Modelfile with Gemma-3 chat template
- [x] Build `setup_models.ps1` for automated GGUF download and Ollama registration
- [x] Support resume-from-partial in dataset generation

### Phase 5: Frontend and User Experience

Build the user-facing application for both students and experts.

- [x] Set up React 19 + TypeScript + Vite + Tailwind + shadcn/ui
- [x] Implement authentication (localStorage-based, student/expert roles)
- [x] Build the Analysis page with Manual and Source modes
- [x] Implement real-time streaming markdown rendering (StreamingOutput)
- [x] Build the Results Dashboard (SkillMatchScore + missing skills + ProjectCard)
- [x] Implement dual output parsing (JSON from Gemini, structured text from fine-tuned model)
- [x] Build the Feedback page with 5-slider rating interface
- [x] Build the 4-phase Evolution Dashboard
- [x] Implement Settings page for model provider configuration
- [x] Build History page for students to review past analyses with feedback
- [x] Create role-based navigation (students: Analysis/History, experts: Feedback/Evolution/Settings)
- [x] Implement profile sync between frontend localStorage and backend JSONL store

### Phase 6: Evaluation and Refinement

Evaluate the system's components and refine based on results.

- [x] Build evaluation framework for hybrid vs symbolic rankers
- [x] Evaluate GNN ranking (Hits@10 metrics)
- [x] Run multiple feedback collection cycles
- [x] Execute prompt evolution iterations (v2_base through v2_evolved_4)
- [x] Generate evolved datasets (student_advisor_dataset_v2_evolved_1 through _4)
- [ ] Conduct formal user studies with students and career counselors
- [ ] Benchmark fine-tuned model quality against base Gemini and base Ollama outputs
- [ ] Measure end-to-end latency and optimize bottlenecks
- [ ] Quantify feedback loop improvement across evolution cycles

### Phase 7: Advanced Features

Extensions and improvements beyond the core system.

- [ ] Implement PDF/DOCX resume upload flow end-to-end through the frontend
- [ ] Add real authentication (OAuth/JWT) replacing localStorage-based auth
- [ ] Expand the skill alias dictionary through automated discovery from job postings
- [ ] Add support for additional LLM providers (local Llama, Claude, etc.)
- [ ] Build a dashboard for monitoring model performance metrics over time
- [ ] Implement A/B testing between prompt versions in production
- [ ] Add multi-language support for non-English CVs and job descriptions
- [ ] Build automated feedback collection from implicit signals (user engagement, return visits)
- [ ] Extend the GNN to incorporate temporal dynamics (skill trends over time)
- [ ] Add a job description gap analysis flow from the frontend (leverage existing JD OCR in Agent-Runtime)
- [ ] Create a CLI tool for batch evaluation of model outputs
- [ ] Implement caching layer for frequently-accessed recommendations
- [ ] Build an admin dashboard for monitoring feedback loop health and evolution history

---

## Current Status

The core system is **functional end-to-end**. All four services (Backend, Frontend, Agent-Runtime, Advanced-Recommendation-System) communicate and deliver the primary value proposition: a student can submit their profile, target a role, and receive a personalized skill gap analysis with project recommendations from a fine-tuned model.

**Key milestones reached:**
- The self-evolving feedback loop has completed 4+ evolution cycles (v2_base through v2_evolved_4)
- The fine-tuned Gemma 3 4B model produces structured JSON outputs suitable for UI rendering
- The GNN-based missing skill ranking achieves 19% Hits@10 with the additive formula
- Expert feedback collection, pattern analysis, and prompt evolution are all operational
- Datasets have been regenerated with evolved prompts and uploaded to HuggingFace

---

## Upcoming Work

Priority items for the next development push:

1. **Formal evaluation** -- Conduct structured user studies and benchmark the fine-tuned model against baselines to quantify the value of the self-evolving loop
2. **Resume upload UX** -- The Agent-Runtime already supports PDF parsing; wire this through the frontend for a seamless upload experience
3. **Authentication upgrade** -- Replace the localStorage auth stub with proper authentication for deployment
4. **Performance profiling** -- Profile end-to-end latency, identify bottlenecks (particularly in the orchestrated `/generate-project-from-sources` flow with multiple service calls)
5. **Expanded evaluation metrics** -- Measure not just ranker accuracy but also the qualitative improvement in model outputs across evolution cycles

---

## Technical Decisions

Key architectural and technical decisions made during development:

| Decision | Rationale |
|----------|-----------|
| **JSONL for persistence** (not SQL/Mongo) | Simple, append-only, human-readable. Suitable for the current scale of feedback and profile data. Easy to inspect and debug. |
| **Separate services** (not monolith) | Each service has distinct computational requirements. The GNN and SHAP models need different dependencies than the LLM serving. Enables independent scaling. |
| **LoRA instead of full fine-tuning** | Only 2.7% of parameters trained, enabling fine-tuning on a single L4 GPU on Colab's free tier. Faster iteration on the feedback loop. |
| **Gemma 3 4B as base model** | Good balance of quality and efficiency. Small enough for quantized local deployment (~2.5 GB GGUF), large enough for coherent structured outputs. |
| **V2 (JSON) output format** | Easier to parse reliably in the frontend than markdown. Directly maps to UI components. The V1 text format is retained for comparison. |
| **Teacher-model data generation** (not manual curation) | Enables the feedback loop to regenerate training data automatically. The smart_generator provides domain expert grounding. |
| **Neo4j over relational DB** | The skill-role-candidate relationships are naturally graph-structured. Cypher queries for multi-hop relationships (skill similarity, project-skill connections) are more expressive than SQL joins. |
| **Vite proxy** (not direct CORS) | Avoids CORS complexity in development. Clean URL rewriting. The proxy configuration documents the full service topology. |
| **Noisy-OR for skill confidence** | Allows multiple evidence sources to contribute multiplicatively. A skill evidenced in work experience AND projects gets higher confidence than either alone. Standard probabilistic approach. |
| **Greedy set-cover for course recs** | Ensures diversity -- each recommended course covers *different* deficit skills rather than all covering the same popular skills. |
