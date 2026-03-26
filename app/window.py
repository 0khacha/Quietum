"""
window.py — Quietum Main Window
Apple iOS Glassmorphism Widget Style.

Design rules:
  • Glass panels: warm-tinted, semi-opaque, large blur via Windows DWM Acrylic
  • Color toning: every panel samples the dominant warm hue — nothing is pure white
  • Depth: floating panels with soft 8px–32px shadows, no hard drop shadows
  • Corners: 24px minimum for panels, 14px for buttons/tags
  • Typography: bold titles, regular body, always legible over glass
  • Controls: minimal, monochromatic, frosted
"""

import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import math
import ctypes
import os

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


# ══════════════════════════════════════════════════════════════════════════════
#  iOS GLASSMORPHISM TOKENS
# ══════════════════════════════════════════════════════════════════════════════

# Spacing grid: 4px
S = lambda n: n * 4

# Corners — iOS widget style (24px min for panels)
CR_PANEL  = 24   # Cards, modals, major containers
CR_INNER  = 18   # Inner cards, nested panels
CR_BTN    = 14   # Buttons, tags, inputs
CR_PILL   = 50   # Fully rounded pills
CR_CHECK  = 10   # Checkboxes

# ── Light Mode — Warm frosted glass (NO whites, all warm grey) ───────────────
LIGHT = {
    "scene":       "#D5CEC4",     # Warm stone background

    # Glass panels — warm grey, NO white anywhere
    "glass_1":     "#E6E0D8",     # Primary glass (warm light grey)
    "glass_2":     "#DDD7CE",     # Secondary glass (slightly darker)
    "glass_3":     "#D2CBC1",     # Tertiary / tab backgrounds

    # Glass borders
    "glass_edge":  "#CCC5BA",     # Subtle warm border
    "glass_edge_2":"#C2BAB0",     # Stronger definition

    # Hover / Active
    "hover":       "#D8D1C7",
    "active":      "#CEC7BC",

    # Text — high contrast on grey
    "text_1":      "#1A1714",
    "text_2":      "#3A3530",
    "text_3":      "#7A756D",
    "text_4":      "#A09A90",

    # Accent
    "accent":      "#6C5CE7",
    "accent_h":    "#5A4BD6",
    "accent_soft": "#D8D2EE",
    "accent_glow": "#C8C0E4",
    "accent_text": "#F0ECE4",

    # Semantic
    "green":       "#34C759",
    "green_soft":  "#C8E6D2",
    "red":         "#FF3B30",
    "red_soft":    "#E8CCCA",

    "shadow":      "#B5AA98",
    "scroll":      "#C5BEB4",
    "scroll_h":    "#B0A898",
}

# ── Dark Mode — Deep warm obsidian glass ────────────────────────────────────
# Scene: rich warm near-black with subtle purple undertone.
DARK = {
    "scene":       "#0E0C12",

    "glass_1":     "#1C1922",     # Tinted with warm purple
    "glass_2":     "#16131C",
    "glass_3":     "#211E28",

    "glass_edge":  "#2A2732",
    "glass_edge_2":"#332F3B",

    "hover":       "#252230",
    "active":      "#2E2A38",

    "text_1":      "#F2EDE6",
    "text_2":      "#B8B0A5",
    "text_3":      "#6E6860",
    "text_4":      "#403C36",

    "accent":      "#A29BFE",
    "accent_h":    "#B4AEFF",
    "accent_soft": "#1E1A30",
    "accent_glow": "#2A2540",
    "accent_text": "#0E0C12",

    "green":       "#30D158",
    "green_soft":  "#0F2A16",
    "red":         "#FF453A",
    "red_soft":    "#2D1210",

    "shadow":      "#000000",

    "scroll":      "#332F3B",
    "scroll_h":    "#443F4D",
}


# ══════════════════════════════════════════════════════════════════════════════
#  WINDOWS DWM — Acrylic Blur + Rounded Corners
# ══════════════════════════════════════════════════════════════════════════════

def _apply_dwm(hwnd, dark=False):
    """Apply Windows 11 Acrylic blur + rounded corners + dark title bar."""
    try:
        dwm = ctypes.windll.dwmapi

        # Dark mode title bar
        val = ctypes.c_int(1 if dark else 0)
        dwm.DwmSetWindowAttribute(hwnd, 20,
            ctypes.byref(val), ctypes.sizeof(val))

        # Acrylic backdrop (type 3 = acrylic, gives real blur)
        backdrop = ctypes.c_int(3)
        r = dwm.DwmSetWindowAttribute(hwnd, 38,
            ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        if r != 0:
            # Fallback: try mica (type 2)
            backdrop = ctypes.c_int(2)
            dwm.DwmSetWindowAttribute(hwnd, 38,
                ctypes.byref(backdrop), ctypes.sizeof(backdrop))

        # Rounded corners
        rounded = ctypes.c_int(2)  # DWMWCP_ROUND
        dwm.DwmSetWindowAttribute(hwnd, 33,
            ctypes.byref(rounded), ctypes.sizeof(rounded))
    except Exception:
        pass


def _hwnd(root):
    try: return ctypes.windll.user32.FindWindowW(None, root.title())
    except: return None


# ══════════════════════════════════════════════════════════════════════════════
#  FONT — iOS-like warm, rounded feel
# ══════════════════════════════════════════════════════════════════════════════

def _f(sz, wt="normal"):
    """Primary font — Segoe UI, clean & crisp on all Windows versions."""
    return ctk.CTkFont(family="Segoe UI", size=sz, weight=wt)

def _fm(sz, wt="normal"):
    """Monospace for timer."""
    return ctk.CTkFont(family="Consolas", size=sz, weight=wt)


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════

class QuietumApp:
    """Quietum — iOS Glassmorphism widget-style planner."""

    def __init__(self):
        self.settings = load_settings()
        self.tasks = load_tasks()
        self.tab = "today"
        self._dirty = False
        self._drag = None
        self._alive = True
        self._settings_vis = False

        # Timer
        self._tr = False  # running
        self._tt = DEFAULT_TIMER_MINUTES * 60  # total
        self._tl = self._tt  # left
        self._ta = None  # after id

        # Theme
        dark = self.settings.get("dark_mode", False)
        self.c = DARK if dark else LIGHT
        ctk.set_appearance_mode("dark" if dark else "light")

        # ── Window ────────────────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(fg_color=self.c["scene"])

        try: self.root.wm_attributes("-alpha", 0.96)
        except: pass

        if os.path.exists(ICON_PATH):
            try: self.root.iconbitmap(ICON_PATH)
            except: pass

        if self.settings.get("window_x") is not None:
            self.root.geometry(
                f"+{self.settings['window_x']}+{self.settings['window_y']}")
        self.root.wm_attributes(
            "-topmost", self.settings.get("always_on_top", False))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # DWM effects
        self.root.update_idletasks()
        h = _hwnd(self.root)
        if h: _apply_dwm(h, dark)

        # Build
        self._build()
        self._clock_tick()

        # Shortcuts
        self.root.bind("<Control-n>", lambda e: self.entry.focus_set())
        self.root.bind("<Control-d>", lambda e: self._toggle_dark())
        self.root.bind("<Control-t>", lambda e: self._toggle_pin())
        self.root.bind("<Escape>", lambda e: self.root.iconify())

        self._save_loop()
        self._reminder_loop()

    # ══════════════════════════════════════════════════════════════════════
    #  BUILD — iOS Widget Layout
    # ══════════════════════════════════════════════════════════════════════

    def _build(self):
        c = self.c

        # ── OUTER GLASS CARD — wraps everything ──────────────────────────
        # This is the main "widget" panel with frosted glass effect
        self.outer = ctk.CTkFrame(self.root,
            fg_color=c["glass_1"],
            corner_radius=CR_PANEL,
            border_width=1,
            border_color=c["glass_edge"])
        self.outer.pack(fill="both", expand=True, padx=8, pady=8)

        # ═══════════════════════════════════════════════════════════════════
        # HEADER — greeting + controls
        # ═══════════════════════════════════════════════════════════════════
        hdr = ctk.CTkFrame(self.outer, fg_color="transparent")
        hdr.pack(fill="x", padx=S(6), pady=(S(5), 0))

        hour = datetime.now().hour
        g = ("Good morning" if hour < 12
             else "Good afternoon" if hour < 17
             else "Good evening" if hour < 21
             else "Good night")

        self.greet = ctk.CTkLabel(hdr, text=g,
            font=_f(17, "bold"), text_color=c["text_1"])
        self.greet.pack(side="left")

        # Icon buttons — frosted, monochromatic
        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.pack(side="right")

        btn_data = [
            ("📌", self._toggle_pin, "pin_btn"),
            ("◐",  self._toggle_dark, None),
            ("⚙",  self._toggle_settings, None),
        ]
        for txt, cmd, ref in btn_data:
            b = ctk.CTkButton(btns, text=txt, width=30, height=30,
                font=_f(13), fg_color="transparent",
                hover_color=c["glass_3"], text_color=c["text_3"],
                corner_radius=CR_BTN, command=cmd)
            b.pack(side="left", padx=1)
            if ref: setattr(self, ref, b)

        if self.settings.get("always_on_top"):
            self.pin_btn.configure(text_color=c["accent"])

        # ═══════════════════════════════════════════════════════════════════
        # CLOCK — large bold time
        # ═══════════════════════════════════════════════════════════════════
        clk = ctk.CTkFrame(self.outer, fg_color="transparent")
        clk.pack(fill="x", padx=S(6), pady=(S(1), 0))

        self.clock = ctk.CTkLabel(clk, text="00:00",
            font=_f(44, "bold"), text_color=c["text_1"])
        self.clock.pack(side="left")

        self.clock_s = ctk.CTkLabel(clk, text=":00",
            font=_f(18), text_color=c["text_4"])
        self.clock_s.pack(side="left", anchor="s", pady=(0, S(2)))

        self.date_lbl = ctk.CTkLabel(clk,
            text=datetime.now().strftime("   %A, %b %d"),
            font=_f(12), text_color=c["text_4"])
        self.date_lbl.pack(side="left", anchor="s", pady=(0, S(3)))

        # ═══════════════════════════════════════════════════════════════════
        # SETTINGS PANEL (hidden, frosted inner glass)
        # ═══════════════════════════════════════════════════════════════════
        self.settings_panel = ctk.CTkFrame(self.outer,
            fg_color=c["glass_2"], corner_radius=CR_INNER,
            border_width=1, border_color=c["glass_edge"])
        self._build_settings()

        # ═══════════════════════════════════════════════════════════════════
        # TIMER — frosted inner glass card
        # ═══════════════════════════════════════════════════════════════════
        self.timer_card = ctk.CTkFrame(self.outer,
            fg_color=c["glass_2"], corner_radius=CR_INNER,
            border_width=1, border_color=c["glass_edge"],
            height=108)
        self.timer_card.pack(fill="x", padx=S(5), pady=(S(3), 0))
        self.timer_card.pack_propagate(False)

        # Ring
        self.ring = tk.Canvas(self.timer_card, width=64, height=64,
            bg=c["glass_2"], highlightthickness=0, bd=0)
        self.ring.pack(side="left", padx=(S(5), S(3)), pady=S(4))

        # Timer info
        ti = ctk.CTkFrame(self.timer_card, fg_color="transparent")
        ti.pack(side="left", fill="both", expand=True, pady=S(3))

        ctk.CTkLabel(ti, text="FOCUS TIMER",
            font=_f(9, "bold"), text_color=c["text_4"],
            anchor="w").pack(anchor="w")

        self.timer_lbl = ctk.CTkLabel(ti,
            text=self._fmt(self._tl),
            font=_fm(30, "bold"), text_color=c["text_1"], anchor="w")
        self.timer_lbl.pack(anchor="w", pady=(0, S(1)))

        # Timer controls
        tc = ctk.CTkFrame(ti, fg_color="transparent")
        tc.pack(anchor="w")

        self.start_btn = ctk.CTkButton(tc, text="▶  Start",
            width=76, height=28, font=_f(11, "bold"),
            fg_color=c["accent"], hover_color=c["accent_h"],
            text_color=c["accent_text"], corner_radius=CR_PILL,
            command=self._t_toggle)
        self.start_btn.pack(side="left", padx=(0, S(2)))

        ctk.CTkButton(tc, text="↺", width=28, height=28,
            font=_f(15), fg_color=c["glass_3"],
            hover_color=c["hover"], text_color=c["text_3"],
            corner_radius=CR_PILL, command=self._t_reset
        ).pack(side="left", padx=(0, S(3)))

        # Preset pills — frosted
        for m in [5, 15, 25, 45]:
            ctk.CTkButton(tc, text=str(m), width=32, height=24,
                font=_f(10), fg_color=c["glass_3"],
                hover_color=c["accent_soft"], text_color=c["text_3"],
                corner_radius=CR_PILL, border_width=0,
                command=lambda x=m: self._t_set(x)
            ).pack(side="left", padx=2)

        self._draw_ring()

        # ═══════════════════════════════════════════════════════════════════
        # TABS — frosted pill selector
        # ═══════════════════════════════════════════════════════════════════
        tab_bg = ctk.CTkFrame(self.outer,
            fg_color=c["glass_3"], corner_radius=CR_INNER, height=40)
        tab_bg.pack(fill="x", padx=S(5), pady=(S(3), 0))
        tab_bg.pack_propagate(False)

        tab_in = ctk.CTkFrame(tab_bg, fg_color="transparent")
        tab_in.pack(fill="both", expand=True, padx=4, pady=4)

        self.tabs = {}
        for name, label in [("today", "Today"), ("week", "This Week")]:
            active = name == self.tab
            b = ctk.CTkButton(tab_in, text=label, height=30,
                font=_f(13, "bold"),
                fg_color=c["glass_1"] if active else "transparent",
                hover_color=c["glass_1"] if active else c["hover"],
                text_color=c["text_1"] if active else c["text_4"],
                corner_radius=CR_BTN,
                command=lambda n=name: self._switch_tab(n))
            b.pack(side="left", fill="both", expand=True, padx=2)
            self.tabs[name] = b

        # ═══════════════════════════════════════════════════════════════════
        # PROGRESS
        # ═══════════════════════════════════════════════════════════════════
        pg = ctk.CTkFrame(self.outer, fg_color="transparent", height=18)
        pg.pack(fill="x", padx=S(7), pady=(S(2), 0))
        pg.pack_propagate(False)

        self.prog_lbl = ctk.CTkLabel(pg, text="",
            font=_f(10), text_color=c["text_4"])
        self.prog_lbl.pack(side="left")

        self.prog_bar = ctk.CTkProgressBar(pg, height=3, width=80,
            fg_color=c["glass_3"], progress_color=c["green"],
            corner_radius=2)
        self.prog_bar.pack(side="right")
        self.prog_bar.set(0)

        # ═══════════════════════════════════════════════════════════════════
        # TASK LIST — scrollable, inside the glass card
        # ═══════════════════════════════════════════════════════════════════
        self.scroll = ctk.CTkScrollableFrame(self.outer,
            fg_color="transparent", corner_radius=0,
            scrollbar_button_color=c["scroll"],
            scrollbar_button_hover_color=c["scroll_h"])
        self.scroll.pack(fill="both", expand=True, padx=S(3), pady=(S(1), 0))

        self._render()

        # ═══════════════════════════════════════════════════════════════════
        # INPUT BAR — frosted glass input
        # ═══════════════════════════════════════════════════════════════════
        iw = ctk.CTkFrame(self.outer, fg_color="transparent")
        iw.pack(fill="x", padx=S(4), pady=(S(2), S(4)))

        ic = ctk.CTkFrame(iw, fg_color=c["glass_2"],
            corner_radius=CR_INNER, border_width=1,
            border_color=c["glass_edge"])
        ic.pack(fill="x")

        ctk.CTkLabel(ic, text="+", font=_f(20, "bold"),
            text_color=c["accent"], width=20
        ).pack(side="left", padx=(S(5), S(2)), pady=S(3))

        self.entry = ctk.CTkEntry(ic,
            placeholder_text="What needs to be done?",
            font=_f(13), fg_color="transparent", border_width=0,
            text_color=c["text_2"],
            placeholder_text_color=c["text_4"], height=40)
        self.entry.pack(side="left", fill="x", expand=True,
            padx=(0, S(2)), pady=S(1))
        self.entry.bind("<Return>", self._add)

        self.add_btn = ctk.CTkButton(ic, text="Add",
            width=54, height=30, font=_f(12, "bold"),
            fg_color=c["accent"], hover_color=c["accent_h"],
            text_color=c["accent_text"], corner_radius=CR_BTN,
            command=self._add)
        self.add_btn.pack(side="right", padx=S(2), pady=S(2))

    # ── Settings ──────────────────────────────────────────────────────────

    def _build_settings(self):
        c = self.c
        frm = self.settings_panel

        row = ctk.CTkFrame(frm, fg_color="transparent")
        row.pack(fill="x", padx=S(5), pady=(S(4), S(1)))
        ctk.CTkLabel(row, text="🚀  Start with Windows",
            font=_f(12), text_color=c["text_2"]).pack(side="left")
        self.startup_sw = ctk.CTkSwitch(row, text="", width=42,
            fg_color=c["glass_3"], progress_color=c["accent"],
            button_color="#FFFFFF", button_hover_color="#F0F0F0",
            command=self._toggle_startup)
        if is_startup_enabled():
            self.startup_sw.select()
        self.startup_sw.pack(side="right")

        ctk.CTkLabel(frm,
            text="⌨  Ctrl+N  Add   ·   Ctrl+D  Theme   ·   Ctrl+T  Pin",
            font=_f(9), text_color=c["text_4"]
        ).pack(padx=S(5), pady=(S(1), S(4)))

    # ══════════════════════════════════════════════════════════════════════
    #  CLOCK
    # ══════════════════════════════════════════════════════════════════════

    def _clock_tick(self):
        if not self._alive: return
        now = datetime.now()
        self.clock.configure(text=now.strftime("%H:%M"))
        self.clock_s.configure(text=now.strftime(":%S"))
        self.root.after(CLOCK_UPDATE_MS, self._clock_tick)

    # ══════════════════════════════════════════════════════════════════════
    #  TIMER — ring drawn on glass
    # ══════════════════════════════════════════════════════════════════════

    def _fmt(self, s):
        m, sec = divmod(max(0, s), 60)
        return f"{m:02d}:{sec:02d}"

    def _draw_ring(self):
        c = self.c
        cv = self.ring
        cv.configure(bg=c["glass_2"])
        cv.delete("all")
        cx, cy, r, lw = 32, 32, 26, 4

        # Track — frosted
        cv.create_oval(cx-r, cy-r, cx+r, cy+r,
            outline=c["glass_3"], width=lw)

        # Progress
        p = self._tl / self._tt if self._tt > 0 else 1
        cv.create_arc(cx-r, cy-r, cx+r, cy+r,
            start=90, extent=-(p * 360),
            outline=c["accent"], width=lw, style="arc")

        # Center
        mins = math.ceil(self._tl / 60)
        cv.create_text(cx, cy, text=str(mins),
            font=("Segoe UI", 14, "bold"),
            fill=c["text_1"])

    def _t_toggle(self):
        if self._tr:
            self._tr = False
            self.start_btn.configure(text="▶  Resume")
            if self._ta: self.root.after_cancel(self._ta)
        else:
            self._tr = True
            self.start_btn.configure(text="⏸  Pause")
            self._t_tick()

    def _t_tick(self):
        if not self._tr or not self._alive: return
        self._tl -= 1
        self.timer_lbl.configure(text=self._fmt(self._tl))
        self._draw_ring()
        if self._tl <= 0:
            self._tr = False
            self.start_btn.configure(text="▶  Start")
            send_task_reminder("Focus session complete! 🎉")
            return
        self._ta = self.root.after(1000, self._t_tick)

    def _t_reset(self):
        self._tr = False
        self._tl = self._tt
        self.start_btn.configure(text="▶  Start")
        if self._ta: self.root.after_cancel(self._ta)
        self.timer_lbl.configure(text=self._fmt(self._tl))
        self._draw_ring()

    def _t_set(self, mins):
        self._tr = False
        self._tt = mins * 60
        self._tl = self._tt
        self.start_btn.configure(text="▶  Start")
        if self._ta: self.root.after_cancel(self._ta)
        self.timer_lbl.configure(text=self._fmt(self._tl))
        self._draw_ring()

    # ══════════════════════════════════════════════════════════════════════
    #  TABS
    # ══════════════════════════════════════════════════════════════════════

    def _switch_tab(self, n):
        if n == self.tab: return
        self.tab = n
        c = self.c
        for k, btn in self.tabs.items():
            a = k == n
            btn.configure(
                fg_color=c["glass_1"] if a else "transparent",
                text_color=c["text_1"] if a else c["text_4"])
        self._render()

    # ══════════════════════════════════════════════════════════════════════
    #  TASK LIST — glass-consistent items
    # ══════════════════════════════════════════════════════════════════════

    def _render(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        items = self.tasks.get(self.tab, [])
        c = self.c

        total = len(items)
        done = sum(1 for t in items if t.get("done"))
        if total > 0:
            self.prog_lbl.configure(text=f"{done} of {total} complete")
            self.prog_bar.set(done / total)
        else:
            self.prog_lbl.configure(text="")
            self.prog_bar.set(0)

        if not items:
            ef = ctk.CTkFrame(self.scroll, fg_color="transparent")
            ef.pack(fill="both", expand=True, pady=S(10))
            ctk.CTkLabel(ef, text="✎", font=_f(34),
                text_color=c["text_4"]).pack()
            ctk.CTkLabel(ef, text="No tasks yet",
                font=_f(16, "bold"), text_color=c["text_3"]
            ).pack(pady=(S(2), S(1)))
            ctk.CTkLabel(ef, text="Press Ctrl+N or type below",
                font=_f(12), text_color=c["text_4"]).pack()
            return

        for i, t in enumerate(items):
            self._task_row(i, t)

    def _task_row(self, idx, task):
        c = self.c
        done = task.get("done", False)

        # Row — frosted hover area with large radius
        row = ctk.CTkFrame(self.scroll, fg_color="transparent",
            corner_radius=CR_BTN, height=48)
        row.pack(fill="x", pady=1, padx=S(2))
        row.pack_propagate(False)
        row._tid = task["id"]

        # Hover
        def _on(e, r=row): r.configure(fg_color=c["hover"])
        def _off(e, r=row): r.configure(fg_color="transparent")
        row.bind("<Enter>", _on)
        row.bind("<Leave>", _off)

        # ── Checkbox — hand-drawn, frosted ────────────────────────────────
        CS = 22
        cv = tk.Canvas(row, width=CS, height=CS,
            bg=c["glass_1"], highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(side="left", padx=(S(2), S(3)), pady=S(3))

        if done:
            # Filled green circle
            cv.create_oval(0, 0, CS, CS, fill=c["green"],
                outline=c["green"], width=0)
            # Hand-drawn checkmark with rounded caps
            cv.create_line(5.5, 11, 9, 15, fill="#FFF",
                width=2, capstyle="round")
            cv.create_line(9, 15, 16.5, 6.5, fill="#FFF",
                width=2, capstyle="round")
        else:
            # Frosted empty circle
            cv.create_oval(1.5, 1.5, CS-1.5, CS-1.5, fill="",
                outline=c["glass_edge_2"], width=1.8)

        cv.bind("<Button-1>", lambda e, tid=task["id"]: self._check(tid))

        # Hover preview: border turns green
        def _cv_on(e, canvas=cv, d=done):
            canvas.configure(bg=c["hover"])
            if not d:
                canvas.delete("all")
                canvas.create_oval(1.5, 1.5, CS-1.5, CS-1.5, fill="",
                    outline=c["green"], width=1.8)
        def _cv_off(e, canvas=cv, d=done):
            canvas.configure(bg=c["glass_1"])
            if not d:
                canvas.delete("all")
                canvas.create_oval(1.5, 1.5, CS-1.5, CS-1.5, fill="",
                    outline=c["glass_edge_2"], width=1.8)

        cv.bind("<Enter>", lambda e: (_on(e), _cv_on(e)))
        cv.bind("<Leave>", lambda e: (_off(e), _cv_off(e)))

        # ── Text ──────────────────────────────────────────────────────────
        tc = c["text_4"] if done else c["text_2"]
        lbl = ctk.CTkLabel(row, text=task["text"],
            font=_f(13) if not done
                 else ctk.CTkFont(family="Segoe UI",
                                  size=13, overstrike=True),
            text_color=tc, anchor="w", cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True,
            padx=(0, S(1)), pady=S(2))
        lbl.bind("<Double-Button-1>",
            lambda e, tid=task["id"]: self._edit(tid))
        lbl.bind("<Enter>", _on)
        lbl.bind("<Leave>", _off)

        # ── Delete — appears on hover, frosted red ────────────────────────
        db = ctk.CTkButton(row, text="×", width=26, height=26,
            font=_f(15), fg_color="transparent",
            hover_color=c["red_soft"], text_color=c["glass_1"],
            corner_radius=CR_CHECK,
            command=lambda tid=task["id"]: self._rm(tid))
        db._is_del = True
        db.pack(side="right", padx=(0, S(2)), pady=S(2))

        # Show/hide delete on row hover
        def _show(e, r=row, btn=db):
            r.configure(fg_color=c["hover"])
            btn.configure(text_color=c["text_3"])
        def _hide(e, r=row, btn=db):
            r.configure(fg_color="transparent")
            btn.configure(text_color=c["glass_1"])

        row.bind("<Enter>", _show)
        row.bind("<Leave>", _hide)
        lbl.bind("<Enter>", _show)
        lbl.bind("<Leave>", _hide)

        # Drag
        for w in [row, lbl]:
            w.bind("<ButtonPress-1>", lambda e, i=idx: self._ds(e, i))
            w.bind("<B1-Motion>", lambda e: None)
            w.bind("<ButtonRelease-1>", self._de)

    # ══════════════════════════════════════════════════════════════════════
    #  TASK ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _add(self, e=None):
        txt = self.entry.get().strip()
        if not txt: return
        self.tasks[self.tab].append(create_task(txt[:MAX_TASK_LENGTH]))
        self._dirty = True
        self.entry.delete(0, "end")
        self._render()

    def _check(self, tid):
        for t in self.tasks[self.tab]:
            if t["id"] == tid:
                toggle_task(t)
                self._dirty = True; break
        self._render()

    def _rm(self, tid):
        self.tasks[self.tab] = [
            t for t in self.tasks[self.tab] if t["id"] != tid]
        self._dirty = True
        self._render()

    def _edit(self, tid):
        task = next((t for t in self.tasks[self.tab]
                     if t["id"] == tid), None)
        if not task: return
        c = self.c

        for row in self.scroll.winfo_children():
            if hasattr(row, "_tid") and row._tid == tid:
                for ch in row.winfo_children():
                    if isinstance(ch, ctk.CTkLabel):
                        try:
                            if ch.cget("text") == task["text"]:
                                ch.destroy()
                                ent = ctk.CTkEntry(row, font=_f(13),
                                    fg_color=c["glass_2"],
                                    text_color=c["text_1"],
                                    border_width=1,
                                    border_color=c["accent"],
                                    corner_radius=CR_CHECK, height=32)
                                ent.insert(0, task["text"])
                                ent.pack(side="left", fill="x",
                                    expand=True, padx=(0, S(1)),
                                    pady=S(1))
                                ent.focus_set()
                                ent.select_range(0, "end")

                                def save(e=None, _t=tid, _e=ent):
                                    new = _e.get().strip()
                                    if new:
                                        for tk_ in self.tasks[self.tab]:
                                            if tk_["id"] == _t:
                                                edit_task(tk_,
                                                    new[:MAX_TASK_LENGTH])
                                                self._dirty = True; break
                                    self._render()

                                ent.bind("<Return>", save)
                                ent.bind("<Escape>",
                                    lambda e: self._render())
                                ent.bind("<FocusOut>", save)
                                return
                        except: pass
                break

    def _ds(self, e, i): self._drag = {"i": i, "y": e.y_root}
    def _de(self, e):
        if not self._drag: return
        dy = e.y_root - self._drag["y"]
        steps = int(dy / 50)
        if steps:
            fi = self._drag["i"]
            ti = max(0, min(fi + steps,
                len(self.tasks[self.tab]) - 1))
            if ti != fi:
                reorder_tasks(self.tasks[self.tab], fi, ti)
                self._dirty = True; self._render()
        self._drag = None

    # ══════════════════════════════════════════════════════════════════════
    #  SETTINGS
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_settings(self):
        if self._settings_vis:
            self.settings_panel.pack_forget()
        else:
            self.settings_panel.pack(fill="x", padx=S(5), pady=(S(2), 0),
                before=self.timer_card)
        self._settings_vis = not self._settings_vis

    def _toggle_dark(self):
        d = not self.settings.get("dark_mode", False)
        self.settings["dark_mode"] = d
        self._dirty = True
        save_tasks(self.tasks)
        save_settings(self.settings)
        self._alive = False; self._tr = False
        self.root.destroy()
        self._alive = True
        self.__init__()

    def _toggle_pin(self):
        on = not self.settings.get("always_on_top", False)
        self.settings["always_on_top"] = on
        self.root.wm_attributes("-topmost", on)
        self.pin_btn.configure(
            text_color=self.c["accent"] if on else self.c["text_3"])
        self._dirty = True

    def _toggle_startup(self):
        if self.startup_sw.get(): enable_startup()
        else: disable_startup()
        self.settings["start_with_windows"] = bool(self.startup_sw.get())
        self._dirty = True

    # ══════════════════════════════════════════════════════════════════════
    #  PERSISTENCE
    # ══════════════════════════════════════════════════════════════════════

    def _save_loop(self):
        if not self._alive: return
        if self._dirty:
            save_tasks(self.tasks); save_settings(self.settings)
            self._dirty = False
        self.root.after(AUTO_SAVE_INTERVAL_MS, self._save_loop)

    def _reminder_loop(self):
        if not self._alive: return
        for sec in ["today", "week"]:
            for t in get_due_reminders(self.tasks.get(sec, [])):
                send_task_reminder(t["text"])
                clear_reminder(t); self._dirty = True
        self.root.after(NOTIFICATION_CHECK_INTERVAL_MS, self._reminder_loop)

    def _on_close(self):
        self._alive = False; self._tr = False
        try:
            self.settings["window_x"] = self.root.winfo_x()
            self.settings["window_y"] = self.root.winfo_y()
        except: pass
        save_tasks(self.tasks); save_settings(self.settings)
        self.root.destroy()

    def run(self):
        self.root.mainloop()
