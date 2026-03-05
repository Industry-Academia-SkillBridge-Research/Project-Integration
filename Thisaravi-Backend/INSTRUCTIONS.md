# Instructions Manual: Skill Gap Analyzer with Self-Evolving Feedback Loop

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites](#2-prerequisites)
3. [Installation & Setup](#3-installation--setup)
4. [Running the Application](#4-running-the-application)
5. [Using the Main UI](#5-using-the-main-ui)
6. [Expert Feedback Portal](#6-expert-feedback-portal)
7. [Self-Evolution Dashboard](#7-self-evolution-dashboard)
8. [Complete Evolution Walkthrough](#8-complete-evolution-walkthrough)
9. [Dataset Generation Pipeline](#9-dataset-generation-pipeline)
10. [Fine-Tuning on Google Colab](#10-fine-tuning-on-google-colab)
11. [Model Deployment with Ollama](#11-model-deployment-with-ollama)
12. [API Reference](#12-api-reference)
13. [File Structure Reference](#13-file-structure-reference)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. System Overview

The Skill Gap Analyzer is an AI-powered system that:

1. Analyzes a student's profile against a target job description
2. Identifies missing skills and computes a match score
3. Recommends a tailored capstone project to bridge the skill gap

The system supports three model providers:
- **Fine-tuned Gemma 3 4B** (local, via Ollama) -- the primary model
- **Generic Gemma 3 1B** (local, via Ollama) -- baseline comparison
- **Google Gemini 3 Flash** (cloud API) -- teacher/reference model

### Self-Evolution Mechanism

The self-evolution layer wraps the core system with a feedback-driven improvement cycle:

```
Generate Outputs --> Collect Expert Feedback --> Detect Patterns
       ^                                            |
       |                                            v
  Re-Fine-Tune  <-- Regenerate Dataset <-- Evolve System Prompt
```

Each phase is **manually triggered** by the researcher, ensuring full control over the evolution process.

---

## 2. Prerequisites

| Requirement | Details |
|-------------|---------|
| Python | 3.9 or higher |
| Ollama | Installed and running (`ollama serve`) |
| GPU (for inference) | Optional but recommended for local models |
| Google Colab | For fine-tuning (requires NVIDIA L4/A100 GPU) |
| Gemini API Key | For cloud model and/or dataset generation |
| Hugging Face Token | For dataset and model uploads |

---

## 3. Installation & Setup

### 3.1 Install Dependencies

```bash
cd gaps-analyzer-and-recommendations
pip install -r requirements.txt
```

### 3.2 Environment Configuration

Create a `.env` file in the project root:

```ini
GEMINI_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
OLLAMA_MODEL_FINETUNED=student-advisor:v2-json
OLLAMA_MODEL_GENERIC=gemma3:1b
GENERATION_MODE=v2
HF_TOKEN=your_huggingface_token_here
```

### 3.3 Pull Ollama Models

```bash
# Fine-tuned model (if already uploaded to HuggingFace)
ollama pull hf.co/Hashinika/gemma-3-4b-student-advisor-v2-GGUF

# Generic baseline model
ollama pull gemma3:1b
```

Or use the setup scripts in `models/`:

```bash
# Linux/Mac
bash models/setup_model.sh

# Windows
powershell models/setup_model.ps1
```

---

## 4. Running the Application

### 4.1 Full Stack (All Services)

```bash
python run.py
```

This launches four services:

| Service | URL | Description |
|---------|-----|-------------|
| FastAPI Backend | http://localhost:8000 | REST API for model inference |
| Main UI | http://localhost:8501 | Student/job input and results |
| Feedback Portal | http://localhost:8502 | Expert feedback collection |
| Evolution Dashboard | http://localhost:8503 | Self-evolution control panel |

Press `Ctrl+C` to stop all services.

### 4.2 Individual Services

Run services separately if needed:

```bash
# Backend only
python main.py

# Main UI only
streamlit run ui.py

# Feedback Portal only
streamlit run feedback_ui.py --server.port 8502

# Evolution Dashboard only
streamlit run evolution_ui.py --server.port 8503
```

**Note:** The backend (FastAPI) must be running for the Main UI to function. The Feedback Portal and Evolution Dashboard work independently by reading/writing JSONL files directly.

---

## 5. Using the Main UI

### 5.1 Open the Interface

Navigate to **http://localhost:8501** in your browser.

### 5.2 Fill in Student Profile

In the left column, enter:
- **Name**: Student's name
- **Current Role**: e.g., "Undergraduate student", "Junior Dev"
- **Major / Background**: e.g., "Computer Science"
- **Interests**: Comma-separated, e.g., "AI, Web Development"
- **Personality Traits**: e.g., "ambitious, problem-solver"
- **Current Skills**: Comma-separated, e.g., "Python, Basic SQL, Git"

### 5.3 Fill in Job Description

In the right column, enter:
- **Target Role**: e.g., "Machine Learning Engineer"
- **Required Skills**: Comma-separated, e.g., "PyTorch, NLP, AWS, MLOps"
- **Job Summary**: Brief description of the role

### 5.4 Select Model Provider

In the sidebar under **Model Provider**, choose:
- **Ollama (Finetuned)**: Uses the fine-tuned Gemma 3 4B model (recommended)
- **Gemini (Cloud)**: Uses Google Gemini via API
- **Ollama (Generic)**: Uses the generic Gemma 3 1B model

### 5.5 Generate and View Results

1. Click **Generate Plan**
2. Watch the real-time streaming output
3. After streaming completes, the parsed dashboard appears with:
   - **Match Score**: Percentage showing current skill alignment
   - **Analysis Summary**: Explanation of the skill gap
   - **Recommended Project**: Title, objective, tech stack, and implementation steps

### 5.6 Test Profile

Click **Load Test Profile** in the sidebar to auto-fill the form with data matching the fine-tuned model's training distribution. This is useful for verifying the model works correctly.

**Important:** Every time you generate output, the system automatically logs the input/output pair for later expert review via the Feedback Portal.

---

## 6. Expert Feedback Portal

### 6.1 Open the Portal

Navigate to **http://localhost:8502**.

### 6.2 Set Your Reviewer ID

In the sidebar, enter your **Reviewer ID** (e.g., "expert_01"). This tags all your feedback entries for tracking.

### 6.3 Select an Output to Review

The dropdown at the top shows all model outputs that have not yet been reviewed. Each entry is labeled as:
```
#1: CS Student -> NLP Engineer
#2: Nurse, 5 years -> Data Scientist
...
```

Select one to load it for review.

### 6.4 Review the Output

The page displays:
- **Original Input**: Student profile and job description
- **Model Output (Parsed)**: The structured response showing gap analysis metrics, missing skills, project recommendation, tech stack, and implementation steps

### 6.5 Provide Ratings

Rate the output on five dimensions using the sliders (1 = Poor, 5 = Excellent):

| Dimension | What to Evaluate |
|-----------|-----------------|
| **Skill Gap Accuracy** | Are the identified missing skills correct and complete? |
| **Project Relevance** | Does the project address the actual skill gaps? |
| **Tech Stack Appropriateness** | Is the tech stack modern, correct, and complete for the project? |
| **Implementation Step Quality** | Are the steps detailed, actionable, and properly sequenced? |
| **Overall Quality** | Holistic assessment of the entire response |

### 6.6 Write Comments

In the **Comments** text area, explain your reasoning. Be specific about what could be improved. Examples of useful feedback:

- "Implementation steps for ML projects should mention model versioning and experiment tracking"
- "Tech stack is missing deployment tools like Docker"
- "The analysis summary is too brief--should be a full paragraph"
- "Good identification of missing skills, but the match percentage seems high"

### 6.7 Submit

Click **Submit Feedback**. The page will refresh and the reviewed output will be removed from the unreviewed list.

### 6.8 Sidebar Statistics

The sidebar shows:
- **Total Reviews**: Number of feedback entries collected
- **Avg Overall**: Average overall quality score
- **Prompt Version**: Which system prompt version the outputs were generated with

---

## 7. Self-Evolution Dashboard

### 7.1 Open the Dashboard

Navigate to **http://localhost:8503**.

### 7.2 Dashboard Status Header

At the top, three metrics show the current state:
- **Prompt Version**: Current active version (e.g., "v2_base", "v2_evolved_1")
- **Total Feedback**: Number of expert reviews collected
- **Evolutions**: Number of prompt evolution cycles completed

### 7.3 Configuration Sidebar

- **LLM Provider**: Choose "ollama" or "gemini" for the LLM used in analysis and evolution (this is the model that analyzes feedback and generates the evolved prompt, not the student model)
- **Current System Prompt**: Preview of the active system prompt

### 7.4 Phase 1: Pattern Analysis

1. Ensure you have collected sufficient feedback (minimum 10 entries recommended; 3 is the absolute minimum)
2. Click **Run Analysis**
3. The system will:
   - Compute per-dimension statistics (mean, median, std)
   - Classify dimensions as WEAK (< 3.0), NEUTRAL (3.0-4.0), or STRONG (>= 4.0)
   - Send all free-text comments to an LLM for theme extraction
   - Generate a Pattern Report

4. Review the results:
   - **Average Ratings**: Progress bars showing per-dimension scores
   - **Weak Dimensions**: Highlighted in red
   - **Strong Dimensions**: Highlighted in green
   - **Recurring Themes**: Criticisms extracted from comments
   - **Actionable Insights**: Specific recommended prompt changes

### 7.5 Phase 2: Prompt Evolution

1. Select the Pattern Report to base the evolution on (defaults to the latest)
2. Click **Preview Evolution** to see a diff of what would change
3. Review the diff to ensure the changes make sense
4. Click **Apply Evolution** to commit the new prompt

The system uses a meta-prompting strategy: an LLM acts as a prompt engineer, receiving the current system prompt and the pattern report, and producing a revised prompt that addresses weaknesses while preserving strengths.

### 7.6 Phase 3: Dataset Regeneration

1. Select the evolution record to use (defaults to the latest)
2. Set the **Target Entry Count** (default: 200)
3. Click **Start Regeneration**
4. The system will run the existing `augment_dataset.py` pipeline with the evolved system prompt, producing a new JSONL dataset file

The new dataset will be saved as:
```
datasets/student_advisor_dataset_<version>.jsonl
```
For example: `datasets/student_advisor_dataset_v2_evolved_1.jsonl`

### 7.7 Phase 4: Re-Fine-Tuning

This phase is semi-manual. The dashboard provides instructions:

1. Upload the new dataset to HuggingFace (use the existing `student_advisor_dataset_v2.py` script, modifying the file path)
2. Open the Colab notebook `notebooks/gemma_3_4b_student_advisor_v2.ipynb`
3. Change the `my_dataset` variable to point to the new dataset
4. Run all cells
5. Download the GGUF model and register with Ollama:
   ```bash
   ollama create student-advisor:<version> -f Modelfile
   ```
6. Update `.env` with the new model tag

### 7.8 Evolution History

The bottom of the dashboard shows all past evolutions with:
- Version transition (e.g., "v2_base -> v2_evolved_1")
- Timestamp
- Change summary
- Side-by-side view of original and evolved prompts

---

## 8. Complete Evolution Walkthrough

This is a step-by-step guide for running a complete evolution cycle from start to finish.

### Step 1: Generate Model Outputs (Main UI)

1. Open http://localhost:8501
2. Enter various student profiles and job descriptions
3. Click **Generate Plan** for each one
4. Repeat for at least 10-15 different inputs to build a diverse set of outputs for review

### Step 2: Collect Expert Feedback (Feedback Portal)

1. Open http://localhost:8502
2. Review each output:
   - Rate all 5 dimensions (1-5)
   - Write detailed comments explaining strengths and weaknesses
3. Submit feedback for each output
4. Continue until you have at least 10 reviewed outputs (more is better)

### Step 3: Run Pattern Analysis (Evolution Dashboard)

1. Open http://localhost:8503
2. In Phase 1, click **Run Analysis**
3. Review the report:
   - Which dimensions are weak?
   - What recurring themes appear in the comments?
   - Do the actionable insights make sense?

### Step 4: Evolve the Prompt (Evolution Dashboard)

1. In Phase 2, click **Preview Evolution**
2. Review the diff:
   - Are the changes addressing the right weaknesses?
   - Is the JSON schema preserved?
   - Are strong-performing aspects left intact?
3. If satisfied, click **Apply Evolution**

### Step 5: Regenerate Dataset (Evolution Dashboard)

1. In Phase 3, set target count (200 recommended)
2. Select provider (ollama or gemini)
3. Click **Start Regeneration**
4. Wait for generation to complete (this may take time depending on the teacher model)

### Step 6: Re-Fine-Tune (Colab)

1. Upload the new dataset to HuggingFace
2. Open the Colab notebook
3. Update `my_dataset` to the new dataset ID
4. Run all cells
5. Download the GGUF model

### Step 7: Deploy New Model (Local)

1. Register the new model with Ollama:
   ```bash
   ollama create student-advisor:v2_evolved_1 -f models/v2-json/Modelfile
   ```
2. Update `.env`:
   ```ini
   OLLAMA_MODEL_FINETUNED=student-advisor:v2_evolved_1
   ```
3. Restart the application (`python run.py`)

### Step 8: Validate (Main UI)

1. Run the same inputs through the new model
2. Compare outputs against the old model's results
3. Collect new feedback to quantify the improvement
4. Repeat the cycle if further improvement is needed

---

## 9. Dataset Generation Pipeline

### 9.1 Seed Generation

Generate fresh seed profiles from role archetypes:

```bash
cd datasets
python generate_seeds.py
```

Output: `datasets/seeds.jsonl` (200 entries from 50 archetypes)

### 9.2 Dataset Augmentation

Generate full training examples using the teacher model:

```bash
cd datasets
python augment_dataset.py
```

Configuration is controlled by environment variables:
- `GENERATION_MODE`: "v1" (text) or "v2" (JSON)
- `TEST_MODE`: Set to any value to generate only 1 test entry

The script supports **resume**: if interrupted, it picks up from the last successfully written entry.

### 9.3 Dataset Verification and Upload

```bash
cd datasets
python student_advisor_dataset_v2.py
```

This validates entry structure and uploads to HuggingFace with an 80/20 train/test split.

---

## 10. Fine-Tuning on Google Colab

### 10.1 Open the Notebook

Upload or open `notebooks/gemma_3_4b_student_advisor_v2.ipynb` in Google Colab.

### 10.2 Select GPU Runtime

Go to **Runtime > Change runtime type > L4 GPU** (or A100 if available).

### 10.3 Configure Variables

In the second cell, set:

```python
HF_TOKEN = "your_huggingface_token"
my_dataset = "Hashinika/student-advisor-dataset-v2"  # Change for evolved datasets
fine_tuned_model = "Hashinika/gemma-3-4b-student-advisor-v2"
gguf_model = "Hashinika/gemma-3-4b-student-advisor-v2-GGUF"
```

### 10.4 Run All Cells

The notebook will:
1. Install Unsloth and dependencies
2. Load Gemma 3 4B pretrained model
3. Configure LoRA (r=64, alpha=64)
4. Load and format the dataset
5. Train for 1 epoch (train_on_responses_only)
6. Test inference
7. Push the model to HuggingFace
8. Export and upload GGUF (Q4_K_M quantization)

### 10.5 Training Output

Expected metrics:
- Trainable parameters: ~119M / 4.4B (2.70%)
- Training time: approximately 5-10 minutes on L4

---

## 11. Model Deployment with Ollama

### 11.1 Download GGUF

If using the setup script:
```bash
bash models/setup_model.sh
```

Or manually:
```bash
# Download from HuggingFace
huggingface-cli download Hashinika/gemma-3-4b-student-advisor-v2-GGUF \
    gemma-3-4b-pt.Q4_K_M.gguf --local-dir models/v2-json/
```

### 11.2 Create Modelfile

The Modelfile template (already in the repo at `models/v2-json/`):

```
FROM ./gemma-3-4b-pt.Q4_K_M.gguf
TEMPLATE """<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
{{ .Response }}<end_of_turn>"""
PARAMETER stop "<end_of_turn>"
```

### 11.3 Register with Ollama

```bash
cd models/v2-json
ollama create student-advisor:v2-json -f Modelfile
```

### 11.4 Test

```bash
ollama run student-advisor:v2-json
```

Paste a test input:
```json
{"student_data": {"demographics": "CS Student", "major": "CS", "interests": ["AI"], "current_skills": ["Python"], "personality": "logical"}, "job_data": {"target_job_role": "ML Engineer", "required_skills": ["PyTorch", "MLOps"], "description": "Build ML models"}}
```

---

## 12. API Reference

### Base URL: `http://localhost:8000`

### POST `/generate-project`

Generate a skill gap analysis and project recommendation.

**Request Body:**
```json
{
    "student_data": {
        "name": "Alex",
        "current_role": "Junior Dev",
        "skills": ["Python", "SQL"],
        "experience_summary": "2 years",
        "major": "Computer Science",
        "interests": ["AI", "Web Dev"],
        "personality": "ambitious"
    },
    "job_data": {
        "role": "ML Engineer",
        "required_skills": ["PyTorch", "MLOps"],
        "description_summary": "Build ML models"
    },
    "target_role": "ML Engineer",
    "model_provider": "ollama",
    "ollama_model": null
}
```

**Response:** Streaming text (text/plain). Parse with `parsers.parse_response()`.

### POST `/submit-feedback`

Submit expert feedback on a model output.

**Request Body:**
```json
{
    "model_input": {"student_data": {...}, "job_data": {...}},
    "model_output": "<raw model response>",
    "model_provider": "ollama",
    "ratings": {
        "skill_gap_accuracy": 4,
        "project_relevance": 3,
        "tech_stack_appropriateness": 2,
        "implementation_step_quality": 2,
        "overall_quality": 3
    },
    "free_text_comments": "Tech stack missing deployment tools...",
    "reviewer_id": "expert_01",
    "prompt_version": "v2_base"
}
```

**Response:** `{"status": "ok", "feedback_id": "fb_a1b2c3d4"}`

### GET `/unreviewed-outputs`

Returns a JSON array of model outputs that have not been reviewed.

### GET `/feedback-status`

Returns the current evolution status:
```json
{
    "current_prompt_version": "v2_base",
    "total_feedback": 15,
    "feedback_per_version": {"v2_base": 15},
    "total_reports": 1,
    "total_evolutions": 0,
    "evolution_history": []
}
```

---

## 13. File Structure Reference

```
gaps-analyzer-and-recommendations/
|
|-- main.py                  # FastAPI backend (inference + feedback API)
|-- ui.py                    # Streamlit main UI (student input + results)
|-- feedback_ui.py           # Streamlit expert feedback portal
|-- evolution_ui.py          # Streamlit evolution dashboard
|-- run.py                   # Launches all 4 services
|-- parsers.py               # Response parsing (JSON + text formats)
|-- compare_models.py        # Model comparison script
|-- test_app.py              # Unit tests (pytest)
|-- requirements.txt         # Python dependencies
|-- .env                     # API keys and model config (not in git)
|
|-- feedback/                # Self-evolution package
|   |-- __init__.py
|   |-- schemas.py           # Pydantic data models
|   |-- storage.py           # JSONL file I/O
|   |-- analysis.py          # Pattern detection (stats + LLM themes)
|   |-- prompt_evolver.py    # Meta-prompting for prompt evolution
|   |-- pipeline.py          # Orchestration of the full cycle
|   |-- feedback_data/       # Data directory (auto-created)
|       |-- expert_feedback.jsonl
|       |-- model_outputs_log.jsonl
|       |-- pattern_reports.jsonl
|       |-- prompt_evolutions.jsonl
|
|-- datasets/                # Training data pipeline
|   |-- seeds.jsonl          # Seed student profiles (200 entries)
|   |-- generate_seeds.py    # Seed generation from archetypes
|   |-- smart_generator.py   # Domain-specific heuristic guidance
|   |-- augment_dataset.py   # Teacher model data generation
|   |-- student_advisor_dataset_v1.jsonl  # V1 dataset (text format)
|   |-- student_advisor_dataset_v2.jsonl  # V2 dataset (JSON format)
|   |-- student_advisor_dataset_v3.jsonl  # V3 dataset
|
|-- notebooks/               # Fine-tuning notebooks (Colab)
|   |-- gemma_3_4b_student_advisor_v1.ipynb
|   |-- gemma_3_4b_student_advisor_v2.ipynb
|   |-- gemma_3_4b_student_advisor_v3.ipynb
|
|-- models/                  # GGUF models and setup scripts
|   |-- v1-text/
|   |-- v2-json/
|   |-- setup_model.sh
|   |-- setup_model.ps1
|
|-- docs/                    # Documentation and reports
|   |-- progress.md
|   |-- gemma_finetuning_notes.md
|   |-- model_comparison_report.md
|
|-- self_evolution_plan.md   # Technical implementation plan
|-- research_paper.tex       # IEEE-format LaTeX research paper
|-- INSTRUCTIONS.md          # This manual
```

---

## 14. Troubleshooting

### "No unreviewed model outputs available"

Generate some outputs first via the Main UI (http://localhost:8501). Every time you click **Generate Plan**, the output is automatically logged for review.

### Feedback Portal shows stale data

The portal reads from JSONL files directly. If you submitted feedback but the list hasn't updated, click the Streamlit rerun button (R) or refresh the page.

### "Ollama Error: model not found"

Ensure the model is registered:
```bash
ollama list
```

If your model is not listed, create it:
```bash
ollama create student-advisor:v2-json -f models/v2-json/Modelfile
```

### Evolution analysis returns poor themes

The quality of theme extraction depends on the LLM used. If using "ollama" with a small model (gemma3:1b), consider switching to "gemini" in the Evolution Dashboard sidebar for better analysis quality.

### Dataset regeneration is slow

The augmentation script generates one entry at a time to handle rate limits. For Gemini, expect 10-second intervals between entries during rate limiting. For Ollama with a large teacher model (qwen3-coder:30b), each entry may take 30-60 seconds.

### Colab notebook runs out of memory

Ensure you selected an L4 or A100 GPU runtime. The default T4 may not have enough VRAM for Gemma 3 4B fine-tuning.

### Backend won't start (import errors)

Make sure you are running from the project root directory:
```bash
cd gaps-analyzer-and-recommendations
python run.py
```

The feedback package imports require the correct working directory.

### Port already in use

If a port is occupied, either stop the conflicting process or change the port:
```bash
streamlit run feedback_ui.py --server.port 8504
```

---

*Last updated: 2026-02-12*
