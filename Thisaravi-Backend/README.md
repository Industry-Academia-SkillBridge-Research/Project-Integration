# Skill Gap Analysis & Project Generator

An AI-powered FastAPI service that analyses a candidate's profile against a target job, identifies skill gaps, and streams a tailored capstone project recommendation. Supports multiple LLM backends and integrates with two companion services in the `upskill` monorepo.

---

## Architecture

```
LinkedIn-Job-Scrape-Scheduler  (port 8000)
        │  job_id → JobResponse
        ▼
AI-Driven-Project-Recommendation  (port 8010)   ◀── this service
        │  streams JSON recommendation
        ▼
  React Frontend  (port 5173)

learning-Path-Recommendation/Agent-Runtime  (port 8002)
        │  candidate_id → CandidateProfile
        ▼
AI-Driven-Project-Recommendation  (port 8010)

learning-Path-Recommendation/Role-Skill-API  (port 8181)
        │  role_key → required skills (market demand)
        ▼
AI-Driven-Project-Recommendation  (port 8010)
```

The new `/generate-project-from-sources` endpoint accepts identifiers for the two companion services instead of raw data, fetches and maps them automatically, then streams the recommendation.

---

## Setup

### Prerequisites
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Ollama](https://ollama.com/) running locally (`ollama serve`)
- Fine-tuned model loaded: `student-advisor:v2-json` (see `models/v2-json/Modelfile`)

### Install & Configure

```bash
# 1. Clone / navigate to this directory
cd AI-Driven-Project-Recommendation

# 2. Install dependencies (uv manages the venv automatically)
uv sync

# 3. Copy and fill in the env file
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY if using Gemini
```

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8010` | Port this API listens on |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model ID |
| `OLLAMA_MODEL_FINETUNED` | `student-advisor:v2-json` | Fine-tuned Ollama model |
| `OLLAMA_MODEL_GENERIC` | `gemma3:1b` | Generic Ollama base model |
| `LINKEDIN_SCRAPER_URL` | `http://localhost:8000` | LinkedIn Scraper API |
| `AGENT_RUNTIME_URL` | `http://localhost:8002` | LPR Agent-Runtime API |
| `ROLE_SKILL_API_URL` | `http://localhost:8181` | LPR Role-Skill-API |

---

## React Frontend (`project-recommendation-frontend/`)

The frontend runs on `http://localhost:5173` and connects to this API via a Vite dev-server proxy (`/api` → port 8010).

### Modes

| Tab | Endpoint | When to use |
|---|---|---|
| **Manual** | `POST /generate-project` | Enter student profile & job fields by hand |
| **From Sources** | `POST /generate-project-from-sources` | Pull data from companion services by ID |

### Source mode wiring

| UI element | Companion service | Proxy path | Real endpoint |
|---|---|---|---|
| Job search (query → results list) | LinkedIn Scraper | `/scraper` → port 8000 | `GET /api/v1/search?query=&page_size=` (returns `{ hits: [...] }`) |
| Job fetch by ID (backend) | LinkedIn Scraper | direct HTTP | `GET /api/v1/job/{job_id}` (singular — Elasticsearch) |
| Candidate dropdown | Agent-Runtime | `/agent-runtime` → port 8002 | `GET /candidates` |
| Role Key dropdown (optional) | Role-Skill-API | `/role-skills` → port 8181 | `GET /roles` |

### Start the LinkedIn Scraper

```bash
cd LinkedIn-Job-Scrape-Scheduler
# Recommended: includes Elasticsearch for search/store
docker-compose up -d   # starts linkedin-scraper-api (8000) + linkedin-elasticsearch (9200)

# Bare Python (scraping only, no Elasticsearch persistence):
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start the frontend

```bash
cd project-recommendation-frontend
npm run dev          # http://localhost:5173
```

---


## Running

```bash
# Development (auto-reload)
uv run uvicorn main:app --host 0.0.0.0 --port 8010 --reload

# Full stack (backend + Streamlit UI)
uv run python run.py
```

| Service | URL |
|---|---|
| API docs (Swagger) | http://localhost:8010/docs |
| Streamlit UI | http://localhost:8501 |

---

## API Endpoints

### `POST /generate-project`
Original endpoint — caller supplies full `StudentData` and `JobData` manually.

```json
{
  "student_data": { "name": "...", "current_role": "...", "skills": [], "experience_summary": "..." },
  "job_data": { "role": "...", "required_skills": [], "description_summary": "..." },
  "target_role": "Data Engineer",
  "model_provider": "ollama_generic"
}
```

### `POST /generate-project-from-sources` *(new)*
Fetches candidate and job data from companion services by ID, then streams a recommendation. All combinations of ID vs inline are supported.

```json
{
  "job_id": "data-engineer-techcorp-123456",
  "candidate_id": "CAND_ML_2024_001",
  "role_key": "data_engineer",
  "model_provider": "gemini"
}
```

| Field | Source |
|---|---|
| `job_id` | LinkedIn Scraper `GET /api/v1/jobs/{id}` |
| `candidate_id` | Agent-Runtime `GET /candidates/{id}` |
| `role_key` | Role-Skill-API `GET /roles/{key}/skills` (optional — enriches required skills) |
| `inline_job` | `JobData` body — skips external fetch |
| `inline_candidate` | `CandidateProfile` body — skips external fetch |

`model_provider` options: `gemini` · `ollama` (fine-tuned) · `ollama_generic`

All endpoints stream `text/plain` (raw JSON from the model).

### Feedback & Evolution Endpoints
| Method | Path | Purpose |
|---|---|---|
| `POST` | `/submit-feedback` | Log expert feedback on an output |
| `GET` | `/unreviewed-outputs` | List outputs awaiting review |
| `POST` | `/run-analysis` | Phase 1: pattern analysis on feedback |
| `POST` | `/preview-evolution` | Preview prompt diff |
| `POST` | `/apply-evolution` | Commit evolved prompt |
| `GET` | `/current-prompt` | Active system prompt + version |
| `POST` | `/run-regeneration` | Regenerate dataset with evolved prompt |

---

## Testing

```bash
# Unit tests
uv run pytest test_app.py -v

# Quick smoke test (inline data, no external services needed)
curl -s -X POST http://localhost:8010/generate-project-from-sources \
  -H "Content-Type: application/json" \
  -d '{
    "inline_job": {
      "role": "Data Engineer",
      "required_skills": ["Python", "Spark", "Kafka", "SQL", "Airflow"],
      "description_summary": "Build scalable real-time data pipelines."
    },
    "inline_candidate": {
      "candidate_id": "test_001",
      "name": "Thisaravi",
      "current_role": "CS Student",
      "skills": [{"skill_name": "Python"}, {"skill_name": "SQL"}],
      "work_experiences": [],
      "projects": []
    },
    "model_provider": "ollama_generic"
  }'
```

---

## Project Structure

```
main.py              FastAPI backend — all endpoints, model runners, data mappers
run.py               Launches backend + Streamlit UI together
ui.py                Streamlit dashboard
parsers.py           Unified streaming response parser (text + JSON modes)
compare_models.py    Offline model comparison against ground truth
test_app.py          Pytest unit tests
.env                 Local secrets (not committed)
.env.example         Template for .env

feedback/            Self-evolution pipeline
  pipeline.py        Orchestrates analysis → evolution → regeneration phases
  analysis.py        Pattern analysis on collected feedback
  prompt_evolver.py  LLM-driven prompt rewriting
  storage.py         JSONL persistence for outputs, feedback, reports
  schemas.py         Pydantic models for feedback data

datasets/            Training data management
  seeds.jsonl        Seed examples for dataset generation
  smart_generator.py Dataset generation script
  student_advisor_dataset_v3.jsonl  Latest training dataset

models/
  v1-text/Modelfile  Ollama Modelfile for text-output fine-tuned model
  v2-json/Modelfile  Ollama Modelfile for JSON-output fine-tuned model

docs/                Reports and notes
notebooks/           Fine-tuning notebooks (Kaggle/Colab)
notebooks2/          Inference & evaluation notebooks
```

