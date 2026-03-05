# Self-Evolving Feedback Loop: Implementation Plan

**Date:** 2026-02-12
**Status:** Proposed
**System:** Skill Gap Analysis & Capstone Project Generator

---

## 1. Overview

This document describes the design and implementation of a **self-evolving feedback loop** that enables the Skill Gap Analyzer to continuously improve through expert feedback. The mechanism collects structured ratings and free-text commentary from domain experts, detects systematic weaknesses through statistical and LLM-powered pattern analysis, autonomously evolves the teacher model's system prompt, regenerates training data, and re-fine-tunes the student model.

### 1.1 Current Pipeline (Linear)

```
Seeds ──> Smart Guidance ──> Teacher Model ──> Dataset (JSONL) ──> HuggingFace ──> Fine-Tune ──> GGUF ──> Ollama ──> FastAPI ──> Streamlit
```

### 1.2 Proposed Pipeline (Closed-Loop)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXISTING LINEAR PIPELINE                            │
│  Seeds -> Smart Guidance -> Teacher Model -> Dataset -> Fine-Tune -> Deploy │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ Model outputs served to users
                                 ▼
                    ┌────────────────────────┐
                    │  1. FEEDBACK COLLECTION │◄── Expert reviewers rate outputs
                    │     (Structured + Text) │    (5 dimensions, 1-5 scale)
                    └───────────┬────────────┘    + free-text comments
                                │
                                ▼
                    ┌────────────────────────┐
                    │  2. PATTERN DETECTION  │    Statistical analysis +
                    │  (Manual Trigger)      │    LLM-powered theme extraction
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  3. PROMPT EVOLUTION   │    LLM synthesizes feedback
                    │  (Manual Trigger)      │    patterns into prompt changes
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  4. DATASET REGEN      │    Teacher model re-generates
                    │  (Manual Trigger)      │    training data with evolved prompt
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  5. RE-FINE-TUNE       │    Same LoRA pipeline on Colab
                    │  (Semi-Manual)         │    with new dataset
                    └───────────┬────────────┘
                                │
                                └──────────> Back to Deploy (new model version)
```

### 1.3 Design Principles

- **Manual Control**: Every phase is manually triggered by the researcher. No automatic loops.
- **Backward Compatible**: Existing pipeline works unchanged when no evolution has occurred.
- **Simple Storage**: Append-only JSONL files (consistent with existing project patterns).
- **No New Dependencies**: Uses only libraries already in `requirements.txt` (pydantic, ollama, google-generativeai, streamlit).

---

## 2. New Modules

### 2.1 Directory Structure

```
gaps-analyzer-and-recommendations/
├── feedback/                        # NEW: Feedback loop package
│   ├── __init__.py
│   ├── schemas.py                   # Pydantic data models
│   ├── storage.py                   # JSONL file I/O
│   ├── analysis.py                  # Pattern detection & theme extraction
│   ├── prompt_evolver.py            # System prompt evolution via meta-prompting
│   ├── pipeline.py                  # Orchestration of the full cycle
│   └── feedback_data/               # Data directory
│       ├── expert_feedback.jsonl
│       ├── model_outputs_log.jsonl
│       ├── pattern_reports.jsonl
│       └── prompt_evolutions.jsonl
├── feedback_ui.py                   # NEW: Streamlit page for expert feedback
├── evolution_ui.py                  # NEW: Streamlit dashboard for evolution control
├── main.py                          # MODIFIED: Add output logging + feedback API
├── ui.py                            # MODIFIED: Add feedback portal link
├── datasets/
│   └── augment_dataset.py           # MODIFIED: Parameterize system prompt
└── run.py                           # MODIFIED: Add feedback UI subprocess
```

---

## 3. Data Schemas

### 3.1 Feedback Ratings

Five dimensions mapped directly to model output structure:

| Dimension | What It Measures | Maps To |
|-----------|-----------------|---------|
| `skill_gap_accuracy` | Are the identified missing skills correct and complete? | `gap_analysis.missing_skills` |
| `project_relevance` | Does the project recommendation address the actual gaps? | `project_recommendation.project_title` + `objective` |
| `tech_stack_appropriateness` | Is the tech stack modern, correct, and complete? | `project_recommendation.tech_stack` |
| `implementation_step_quality` | Are steps detailed, actionable, and properly sequenced? | `project_recommendation.implementation_steps` |
| `overall_quality` | Holistic assessment of the entire response | Full output |

All ratings use a 1-5 integer scale (1 = Poor, 5 = Excellent).

### 3.2 Schema Definitions

#### FeedbackEntry

```json
{
    "feedback_id": "fb_a1b2c3d4",
    "timestamp": "2026-02-12T14:30:00Z",
    "model_input": {
        "student_data": {
            "demographics": "CS Student",
            "major": "Computer Science",
            "interests": ["NLP"],
            "current_skills": ["Python", "SQL"],
            "personality": "logical, problem-solver"
        },
        "job_data": {
            "target_job_role": "NLP Engineer",
            "required_skills": ["PyTorch", "Transformers", "API deployment"],
            "description": "Build NLP systems"
        }
    },
    "model_output": "{\"gap_analysis\": {...}, \"project_recommendation\": {...}}",
    "model_provider": "ollama",
    "ratings": {
        "skill_gap_accuracy": 4,
        "project_relevance": 3,
        "tech_stack_appropriateness": 2,
        "implementation_step_quality": 2,
        "overall_quality": 3
    },
    "free_text_comments": "The missing skills are accurate but the tech stack is outdated. Implementation steps lack detail about model training specifics.",
    "reviewer_id": "expert_01",
    "prompt_version": "v2_base"
}
```

#### ModelOutputLog

```json
{
    "output_id": "out_e5f6g7h8",
    "timestamp": "2026-02-12T14:25:00Z",
    "model_input": {"student_data": {...}, "job_data": {...}},
    "model_output": "<full raw model response text>",
    "model_provider": "ollama",
    "prompt_version": "v2_base",
    "has_feedback": false
}
```

#### PatternReport

```json
{
    "report_id": "rpt_i9j0k1l2",
    "timestamp": "2026-02-12T15:00:00Z",
    "total_feedback_analyzed": 30,
    "avg_ratings": {
        "skill_gap_accuracy": 3.8,
        "project_relevance": 3.5,
        "tech_stack_appropriateness": 2.4,
        "implementation_step_quality": 2.1,
        "overall_quality": 3.0
    },
    "low_scoring_dimensions": ["tech_stack_appropriateness", "implementation_step_quality"],
    "recurring_themes": [
        "Implementation steps lack ML-specific detail",
        "Tech stacks often miss deployment tools (Docker, CI/CD)",
        "Steps don't mention testing strategies"
    ],
    "actionable_insights": [
        "Add instruction to always include at least one deployment/DevOps tool",
        "Require ML projects to mention model versioning and experiment tracking",
        "Mandate that each implementation step includes a concrete deliverable"
    ],
    "raw_summary": "<full LLM analysis text>"
}
```

#### PromptEvolution

```json
{
    "evolution_id": "evo_m3n4o5p6",
    "timestamp": "2026-02-12T15:30:00Z",
    "parent_prompt_version": "v2_base",
    "new_prompt_version": "v2_evolved_1",
    "pattern_report_id": "rpt_i9j0k1l2",
    "original_prompt": "<full SYSTEM_PROMPT_JSON text>",
    "evolved_prompt": "<full evolved prompt text>",
    "change_summary": "Added deployment tool requirement. Enhanced ML-specific instructions."
}
```

---

## 4. Module Specifications

### 4.1 `feedback/schemas.py`

Pydantic models for all data types. Pure data definitions, no business logic.

```python
from pydantic import BaseModel
from typing import List, Optional

class FeedbackRatings(BaseModel):
    skill_gap_accuracy: int         # 1-5
    project_relevance: int          # 1-5
    tech_stack_appropriateness: int # 1-5
    implementation_step_quality: int # 1-5
    overall_quality: int            # 1-5

class FeedbackEntry(BaseModel):
    feedback_id: str
    timestamp: str
    model_input: dict
    model_output: str
    model_provider: str
    ratings: FeedbackRatings
    free_text_comments: str
    reviewer_id: Optional[str] = None
    prompt_version: str

class PatternReport(BaseModel):
    report_id: str
    timestamp: str
    total_feedback_analyzed: int
    avg_ratings: dict
    low_scoring_dimensions: List[str]
    recurring_themes: List[str]
    actionable_insights: List[str]
    raw_summary: str

class PromptEvolution(BaseModel):
    evolution_id: str
    timestamp: str
    parent_prompt_version: str
    new_prompt_version: str
    pattern_report_id: str
    original_prompt: str
    evolved_prompt: str
    change_summary: str
```

### 4.2 `feedback/storage.py`

JSONL file I/O following the project's existing data patterns.

**Key Functions:**

| Function | Description |
|----------|-------------|
| `save_feedback(entry)` | Append a FeedbackEntry to `expert_feedback.jsonl` |
| `load_all_feedback(prompt_version=None)` | Load all feedback, optionally filtered |
| `save_pattern_report(report)` | Append PatternReport to `pattern_reports.jsonl` |
| `load_pattern_reports()` | Load all pattern reports |
| `save_prompt_evolution(evolution)` | Append PromptEvolution record |
| `load_prompt_evolutions()` | Load all evolution records |
| `get_current_prompt_version()` | Return latest version string (default: `"v2_base"`) |
| `get_current_system_prompt()` | Return the active system prompt text |
| `log_model_output(input, output, provider, version)` | Log an output for later review |
| `load_unreviewed_outputs()` | Load outputs without feedback |

### 4.3 `feedback/analysis.py`

Two-phase pattern detection combining deterministic statistics with LLM-powered qualitative analysis.

**Phase A: Statistical Analysis**

```python
def compute_rating_statistics(feedback_entries: List[FeedbackEntry]) -> dict:
    """
    For each of the 5 rating dimensions, compute:
    - mean, median, standard deviation, count
    - Classification: WEAK (mean < 3.0), NEUTRAL (3.0-4.0), STRONG (>= 4.0)

    Returns:
    {
        "skill_gap_accuracy": {"mean": 3.8, "median": 4, "std": 0.6, "class": "NEUTRAL"},
        "tech_stack_appropriateness": {"mean": 2.4, "median": 2, "std": 0.9, "class": "WEAK"},
        ...
        "weak_dimensions": ["tech_stack_appropriateness", "implementation_step_quality"],
        "strong_dimensions": ["skill_gap_accuracy"]
    }
    """
```

**Phase B: LLM-Powered Theme Extraction**

```python
def extract_text_themes(feedback_entries: List[FeedbackEntry], provider: str) -> dict:
    """
    Concatenate all free_text_comments into a numbered list.
    Prepend statistical summary as context.
    Send to LLM with meta-prompt:

    "You are a research analyst reviewing {N} expert evaluations...
     RATING STATISTICS: {formatted_stats}
     EXPERT COMMENTS: {numbered_comments}

     Identify:
     1. Top 5 RECURRING CRITICISMS
     2. Top 3 STRENGTHS
     3. 5 SPECIFIC, ACTIONABLE prompt modifications

     Output as JSON: {criticisms: [...], praises: [...], recommendations: [...]}"

    Returns parsed JSON with themes.
    """
```

**Master Function:**

```python
def generate_pattern_report(feedback_entries, provider) -> PatternReport:
    """
    1. compute_rating_statistics()
    2. extract_text_themes()
    3. Merge into PatternReport
    4. Save and return
    """
```

### 4.4 `feedback/prompt_evolver.py`

Meta-prompting to evolve the system prompt based on feedback patterns.

```python
def evolve_prompt(current_prompt: str, pattern_report: PatternReport, provider: str) -> PromptEvolution:
    """
    Sends a meta-prompt to the LLM:

    "You are an expert Prompt Engineer.

    CURRENT SYSTEM PROMPT:
    {current_prompt}

    EXPERT FEEDBACK ANALYSIS:
    - Weak areas: {low_scoring_dimensions}
    - Recurring criticisms: {recurring_themes}
    - Specific recommendations: {actionable_insights}
    - Strengths to preserve: {strong_dimensions}

    RULES:
    1. PRESERVE the exact JSON output schema
    2. ADD specific, measurable instructions addressing each criticism
    3. PRESERVE instructions corresponding to strong dimensions
    4. Add domain-specific guidance where feedback indicates gaps
    5. Keep prompt under 800 words

    OUTPUT: The complete revised instruction prompt only."

    Returns PromptEvolution with old prompt, new prompt, and change summary.
    """

def preview_evolution(current_prompt, pattern_report) -> str:
    """Human-readable diff preview using difflib."""
```

### 4.5 `feedback/pipeline.py`

Orchestration of the full evolution cycle.

```python
def run_analysis_phase(prompt_version=None, provider="ollama") -> PatternReport:
    """Phase 2: Load feedback -> Analyze -> Generate PatternReport."""

def run_evolution_phase(pattern_report_id, provider="ollama") -> PromptEvolution:
    """Phase 3: Load report -> Evolve prompt -> Save evolution."""

def run_regeneration_phase(evolution_id, provider="ollama", target_count=200) -> str:
    """Phase 4: Load evolved prompt -> Call augment_dataset() -> New JSONL.
    `provider` selects the teacher LLM ("ollama" or "gemini") used during data
    generation. Returns path to new dataset file."""

def get_evolution_status() -> dict:
    """Return current state: feedback count, prompt version, evolution history."""
```

---

## 5. Existing File Modifications

### 5.1 `datasets/augment_dataset.py`

**Change:** Parameterize `augment_dataset()` to accept optional custom prompt and output file.

```python
# BEFORE (line 232):
def augment_dataset():

# AFTER:
def augment_dataset(custom_system_prompt: str = None, custom_output_file: str = None):
    # ... existing setup code ...

    # Replace hardcoded prompt selection:
    if custom_system_prompt:
        current_system_prompt = custom_system_prompt
    else:
        current_system_prompt = SYSTEM_PROMPT_TEXT if GENERATION_MODE == "v1" else SYSTEM_PROMPT_JSON

    # Replace hardcoded output file:
    if custom_output_file:
        output_file = custom_output_file
    else:
        output_file = OUTPUT_FILE

    # ... rest of function uses output_file instead of OUTPUT_FILE ...
```

This is backward-compatible: calling `augment_dataset()` with no arguments behaves identically to the current code.

### 5.2 `main.py`

**Changes:**

1. **Add output logging wrapper** to capture streaming output:

```python
from feedback.storage import log_model_output, get_current_prompt_version

async def logging_wrapper(generator, input_data, provider):
    """Wraps async generators to log complete output after streaming."""
    full_text = ""
    async for chunk in generator:
        full_text += chunk
        yield chunk
    # Stream complete - log the output
    prompt_version = get_current_prompt_version()
    log_model_output(input_data, full_text, provider, prompt_version)
```

2. **Wrap generators** in the `/generate-project` endpoint.

3. **Add API endpoints:**

```python
@app.post("/submit-feedback")
async def submit_feedback(entry: FeedbackEntry):
    save_feedback(entry)
    return {"status": "ok", "feedback_id": entry.feedback_id}

@app.get("/unreviewed-outputs")
async def get_unreviewed():
    return load_unreviewed_outputs()
```

### 5.3 `ui.py`

**Change:** Minimal - add feedback portal link after results display (around line 244):

```python
if parsed_data:
    st.divider()
    st.caption("Expert? [Open Feedback Portal](http://localhost:8502) to review this output.")
```

### 5.4 `run.py`

**Optional change:** Add feedback UI as third subprocess on port 8502.

---

## 6. UI Design

### 6.1 Expert Feedback Portal (`feedback_ui.py`)

```
┌──────────────────────────────────────────────────────────────────┐
│  Expert Feedback Portal                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Select Output to Review ▼]  (dropdown of unreviewed outputs)   │
│                                                                  │
│  ── Original Input ──────────────────────────────────────────    │
│  Student: Jordan | Major: CS | Skills: Python, SQL               │
│  Target: Junior NLP Engineer                                     │
│  Required: Transformers, PyTorch, API deployment                 │
│                                                                  │
│  ── Model Output (Parsed) ───────────────────────────────────    │
│  Gap Analysis:                                                   │
│    Missing Skills: PyTorch, Transformers, FastAPI, Docker         │
│    Match: 35%                                                    │
│    Summary: "The candidate has a solid foundational base..."     │
│  Project: "Enterprise-Grade Semantic Search Service"             │
│    Tech Stack: Python, PyTorch, HuggingFace, FastAPI, Docker     │
│    Steps: 1. Data Engineering... 2. Model Selection...           │
│                                                                  │
│  ── Your Ratings (1-5) ──────────────────────────────────────    │
│  Skill Gap Accuracy:          [====------] 4                     │
│  Project Relevance:           [===-------] 3                     │
│  Tech Stack Appropriateness:  [==--------] 2                     │
│  Implementation Step Quality: [==--------] 2                     │
│  Overall Quality:             [===-------] 3                     │
│                                                                  │
│  ── Comments ────────────────────────────────────────────────    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ The missing skills are accurate but the tech stack...    │    │
│  │ Implementation steps lack detail about model training... │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Reviewer ID (optional): [expert_01     ]                        │
│                                                                  │
│  [Submit Feedback]                                               │
│                                                                  │
│  ── Sidebar ─────────────────                                    │
│  Total Reviews: 23                                               │
│  Avg Overall: 3.2/5                                              │
│  Current Prompt: v2_base                                         │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Evolution Dashboard (`evolution_ui.py`)

```
┌──────────────────────────────────────────────────────────────────┐
│  Self-Evolution Dashboard                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Status: Prompt Version v2_base | Feedback: 47 entries           │
│                                                                  │
│  ══ Phase 1: Pattern Analysis ═══════════════════════════════    │
│  [Run Analysis]                                                  │
│                                                                  │
│  Results (after running):                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ WEAK: implementation_step_quality (2.1), tech_stack (2.4) │  │
│  │ STRONG: skill_gap_accuracy (3.8)                          │  │
│  │ Themes:                                                   │  │
│  │  - Steps lack ML-specific detail                          │  │
│  │  - Tech stacks miss deployment tools                      │  │
│  │ Recommendations:                                          │  │
│  │  - Add deployment/DevOps tool requirement                 │  │
│  │  - Require model versioning for ML projects               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ══ Phase 2: Prompt Evolution ═══════════════════════════════    │
│  [Preview Evolution]  [Apply Evolution]                          │
│                                                                  │
│  Preview (diff):                                                 │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ - "Step 1: Detailed Architectural Setup (3-4 sentences)"  │  │
│  │ + "Step 1: Detailed Architectural Setup (4-5 sentences).  │  │
│  │ +  For ML/AI projects, include GPU setup, data pipeline,  │  │
│  │ +  and model versioning strategy."                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ══ Phase 3: Dataset Regeneration ═══════════════════════════    │
│  Target Count: [200]  Provider: [ollama ▼]                       │
│  [Start Regeneration]                                            │
│  Progress: [████████████░░░░░░░░] 120/200                        │
│                                                                  │
│  ══ Phase 4: Re-Fine-Tuning ═════════════════════════════════    │
│  New Dataset: datasets/student_advisor_dataset_v2_evolved_1.jsonl│
│  [Upload to HuggingFace]                                         │
│  Instructions:                                                   │
│    1. Open Colab notebook gemma_3_4b_student_advisor_v2.ipynb    │
│    2. Change dataset ID to the new HuggingFace dataset           │
│    3. Run all cells                                              │
│    4. Download GGUF and register with Ollama                     │
│                                                                  │
│  ══ Evolution History ═══════════════════════════════════════    │
│  v2_base -> v2_evolved_1 (2026-02-10)                            │
│    Changes: Added deployment tool requirement...                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 7. Pattern Analysis Algorithm

### Step-by-Step Process

```
1. LOAD all FeedbackEntry records for current prompt_version

2. STATISTICAL ANALYSIS (deterministic):
   For each of 5 rating dimensions:
     a. Compute mean, median, standard deviation
     b. Classify: WEAK (mean < 3.0), NEUTRAL (3.0-4.0), STRONG (>= 4.0)
   Sort dimensions by mean (ascending)
   Identify weak_dimensions = all with mean < 3.0

3. QUALITATIVE ANALYSIS (LLM-powered):
   a. Concatenate all free_text_comments into numbered list
   b. Prepend statistical summary as context
   c. Send to LLM with meta-prompt requesting:
      - Top 5 recurring criticisms
      - Top 3 strengths
      - 5 specific, actionable prompt modifications
   d. Parse LLM response as JSON

4. MERGE into PatternReport:
   - low_scoring_dimensions from step 2
   - recurring_themes = criticisms from step 3
   - actionable_insights = recommendations from step 3
   - raw_summary = full LLM response

5. SAVE report and return
```

### Meta-Prompt for Theme Extraction

```
You are a research analyst reviewing {N} expert evaluations of an AI career
coaching system. The system analyzes student profiles against target jobs and
recommends capstone projects.

RATING STATISTICS:
- skill_gap_accuracy: mean={x}/5 ({CLASS})
- project_relevance: mean={x}/5 ({CLASS})
- tech_stack_appropriateness: mean={x}/5 ({CLASS})
- implementation_step_quality: mean={x}/5 ({CLASS})
- overall_quality: mean={x}/5 ({CLASS})

EXPERT COMMENTS:
1. "{comment_1}"
2. "{comment_2}"
...
N. "{comment_N}"

Analyze these reviews and identify:
1. Top 5 RECURRING CRITICISMS (patterns mentioned across multiple comments)
2. Top 3 STRENGTHS (things consistently praised)
3. 5 SPECIFIC, ACTIONABLE changes to make to the system's instruction prompt.
   Each change must be a concrete wording modification, not a vague suggestion.

Output as JSON:
{"criticisms": [...], "praises": [...], "recommendations": [...]}
```

---

## 8. Prompt Evolution Strategy

### Meta-Prompt for Prompt Engineering

```
You are an expert Prompt Engineer specializing in LLM instruction design.

CURRENT SYSTEM PROMPT:
"""
{current_system_prompt}
"""

EXPERT FEEDBACK ANALYSIS:
- Dimensions scoring BELOW 3.0/5.0: {low_scoring_dimensions}
- Recurring criticisms from {N} expert reviewers:
  1. {criticism_1}
  2. {criticism_2}
  ...
- Specific recommended changes:
  1. {recommendation_1}
  2. {recommendation_2}
  ...
- Dimensions scoring ABOVE 4.0/5.0 (PRESERVE these strengths):
  {strong_dimensions}

RULES FOR REVISION:
1. PRESERVE the exact JSON output schema (gap_analysis, project_recommendation).
   Do NOT change field names or structure.
2. ADD specific, measurable instructions that address each criticism.
   Example: Instead of "be detailed", write "each implementation step must be
   4-5 sentences and mention specific tool versions and configuration decisions."
3. PRESERVE existing instructions that correspond to the strong dimensions.
4. Add domain-specific guidance where feedback indicates gaps (e.g., "For ML/AI
   roles, always include model versioning, experiment tracking, and GPU setup").
5. Keep the prompt under 800 words to avoid context window issues.

OUTPUT: The complete revised instruction prompt. Nothing else.
```

### Evolution Example

**Before (current SYSTEM_PROMPT_JSON):**
```
"implementation_steps": [
    "Step 1: Detailed Architectural Setup. Explain the environment setup,
     database choices, and initial project scaffolding in detail (3-4 sentences).",
    ...
]
```

**After (evolved prompt, addressing "steps lack ML detail" criticism):**
```
"implementation_steps": [
    "Step 1: Detailed Architectural Setup. Explain the environment setup,
     database choices, and initial project scaffolding in detail (4-5 sentences).
     For ML/AI projects, explicitly mention GPU setup, data pipeline architecture,
     model versioning strategy, and experiment tracking tools.",
    ...
]
```

### Version Naming Convention

- `v2_base` - Original system prompt
- `v2_evolved_1` - First evolution
- `v2_evolved_2` - Second evolution (from v2_evolved_1)
- Pattern: `v2_evolved_{N}` where N increments with each evolution cycle

---

## 9. Implementation Sequence

The implementation follows a dependency-ordered sequence that maintains a working system at every step.

| Step | Action | Dependencies |
|------|--------|-------------|
| 1 | Create `feedback/schemas.py` | None (pure data models) |
| 2 | Create `feedback/__init__.py` | None |
| 3 | Create `feedback/storage.py` | schemas.py |
| 4 | Create `feedback/analysis.py` | schemas.py, storage.py, ollama/genai |
| 5 | Create `feedback/prompt_evolver.py` | schemas.py, storage.py, analysis.py |
| 6 | Modify `datasets/augment_dataset.py` | None (backward-compatible change) |
| 7 | Create `feedback/pipeline.py` | All feedback modules + augment_dataset |
| 8 | Modify `main.py` | storage.py (output logging + API endpoints) |
| 9 | Create `feedback_ui.py` | storage.py, parsers.py |
| 10 | Create `evolution_ui.py` | pipeline.py |
| 11 | Modify `ui.py` | None (add link only) |
| 12 | Modify `run.py` | None (add subprocess) |

---

## 10. Testing Strategy

### Unit Tests

- **schemas.py**: Validate Pydantic models accept/reject correct/incorrect data
- **storage.py**: Write and read back entries, verify JSONL format integrity
- **analysis.py**: Test statistical computation with known data (mock LLM for theme extraction)
- **prompt_evolver.py**: Test with mock LLM responses, verify prompt structure preserved

### Integration Tests

- **Full pipeline**: Seed 5 feedback entries -> run analysis -> evolve prompt -> verify evolved prompt retains JSON schema
- **API endpoints**: Test `/submit-feedback` and `/unreviewed-outputs` via httpx
- **UI smoke test**: Run feedback_ui.py and evolution_ui.py, verify pages load

### End-to-End Verification

1. Generate model outputs using the existing pipeline
2. Submit 10+ expert feedback entries via feedback_ui.py
3. Trigger analysis in evolution_ui.py, verify statistical report
4. Preview and apply prompt evolution
5. Regenerate 10 test samples with evolved prompt (TEST_MODE)
6. Compare evolved output quality against base output for the same inputs

---

## 11. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Evolved prompt degrades output quality | Preview before applying; keep version history; can revert to any previous version |
| Insufficient feedback for meaningful patterns | Minimum 10 feedback entries recommended; UI shows warning below threshold |
| LLM produces invalid evolved prompt | Validate evolved prompt preserves JSON schema keywords; reject if validation fails |
| Pattern extraction misidentifies themes | Researcher reviews PatternReport before proceeding to evolution |
| Prompt drift after multiple evolution cycles | Track all versions; compare against original baseline periodically |

---

## 12. Future Extensions

- **Automated A/B Testing**: Serve both base and evolved models, compare real-time expert ratings
- **Domain-Specific Evolution**: Segment feedback by job role domain (ML, Finance, Medical) and evolve domain-specific prompt branches
- **Confidence-Based Triggering**: Replace manual trigger with statistical confidence thresholds
- **DPO Integration**: Use paired (preferred, rejected) feedback entries for Direct Preference Optimization
- **Multi-Model Evolution**: Evolve different prompts for different teacher models (Gemini vs Qwen)
