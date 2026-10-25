"""RAPHA visual design tokens (styling only - no application logic).

Palette: soft neutrals + one accent (RAPHA green) + deep teal for primary
actions and headings.  Red appears only for delete / error states.
"glass" colours are solid colours computed by blending a white tint over the
backdrop's average colour, because Tk widgets cannot be translucent.
"""

RAPHA_GREEN = "#2EAA4F"
DEEP_TEAL = "#0B5E6E"
TAGLINE = "Technology organized around the art of healing."
BRAND = "RAPHA"
BRAND_FULL = "RAPHA – Hospital Management System"

# 8px spacing grid
GRID = 8
RADIUS_PANEL = 12
RADIUS_INPUT = 8

# --- backdrop (blurred abstract blobs): base colour + blob colours ---------
BACKDROP = {
    "light": {"base": "#E3EBE8", "blobs": ["#C9DEDB", "#D3E4D2", "#F1EFE8", "#BFD6D6"]},
    "dark": {"base": "#0E191B", "blobs": ["#16302F", "#15291F", "#1A2528", "#12313A"]},
}

LIGHT = {
    # surfaces (60% white glass over the backdrop)
    "bg": "#E3EBE8",            # window / backdrop average
    "sidebar": "#F1F6F4",       # glass panels at the window edge
    "panel": "#F5F9F8",         # glass sheet holding the pages
    "card": "#FBFDFC",          # glass cards on the sheet
    "border": "#D5E1DE",
    "highlight": "#FFFFFF",     # faint top-edge highlight
    "input": "#FFFFFF",
    "chip": "#E9F1EF",
    # text
    "text": "#1B2B2E",
    "muted": "#566B6E",
    "primary": "#0B5E6E",        # fills: primary buttons
    "primary_hover": "#0F7387",
    "primary_text": "#0B5E6E",   # headings / links
    "accent": "#2EAA4F",         # RAPHA green (lines, fills)
    "success": "#2EAA4F",
    "success_text": "#1F7A38",
    "danger": "#C0392B",
    "danger_hover": "#A02F23",
    "danger_text": "#B03226",
    # sidebar items
    "sidebar_hover": "#E4EEEB",
    "sidebar_active": "#FFFFFF",
    "sidebar_text": "#2B4043",
    # tables
    "header": "#E4EDEA",
    "header_text": "#1B2B2E",
    "row_alt": "#F4F8F7",
    "row_hover": "#E7F0EE",
    "row_sel": "#D4EDD9",
    "row_sel_text": "#12301C",
    # canvas drawings
    "canvas_bg": "#FAFCFB",
    "node": "#FFFFFF",
    "node_line": "#0B5E6E",
    "node_hot": "#F2C14E",
    "node_found": "#2EAA4F",
    "node_miss": "#E6ECEA",
    "collide": "#F6E7C8",
    "faint": "#C3D1CE",
    "pruned": "#E1E8E6",
    "visited": "#CFE6E3",
    "arrow": "#8FA3A1",
    "on_fill": "#14262A",        # text drawn on coloured fills
}

DARK = {
    "bg": "#0E191B",
    "sidebar": "#142326",
    "panel": "#132024",
    "card": "#1A2C30",
    "border": "#2B4147",
    "highlight": "#3A5359",
    "input": "#13232A",
    "chip": "#203539",
    "text": "#E7F0F0",
    "muted": "#9DB3B5",
    "primary": "#0F7A8D",
    "primary_hover": "#1590A5",
    "primary_text": "#6CC4D2",
    "accent": "#2EAA4F",
    "success": "#2EAA4F",
    "success_text": "#5FCB7C",
    "danger": "#C0392B",
    "danger_hover": "#A02F23",
    "danger_text": "#F0877B",
    "sidebar_hover": "#1D3338",
    "sidebar_active": "#233B40",
    "sidebar_text": "#D5E4E5",
    "header": "#223A3F",
    "header_text": "#E7F0F0",
    "row_alt": "#1E3135",
    "row_hover": "#27434A",
    "row_sel": "#2C5A3C",
    "row_sel_text": "#F2FAF4",
    "canvas_bg": "#15262A",
    "node": "#223A3F",
    "node_line": "#6CC4D2",
    "node_hot": "#D4A62E",
    "node_found": "#2EAA4F",
    "node_miss": "#2C4146",
    "collide": "#5A4A26",
    "faint": "#3A5258",
    "pruned": "#25383C",
    "visited": "#2B5A63",
    "arrow": "#7C9597",
    "on_fill": "#0E1B1E",
}

# Restrained, desaturated department colours (no red, no purple)
DEPT_COLORS = {
    "Cardiology": "#0B5E6E",
    "Orthopedics": "#8A6D3B",
    "Pediatrics": "#238041",
    "General Medicine": "#5B7083",
    "Neurology": "#5E7230",
    "ENT": "#2F7A76",
}
DEFAULT_DEPT_COLOR = "#6C7F82"

# Typography: Segoe UI with fallbacks (resolved at run time)
FONT_CANDIDATES = ["Segoe UI", "Helvetica", "Arial"]
SEMIBOLD_FAMILY = "Segoe UI Semibold"
MONO_FAMILY = "Consolas"
