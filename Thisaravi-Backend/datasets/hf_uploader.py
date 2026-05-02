"""
hf_uploader.py
──────────────
Auto-uploads generated JSONL datasets to a HuggingFace Hub dataset repository
after each training/generation run.

Environment variables (loaded from .env):
  HF_TOKEN          – HuggingFace write token (required)
  HF_DATASET_REPO   – Target repo in "owner/dataset-name" format
                      (default: auto-derived from HF whoami + "student-advisor-dataset")
"""

import os
import logging
import json
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_UPLOAD_STATUS_SUFFIX = ".hf_upload_status.json"

# ── Resolve .env path ──────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
_BACKEND_DIR = _SCRIPT_DIR.parent

# Try local datasets/.env first, then backend root .env
for _env_path in [_SCRIPT_DIR / ".env", _BACKEND_DIR / ".env"]:
    if _env_path.exists():
        load_dotenv(_env_path, override=False)
        break


def _get_hf_token() -> str | None:
    """Load HF_TOKEN from environment (already populated via load_dotenv above)."""
    return os.getenv("HF_TOKEN")


def _resolve_repo_id(token: str) -> str:
    """
    Return the target HuggingFace dataset repo id.
    Prefers HF_DATASET_REPO env var; falls back to "<username>/student-advisor-dataset".
    """
    repo_env = os.getenv("HF_DATASET_REPO", "").strip()
    if repo_env:
        return repo_env

    # Auto-derive from HF whoami
    try:
        from huggingface_hub import whoami
        username = whoami(token=token)["name"]
        return f"{username}/student-advisor-dataset"
    except Exception:
        return "student-advisor-dataset"


def _upload_status_path(file_path: Path) -> Path:
    return file_path.with_name(f"{file_path.name}{_UPLOAD_STATUS_SUFFIX}")


def write_upload_failure(file_path: str, reason: str) -> None:
    path = Path(file_path).resolve()
    status_path = _upload_status_path(path)
    payload = {
        "status": "failed",
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_upload_failure(file_path: str) -> None:
    status_path = _upload_status_path(Path(file_path).resolve())
    if status_path.exists():
        status_path.unlink()


def read_upload_status(file_path: str) -> dict | None:
    status_path = _upload_status_path(Path(file_path).resolve())
    if not status_path.exists():
        return None

    try:
        return json.loads(status_path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "failed", "reason": "Unparseable upload status file"}


def upload_dataset(
    file_path: str,
    commit_message: str | None = None,
    repo_id: str | None = None,
) -> bool:
    """
    Upload *file_path* (a .jsonl dataset file) to HuggingFace Hub.

    Returns True on success, False on failure (logs error, never raises).

    Args:
        file_path:       Absolute or relative path to the JSONL file to upload.
        commit_message:  Custom commit message; auto-generated when omitted.
        repo_id:         Target "owner/repo" on HuggingFace Hub.
                         Falls back to HF_DATASET_REPO env var or auto-derived name.
    """
    token = _get_hf_token()
    if not token:
        logger.warning(
            "[HF Upload] HF_TOKEN not found in environment. "
            "Set HF_TOKEN in your .env file to enable automatic dataset uploads."
        )
        write_upload_failure(file_path, "HF_TOKEN not found in environment")
        return False

    file_path = Path(file_path).resolve()
    if not file_path.exists():
        logger.warning(f"[HF Upload] Dataset file not found: {file_path}")
        write_upload_failure(str(file_path), "Dataset file not found")
        return False

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        target_repo = repo_id or _resolve_repo_id(token)

        # Create repo if it doesn't exist yet
        api.create_repo(
            repo_id=target_repo,
            repo_type="dataset",
            exist_ok=True,
            private=False,
        )

        path_in_repo = file_path.name  # store at repo root with same filename
        message = commit_message or f"Auto-upload after generation: {file_path.name}"

        api.upload_file(
            path_or_fileobj=str(file_path),
            path_in_repo=path_in_repo,
            repo_id=target_repo,
            repo_type="dataset",
            commit_message=message,
        )

        logger.info(
            f"[HF Upload] ✓ Uploaded '{file_path.name}' → "
            f"https://huggingface.co/datasets/{target_repo}"
        )
        print(
            f"[HF Upload] ✓ Uploaded '{file_path.name}' → "
            f"https://huggingface.co/datasets/{target_repo}"
        )
        clear_upload_failure(str(file_path))
        return True

    except Exception as exc:
        logger.error(f"[HF Upload] Upload failed: {exc}")
        print(f"[HF Upload] Upload failed: {exc}")
        write_upload_failure(str(file_path), str(exc))
        return False
