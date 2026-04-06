# Self-Evolving Skill Gap Analyzer and Guidance System

A research-grade, multi-service platform that analyzes a candidate's skills against target career roles and generates personalized gap analyses, course recommendations, and capstone project proposals. The system features a **self-evolving feedback loop** that continuously improves its LLM-based guidance through expert review, prompt evolution, and automated model re-training.

## Table of Contents

- [Overview](#overview)
- [System Components](#system-components)
- [Backend (This Repository)](#backend-this-repository)
  - [Core Generation](#core-generation)
  - [Self-Evolving Feedback Loop](#self-evolving-feedback-loop)
  - [Training Data Pipeline](#training-data-pipeline)
  - [Fine-Tuning Notebooks](#fine-tuning-notebooks)
  - [Candidate Profiles](#candidate-profiles)
  - [Job Data (Neo4j)](#job-data-neo4j)
- [API Reference](#api-reference)
- [Connected Services](#connected-services)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [Related Documentation](#related-documentation)

## Overview

The system addresses a core problem: students and career-changers lack personalized, actionable guidance on bridging the gap between their current skillset and their target role. Generic career advice fails to account for individual backgrounds, interests, and the evolving demands of the job market.

This platform solves this by:

1. **Analyzing skill gaps** using evidence-weighted confidence scoring, TF-IDF role importance, GNN-based link prediction, and graded fuzzy skill matching -- all powered by a shared Neo4j knowledge graph.
2. **Generating personalized guidance** via fine-tuned LLMs (Gemma 3 4B) that produce gap analyses with match percentages, missing skill inventories, and detailed capstone project recommendations with tech stacks and implementation steps.
3. **Continuously improving** through a closed-loop feedback system where expert reviewers rate model outputs, statistical + LLM analysis identifies weaknesses, system prompts are autonomously evolved, training data is regenerated, and the model is re-fine-tuned.

The backend in this repository serves as the **central orchestrator** -- it is the API gateway that the frontend communicates with, delegating specialized tasks to the Agent-Runtime (CV processing, knowledge graph writing) and the Advanced-Recommendation-System (skill analytics, course recommendations, GNN inference).

## System Components

| Component | Port | Role |
|-----------|------|------|
| **Backend** (this repo) | 8185 | API gateway, LLM generation, feedback loop, data pipeline |
| **Frontend** | 5173 | React UI for students (analysis) and experts (feedback/evolution) |
| **Agent-Runtime** | 8002 | CV parsing, skill normalization, knowledge graph writing, XAI |
| **Advanced-Recommendation-System** | 8001 | TF-IDF skill importance, deficit analysis, course recommendations, GNN ranking, SHAP explainability |
| **Neo4j Aura** | cloud | Shared knowledge graph (candidates, skills, jobs, roles, courses) |
| **Ollama** | local/remote | Serves fine-tuned Gemma 3 4B GGUF models for inference |

## Backend (This Repository)

### Core Generation

The primary feature is the `/generate-project` endpoint, which accepts a student profile and target job, then streams a personalized skill gap analysis and project recommendation. Three model providers are supported:

- **Gemini** (`gemini-3-flash-preview`) -- Google's cloud API with streaming
- **Ollama fine-tuned** (`student-advisor`) -- locally-served Gemma 3 4B, fine-tuned on the project's own generated dataset
- **Ollama generic** (`gemma3:1b`) -- any base Ollama model with the full system prompt injected

The `/generate-project-from-sources` endpoint provides a richer orchestrated analysis by resolving candidate data from Agent-Runtime, job data from Neo4j, and enriched skill profiles, then calling the Advanced-Recommendation-System for deficit analysis, course recommendations, project relevance scoring, and GNN-based missing skill ranking.

### Self-Evolving Feedback Loop

The distinguishing research contribution. A 4-phase continuous improvement cycle:

**Phase 1 -- Feedback Collection**: Every model output is logged. Expert reviewers rate outputs on 5 dimensions (1-5 scale): skill gap accuracy, project relevance, tech stack appropriateness, implementation step quality, and overall quality. Free-text comments capture qualitative insights.

**Phase 2 -- Pattern Analysis** (`/run-analysis`): Combines deterministic statistical analysis (per-dimension mean/median/stddev, dimension classification as WEAK/NEUTRAL/STRONG) with LLM-powered theme extraction from expert comments. Produces a `PatternReport` with recurring criticisms, praises, and actionable recommendations.

**Phase 3 -- Prompt Evolution** (`/preview-evolution`, `/apply-evolution`): An LLM acts as a Prompt Engineer -- it receives the current system prompt plus the pattern report and generates an improved prompt. Rules enforce: preserve the JSON output schema, add specific measurable instructions addressing each criticism, stay under 800 words. Prompts are version-tracked (`v2_base` -> `v2_evolved_1` -> `v2_evolved_2` ...). Unified diffs are generated for human review before committing.

**Phase 4 -- Dataset Regeneration & Re-Training** (`/run-regeneration`): The evolved prompt is used with a teacher model (Gemini or Ollama) to regenerate the training dataset (default 200 entries). The dataset is auto-uploaded to HuggingFace Hub (`Hashinika/student-advisor-dataset`). The fine-tuning notebooks are then re-run on Google Colab to produce an updated model, which is deployed back to Ollama.

### Training Data Pipeline

Located in `datasets/`, the pipeline generates high-quality training data for the fine-tuned model:

- **Seed Generation** (`generate_seeds.py`): Creates diverse synthetic candidate profiles across 50+ role archetypes (nurses, pilots, chefs, detectives, poets, etc.) using Ollama.
- **Real Seed Extraction** (`extract_real_seeds.py`): Harvests deduplicated seed data from actual user interactions logged by the system. Uses SHA-256 hashing for deduplication.
- **Smart Generator** (`smart_generator.py`): A deterministic, domain-expert engine that maps student backgrounds (finance, medical, creative, engineering, security, etc.) to curated skill gaps, project titles, tech stacks, and implementation plans. Provides expert-guided context to the teacher model.
- **Dataset Augmentation** (`augment_dataset.py`): Takes seeds, enriches them with smart generator context, and sends constructed prompts to a teacher model (Gemini or Ollama). Supports V1 (text) and V2 (JSON) output formats. Resumes from partial runs.
- **HuggingFace Upload** (`hf_uploader.py`): Auto-uploads generated JSONL datasets to `Hashinika/student-advisor-dataset` on HuggingFace Hub.

### Fine-Tuning Notebooks

Located in `notebooks/`, two Jupyter notebooks fine-tune **Google Gemma 3 4B** (`unsloth/gemma-3-4b-pt`) on Google Colab using an NVIDIA L4 GPU:

| Aspect | V1 Notebook | V2 Notebook |
|--------|-------------|-------------|
| **Dataset** | `Hashinika/student-advisor-dataset-v1` | `Hashinika/student-advisor-dataset-v2` |
| **Output format** | Structured markdown (headings-based) | Structured JSON (`gap_analysis` + `project_recommendation`) |
| **Output model** | `Hashinika/gemma-3-4b-student-advisor-v1` | `Hashinika/gemma-3-4b-student-advisor-v2` |
| **GGUF model** | `Hashinika/gemma-3-4b-student-advisor-v1-GGUF` | `Hashinika/gemma-3-4b-student-advisor-v2-GGUF` |
| **Test temperature** | 0.7 | 1.0 |

**Training Configuration (both notebooks):**
- **Method**: LoRA (Low-Rank Adaptation) via Unsloth
- **LoRA rank**: r=64, alpha=64
- **Target modules**: Attention + MLP layers (language only, not vision)
- **Trainable parameters**: 119,209,984 / 4,419,289,456 total (2.70%)
- **Precision**: 16-bit (no 4-bit quantization during training)
- **Max sequence length**: 4,096 tokens
- **Training**: 1 epoch, 20 steps, batch size 8, learning rate 2e-4, AdamW 8-bit optimizer, linear scheduler
- **Masking**: `train_on_responses_only` -- the model only learns from the assistant turn, user input is masked
- **Dataset size**: 160 training / 40 test examples (200 total)
- **Quantization**: Q4_K_M GGUF (~2.49 GB) for local deployment via Ollama

**Pipeline flow:**

```
generate_seeds.py / extract_real_seeds.py
  -> smart_generator.py (expert heuristics)
    -> augment_dataset.py (teacher model generation)
      -> hf_uploader.py (upload to HuggingFace)
        -> notebooks/ (fine-tune on Colab)
          -> GGUF export (Ollama deployment)
            -> main.py (inference at runtime)
```

### Candidate Profiles

A JSONL-backed profile store (`profiles/`) supports CRUD operations for candidate data. Profiles can be created directly via the API or synced from the Agent-Runtime service (`/profiles/{candidate_id}/sync-from-runtime`). Profile data includes skills with proficiency levels, work experiences, projects, field of study, interests, and personality traits.

### Job Data (Neo4j)

The backend queries a shared Neo4j Aura instance (`neo4j+s://2185b358.databases.neo4j.io`) directly for job listings. This includes:
- Fetching job details by ID for orchestrated analysis
- Browsing jobs grouped by role (`/jobs-by-role`)
- Full-text search across job nodes (`/search-jobs`)

## API Reference

### Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-project` | Stream a skill gap analysis + project recommendation |
| POST | `/generate-project-from-sources` | Orchestrated analysis using Agent-Runtime + Recommendation System |

### Jobs & Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/roles` | List available roles (proxied from Recommendation System) |
| GET | `/jobs-by-role` | Jobs grouped by role_key. Optional `?role_key=` filter |
| GET | `/search-jobs` | Full-text search. Params: `query`, `location`, `company`, pagination |

### Profiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profiles` | List all candidate profiles |
| GET | `/profiles/{candidate_id}` | Get a single profile |
| POST | `/profiles` | Create or update a profile |
| DELETE | `/profiles/{candidate_id}` | Delete a profile |
| POST | `/profiles/{candidate_id}/sync-from-runtime` | Pull profile from Agent-Runtime |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submit-feedback` | Submit expert feedback (5 ratings + free text) |
| GET | `/unreviewed-outputs` | Model outputs awaiting review |
| GET | `/all-feedback` | All submitted feedback entries |
| GET | `/my-outputs` | Outputs for a specific student (by name) |
| GET | `/feedback-status` | Current feedback/evolution status |

### Evolution Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/run-analysis` | Trigger pattern analysis on feedback |
| GET | `/pattern-reports` | List pattern analysis reports |
| POST | `/preview-evolution` | Preview prompt evolution diff |
| POST | `/apply-evolution` | Commit prompt evolution |
| GET | `/prompt-evolutions` | List prompt evolution history |
| GET | `/current-prompt` | Get current active prompt and version |
| POST | `/run-regeneration` | Regenerate training dataset with evolved prompt |

### Datasets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/list-datasets` | List generated JSONL datasets with entry counts |
| POST | `/upload-to-hf` | Upload a dataset to HuggingFace Hub |

## Connected Services

### Agent-Runtime (Port 8002)

Handles CV/resume processing and knowledge graph population. The backend connects via `clients/agent_runtime_client.py`:

- `POST /agent/run` -- Run the full Extract -> Normalize -> KG Write -> Gap Analyze pipeline on JSON CV data
- `POST /agent/run-from-pdf` -- Upload a PDF/DOCX resume for processing
- `GET /runtime/skill-explain` -- Skill-level explainability with contribution percentages
- `GET /runtime/predict-explain` -- SHAP-based model-level explainability
- `GET /candidates/{id}` -- Fetch candidate profiles from the knowledge graph

The Agent-Runtime maintains a 200+ entry skill alias dictionary, writes structured candidate data (Person, Skill, WorkExperience, Project, Certification nodes) to Neo4j, and supports OCR of job description images via the Chandra HuggingFace model with EasyOCR fallback.

### Advanced-Recommendation-System (Port 8001)

Provides graph-based skill analytics and recommendations. Connected via `clients/recommendation_client.py`:

- `GET /roles` -- List roles with TF-IDF skill importance profiles
- `GET /candidates/{id}/roles/{role}/skill-gap-advanced` -- Graded skill gap analysis with deficit ranking and category grouping
- `GET /candidates/{id}/roles/{role}/recommendations` -- Deficit-driven course recommendations using a greedy set-cover algorithm
- `GET /candidates/{id}/roles/{role}/project-relevance` -- Evaluate how relevant a candidate's projects are to the target role
- `GET /candidates/{id}/roles/{role}/missing-skills-gnn` -- GNN-based missing skill ranking using a HeteroGNN (SAGEConv, 128-dim) trained on 51K+ person-skill edges

**Key algorithms**: Evidence-weighted skill confidence (noisy-OR: `P(has) = 1 - product(1 - w_i)`), TF-IDF importance scoring, 4-tier graded matching (exact=1.0, cluster=0.7, high-sim=0.6, mid-sim=0.4), multiplicative hybrid ranking (`gap * importance_norm * P_gnn`), and 3-level SHAP explainability.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastAPI + Uvicorn |
| **LLM Providers** | Google Gemini (`gemini-3-flash-preview`), Ollama (local/remote) |
| **Fine-Tuning** | Unsloth + LoRA on Google Colab (NVIDIA L4) |
| **Base Model** | Google Gemma 3 4B, quantized to Q4_K_M GGUF for deployment |
| **Database** | Neo4j Aura (shared knowledge graph) |
| **Data Validation** | Pydantic v2 |
| **Dataset Hosting** | HuggingFace Hub (`Hashinika/student-advisor-dataset`) |
| **Model Hosting** | HuggingFace Hub (`Hashinika/gemma-3-4b-student-advisor-*`) |
| **Persistence** | JSONL (profiles, feedback, outputs, pattern reports, prompt evolutions) |
| **Frontend** | React 19 + TypeScript + Vite + shadcn/ui + TanStack Query |

## Project Structure

```
Thisaravi-Backend/
├── main.py                     # FastAPI application (API gateway)
├── requirements.txt
├── .env
│
├── clients/                    # HTTP clients for external microservices
│   ├── agent_runtime_client.py #   -> Agent-Runtime (port 8002)
│   ├── recommendation_client.py#   -> Advanced-Recommendation (port 8001)
│   └── integration_test.py     #   End-to-end integration test
│
├── feedback/                   # Self-evolving feedback loop
│   ├── schemas.py              #   Pydantic models (ratings, patterns, evolutions)
│   ├── storage.py              #   JSONL persistence + prompt version tracking
│   ├── analysis.py             #   Statistical + LLM theme extraction
│   ├── prompt_evolver.py       #   Meta-prompting for prompt improvement
│   ├── pipeline.py             #   Orchestration (analysis -> evolution -> regeneration)
│   └── feedback_data/          #   Persisted JSONL data files
│
├── profiles/                   # Candidate profile storage
│   ├── storage.py              #   JSONL-based CRUD
│   └── profile_data/
│
├── datasets/                   # Training data generation pipeline
│   ├── seeds.jsonl             #   Synthetic seed profiles (50+ archetypes)
│   ├── real_seeds.jsonl        #   Seeds from real user interactions
│   ├── generate_seeds.py       #   Seed generation via Ollama
│   ├── extract_real_seeds.py   #   Real seed extraction with deduplication
│   ├── smart_generator.py      #   Deterministic expert-knowledge engine
│   ├── augment_dataset.py      #   Teacher-model dataset generation
│   └── hf_uploader.py          #   HuggingFace Hub upload
│
├── notebooks/                  # Fine-tuning pipelines (Google Colab)
│   ├── gemma_3_4b_student_advisor_v1.ipynb  # V1: markdown output format
│   └── gemma_3_4b_student_advisor_v2.ipynb  # V2: JSON output format
│
├── models/                     # Model setup utilities
│   └── setup_models.ps1        #   Download GGUF + register with Ollama
│
└── docs/                       # Documentation
    ├── README.md               #   This file
    ├── architecture.md         #   System architecture with diagrams
    └── plan.md                 #   Development roadmap and proposal
```

## Setup and Installation

### Prerequisites

- Python 3.12+
- Neo4j Aura account (or local Neo4j instance)
- Ollama installed (for local model inference)
- Google Gemini API key (for cloud inference and dataset generation)
- HuggingFace account with write token (for dataset/model uploads)

### Installation

```bash
cd Thisaravi-Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
# Start the backend
uvicorn main:app --host 0.0.0.0 --port 8185 --reload

# The backend expects these companion services to be running:
# - Agent-Runtime on port 8002
# - Advanced-Recommendation-System on port 8001
```

### Setting Up the Fine-Tuned Model

1. Open `notebooks/gemma_3_4b_student_advisor_v2.ipynb` in Google Colab
2. Run all cells to fine-tune and export the GGUF model
3. Download the GGUF file or use `models/setup_models.ps1` to pull from HuggingFace
4. Register with Ollama: `ollama create student-advisor -f Modelfile`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `HF_TOKEN` | HuggingFace write token |
| `HF_DATASET_REPO` | HuggingFace dataset repository (`Hashinika/student-advisor-dataset`) |
| `OLLAMA_MODEL_FINETUNED` | Fine-tuned Ollama model name (default: `student-advisor`) |
| `OLLAMA_MODEL_GENERIC` | Generic Ollama model (default: `gemma3:1b`) |
| `GEMINI_MODEL` | Gemini model name (default: `gemini-3-flash-preview`) |
| `GENERATION_MODE` | Dataset output format: `v1` (text) or `v2` (JSON) |
| `OLLAMA_HOST` | Ollama server URL (default: `https://ollama.adithyasean.com`) |
| `OLLAMA_CF_CLIENT_ID` | Cloudflare tunnel client ID for remote Ollama |
| `OLLAMA_CF_CLIENT_SECRET` | Cloudflare tunnel client secret |
| `NEO4J_URI` | Neo4j connection URI |
| `NEO4J_USER` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `PORT` | Server port (default: `8185`) |

## Related Documentation

- [Architecture](./architecture.md) -- System architecture with Mermaid diagrams
- [Development Plan](./plan.md) -- Development roadmap and project proposal
- [Self-Evolution Design](./self_evolution_plan.md) -- Detailed design doc for the feedback loop
- [Client Usage](../clients/README.md) -- Agent-Runtime and Recommendation client documentation
- [Progress Report](./progress.md) -- Project progress notes
