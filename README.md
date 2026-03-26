# Quietum — Calm Daily Planner

A minimal, distraction-free desktop productivity app for daily and weekly planning.  
Feels like a personal companion, not a complex productivity system.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Today** section for daily tasks
- **This Week** section for weekly planning
- Add, edit, delete, and complete tasks
- Auto-save all data locally (JSON)
- Dark mode toggle
- Always-on-top toggle
- Drag-and-drop task reordering
- Keyboard shortcuts (`Ctrl+N` quick add, `Ctrl+D` dark mode, `Ctrl+T` always-on-top)
- Reminder notifications (Windows toast)
- Extremely fast launch, low memory usage
- Windows startup integration

---

## Project Structure

```
Quietum/
├── main.py              # Entry point
├── app/
│   ├── __init__.py
│   ├── window.py        # Main window & UI
│   ├── task_manager.py  # Task CRUD logic
│   ├── storage.py       # JSON persistence
│   ├── theme.py         # Light/dark theme definitions
│   ├── notifications.py # Windows toast notifications
│   ├── startup.py       # Windows startup integration
│   └── constants.py     # App-wide constants
├── data/                # Auto-created, stores tasks.json
├── assets/
│   └── icon.ico         # App icon (optional)
├── requirements.txt
├── build.bat            # One-click build to .exe
├── install_startup.bat  # Enable startup on boot
└── README.md
```

---

## Quick Start

### 1. Install Python 3.8+

Download from [python.org](https://www.python.org/downloads/).

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python main.py
```

---

## Build to .exe

```bash
build.bat
```

This uses PyInstaller to create a standalone `Quietum.exe` in the `dist/` folder.

---

## Enable Startup on Boot

### Option A: Run the batch file

```bash
install_startup.bat
```

### Option B: From the app

Use **Settings → Start with Windows** toggle inside the app.

### Option C: Manual

1. Press `Win + R`, type `shell:startup`
2. Create a shortcut to `Quietum.exe` (or `main.py`) in that folder

---

## Keyboard Shortcuts

| Shortcut     | Action               |
| ------------ | -------------------- |
| `Ctrl+N`     | Quick add task       |
| `Ctrl+D`     | Toggle dark mode     |
| `Ctrl+T`     | Toggle always-on-top |
| `Delete`     | Delete selected task |
| `Escape`     | Close/minimize       |

---

## Configuration

All data is stored in `data/tasks.json`. Settings are in `data/settings.json`.  
No cloud, no login, fully offline.

---

## License

MIT — free for personal and commercial use.
