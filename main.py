"""
Quietum — Calm Daily Planner
Entry point.

    python main.py              Full app
    python main.py --mini       Mini widget (today only)
    python main.py --startup    Mini widget (startup mode)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def full():
    from app.window import QuietumApp
    QuietumApp().run()


def mini():
    from app.mini_widget import MiniWidget
    MiniWidget(on_open_full=full).run()


if __name__ == "__main__":
    if "--mini" in sys.argv or "--startup" in sys.argv:
        mini()
    else:
        full()
