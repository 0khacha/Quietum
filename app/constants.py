"""
constants.py — App-wide constants for Quietum.
"""

import os
import sys

# ── App Info ──────────────────────────────────────────────────────────────────
APP_NAME = "Quietum"
APP_VERSION = "1.1.0"

# ── Paths ─────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")

# ── Full Window ───────────────────────────────────────────────────────────────
WINDOW_WIDTH = 420
WINDOW_HEIGHT = 680
MIN_WIDTH = 380
MIN_HEIGHT = 560

# ── Mini Widget (startup mode) ────────────────────────────────────────────────
MINI_WIDTH = 340
MINI_HEIGHT = 400

# ── Timing ────────────────────────────────────────────────────────────────────
AUTO_SAVE_INTERVAL_MS = 2000
CLOCK_UPDATE_MS = 1000
NOTIFICATION_CHECK_INTERVAL_MS = 60000

# ── Task Defaults ─────────────────────────────────────────────────────────────
MAX_TASK_LENGTH = 200

# ── Timer Presets (minutes) ───────────────────────────────────────────────────
TIMER_PRESETS = [5, 15, 25, 45, 60]
DEFAULT_TIMER_MINUTES = 25  # Pomodoro default
