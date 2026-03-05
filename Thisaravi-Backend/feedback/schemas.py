from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone


class FeedbackRatings(BaseModel):
    """Structured numeric ratings (1-5 scale) for expert evaluation."""
    skill_gap_accuracy: int = Field(..., ge=1, le=5)
    project_relevance: int = Field(..., ge=1, le=5)
    tech_stack_appropriateness: int = Field(..., ge=1, le=5)
    implementation_step_quality: int = Field(..., ge=1, le=5)
    overall_quality: int = Field(..., ge=1, le=5)


class FeedbackEntry(BaseModel):
    """A single expert feedback record tied to a specific model output."""
    feedback_id: str = Field(default_factory=lambda: f"fb_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_input: dict
    model_output: str
    model_provider: str
    ratings: FeedbackRatings
    free_text_comments: str
    reviewer_id: Optional[str] = None
    prompt_version: str


class ModelOutputLog(BaseModel):
    """A logged model output awaiting expert review."""
    output_id: str = Field(default_factory=lambda: f"out_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_input: dict
    model_output: str
    model_provider: str
    prompt_version: str
    has_feedback: bool = False


class PatternReport(BaseModel):
    """Output of the pattern analysis phase."""
    report_id: str = Field(default_factory=lambda: f"rpt_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_feedback_analyzed: int
    avg_ratings: dict
    low_scoring_dimensions: List[str]
    strong_dimensions: List[str] = []
    recurring_themes: List[str]
    actionable_insights: List[str]
    raw_summary: str


class PromptEvolution(BaseModel):
    """Record of a prompt evolution event."""
    evolution_id: str = Field(default_factory=lambda: f"evo_{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_prompt_version: str
    new_prompt_version: str
    pattern_report_id: str
    original_prompt: str
    evolved_prompt: str
    change_summary: str
