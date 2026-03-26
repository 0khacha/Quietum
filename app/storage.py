"""
storage.py — JSON-based local persistence for Quietum.
Handles reading/writing tasks and settings to disk.
Thread-safe and atomic writes to prevent data corruption.
"""

import json
import os
import tempfile
from app.constants import DATA_DIR, TASKS_FILE, SETTINGS_FILE


def _ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _atomic_write(filepath: str, data: dict):
    """
    Write data to file atomically using a temp file + rename.
    Prevents data corruption if the app crashes mid-write.
    """
    _ensure_data_dir()
    dir_name = os.path.dirname(filepath)

    # Write to a temp file first, then rename (atomic on most OS)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # On Windows, we need to remove the target first
        if os.path.exists(filepath):
            os.replace(tmp_path, filepath)
        else:
            os.rename(tmp_path, filepath)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _read_json(filepath: str, default: dict) -> dict:
    """Read a JSON file, returning a default if it doesn't exist or is corrupt."""
    if not os.path.exists(filepath):
        return default.copy()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default.copy()


# ── Tasks ─────────────────────────────────────────────────────────────────────

DEFAULT_TASKS = {
    "today": [],
    "week": []
}


def load_tasks() -> dict:
    """Load all tasks from disk."""
    data = _read_json(TASKS_FILE, DEFAULT_TASKS)
    # Ensure both sections exist
    if "today" not in data:
        data["today"] = []
    if "week" not in data:
        data["week"] = []
    return data


def save_tasks(tasks: dict):
    """Save all tasks to disk (atomic write)."""
    _atomic_write(TASKS_FILE, tasks)


# ── Settings ──────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "dark_mode": False,
    "always_on_top": False,
    "start_with_windows": False,
    "window_x": None,
    "window_y": None,
}


def load_settings() -> dict:
    """Load app settings from disk."""
    data = _read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    # Merge with defaults for any missing keys
    for key, value in DEFAULT_SETTINGS.items():
        if key not in data:
            data[key] = value
    return data


def save_settings(settings: dict):
    """Save app settings to disk (atomic write)."""
    _atomic_write(SETTINGS_FILE, settings)
