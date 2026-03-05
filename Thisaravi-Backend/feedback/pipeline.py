import os
import sys
from typing import Optional

from .schemas import PatternReport, PromptEvolution
from .storage import (
    load_all_feedback,
    load_pattern_reports,
    load_prompt_evolutions,
    get_current_prompt_version,
    get_current_system_prompt,
    get_pattern_report_by_id,
)
from .analysis import generate_pattern_report
from .prompt_evolver import evolve_prompt, preview_evolution


def run_analysis_phase(
    prompt_version: Optional[str] = None,
    provider: str = "ollama",
) -> PatternReport:
    """
    Phase 2: Load feedback -> Analyze -> Generate PatternReport.

    Args:
        prompt_version: Filter feedback to a specific prompt version.
                       If None, uses the current version.
        provider: LLM provider for theme extraction ("ollama" or "gemini").

    Returns:
        PatternReport with statistics, themes, and actionable insights.
    """
    if prompt_version is None:
        prompt_version = get_current_prompt_version()

    feedback = load_all_feedback(prompt_version=prompt_version)
    if not feedback:
        # Try loading all feedback if version-specific returned nothing
        feedback = load_all_feedback()

    if not feedback:
        raise ValueError("No feedback entries found. Collect expert feedback first.")

    return generate_pattern_report(feedback, provider=provider)


def run_evolution_phase(
    pattern_report_id: str,
    provider: str = "ollama",
) -> PromptEvolution:
    """
    Phase 3: Load pattern report -> Evolve prompt -> Save evolution record.

    Args:
        pattern_report_id: ID of the pattern report to base evolution on.
        provider: LLM provider for prompt evolution.

    Returns:
        PromptEvolution record with old and new prompts.
    """
    report = get_pattern_report_by_id(pattern_report_id)
    if report is None:
        raise ValueError(f"Pattern report '{pattern_report_id}' not found.")

    current_prompt = get_current_system_prompt()
    return evolve_prompt(current_prompt, report, provider=provider)


def run_preview_phase(
    pattern_report_id: str,
    provider: str = "ollama",
) -> str:
    """
    Preview what the evolution would produce, without committing.

    Returns:
        Unified diff string of current vs evolved prompt.
    """
    report = get_pattern_report_by_id(pattern_report_id)
    if report is None:
        raise ValueError(f"Pattern report '{pattern_report_id}' not found.")

    current_prompt = get_current_system_prompt()
    return preview_evolution(current_prompt, report, provider=provider)


def run_regeneration_phase(
    evolution_id: str,
    provider: str = "ollama",
    target_count: int = 200,
    generation_mode: str = "v2",
) -> str:
    """
    Phase 4: Load evolved prompt -> Call augment_dataset() -> New JSONL dataset.

    Args:
        evolution_id: ID of the evolution record to use.
        provider: Teacher model provider for data generation.
        target_count: Number of entries to generate.
        generation_mode: Output format - "v1" (detailed text) or "v2" (detailed JSON).
                         Determines both the system prompt style and the output filename.

    Returns:
        Path to the new dataset file.
    """
    evolutions = load_prompt_evolutions()
    evolution = None
    for e in evolutions:
        if e.evolution_id == evolution_id:
            evolution = e
            break

    if evolution is None:
        raise ValueError(f"Evolution record '{evolution_id}' not found.")

    # Determine output file name.
    # When generation_mode is "v1" (text), prefix the filename with "v1_" so it
    # stays separate from the JSON ("v2") evolved datasets.
    datasets_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "datasets",
    )
    # Extract evolution number from version string (e.g., "v2_evolved_3" → "3")
    try:
        evo_num = evolution.new_prompt_version.split("_")[-1]
    except (AttributeError, IndexError):
        evo_num = "1"
    if generation_mode == "v1":
        base_name = f"student_advisor_dataset_v1_evolved_{evo_num}.jsonl"
    else:
        base_name = f"student_advisor_dataset_v2_evolved_{evo_num}.jsonl"

    output_file = os.path.join(datasets_dir, base_name)

    # Add datasets dir to path so augment_dataset can find smart_generator
    if datasets_dir not in sys.path:
        sys.path.insert(0, datasets_dir)

    from datasets.augment_dataset import augment_dataset

    # pass provider through so dataset generation uses the selected LLM
    augment_dataset(
        custom_system_prompt=evolution.evolved_prompt,
        custom_output_file=output_file,
        custom_target_count=target_count,
        provider=provider,
        custom_generation_mode=generation_mode,
    )

    return output_file


def get_evolution_status() -> dict:
    """
    Return current state for the dashboard UI.
    """
    feedback = load_all_feedback()
    reports = load_pattern_reports()
    evolutions = load_prompt_evolutions()

    current_version = get_current_prompt_version()

    # Count feedback per version
    version_counts = {}
    for f in feedback:
        v = f.prompt_version
        version_counts[v] = version_counts.get(v, 0) + 1

    return {
        "current_prompt_version": current_version,
        "total_feedback": len(feedback),
        "feedback_per_version": version_counts,
        "total_reports": len(reports),
        "total_evolutions": len(evolutions),
        "evolution_history": [
            {
                "from": e.parent_prompt_version,
                "to": e.new_prompt_version,
                "timestamp": e.timestamp,
                "summary": e.change_summary,
            }
            for e in evolutions
        ],
    }
