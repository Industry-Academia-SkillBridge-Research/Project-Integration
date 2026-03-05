import difflib

from .schemas import PatternReport, PromptEvolution
from .storage import (
    get_current_prompt_version,
    get_current_system_prompt,
    get_next_version_string,
    save_prompt_evolution,
)
from .analysis import _call_llm


def _build_evolution_prompt(
    current_prompt: str,
    pattern_report: PatternReport,
) -> str:
    """Construct the meta-prompt for the LLM to act as a prompt engineer."""
    weak_list = "\n".join(
        f"  - {d.replace('_', ' ').title()}"
        for d in pattern_report.low_scoring_dimensions
    ) or "  (none identified)"

    strong_list = "\n".join(
        f"  - {d.replace('_', ' ').title()}"
        for d in pattern_report.strong_dimensions
    ) or "  (none identified)"

    criticisms = "\n".join(
        f"  {i+1}. {t}"
        for i, t in enumerate(pattern_report.recurring_themes)
    ) or "  (none)"

    recommendations = "\n".join(
        f"  {i+1}. {r}"
        for i, r in enumerate(pattern_report.actionable_insights)
    ) or "  (none)"

    return f"""You are an expert Prompt Engineer specializing in LLM instruction design.

CURRENT SYSTEM PROMPT:
\"\"\"
{current_prompt}
\"\"\"

EXPERT FEEDBACK ANALYSIS (from {pattern_report.total_feedback_analyzed} expert reviews):
- Dimensions scoring BELOW 3.0/5.0 (WEAK):
{weak_list}
- Recurring criticisms:
{criticisms}
- Specific recommended changes:
{recommendations}
- Dimensions scoring ABOVE 4.0/5.0 (PRESERVE these strengths):
{strong_list}

RULES FOR REVISION:
1. PRESERVE the exact JSON output schema (gap_analysis, project_recommendation). Do NOT change the field names or structure.
2. ADD specific, measurable instructions that address each criticism. Example: Instead of "be detailed", write "each implementation step must be 4-5 sentences and mention specific tool versions and configuration decisions."
3. PRESERVE existing instructions that correspond to the strong dimensions.
4. Add domain-specific guidance where feedback indicates gaps (e.g., "For ML/AI roles, always include model versioning, experiment tracking, and GPU setup in the implementation steps").
5. Keep the prompt under 800 words to avoid context window issues during generation.

OUTPUT: The complete revised instruction prompt. Nothing else -- no explanations, no markdown fencing, just the prompt text."""


def evolve_prompt(
    current_prompt: str,
    pattern_report: PatternReport,
    provider: str = "ollama",
) -> PromptEvolution:
    """
    Use an LLM to synthesize feedback patterns into a modified system prompt.

    Returns a PromptEvolution record with both old and new prompts.
    """
    meta_prompt = _build_evolution_prompt(current_prompt, pattern_report)
    evolved_prompt = _call_llm(meta_prompt, provider)

    # Clean up: strip markdown fencing if present
    evolved_prompt = evolved_prompt.strip()
    if evolved_prompt.startswith("```"):
        lines = evolved_prompt.split("\n")
        # Remove first and last lines if they are fencing
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        evolved_prompt = "\n".join(lines).strip()

    # Generate change summary
    change_summary = _generate_diff_summary(current_prompt, evolved_prompt)

    parent_version = get_current_prompt_version()
    new_version = get_next_version_string()

    evolution = PromptEvolution(
        parent_prompt_version=parent_version,
        new_prompt_version=new_version,
        pattern_report_id=pattern_report.report_id,
        original_prompt=current_prompt,
        evolved_prompt=evolved_prompt,
        change_summary=change_summary,
    )

    save_prompt_evolution(evolution)
    return evolution


def preview_evolution(
    current_prompt: str,
    pattern_report: PatternReport,
    provider: str = "ollama",
) -> str:
    """
    Preview the evolved prompt without committing.
    Returns a human-readable unified diff.
    """
    meta_prompt = _build_evolution_prompt(current_prompt, pattern_report)
    evolved_prompt = _call_llm(meta_prompt, provider)

    # Clean up markdown fencing
    evolved_prompt = evolved_prompt.strip()
    if evolved_prompt.startswith("```"):
        lines = evolved_prompt.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        evolved_prompt = "\n".join(lines).strip()

    diff = difflib.unified_diff(
        current_prompt.splitlines(keepends=True),
        evolved_prompt.splitlines(keepends=True),
        fromfile="current_prompt",
        tofile="evolved_prompt",
        lineterm="",
    )
    return "\n".join(diff)


def _generate_diff_summary(original: str, evolved: str) -> str:
    """Generate a brief human-readable summary of changes."""
    orig_lines = set(original.strip().splitlines())
    evol_lines = set(evolved.strip().splitlines())

    added = evol_lines - orig_lines
    removed = orig_lines - evol_lines

    parts = []
    if added:
        parts.append(f"Added {len(added)} new line(s)")
    if removed:
        parts.append(f"Removed {len(removed)} line(s)")
    if not parts:
        parts.append("No textual changes detected")

    return ". ".join(parts) + "."
