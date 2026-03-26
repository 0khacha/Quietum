"""
mini_widget.py — Startup floating widget for Quietum.
Shows only today's tasks in a small, borderless, draggable card.
Pure customtkinter — no HTML dependency.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math

from app.constants import APP_NAME, MINI_WIDTH, MINI_HEIGHT, CLOCK_UPDATE_MS, ICON_PATH
from app.storage import load_tasks, save_tasks, load_settings
from app.task_manager import toggle_task as toggle_fn
import os

# Colors (same as main window)
LIGHT = {
    "bg": "#F6F6F4", "surface": "#FFFFFF", "surface2": "#EEEEE9",
    "hover": "#F0F0EB", "text": "#1B1B18", "text2": "#6E6E69",
    "text3": "#A3A39E", "accent": "#6366F1", "accent_h": "#5558DD",
    "green": "#22C55E", "green_s": "#E8FAF0", "border": "#E4E4DF",
    "card_bd": "#ECECEA",
}
DARK = {
    "bg": "#09090B", "surface": "#131316", "surface2": "#1A1A1F",
    "hover": "#1F1F24", "text": "#ECECEC", "text2": "#8B8B8B",
    "text3": "#525252", "accent": "#818CF8", "accent_h": "#9BA3FB",
    "green": "#34D399", "green_s": "#0D2818", "border": "#1F1F24",
    "card_bd": "#27272D",
}


class MiniWidget:
    """Floating mini widget — today's tasks only."""

    def __init__(self, on_open_full=None):
        self.on_open_full = on_open_full
        self.settings = load_settings()
        self.tasks = load_tasks()

        is_dark = self.settings.get("dark_mode", False)
        self.c = DARK if is_dark else LIGHT
        ctk.set_appearance_mode("dark" if is_dark else "light")

        # ── Window ────────────────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{MINI_WIDTH}x{MINI_HEIGHT}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(fg_color=self.c["bg"])

        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass

        # Position bottom-right
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{sw - MINI_WIDTH - 24}+{sh - MINI_HEIGHT - 60}")

        # Dragging
        self._dx = 0
        self._dy = 0

        # Build
        self._build()
        self._update_clock()

        # Fade in
        self.root.attributes("-alpha", 0.0)
        self._fade(0.0, 0.95, 0.06)

    def _build(self):
        c = self.c
        F = ctk.CTkFont

        # Outer card
        card = ctk.CTkFrame(self.root, fg_color=c["surface"],
            corner_radius=16, border_width=1, border_color=c["card_bd"])
        card.pack(fill="both", expand=True, padx=4, pady=4)

        # Draggable top area
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 0))
        top.bind("<ButtonPress-1>", self._drag_start)
        top.bind("<B1-Motion>", self._drag_move)

        # Clock
        self.clock_lbl = ctk.CTkLabel(top, text="00:00",
            font=F(family="Segoe UI Variable", size=28, weight="bold"),
            text_color=c["text"])
        self.clock_lbl.pack(side="left")
        self.clock_lbl.bind("<ButtonPress-1>", self._drag_start)
        self.clock_lbl.bind("<B1-Motion>", self._drag_move)

        # Close
        ctk.CTkButton(top, text="×", width=26, height=26,
            font=F(size=14), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text3"],
            corner_radius=13, command=self._dismiss).pack(side="right")

        # Date + greeting
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Good night"
        date_str = datetime.now().strftime("%A, %b %d")

        ctk.CTkLabel(card, text=f"{greet}  ·  {date_str}",
            font=F(family="Segoe UI Variable", size=11),
            text_color=c["text3"]).pack(fill="x", padx=18, pady=(4, 10))

        # Divider
        ctk.CTkFrame(card, fg_color=c["border"], height=1).pack(fill="x", padx=16)

        # Section label
        today_items = self.tasks.get("today", [])
        pending = sum(1 for t in today_items if not t.get("done"))
        ctk.CTkLabel(card, text=f"TODAY'S TASKS  ·  {pending} pending",
            font=F(family="Segoe UI Variable", size=10, weight="bold"),
            text_color=c["text3"]).pack(fill="x", padx=18, pady=(12, 6))

        # Task list
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
            corner_radius=0, scrollbar_button_color=c["border"])
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        if not today_items:
            ctk.CTkLabel(scroll, text="No tasks for today ✨",
                font=F(family="Segoe UI Variable", size=12),
                text_color=c["text3"]).pack(pady=24)
        else:
            for task in today_items[:10]:
                self._make_row(scroll, task)
            if len(today_items) > 10:
                ctk.CTkLabel(scroll, text=f"+{len(today_items)-10} more",
                    font=F(size=11), text_color=c["text3"]).pack(pady=4)

        # Bottom buttons
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(bottom, text="Open Quietum",
            height=34, font=F(family="Segoe UI Variable", size=12, weight="bold"),
            fg_color=c["accent"], hover_color=c["accent_h"],
            text_color="#FFFFFF", corner_radius=17,
            command=self._open_full).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(bottom, text="Dismiss", width=80,
            height=34, font=F(family="Segoe UI Variable", size=12),
            fg_color="transparent", hover_color=c["hover"],
            text_color=c["text2"], corner_radius=17,
            border_width=1, border_color=c["border"],
            command=self._dismiss).pack(side="right")

    def _make_row(self, parent, task):
        c = self.c
        done = task.get("done", False)

        row = ctk.CTkFrame(parent, fg_color="transparent", height=32)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Checkbox
        cs = 18
        cv = tk.Canvas(row, width=cs, height=cs,
            bg=c["surface"], highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=(6, 8), pady=6)

        if done:
            cv.create_oval(1, 1, cs-1, cs-1, fill=c["green"], outline=c["green"])
            cv.create_text(cs//2, cs//2, text="✓",
                font=("Segoe UI", 9, "bold"), fill="#FFF")
        else:
            cv.create_oval(2, 2, cs-2, cs-2, fill="", outline=c["border"], width=2)

        cv.bind("<Button-1>", lambda e, tid=task["id"]: self._toggle(tid))

        # Text
        ctk.CTkLabel(row, text=task["text"],
            font=ctk.CTkFont(family="Segoe UI Variable", size=12,
                             overstrike=done),
            text_color=c["text3"] if done else c["text"],
            anchor="w").pack(side="left", fill="x", expand=True)

    def _toggle(self, tid):
        for t in self.tasks.get("today", []):
            if t["id"] == tid:
                toggle_fn(t)
                save_tasks(self.tasks)
                break
        # Rebuild
        for w in self.root.winfo_children():
            w.destroy()
        self._build()

    def _update_clock(self):
        self.clock_lbl.configure(text=datetime.now().strftime("%H:%M"))
        self.root.after(CLOCK_UPDATE_MS, self._update_clock)

    def _drag_start(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def _open_full(self):
        self.root.destroy()
        if self.on_open_full:
            self.on_open_full()

    def _dismiss(self):
        self._fade(0.95, 0.0, -0.06)

    def _fade(self, cur, target, step):
        if (step > 0 and cur < target) or (step < 0 and cur > 0.05):
            cur += step
            self.root.attributes("-alpha", max(0, min(1, cur)))
            self.root.after(16, lambda: self._fade(cur, target, step))
        elif step < 0:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
