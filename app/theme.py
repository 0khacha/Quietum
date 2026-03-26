"""
theme.py — Premium color palettes for Quietum.
Carefully curated warm neutral + accent colors.
"""


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTES
# ══════════════════════════════════════════════════════════════════════════════

LIGHT = {
    "bg":               "#e3ded8",
    "bg_secondary":     "#EFEBE5",
    "bg_card":          "#e3ded8",
    "bg_card_hover":    "#FBF8F5",
    "bg_input":         "#FFFFFF",
    "bg_done":          "#F2EFEB",

    "text":             "#1A1816",
    "text_secondary":   "#7A756E",
    "text_muted":       "#AEA8A0",
    "text_done":        "#C0BAB2",

    "accent":           "#C27B45",
    "accent_hover":     "#A8653A",
    "accent_soft":      "#F2E4D6",

    "green":            "#5BA65B",
    "green_soft":       "#E4F2E4",
    "red":              "#D05050",
    "red_soft":         "#F8E4E4",

    "border":           "#E4DFD8",
    "border_focus":     "#C27B45",

    "timer_ring":       "#C27B45",
    "timer_bg":         "#EFEBE5",
    "timer_text":       "#1A1816",

    "mode": "light",
}

DARK = {
    "bg":               "#161412",
    "bg_secondary":     "#1E1C19",
    "bg_card":          "#242220",
    "bg_card_hover":    "#2C2A28",
    "bg_input":         "#242220",
    "bg_done":          "#1C1A18",

    "text":             "#E8E4DE",
    "text_secondary":   "#908A82",
    "text_muted":       "#5A5650",
    "text_done":        "#4A4640",

    "accent":           "#D4935C",
    "accent_hover":     "#E0A87C",
    "accent_soft":      "#2E241C",

    "green":            "#6BBF6B",
    "green_soft":       "#1C2E1C",
    "red":              "#E06060",
    "red_soft":         "#2E1C1C",

    "border":           "#2E2C2A",
    "border_focus":     "#D4935C",

    "timer_ring":       "#D4935C",
    "timer_bg":         "#1E1C19",
    "timer_text":       "#E8E4DE",

    "mode": "dark",
}


def get_theme(dark_mode: bool) -> dict:
    """Return the appropriate theme palette."""
    return DARK if dark_mode else LIGHT
