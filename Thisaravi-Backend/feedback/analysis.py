import json
import os
import statistics
from typing import List

import ollama
import google.genai as genai
from dotenv import load_dotenv

from .schemas import FeedbackEntry, PatternReport
from .storage import save_pattern_report

load_dotenv()
# Also try parent .env
_parent_env = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
load_dotenv(_parent_env)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

RATING_DIMENSIONS = [
    "skill_gap_accuracy",
    "project_relevance",
    "tech_stack_appropriateness",
    "implementation_step_quality",
    "overall_quality",
]


def compute_rating_statistics(feedback_entries: List[FeedbackEntry]) -> dict:
    """
    Compute per-dimension statistics from structured ratings.

    Returns dict with per-dimension stats and classified weak/strong lists.
    """
    stats = {}
    for dim in RATING_DIMENSIONS:
        values = [getattr(e.ratings, dim) for e in feedback_entries]
        if not values:
            continue
        mean = statistics.mean(values)
        med = statistics.median(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0

        if mean < 3.0:
            classification = "WEAK"
        elif mean >= 4.0:
            classification = "STRONG"
        else:
            classification = "NEUTRAL"

        stats[dim] = {
            "mean": round(mean, 2),
            "median": med,
            "std": round(std, 2),
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "class": classification,
        }

    weak = [d for d, s in stats.items() if s["class"] == "WEAK"]
    strong = [d for d, s in stats.items() if s["class"] == "STRONG"]

    return {
        "dimensions": stats,
        "weak_dimensions": weak,
        "strong_dimensions": strong,
    }


def _format_stats_for_prompt(stat_result: dict) -> str:
    """Format statistical results as readable text for the LLM prompt."""
    lines = []
    for dim, s in stat_result["dimensions"].items():
        label = dim.replace("_", " ").title()
        lines.append(f"- {label}: mean={s['mean']}/5 ({s['class']})")
    return "\n".join(lines)


def extract_text_themes(
    feedback_entries: List[FeedbackEntry],
    stat_result: dict,
    provider: str = "ollama",
) -> dict:
    """
    Use an LLM to analyze all free-text comments and extract recurring themes.

    Returns dict with criticisms, praises, and recommendations.
    """
    comments = [
        f"{i+1}. \"{e.free_text_comments}\""
        for i, e in enumerate(feedback_entries)
        if e.free_text_comments.strip()
    ]
    if not comments:
        return {
            "criticisms": ["No free-text comments to analyze"],
            "praises": [],
            "recommendations": [],
        }

    formatted_stats = _format_stats_for_prompt(stat_result)
    comments_text = "\n".join(comments)

    prompt = f"""You are a research analyst reviewing {len(comments)} expert evaluations of an AI career coaching system. The system analyzes student profiles against target jobs and recommends capstone projects.

RATING STATISTICS:
{formatted_stats}

EXPERT COMMENTS:
{comments_text}

Analyze these reviews and identify:
1. Top 5 RECURRING CRITICISMS (patterns mentioned across multiple comments)
2. Top 3 STRENGTHS (things consistently praised)
3. 5 SPECIFIC, ACTIONABLE changes to make to the system's instruction prompt. Each change must be a concrete wording modification, not a vague suggestion.

Output ONLY valid JSON with this structure:
{{"criticisms": ["..."], "praises": ["..."], "recommendations": ["..."]}}"""

    response_text = _call_llm(prompt, provider)

    # Parse the LLM response
    try:
        # Try extracting JSON from the response
        import re
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: return the raw text as a single theme
    return {
        "criticisms": [response_text[:500] if response_text else "Analysis failed"],
        "praises": [],
        "recommendations": [],
    }


def _call_llm(prompt: str, provider: str) -> str:
    """Call the LLM (Gemini or Ollama) with a prompt."""
    if provider == "gemini":
        return _call_gemini(prompt)
    return _call_ollama(prompt)


def _call_gemini(prompt: str) -> str:
    """Call Gemini API."""
    try:
        if not gemini_client:
            return "Gemini API error: API key not configured"
        response = gemini_client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Gemini API error: {e}"


def _call_ollama(prompt: str, model_name: str = None) -> str:
    """Call Ollama with a local model."""
    if model_name is None:
        model_name = os.getenv("OLLAMA_MODEL_GENERIC", "gemma3:1b")
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={"num_ctx": 8192},
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Ollama error: {e}"


def generate_pattern_report(
    feedback_entries: List[FeedbackEntry],
    provider: str = "ollama",
) -> PatternReport:
    """
    Master function: combines statistical analysis and text theme extraction
    into a single PatternReport.
    """
    # Phase A: Statistical analysis
    stat_result = compute_rating_statistics(feedback_entries)

    # Phase B: Qualitative theme extraction
    themes = extract_text_themes(feedback_entries, stat_result, provider)

    # Compute average ratings dict
    avg_ratings = {
        dim: s["mean"]
        for dim, s in stat_result["dimensions"].items()
    }

    report = PatternReport(
        total_feedback_analyzed=len(feedback_entries),
        avg_ratings=avg_ratings,
        low_scoring_dimensions=stat_result["weak_dimensions"],
        strong_dimensions=stat_result["strong_dimensions"],
        recurring_themes=themes.get("criticisms", []),
        actionable_insights=themes.get("recommendations", []),
        raw_summary=json.dumps(themes, indent=2),
    )

    save_pattern_report(report)
    return report
