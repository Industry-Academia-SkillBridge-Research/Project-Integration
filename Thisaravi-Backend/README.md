# Thisaravi Backend

**Self-Evolving Skill Gap Analyzer and Guidance System**

The Thisaravi Backend is the central API gateway and orchestration layer for a career guidance platform that analyzes skill gaps between candidates and target roles, generates personalized capstone project recommendations via LLMs, and continuously improves through a self-evolving feedback loop.

## Overview

This service acts as the main backend for the Thisaravi Frontend. It orchestrates two downstream microservices -- **Agent-Runtime** (CV processing, knowledge graph writing, explainability) and **Advanced-Recommendation-System** (skill gap analysis, course recommendations, GNN-based skill ranking) -- while also providing its own LLM-powered project generation, expert feedback collection, and prompt self-evolution capabilities.

### Key Capabilities

- **Skill Gap Analysis & Project Generation**: Streams personalized skill gap analyses and capstone project recommendations using Google Gemini or fine-tuned Ollama models (Gemma 3 4B)
- **Multi-Service Orchestration**: Aggregates results from Agent-Runtime and Advanced-Recommendation-System into unified responses for the frontend
- **Self-Evolving Feedback Loop**: Collects structured expert feedback, detects patterns via statistical + LLM analysis, evolves system prompts, regenerates training datasets, and uploads to HuggingFace for model re-fine-tuning
- **Candidate Profile Management**: JSONL-backed local storage with sync from Agent-Runtime
- **Job Search**: Direct Neo4j queries against scraped LinkedIn job data
- **Training Data Pipeline**: Seed generation, smart-guided LLM augmentation, and HuggingFace dataset upload

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI + Uvicorn |
| Language | Python 3.12+ |
| LLM Providers | Google Gemini, Ollama (local/remote) |
| Database | Neo4j AuraDB (graph), JSONL (local storage) |
| Fine-Tuned Model | Gemma 3 4B (LoRA, GGUF quantized) |
| Dataset Hub | HuggingFace Hub |
| Validation | Pydantic v2 |

## Architecture

```
Thisaravi Frontend (React, port 5173)
        |
        v
Thisaravi Backend (FastAPI, port 8010)  <-- this service
        |
        +---> Agent-Runtime (port 8002)
        |       - CV parsing (PDF/DOCX)
        |       - Skill normalization
        |       - Knowledge graph write (Neo4j)
        |       - Gap analysis orchestration
        |       - XAI / SHAP explainability
        |
        +---> Advanced-Recommendation-System (port 8001)
        |       - TF-IDF role skill importance
        |       - Evidence-weighted skill confidence
        |       - Course recommendations (greedy set cover)
        |       - Project relevance scoring
        |       - GNN link prediction for missing skills
        |       - Hybrid ranking (gap x importance x P_gnn)
        |
        +---> Neo4j AuraDB (direct)
        |       - Job search and filtering
        |       - Role/job data queries
        |
        +---> Google Gemini / Ollama
                - LLM streaming generation
                - Feedback analysis & prompt evolution
```

For detailed architecture documentation with diagrams, see [architecture.md](./architecture.md).

## Project Structure

```
Thisaravi-Backend/
├── main.py                      # FastAPI app, all route handlers (~1168 lines)
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration (not committed)
│
├── clients/                     # HTTP client wrappers for downstream services
│   ├── agent_runtime_client.py  # AgentRuntimeClient (port 8002)
│   ├── recommendation_client.py # RecommendationClient (port 8001)
│   ├── integration_test.py      # End-to-end integration tests
│   └── README.md                # Client library documentation
│
├── feedback/                    # Self-evolving feedback loop system
│   ├── schemas.py               # Pydantic models for feedback data
│   ├── storage.py               # JSONL file I/O for all feedback data
│   ├── analysis.py              # Statistical + LLM-powered pattern detection
│   ├── prompt_evolver.py        # Meta-prompting to evolve system prompts
│   ├── pipeline.py              # Orchestration of full evolution cycle
│   └── feedback_data/           # JSONL data files
│       ├── expert_feedback.jsonl
│       ├── model_outputs_log.jsonl
│       ├── pattern_reports.jsonl
│       └── prompt_evolutions.jsonl
│
├── profiles/                    # Local candidate profile storage
│   ├── storage.py               # JSONL-backed CRUD
│   └── profile_data/
│       └── candidate_profiles.jsonl
│
├── datasets/                    # Training data generation pipeline
│   ├── seeds.jsonl              # Synthetic seed profiles
│   ├── real_seeds.jsonl         # Seeds extracted from real sessions
│   ├── generate_seeds.py        # Seed generation via Ollama
│   ├── extract_real_seeds.py    # Extract seeds from model output logs
│   ├── smart_generator.py       # Deterministic domain-expert recommendation logic
│   ├── augment_dataset.py       # Teacher model data generation pipeline
│   └── hf_uploader.py           # Auto-upload datasets to HuggingFace
│
├── models/
│   └── setup_models.ps1         # Download and register Ollama models
│
└── docs/
    ├── progress.md              # Project progress report
    └── self_evolution_plan.md   # Feedback loop design document
```

## API Endpoints

### Core Generation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/generate-project` | Stream skill gap analysis + project recommendation (Gemini or Ollama) |
| `POST` | `/generate-project-from-sources` | Orchestrate Agent-Runtime + Recommendation System from candidate/job IDs |

### Jobs & Roles (Neo4j)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/roles` | List available roles (proxied from Recommendation System) |
| `GET` | `/jobs-by-role` | Jobs grouped by role key |
| `GET` | `/search-jobs` | Full-text search over Job nodes |

### Feedback & Self-Evolution

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/submit-feedback` | Submit expert feedback (5 dimensions, 1-5 scale) |
| `GET` | `/unreviewed-outputs` | Model outputs pending expert review |
| `GET` | `/feedback-status` | Current evolution status (prompt version, counts) |
| `GET` | `/all-feedback` | All submitted feedback entries |
| `GET` | `/my-outputs` | Student's analysis history with feedback |
| `POST` | `/run-analysis` | Trigger pattern analysis on accumulated feedback |
| `GET` | `/pattern-reports` | List pattern analysis reports |
| `POST` | `/preview-evolution` | Preview prompt evolution diff |
| `POST` | `/apply-evolution` | Apply prompt evolution permanently |
| `GET` | `/prompt-evolutions` | List all prompt evolution records |
| `GET` | `/current-prompt` | Current active system prompt and version |
| `POST` | `/run-regeneration` | Regenerate training dataset with evolved prompt |
| `GET` | `/list-datasets` | List generated dataset files |
| `POST` | `/upload-to-hf` | Upload dataset to HuggingFace Hub |

### Candidate Profiles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/profiles` | List all candidate profiles |
| `GET` | `/profiles/{id}` | Get a single profile |
| `POST` | `/profiles` | Create or update a profile |
| `DELETE` | `/profiles/{id}` | Delete a profile |
| `POST` | `/profiles/{id}/sync-from-runtime` | Pull profile from Agent-Runtime |

## Getting Started

### Prerequisites

- Python 3.12+
- Neo4j AuraDB instance (or local Neo4j)
- Google Gemini API key and/or Ollama instance
- Agent-Runtime running on port 8002
- Advanced-Recommendation-System running on port 8001

### Installation

```bash
# Clone and navigate
cd Project-Integration

# Create virtual environment
uv venv

# Install dependencies
uv sync
```

### Configuration

Create a `.env` file with the following variables:

```env
# LLM Providers
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FINETUNED=student-advisor
OLLAMA_MODEL_GENERIC=gemma3:1b

# Neo4j
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=your_username
NEO4J_PASSWORD=your_password

# Service URLs
AGENT_RUNTIME_URL=http://localhost:8002
ROLE_SKILL_API_URL=http://localhost:8181

# HuggingFace (for dataset upload)
HF_TOKEN=your_hf_token
HF_DATASET_REPO=your-org/your-dataset

# Server
PORT=8010
```

### Running

```bash
uv run Thisaravi-Backend/main.py
```

The server starts on `http://0.0.0.0:8010` by default.

### Running with Downstream Services

For full functionality, start all services:

```bash
# Terminal 1 - Recommendation System
cd ../Advanced-Recommendation-System && python main.py  # port 8001

# Terminal 2 - Agent Runtime
cd ../Agent-Runtime && python main.py                   # port 8002

# Terminal 3 - This Backend
cd ../Thisaravi-Backend && python main.py               # port 8010

# Terminal 4 - Frontend
cd ../Thisaravi-Frontend && npm run dev                  # port 5173
```

## Self-Evolution Feedback Loop

The system implements a closed-loop improvement cycle:

1. **Feedback Collection** -- Experts rate model outputs on 5 dimensions (skill gap accuracy, project relevance, tech stack, implementation quality, overall) and provide free-text comments
2. **Pattern Detection** -- Statistical analysis identifies weak/strong dimensions; LLM extracts recurring themes from expert comments
3. **Prompt Evolution** -- Meta-prompting generates an improved system prompt addressing identified weaknesses while preserving strengths
4. **Dataset Regeneration** -- Teacher model generates new training data using the evolved prompt
5. **Re-Fine-Tuning** -- New dataset uploaded to HuggingFace; model re-fine-tuned via Colab notebook

Each phase is manually triggered by the researcher through the frontend's Evolution Dashboard, maintaining full control over the improvement cycle.

## Related Components

| Component | Port | Repository Path | Description |
|-----------|------|-----------------|-------------|
| Thisaravi Frontend | 5173 | `../Thisaravi-Frontend` | React SPA (Vite + TypeScript + shadcn/ui) |
| Advanced-Recommendation-System | 8001 | `../Advanced-Recommendation-System` | Skill gap analysis, courses, GNN ranking |
| Agent-Runtime | 8002 | `../Agent-Runtime` | CV processing, KG writing, XAI |
