"""
mini_widget.py — Floating startup widget for Quietum.
Apple iOS glassmorphism card — warm grey, truly rounded corners.
Uses -transparentcolor trick for genuine rounded window appearance.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import ctypes
import os

from app.constants import APP_NAME, MINI_WIDTH, MINI_HEIGHT, CLOCK_UPDATE_MS, ICON_PATH
from app.storage import load_tasks, save_tasks, load_settings
from app.task_manager import toggle_task as do_toggle

# ── Glassmorphism Tokens (NO whites) ──────────────────────────────────────────
S = lambda n: n * 4
CR_PANEL = 24
CR_INNER = 18
CR_BTN   = 14
CR_PILL  = 50

# Transparent key — this exact color becomes invisible
_TKEY = "#010101"

LIGHT = {
    "scene": _TKEY,  # Window bg = transparent
    "glass_1": "#E6E0D8", "glass_2": "#DDD7CE",
    "glass_3": "#D2CBC1", "glass_edge": "#CCC5BA",
    "hover": "#D8D1C7", "text_1": "#1A1714", "text_2": "#3A3530",
    "text_3": "#7A756D", "text_4": "#A09A90",
    "accent": "#6C5CE7", "accent_h": "#5A4BD6", "accent_text": "#F0ECE4",
    "green": "#34C759", "border": "#C2BAB0", "separator": "#CCC5BA",
}
DARK = {
    "scene": _TKEY,
    "glass_1": "#1C1922", "glass_2": "#16131C",
    "glass_3": "#211E28", "glass_edge": "#2A2732",
    "hover": "#252230", "text_1": "#F2EDE6", "text_2": "#B8B0A5",
    "text_3": "#6E6860", "text_4": "#403C36",
    "accent": "#A29BFE", "accent_h": "#B4AEFF", "accent_text": "#0E0C12",
    "green": "#30D158", "border": "#332F3B", "separator": "#252228",
}

def _f(sz, wt="normal"):
    return ctk.CTkFont(family="Segoe UI", size=sz, weight=wt)


class MiniWidget:
    """Floating glass widget — today's tasks only.
    Uses -transparentcolor for truly rounded window corners."""

    def __init__(self, on_open_full=None):
        self.on_open_full = on_open_full
        self.settings = load_settings()
        self.tasks = load_tasks()
        self._alive = True

        dark = self.settings.get("dark_mode", False)
        self.c = DARK if dark else LIGHT
        ctk.set_appearance_mode("dark" if dark else "light")

        # ── Window ────────────────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{MINI_WIDTH}x{MINI_HEIGHT}")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(fg_color=_TKEY)

        # Make the transparent key color truly invisible
        try:
            self.root.wm_attributes("-transparentcolor", _TKEY)
        except:
            pass

        if os.path.exists(ICON_PATH):
            try: self.root.iconbitmap(ICON_PATH)
            except: pass

        # Position bottom-right
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{sw - MINI_WIDTH - 24}+{sh - MINI_HEIGHT - 60}")

        self._dx = 0; self._dy = 0

        # Build
        self._build()
        self._tick()

        # Fade in
        self.root.wm_attributes("-alpha", 0.0)
        self._fade_to(0.96)

    def _build(self):
        c = self.c
        today = self.tasks.get("today", [])
        pending = sum(1 for t in today if not t.get("done"))

        # ── Glass card — the visible rounded panel ────────────────────────
        card = ctk.CTkFrame(self.root, fg_color=c["glass_1"],
            corner_radius=CR_PANEL, border_width=1,
            border_color=c["glass_edge"])
        card.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Draggable header ──────────────────────────────────────────────
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=S(5), pady=(S(5), 0))
        top.bind("<ButtonPress-1>", self._drag_start)
        top.bind("<B1-Motion>", self._drag_move)

        self.clock_lbl = ctk.CTkLabel(top, text="00:00",
            font=_f(30, "bold"), text_color=c["text_1"])
        self.clock_lbl.pack(side="left")
        self.clock_lbl.bind("<ButtonPress-1>", self._drag_start)
        self.clock_lbl.bind("<B1-Motion>", self._drag_move)

        ctk.CTkButton(top, text="×", width=26, height=26,
            font=_f(14), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text_4"],
            corner_radius=CR_BTN, command=self._dismiss).pack(side="right")

        # ── Greeting ──────────────────────────────────────────────────────
        hour = datetime.now().hour
        g = ("Good morning" if hour < 12 else "Good afternoon" if hour < 17
             else "Good evening" if hour < 21 else "Good night")

        ctk.CTkLabel(card, text=g, font=_f(16, "bold"),
            text_color=c["text_1"], anchor="w"
        ).pack(fill="x", padx=S(5), pady=(S(1), 0))

        ctk.CTkLabel(card, text=datetime.now().strftime("%A, %B %d"),
            font=_f(11), text_color=c["text_4"], anchor="w"
        ).pack(fill="x", padx=S(5), pady=(0, S(3)))

        # ── Separator ────────────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color=c["separator"], height=1
        ).pack(fill="x", padx=S(5))

        # ── Section ───────────────────────────────────────────────────────
        ctk.CTkLabel(card, text=f"TODAY  ·  {pending} pending",
            font=_f(9, "bold"), text_color=c["text_4"], anchor="w"
        ).pack(fill="x", padx=S(5), pady=(S(3), S(1)))

        # ── Tasks ─────────────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent",
            corner_radius=0, scrollbar_button_color=c["border"])
        scroll.pack(fill="both", expand=True, padx=S(2), pady=(0, S(1)))

        if not today:
            ctk.CTkLabel(scroll, text="No tasks for today ✨",
                font=_f(12), text_color=c["text_4"]).pack(pady=S(6))
        else:
            for task in today[:10]:
                self._row(scroll, task)
            if len(today) > 10:
                ctk.CTkLabel(scroll, text=f"+{len(today)-10} more…",
                    font=_f(10), text_color=c["text_4"]).pack(pady=S(1))

        # ── Bottom actions ────────────────────────────────────────────────
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=S(4), pady=(0, S(4)))

        ctk.CTkButton(bottom, text="Open Quietum", height=36,
            font=_f(13, "bold"), fg_color=c["accent"],
            hover_color=c["accent_h"], text_color=c["accent_text"],
            corner_radius=CR_PILL, command=self._open
        ).pack(side="left", fill="x", expand=True, padx=(0, S(2)))

        ctk.CTkButton(bottom, text="Dismiss", width=80, height=36,
            font=_f(12), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text_3"],
            corner_radius=CR_PILL, border_width=1,
            border_color=c["glass_edge"], command=self._dismiss
        ).pack(side="right")

    def _row(self, parent, task):
        c = self.c
        done = task.get("done", False)
        CS = 18

        row = ctk.CTkFrame(parent, fg_color="transparent",
            corner_radius=CR_BTN, height=34)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        def _on(e, r=row): r.configure(fg_color=c["hover"])
        def _off(e, r=row): r.configure(fg_color="transparent")
        row.bind("<Enter>", _on); row.bind("<Leave>", _off)

        cv = tk.Canvas(row, width=CS, height=CS,
            bg=c["glass_1"], highlightthickness=0, cursor="hand2")
        cv.pack(side="left", padx=(S(2), S(2)), pady=S(1))

        if done:
            cv.create_oval(0, 0, CS, CS, fill=c["green"], outline=c["green"])
            cv.create_line(4, 9, 7.5, 12.5, fill="#FFF", width=1.5, capstyle="round")
            cv.create_line(7.5, 12.5, 14, 5.5, fill="#FFF", width=1.5, capstyle="round")
        else:
            cv.create_oval(1, 1, CS-1, CS-1, fill="",
                outline=c["border"], width=1.5)

        cv.bind("<Button-1>", lambda e, tid=task["id"]: self._toggle(tid))
        cv.bind("<Enter>", _on); cv.bind("<Leave>", _off)

        ctk.CTkLabel(row, text=task["text"],
            font=ctk.CTkFont(family="Segoe UI", size=12,
                             overstrike=done),
            text_color=c["text_4"] if done else c["text_2"], anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=(0, S(1)))

    def _toggle(self, tid):
        for t in self.tasks.get("today", []):
            if t["id"] == tid:
                do_toggle(t); save_tasks(self.tasks); break
        for w in self.root.winfo_children(): w.destroy()
        self._build()

    def _tick(self):
        if not self._alive: return
        self.clock_lbl.configure(text=datetime.now().strftime("%H:%M"))
        self.root.after(CLOCK_UPDATE_MS, self._tick)

    def _drag_start(self, e): self._dx, self._dy = e.x, e.y
    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def _open(self):
        self._alive = False
        self.root.destroy()
        if self.on_open_full: self.on_open_full()

    def _dismiss(self):
        self._alive = False
        self._fade_to(0.0, closing=True)

    def _fade_to(self, target, closing=False):
        try: cur = float(self.root.wm_attributes("-alpha"))
        except: return
        diff = target - cur
        if abs(diff) < 0.04:
            self.root.wm_attributes("-alpha", target)
            if closing: self.root.destroy()
            return
        step = 0.05 if diff > 0 else -0.05
        self.root.wm_attributes("-alpha", cur + step)
        self.root.after(14, lambda: self._fade_to(target, closing))

    def run(self):
        self.root.mainloop()
