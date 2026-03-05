import json
import os
from typing import List, Optional

from .schemas import (
    FeedbackEntry,
    ModelOutputLog,
    PatternReport,
    PromptEvolution,
)

# --- File Paths ---
FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "feedback_data")
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "expert_feedback.jsonl")
OUTPUT_LOG_FILE = os.path.join(FEEDBACK_DIR, "model_outputs_log.jsonl")
PATTERNS_FILE = os.path.join(FEEDBACK_DIR, "pattern_reports.jsonl")
EVOLUTIONS_FILE = os.path.join(FEEDBACK_DIR, "prompt_evolutions.jsonl")

# Base system prompt (copied from augment_dataset.py for reference)
BASE_SYSTEM_PROMPT = """
You are an expert Technical Career Coach and Solutions Architect.
Your goal is to identify skill gaps and recommend a high-impact capstone project.

Output must be valid JSON with this structure:
{
    "gap_analysis": {
        "missing_skills": ["List", "of", "skills"],
        "match_percentage": <0-100>,
        "analysis_summary": "Detailed gap explanation. Write a full paragraph explaining WHY specific skills are missing relative to the job requirements. Use professional but encouraging tone."
    },
    "project_recommendation": {
        "project_title": "Impressive Project Name",
        "objective": "Primary learning goal.",
        "tech_stack": ["Tech1", "Tech2", "Tech3"],
        "implementation_steps": [
            "Step 1: Detailed Architectual Setup. Explain the environment setup, database choices, and initial project scaffolding in detail (3-4 sentences).",
            "Step 2: Core Feature Implementation. Explain the backend logic, API design, or data processing steps involved (3-4 sentences).",
            "Step 3: Frontend/Visualization. Describe how the user will interact with the system or how data will be presented (3-4 sentences).",
            "Step 4: Deployment & Polish. Explain deployment (Docker/Cloud) and final touches (CI/CD, README) (3-4 sentences)."
        ]
    }
}
"""


def _ensure_dir():
    """Ensure the feedback data directory exists."""
    os.makedirs(FEEDBACK_DIR, exist_ok=True)


def _append_jsonl(filepath: str, data: dict):
    """Append a single JSON object as a line to a JSONL file."""
    _ensure_dir()
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def _load_jsonl(filepath: str) -> List[dict]:
    """Load all entries from a JSONL file."""
    if not os.path.exists(filepath):
        return []
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# --- Feedback ---

def save_feedback(entry: FeedbackEntry) -> None:
    """Append a feedback entry and mark the corresponding output as reviewed."""
    _append_jsonl(FEEDBACK_FILE, entry.model_dump())
    # Mark the output as having feedback
    _mark_output_reviewed(entry.model_input, entry.model_output)


def load_all_feedback(prompt_version: Optional[str] = None) -> List[FeedbackEntry]:
    """Load all feedback entries, optionally filtered by prompt version."""
    raw = _load_jsonl(FEEDBACK_FILE)
    entries = [FeedbackEntry(**r) for r in raw]
    if prompt_version:
        entries = [e for e in entries if e.prompt_version == prompt_version]
    return entries


# --- Model Output Logging ---

def log_model_output(
    input_data: dict,
    output_text: str,
    provider: str,
    prompt_version: str,
) -> str:
    """Log a model output for later expert review. Returns the output_id."""
    entry = ModelOutputLog(
        model_input=input_data,
        model_output=output_text,
        model_provider=provider,
        prompt_version=prompt_version,
    )
    _append_jsonl(OUTPUT_LOG_FILE, entry.model_dump())
    return entry.output_id


def load_unreviewed_outputs() -> List[dict]:
    """Load model outputs that have not yet received feedback."""
    raw = _load_jsonl(OUTPUT_LOG_FILE)
    return [r for r in raw if not r.get("has_feedback", False)]


def load_all_outputs() -> List[dict]:
    """Load all model outputs."""
    return _load_jsonl(OUTPUT_LOG_FILE)


def _mark_output_reviewed(model_input: dict, model_output: str):
    """Mark a logged output as having received feedback (rewrite file)."""
    if not os.path.exists(OUTPUT_LOG_FILE):
        return
    entries = _load_jsonl(OUTPUT_LOG_FILE)
    updated = False
    for entry in entries:
        if (entry.get("model_output") == model_output
                and not entry.get("has_feedback", False)):
            entry["has_feedback"] = True
            updated = True
            break
    if updated:
        _ensure_dir()
        with open(OUTPUT_LOG_FILE, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")


# --- Pattern Reports ---

def save_pattern_report(report: PatternReport) -> None:
    """Append a pattern report."""
    _append_jsonl(PATTERNS_FILE, report.model_dump())


def load_pattern_reports() -> List[PatternReport]:
    """Load all pattern reports."""
    raw = _load_jsonl(PATTERNS_FILE)
    return [PatternReport(**r) for r in raw]


def get_pattern_report_by_id(report_id: str) -> Optional[PatternReport]:
    """Load a specific pattern report by ID."""
    reports = load_pattern_reports()
    for r in reports:
        if r.report_id == report_id:
            return r
    return None


# --- Prompt Evolutions ---

def save_prompt_evolution(evolution: PromptEvolution) -> None:
    """Append a prompt evolution record."""
    _append_jsonl(EVOLUTIONS_FILE, evolution.model_dump())


def load_prompt_evolutions() -> List[PromptEvolution]:
    """Load all evolution records, ordered by timestamp."""
    raw = _load_jsonl(EVOLUTIONS_FILE)
    evolutions = [PromptEvolution(**r) for r in raw]
    evolutions.sort(key=lambda e: e.timestamp)
    return evolutions


def get_current_prompt_version() -> str:
    """Return the latest prompt version string, or 'v2_base' if none."""
    evolutions = load_prompt_evolutions()
    if evolutions:
        return evolutions[-1].new_prompt_version
    return "v2_base"


def get_current_system_prompt() -> str:
    """Return the current active system prompt text (latest evolved, or base)."""
    evolutions = load_prompt_evolutions()
    if evolutions:
        return evolutions[-1].evolved_prompt
    return BASE_SYSTEM_PROMPT


def get_next_version_string() -> str:
    """Generate the next evolution version string."""
    evolutions = load_prompt_evolutions()
    if not evolutions:
        return "v2_evolved_1"
    # Extract the number from the latest version
    latest = evolutions[-1].new_prompt_version
    try:
        num = int(latest.split("_")[-1])
        return f"v2_evolved_{num + 1}"
    except (ValueError, IndexError):
        return f"v2_evolved_{len(evolutions) + 1}"
