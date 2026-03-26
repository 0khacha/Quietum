"""
window.py — Quietum Main Window
Premium minimalist UI built with customtkinter.
Design inspired by Linear, Notion, and Apple Reminders.
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math

from app.constants import (
    APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    AUTO_SAVE_INTERVAL_MS, CLOCK_UPDATE_MS, NOTIFICATION_CHECK_INTERVAL_MS,
    MAX_TASK_LENGTH, DEFAULT_TIMER_MINUTES, ICON_PATH,
)
from app.storage import load_tasks, save_tasks, load_settings, save_settings
from app.task_manager import (
    create_task, toggle_task, edit_task, reorder_tasks,
    get_due_reminders, clear_reminder,
)
from app.notifications import send_task_reminder
from app.startup import enable_startup, disable_startup, is_startup_enabled
import os


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTES
# ══════════════════════════════════════════════════════════════════════════════

LIGHT = {
    "bg":       "#F6F6F4",  "surface":  "#FFFFFF",  "surface2": "#EEEEE9",
    "hover":    "#F0F0EB",  "active":   "#E6E6E1",
    "text":     "#1B1B18",  "text2":    "#6E6E69",  "text3":    "#A3A39E",
    "accent":   "#6366F1",  "accent_h": "#5558DD",  "accent_s": "#EEEEFF",
    "green":    "#22C55E",  "green_s":  "#E8FAF0",
    "red":      "#EF4444",  "red_s":    "#FEF2F2",
    "border":   "#E4E4DF",  "card_bd":  "#ECECEA",
}

DARK = {
    "bg":       "#09090B",  "surface":  "#131316",  "surface2": "#1A1A1F",
    "hover":    "#1F1F24",  "active":   "#27272D",
    "text":     "#ECECEC",  "text2":    "#8B8B8B",  "text3":    "#525252",
    "accent":   "#818CF8",  "accent_h": "#9BA3FB",  "accent_s": "#1E1E2E",
    "green":    "#34D399",  "green_s":  "#0D2818",
    "red":      "#F87171",  "red_s":    "#2D1212",
    "border":   "#1F1F24",  "card_bd":  "#27272D",
}


class QuietumApp:
    """Main Quietum application."""

    def __init__(self):
        # ── State ─────────────────────────────────────────────────────────
        self.settings = load_settings()
        self.tasks = load_tasks()
        self.current_tab = "today"
        self._dirty = False
        self._drag_data = None
        self._settings_open = False
        self._alive = True  # Track if window is active (prevents after errors)

        # Timer
        self._timer_running = False
        self._timer_total = DEFAULT_TIMER_MINUTES * 60
        self._timer_remaining = self._timer_total
        self._timer_after = None

        # Theme
        is_dark = self.settings.get("dark_mode", False)
        self.c = DARK if is_dark else LIGHT
        ctk.set_appearance_mode("dark" if is_dark else "light")

        # ── Window ────────────────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(fg_color=self.c["bg"])

        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass

        if self.settings.get("window_x") is not None:
            self.root.geometry(f"+{self.settings['window_x']}+{self.settings['window_y']}")
        self.root.attributes("-topmost", self.settings.get("always_on_top", False))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Build ─────────────────────────────────────────────────────────
        self._build()
        self._update_clock()

        # ── Shortcuts ─────────────────────────────────────────────────────
        self.root.bind("<Control-n>", lambda e: self.entry.focus_set())
        self.root.bind("<Control-d>", lambda e: self._toggle_dark())
        self.root.bind("<Control-t>", lambda e: self._toggle_pin())
        self.root.bind("<Escape>", lambda e: self.root.iconify())

        # ── Periodic ──────────────────────────────────────────────────────
        self._auto_save_loop()
        self._reminder_loop()

    # ══════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════

    def _build(self):
        c = self.c
        F = ctk.CTkFont

        # ── HEADER ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self.root, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(22, 0))

        # Greeting
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening" if hour < 21 else "Good night"
        self.greet_lbl = ctk.CTkLabel(hdr, text=greet,
            font=F(family="Segoe UI Variable", size=17, weight="bold"),
            text_color=c["text"])
        self.greet_lbl.pack(side="left")

        # Header buttons
        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.pack(side="right")

        self.pin_btn = ctk.CTkButton(btns, text="📌", width=30, height=30,
            font=F(size=13), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text3"] if not self.settings.get("always_on_top") else c["accent"],
            corner_radius=8, command=self._toggle_pin)
        self.pin_btn.pack(side="left", padx=1)

        self.theme_btn = ctk.CTkButton(btns, text="◐", width=30, height=30,
            font=F(size=15), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text3"],
            corner_radius=8, command=self._toggle_dark)
        self.theme_btn.pack(side="left", padx=1)

        self.gear_btn = ctk.CTkButton(btns, text="⚙", width=30, height=30,
            font=F(size=14), fg_color="transparent",
            hover_color=c["hover"], text_color=c["text3"],
            corner_radius=8, command=self._toggle_settings)
        self.gear_btn.pack(side="left", padx=1)

        # ── CLOCK ROW ────────────────────────────────────────────────────
        clock_row = ctk.CTkFrame(self.root, fg_color="transparent")
        clock_row.pack(fill="x", padx=24, pady=(4, 0))

        self.clock_lbl = ctk.CTkLabel(clock_row, text="00:00",
            font=F(family="Segoe UI Variable", size=40, weight="bold"),
            text_color=c["text"])
        self.clock_lbl.pack(side="left")

        self.sec_lbl = ctk.CTkLabel(clock_row, text=":00",
            font=F(family="Segoe UI Variable", size=16),
            text_color=c["text3"])
        self.sec_lbl.pack(side="left", anchor="s", pady=(0, 8))

        date_str = datetime.now().strftime("  %A, %b %d")
        self.date_lbl = ctk.CTkLabel(clock_row, text=date_str,
            font=F(family="Segoe UI Variable", size=12),
            text_color=c["text3"])
        self.date_lbl.pack(side="left", anchor="s", pady=(0, 10))

        # ── SETTINGS PANEL (hidden) ──────────────────────────────────────
        self.settings_frame = ctk.CTkFrame(self.root, fg_color=c["surface"],
            corner_radius=12, border_width=1, border_color=c["border"])
        self._build_settings()

        # ── TIMER CARD ────────────────────────────────────────────────────
        self.timer_card = ctk.CTkFrame(self.root, fg_color=c["surface"],
            corner_radius=14, border_width=1, border_color=c["card_bd"], height=100)
        self.timer_card.pack(fill="x", padx=24, pady=(14, 0))
        self.timer_card.pack_propagate(False)

        # Timer ring (canvas)
        self.timer_canvas = tk.Canvas(self.timer_card, width=58, height=58,
            bg=c["surface"], highlightthickness=0, bd=0)
        self.timer_canvas.pack(side="left", padx=(16, 12), pady=10)

        # Timer info
        timer_info = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        timer_info.pack(side="left", fill="both", expand=True, pady=10)

        ctk.CTkLabel(timer_info, text="FOCUS TIMER",
            font=F(family="Segoe UI Variable", size=10, weight="bold"),
            text_color=c["text3"]).pack(anchor="w")

        self.timer_lbl = ctk.CTkLabel(timer_info,
            text=self._fmt_time(self._timer_remaining),
            font=F(family="Consolas", size=26, weight="bold"),
            text_color=c["text"])
        self.timer_lbl.pack(anchor="w", pady=(0, 4))

        # Timer buttons row
        timer_btns = ctk.CTkFrame(timer_info, fg_color="transparent")
        timer_btns.pack(anchor="w")

        self.start_btn = ctk.CTkButton(timer_btns, text="▶  Start",
            width=72, height=26,
            font=F(family="Segoe UI Variable", size=11, weight="bold"),
            fg_color=c["accent"], hover_color=c["accent_h"],
            text_color="#FFFFFF", corner_radius=13,
            command=self._timer_toggle)
        self.start_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(timer_btns, text="↺", width=26, height=26,
            font=F(size=13), fg_color=c["surface2"],
            hover_color=c["hover"], text_color=c["text2"],
            corner_radius=13, command=self._timer_reset).pack(side="left", padx=(0, 8))

        for m in [5, 15, 25, 45]:
            ctk.CTkButton(timer_btns, text=f"{m}", width=28, height=22,
                font=F(family="Segoe UI Variable", size=10),
                fg_color="transparent", hover_color=c["accent_s"],
                text_color=c["text3"], corner_radius=11,
                border_width=1, border_color=c["border"],
                command=lambda mins=m: self._timer_set(mins)).pack(side="left", padx=1)

        self._draw_ring()

        # ── TABS ──────────────────────────────────────────────────────────
        tab_wrap = ctk.CTkFrame(self.root, fg_color=c["surface2"],
            corner_radius=10, height=38)
        tab_wrap.pack(fill="x", padx=24, pady=(14, 0))
        tab_wrap.pack_propagate(False)

        inner_pad = ctk.CTkFrame(tab_wrap, fg_color="transparent")
        inner_pad.pack(fill="both", expand=True, padx=3, pady=3)

        self.tab_today = ctk.CTkButton(inner_pad, text="Today",
            height=30, font=F(family="Segoe UI Variable", size=13, weight="bold"),
            fg_color=c["surface"], hover_color=c["surface"],
            text_color=c["text"], corner_radius=8,
            command=lambda: self._switch_tab("today"))
        self.tab_today.pack(side="left", fill="both", expand=True, padx=(0, 2))

        self.tab_week = ctk.CTkButton(inner_pad, text="This Week",
            height=30, font=F(family="Segoe UI Variable", size=13, weight="bold"),
            fg_color="transparent", hover_color=c["hover"],
            text_color=c["text3"], corner_radius=8,
            command=lambda: self._switch_tab("week"))
        self.tab_week.pack(side="left", fill="both", expand=True, padx=(2, 0))

        # ── PROGRESS ─────────────────────────────────────────────────────
        prog_row = ctk.CTkFrame(self.root, fg_color="transparent", height=20)
        prog_row.pack(fill="x", padx=28, pady=(10, 0))
        prog_row.pack_propagate(False)

        self.prog_lbl = ctk.CTkLabel(prog_row, text="",
            font=F(family="Segoe UI Variable", size=11),
            text_color=c["text3"])
        self.prog_lbl.pack(side="left")

        self.prog_bar = ctk.CTkProgressBar(prog_row, height=3, width=80,
            fg_color=c["surface2"], progress_color=c["green"], corner_radius=2)
        self.prog_bar.pack(side="right")
        self.prog_bar.set(0)

        # ── TASK LIST ─────────────────────────────────────────────────────
        self.task_scroll = ctk.CTkScrollableFrame(self.root,
            fg_color="transparent", corner_radius=0,
            scrollbar_button_color=c["border"],
            scrollbar_button_hover_color=c["text3"])
        self.task_scroll.pack(fill="both", expand=True, padx=18, pady=(6, 0))

        self._render_tasks()

        # ── INPUT BAR ─────────────────────────────────────────────────────
        input_wrap = ctk.CTkFrame(self.root, fg_color="transparent")
        input_wrap.pack(fill="x", padx=20, pady=(8, 16))

        input_card = ctk.CTkFrame(input_wrap, fg_color=c["surface"],
            corner_radius=12, border_width=1, border_color=c["card_bd"])
        input_card.pack(fill="x")

        ctk.CTkLabel(input_card, text="+",
            font=F(size=18, weight="bold"),
            text_color=c["accent"], width=20).pack(side="left", padx=(14, 6), pady=10)

        self.entry = ctk.CTkEntry(input_card,
            placeholder_text="What needs to be done?",
            font=F(family="Segoe UI Variable", size=13),
            fg_color="transparent", border_width=0,
            text_color=c["text"], placeholder_text_color=c["text3"],
            height=36)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=4)
        self.entry.bind("<Return>", self._add_task)

        self.add_btn = ctk.CTkButton(input_card, text="Add",
            width=52, height=28,
            font=F(family="Segoe UI Variable", size=12, weight="bold"),
            fg_color=c["accent"], hover_color=c["accent_h"],
            text_color="#FFFFFF", corner_radius=8,
            command=self._add_task)
        self.add_btn.pack(side="right", padx=(0, 8), pady=6)

    def _build_settings(self):
        """Build settings panel content."""
        c = self.c
        F = ctk.CTkFont
        frm = self.settings_frame

        # Startup toggle
        row1 = ctk.CTkFrame(frm, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(row1, text="🚀  Start with Windows",
            font=F(family="Segoe UI Variable", size=12),
            text_color=c["text"]).pack(side="left")
        self.startup_sw = ctk.CTkSwitch(row1, text="", width=40,
            fg_color=c["surface2"], progress_color=c["accent"],
            button_color="#FFFFFF", button_hover_color="#F0F0F0",
            command=self._toggle_startup)
        if is_startup_enabled():
            self.startup_sw.select()
        self.startup_sw.pack(side="right")

        # Shortcuts
        ctk.CTkLabel(frm,
            text="⌨  Ctrl+N Add  ·  Ctrl+D Theme  ·  Ctrl+T Pin",
            font=F(family="Segoe UI Variable", size=10),
            text_color=c["text3"]).pack(padx=14, pady=(6, 12))

    # ══════════════════════════════════════════════════════════════════════
    #  CLOCK
    # ══════════════════════════════════════════════════════════════════════

    def _update_clock(self):
        if not self._alive:
            return
        now = datetime.now()
        self.clock_lbl.configure(text=now.strftime("%H:%M"))
        self.sec_lbl.configure(text=now.strftime(":%S"))
        self.root.after(CLOCK_UPDATE_MS, self._update_clock)

    # ══════════════════════════════════════════════════════════════════════
    #  TIMER
    # ══════════════════════════════════════════════════════════════════════

    def _fmt_time(self, s):
        m, sec = divmod(max(0, s), 60)
        return f"{m:02d}:{sec:02d}"

    def _draw_ring(self):
        cv = self.timer_canvas
        c = self.c
        cv.configure(bg=c["surface"])
        cv.delete("all")
        cx, cy, r, w = 29, 29, 23, 3.5

        # Background ring
        cv.create_oval(cx-r, cy-r, cx+r, cy+r, outline=c["surface2"], width=w)

        # Progress arc
        progress = self._timer_remaining / self._timer_total if self._timer_total > 0 else 1
        extent = progress * 360
        cv.create_arc(cx-r, cy-r, cx+r, cy+r, start=90, extent=-extent,
            outline=c["accent"], width=w, style="arc")

        # Center text
        mins = math.ceil(self._timer_remaining / 60)
        cv.create_text(cx, cy, text=str(mins),
            font=("Segoe UI Variable", 13, "bold"), fill=c["text"])

    def _timer_toggle(self):
        if self._timer_running:
            self._timer_running = False
            self.start_btn.configure(text="▶  Resume")
            if self._timer_after:
                self.root.after_cancel(self._timer_after)
        else:
            self._timer_running = True
            self.start_btn.configure(text="⏸  Pause")
            self._timer_tick()

    def _timer_tick(self):
        if not self._timer_running or not self._alive:
            return
        self._timer_remaining -= 1
        self.timer_lbl.configure(text=self._fmt_time(self._timer_remaining))
        self._draw_ring()
        if self._timer_remaining <= 0:
            self._timer_running = False
            self.start_btn.configure(text="▶  Start")
            send_task_reminder("Focus session complete! 🎉")
            return
        self._timer_after = self.root.after(1000, self._timer_tick)

    def _timer_reset(self):
        self._timer_running = False
        self._timer_remaining = self._timer_total
        self.start_btn.configure(text="▶  Start")
        if self._timer_after:
            self.root.after_cancel(self._timer_after)
        self.timer_lbl.configure(text=self._fmt_time(self._timer_remaining))
        self._draw_ring()

    def _timer_set(self, mins):
        self._timer_running = False
        self._timer_total = mins * 60
        self._timer_remaining = self._timer_total
        self.start_btn.configure(text="▶  Start")
        if self._timer_after:
            self.root.after_cancel(self._timer_after)
        self.timer_lbl.configure(text=self._fmt_time(self._timer_remaining))
        self._draw_ring()

    # ══════════════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════════════

    def _switch_tab(self, tab):
        if tab == self.current_tab:
            return
        self.current_tab = tab
        c = self.c
        if tab == "today":
            self.tab_today.configure(fg_color=c["surface"], text_color=c["text"])
            self.tab_week.configure(fg_color="transparent", text_color=c["text3"])
        else:
            self.tab_week.configure(fg_color=c["surface"], text_color=c["text"])
            self.tab_today.configure(fg_color="transparent", text_color=c["text3"])
        self._render_tasks()

    # ══════════════════════════════════════════════════════════════════════
    #  TASK RENDERING
    # ══════════════════════════════════════════════════════════════════════

    def _render_tasks(self):
        for w in self.task_scroll.winfo_children():
            w.destroy()

        items = self.tasks.get(self.current_tab, [])
        c = self.c
        F = ctk.CTkFont

        # Update progress
        total = len(items)
        done = sum(1 for t in items if t.get("done"))
        if total > 0:
            self.prog_lbl.configure(text=f"{done}/{total} done")
            self.prog_bar.set(done / total)
        else:
            self.prog_lbl.configure(text="")
            self.prog_bar.set(0)

        # Empty state
        if not items:
            empty_frame = ctk.CTkFrame(self.task_scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=50)
            ctk.CTkLabel(empty_frame, text="✎",
                font=F(size=28), text_color=c["text3"]).pack()
            ctk.CTkLabel(empty_frame, text="No tasks yet",
                font=F(family="Segoe UI Variable", size=14),
                text_color=c["text3"]).pack(pady=(8, 2))
            ctk.CTkLabel(empty_frame, text="Type below and press Enter",
                font=F(family="Segoe UI Variable", size=12),
                text_color=c["text3"]).pack()
            return

        # Render tasks
        for idx, task in enumerate(items):
            self._make_task(idx, task)

    def _make_task(self, idx, task):
        """Create a single task row."""
        c = self.c
        F = ctk.CTkFont
        done = task.get("done", False)

        row = ctk.CTkFrame(self.task_scroll, fg_color="transparent",
            corner_radius=8, height=42)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        row._idx = idx
        row._tid = task["id"]

        # Hover effect
        def enter(e, r=row):
            r.configure(fg_color=c["hover"])
        def leave(e, r=row):
            r.configure(fg_color="transparent")
        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)

        # ── Checkbox (canvas-drawn circle) ────────────────────────────────
        check_size = 22
        check_cv = tk.Canvas(row, width=check_size, height=check_size,
            bg=c["bg"] if not done else c["bg"],
            highlightthickness=0, bd=0, cursor="hand2")
        check_cv.pack(side="left", padx=(10, 8), pady=8)

        if done:
            # Filled green circle with checkmark
            check_cv.create_oval(1, 1, check_size-1, check_size-1,
                fill=c["green"], outline=c["green"], width=0)
            check_cv.create_text(check_size//2, check_size//2, text="✓",
                font=("Segoe UI Variable", 10, "bold"), fill="#FFFFFF")
        else:
            # Empty circle with border
            check_cv.create_oval(2, 2, check_size-2, check_size-2,
                fill="", outline=c["border"], width=2)

        check_cv.bind("<Button-1>", lambda e, tid=task["id"]: self._toggle(tid))
        check_cv.bind("<Enter>", enter)
        check_cv.bind("<Leave>", leave)

        # Update canvas bg on hover
        def check_enter(e, cv=check_cv):
            cv.configure(bg=c["hover"])
        def check_leave(e, cv=check_cv):
            cv.configure(bg=c["bg"] if not done else c["bg"])
        check_cv.bind("<Enter>", lambda e: (enter(e), check_enter(e)))
        check_cv.bind("<Leave>", lambda e: (leave(e), check_leave(e)))

        # ── Task text ─────────────────────────────────────────────────────
        text_color = c["text3"] if done else c["text"]
        lbl = ctk.CTkLabel(row, text=task["text"],
            font=F(family="Segoe UI Variable", size=13,
                   overstrike=done),
            text_color=text_color, anchor="w", cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=8)
        lbl.bind("<Double-Button-1>", lambda e, tid=task["id"]: self._edit(tid))
        lbl.bind("<Enter>", enter)
        lbl.bind("<Leave>", leave)

        # ── Delete button (only visible on hover via parent) ──────────────
        del_btn = ctk.CTkButton(row, text="×", width=24, height=24,
            font=F(size=14), fg_color="transparent",
            hover_color=c["red_s"], text_color=c["text3"],
            corner_radius=6, command=lambda tid=task["id"]: self._delete(tid))
        del_btn.pack(side="right", padx=(0, 8), pady=8)

        # ── Drag ──────────────────────────────────────────────────────────
        for w in [row, lbl]:
            w.bind("<ButtonPress-1>", lambda e, i=idx: self._drag_start(e, i))
            w.bind("<B1-Motion>", self._drag_motion)
            w.bind("<ButtonRelease-1>", self._drag_end)

    # ══════════════════════════════════════════════════════════════════════
    #  TASK ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _add_task(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        task = create_task(text[:MAX_TASK_LENGTH])
        self.tasks[self.current_tab].append(task)
        self._dirty = True
        self.entry.delete(0, "end")
        self._render_tasks()

    def _toggle(self, tid):
        for t in self.tasks[self.current_tab]:
            if t["id"] == tid:
                toggle_task(t)
                self._dirty = True
                break
        self._render_tasks()

    def _delete(self, tid):
        self.tasks[self.current_tab] = [
            t for t in self.tasks[self.current_tab] if t["id"] != tid
        ]
        self._dirty = True
        self._render_tasks()

    def _edit(self, tid):
        task = None
        for t in self.tasks[self.current_tab]:
            if t["id"] == tid:
                task = t
                break
        if not task:
            return

        c = self.c
        for row in self.task_scroll.winfo_children():
            if hasattr(row, "_tid") and row._tid == tid:
                for child in row.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and hasattr(child, '_text'):
                        pass
                    if isinstance(child, ctk.CTkLabel):
                        try:
                            if child.cget("text") == task["text"]:
                                child.destroy()
                                entry = ctk.CTkEntry(row,
                                    font=ctk.CTkFont(family="Segoe UI Variable", size=13),
                                    fg_color=c["surface"], text_color=c["text"],
                                    border_width=1, border_color=c["accent"],
                                    corner_radius=6, height=28)
                                entry.insert(0, task["text"])
                                entry.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=6)
                                entry.focus_set()
                                entry.select_range(0, "end")

                                def save(e=None, t_id=tid, ent=entry):
                                    new = ent.get().strip()
                                    if new:
                                        for tk_ in self.tasks[self.current_tab]:
                                            if tk_["id"] == t_id:
                                                edit_task(tk_, new[:MAX_TASK_LENGTH])
                                                self._dirty = True
                                                break
                                    self._render_tasks()

                                entry.bind("<Return>", save)
                                entry.bind("<Escape>", lambda e: self._render_tasks())
                                entry.bind("<FocusOut>", save)
                                return
                        except Exception:
                            pass
                break

    # ══════════════════════════════════════════════════════════════════════
    #  DRAG AND DROP
    # ══════════════════════════════════════════════════════════════════════

    def _drag_start(self, e, idx):
        self._drag_data = {"idx": idx, "y": e.y_root}

    def _drag_motion(self, e):
        pass

    def _drag_end(self, e):
        if not self._drag_data:
            return
        dy = e.y_root - self._drag_data["y"]
        steps = int(dy / 44)
        if steps:
            from_i = self._drag_data["idx"]
            to_i = max(0, min(from_i + steps, len(self.tasks[self.current_tab]) - 1))
            if to_i != from_i:
                reorder_tasks(self.tasks[self.current_tab], from_i, to_i)
                self._dirty = True
                self._render_tasks()
        self._drag_data = None

    # ══════════════════════════════════════════════════════════════════════
    #  SETTINGS
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_settings(self):
        if self._settings_open:
            self.settings_frame.pack_forget()
        else:
            self.settings_frame.pack(fill="x", padx=24, pady=(8, 0),
                before=self.timer_card)
        self._settings_open = not self._settings_open

    def _toggle_dark(self):
        is_dark = not self.settings.get("dark_mode", False)
        self.settings["dark_mode"] = is_dark
        self._dirty = True

        # Save state before destroying
        save_tasks(self.tasks)
        save_settings(self.settings)

        # Stop all callbacks, destroy, and rebuild
        self._alive = False
        self._timer_running = False
        self.root.destroy()

        # Rebuild with new theme
        self._alive = True
        self.__init__()

    def _toggle_pin(self):
        on = not self.settings.get("always_on_top", False)
        self.settings["always_on_top"] = on
        self.root.attributes("-topmost", on)
        c = self.c
        self.pin_btn.configure(text_color=c["accent"] if on else c["text3"])
        self._dirty = True

    def _toggle_startup(self):
        if self.startup_sw.get():
            enable_startup()
        else:
            disable_startup()
        self.settings["start_with_windows"] = bool(self.startup_sw.get())
        self._dirty = True

    # ══════════════════════════════════════════════════════════════════════
    #  PERSISTENCE
    # ══════════════════════════════════════════════════════════════════════

    def _auto_save_loop(self):
        if not self._alive:
            return
        if self._dirty:
            save_tasks(self.tasks)
            save_settings(self.settings)
            self._dirty = False
        self.root.after(AUTO_SAVE_INTERVAL_MS, self._auto_save_loop)

    def _reminder_loop(self):
        if not self._alive:
            return
        for sec in ["today", "week"]:
            due = get_due_reminders(self.tasks.get(sec, []))
            for t in due:
                send_task_reminder(t["text"])
                clear_reminder(t)
                self._dirty = True
        self.root.after(NOTIFICATION_CHECK_INTERVAL_MS, self._reminder_loop)

    def _on_close(self):
        self._alive = False
        self._timer_running = False
        try:
            self.settings["window_x"] = self.root.winfo_x()
            self.settings["window_y"] = self.root.winfo_y()
        except Exception:
            pass
        save_tasks(self.tasks)
        save_settings(self.settings)
        self.root.destroy()

    def run(self):
        self.root.mainloop()
