"""
main.py — Entry point for Quietum, the calm daily planner.

Launch modes:
    python main.py                 → Full app window
    python main.py --mini          → Mini widget (today's tasks only)
    python main.py --startup       → Mini widget (for Windows startup)

Build:
    pyinstaller --onefile --windowed --name Quietum main.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def launch_full_app():
    """Launch the full Quietum application window."""
    from app.window import QuietumApp
    app = QuietumApp()
    app.run()


def launch_mini_widget():
    """Launch the lightweight mini widget showing today's tasks."""
    from app.mini_widget import MiniWidget
    widget = MiniWidget(on_open_full=launch_full_app)
    widget.run()


def main():
    """Determine launch mode and start the app."""
    args = sys.argv[1:]

    if "--mini" in args or "--startup" in args:
        # Startup mode: show only the mini widget with today's tasks
        launch_mini_widget()
    else:
        # Normal mode: launch the full app
        launch_full_app()


if __name__ == "__main__":
    main()
