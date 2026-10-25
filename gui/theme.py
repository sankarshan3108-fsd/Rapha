"""Colours, fonts and spacing for light and dark mode.

RESTYLE: the actual design tokens now live in gui/gui_theme.py; this module
keeps the same function names the pages already use (pal, pair, font ...).
"""
import tkinter.font as tkfont

import customtkinter as ctk

from gui import gui_theme
from gui.gui_theme import DARK, DEFAULT_DEPT_COLOR, DEPT_COLORS, LIGHT

_mode = {"name": "light"}
FONT_FAMILY = "Segoe UI"
_semibold = {"ok": False}


def init_fonts():
    """Pick Segoe UI (fallback Helvetica / Arial); detect the semibold face."""
    global FONT_FAMILY
    families = tkfont.families()
    for candidate in gui_theme.FONT_CANDIDATES:
        if candidate in families:
            FONT_FAMILY = candidate
            break
    _semibold["ok"] = FONT_FAMILY == "Segoe UI" and gui_theme.SEMIBOLD_FAMILY in families


def font(size=11, weight="normal"):
    """Font tuple understood by both Tk and CustomTkinter.

    'bold' is rendered as Segoe UI Semibold (lighter, more refined) when present.
    """
    if weight == "bold" and _semibold["ok"]:
        return (gui_theme.SEMIBOLD_FAMILY, size)
    return (FONT_FAMILY, size, weight)


def mono(size=10, weight="normal"):
    """Consolas, used for IDs and numbers so digits line up."""
    return (gui_theme.MONO_FAMILY, size, weight)


def mode():
    return _mode["name"]


def set_mode(name):
    """Switch palette and CustomTkinter appearance ('light' or 'dark')."""
    _mode["name"] = name
    ctk.set_appearance_mode(name)


def pal():
    """Current palette (dict of hex colours)."""
    return DARK if _mode["name"] == "dark" else LIGHT


def pair(name):
    """(light, dark) tuple that CustomTkinter switches automatically."""
    return (LIGHT[name], DARK[name])


def dept_color(department):
    return DEPT_COLORS.get(department, DEFAULT_DEPT_COLOR)


PAD = gui_theme.GRID * 2
RADIUS = gui_theme.RADIUS_PANEL

SCALE = [1.0]


def init_scale(root):
    """Remember the screen DPI scale so Canvas pixel sizes match CTk widgets."""
    SCALE[0] = root.winfo_fpixels("1i") / 96.0


def S(pixels):
    """Scale a pixel size for tk Canvas drawings."""
    return int(round(pixels * SCALE[0]))
