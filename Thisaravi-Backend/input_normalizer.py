"""
Normalize runtime input to match the finetuned model's training data format.

Training data characteristics (student_advisor_dataset_v1.jsonl, 200 entries):
  - demographics: brief role descriptor, NO names. E.g. "Undergraduate, CS Major"
  - major: short abbrev. E.g. "CS", "Bootcamp"
  - interests: 1-2 items max
  - current_skills: list of skill strings
  - personality: comma-separated adjectives
  - target_job_role: role title
  - required_skills: 2-4 items (usually 3)
  - description: short formulaic "Targeting a role as X" (20-62 chars)
"""

import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Generic Ollama model for lightweight normalization calls
_NORMALIZER_MODEL = "gemma3:1b"

# Max items per field to match training distribution
_MAX_REQUIRED_SKILLS = 3
_MAX_INTERESTS = 2


def normalize_demographics(current_role: str, major: Optional[str]) -> str:
    """
    Build a brief academic/professional descriptor WITHOUT the person's name.

    Training examples:
      "Undergraduate, CS Major" | "Senior Dev" | "PhD, Biology"
      "Bootcamp Grad, Generalist" | "Economics Grad" | "IT"

    Strategy:
      1. If current_role is already short (≤5 words) and doesn't look like
         it contains a full name, use it directly (optionally paired with major).
      2. Otherwise, call a small Ollama model to rephrase into the training style.
    """
    role = (current_role or "").strip()
    mjr = (major or "").strip()

    # Quick heuristic: already looks training-style if short and no commas aside from descriptor
    words = role.split()
    looks_short = len(words) <= 5

    if looks_short and role:
        # Combine with major if both present and major not already embedded in role
        if mjr and mjr.lower() not in role.lower():
            return f"{role}, {mjr}"
        return role

    # Longer / complex role — use Ollama to condense
    try:
        import thisaravi

        raw = f"{role}, {mjr}" if mjr else role
        resp = thisaravi.chat(
            model=_NORMALIZER_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    "Rewrite this person's background as a brief 2-5 word "
                    "academic/professional descriptor. Do NOT include any "
                    "person's name. Output ONLY the descriptor, nothing else.\n"
                    "Examples: 'Undergraduate, CS Major', 'Senior Dev', "
                    "'PhD, Biology', 'Bootcamp Grad, Generalist'\n\n"
                    f"Input: {raw}"
                ),
            }],
            stream=False,
            options={"temperature": 0.1},
        )
        result = resp["message"]["content"].strip().strip('"').strip("'")
        # Sanity: if result is too long or empty, fall back
        if result and len(result.split()) <= 6:
            return result
        logger.warning("Ollama normalizer returned unexpected length: %s", result)
    except Exception as e:
        logger.warning("Demographics normalization via Ollama failed: %s", e)

    # Fallback: just truncate
    if mjr and mjr.lower() not in role.lower():
        return f"{role}, {mjr}"
    return role


def normalize_required_skills(
    job_skills: List[str],
    recommendation_results: dict,
) -> List[str]:
    """
    Produce exactly _MAX_REQUIRED_SKILLS items, prioritizing deficit skills
    from the recommendation engine.

    Priority order:
      1. Top deficit skills (sorted by deficit * importance)
      2. Remaining slots filled from job_skills
    """
    # Extract deficit skills from recommendation results
    deficit_skills: List[str] = []
    gap_data = recommendation_results.get("skill_gap", {})
    deficits = gap_data.get("deficits", [])
    if deficits:
        # Sort by deficit * importance (higher = more critical gap)
        scored = []
        for d in deficits:
            deficit_val = abs(d.get("deficit", 0))
            importance = d.get("importance", 0)
            scored.append((d.get("skill_name", ""), deficit_val * importance))
        scored.sort(key=lambda x: x[1], reverse=True)
        deficit_skills = [name for name, _ in scored if name]

    # Build final list: deficits first, then job skills for remaining slots
    seen = set()
    result: List[str] = []

    for skill in deficit_skills:
        if len(result) >= _MAX_REQUIRED_SKILLS:
            break
        key = skill.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(skill)

    for skill in job_skills:
        if len(result) >= _MAX_REQUIRED_SKILLS:
            break
        key = skill.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(skill)

    # If we still have fewer than target, pad with generic placeholders
    # (shouldn't happen with Neo4j roles that have 30 skills)
    return result[:_MAX_REQUIRED_SKILLS]


def normalize_description(target_role: str) -> str:
    """
    Always produce the formulaic description matching 100% of training data.
    Ignores any long job descriptions from scraped data.
    """
    return f"Targeting a role as {target_role}"


def normalize_interests(interests: Optional[List[str]]) -> List[str]:
    """Cap interests to match training distribution (1-2 items)."""
    if not interests:
        return []
    return interests[:_MAX_INTERESTS]


def build_finetuned_input(
    student_data,
    job_data,
    target_role: str,
    recommendation_results: dict,
) -> str:
    """
    Build the exact JSON string that the finetuned model expects as user input.

    Returns a JSON string matching the training format:
    {
      "student_data": {
        "demographics": "...",
        "major": "...",
        "interests": [...],
        "current_skills": [...],
        "personality": "..."
      },
      "job_data": {
        "target_job_role": "...",
        "required_skills": [...],  // exactly 3, deficit-prioritized
        "description": "Targeting a role as ..."
      }
    }
    """
    demographics = normalize_demographics(
        student_data.current_role,
        student_data.major,
    )
    interests = normalize_interests(student_data.interests or [])
    required_skills = normalize_required_skills(
        job_data.required_skills,
        recommendation_results,
    )
    description = normalize_description(target_role)

    input_json = {
        "student_data": {
            "demographics": demographics,
            "major": student_data.major or "Undeclared",
            "interests": interests,
            "current_skills": student_data.skills,
            "personality": student_data.personality or "ambitious, learner",
        },
        "job_data": {
            "target_job_role": target_role,
            "required_skills": required_skills,
            "description": description,
        },
    }

    # Keep compact JSON so model input string matches training-style payloads.
    return json.dumps(input_json, separators=(",", ":"), ensure_ascii=False)


def build_finetuned_chat_payload(
    student_data,
    job_data,
    target_role: str,
    recommendation_results: dict,
) -> dict:
    """
    Build the exact chat payload shape used by the finetuned model training.

    Returned structure:
    {
      "messages": [
        {
          "role": "user",
          "content": "{...normalized-json-string...}"
        }
      ]
    }
    """
    return {
        "messages": [
            {
                "role": "user",
                "content": build_finetuned_input(
                    student_data,
                    job_data,
                    target_role,
                    recommendation_results,
                ),
            }
        ]
    }
