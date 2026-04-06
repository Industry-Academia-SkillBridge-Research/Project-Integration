"""
Local JSONL-backed candidate profile storage.

Mirrors the feedback/ pattern: append-only JSONL files with
helper functions for CRUD operations.

File: profiles/profile_data/candidate_profiles.jsonl
Each line is a full CandidateProfile dict keyed by candidate_id.
On update the whole file is rewritten (profiles are small).
"""
import json
import os
import logging
from typing import List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "profile_data")
PROFILES_FILE = os.path.join(PROFILE_DIR, "candidate_profiles.jsonl")


def _ensure_dir():
    os.makedirs(PROFILE_DIR, exist_ok=True)


def _load_all_lines() -> List[dict]:
    if not os.path.exists(PROFILES_FILE):
        return []
    entries = []
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def _write_all(entries: List[dict]):
    _ensure_dir()
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ── Public API ─────────────────────────────────────────────────────────────

def save_profile(profile: dict) -> dict:
    """
    Create or update a candidate profile.
    Keyed on candidate_id.  Adds/overwrites updated_at timestamp.
    """
    candidate_id = profile.get("candidate_id")
    if not candidate_id:
        raise ValueError("candidate_id is required")

    profile["updated_at"] = datetime.now(timezone.utc).isoformat()

    entries = _load_all_lines()
    replaced = False
    for i, e in enumerate(entries):
        if e.get("candidate_id") == candidate_id:
            entries[i] = profile
            replaced = True
            break

    if not replaced:
        profile.setdefault("created_at", profile["updated_at"])
        entries.append(profile)

    _write_all(entries)
    logger.info(f"Profile saved: {candidate_id} ({'updated' if replaced else 'created'})")
    return profile


def get_profile(candidate_id: str) -> Optional[dict]:
    """Return a single profile by candidate_id, or None."""
    for entry in _load_all_lines():
        if entry.get("candidate_id") == candidate_id:
            return entry
    return None


def list_profiles() -> List[dict]:
    """Return all stored profiles."""
    return _load_all_lines()


def delete_profile(candidate_id: str) -> bool:
    """Delete a profile. Returns True if it existed."""
    entries = _load_all_lines()
    new_entries = [e for e in entries if e.get("candidate_id") != candidate_id]
    if len(new_entries) == len(entries):
        return False
    _write_all(new_entries)
    logger.info(f"Profile deleted: {candidate_id}")
    return True
