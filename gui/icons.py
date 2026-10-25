"""Line icons and the RAPHA logo, drawn with Pillow.

Every icon uses the same 24-unit grid, a 2-unit stroke and rounded caps.
Images are drawn at 4x and down-sampled for smooth edges.  If Pillow is not
available the functions return None and the GUI simply shows text.
"""
import math
import os

try:
    from PIL import Image, ImageDraw
    AVAILABLE = True
except ImportError:          # pragma: no cover - the app still runs without icons
    AVAILABLE = False

from gui.gui_theme import DARK, LIGHT, RAPHA_GREEN

SUPERSAMPLE = 4
_cache = {}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _line(draw, points, width, color):
    """Polyline with rounded joins and caps."""
    draw.line(points, fill=color, width=width)
    radius = width / 2.0
    for x, y in points:       # a round dot at every vertex = round joins and caps
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _finish(image, size):
    return image.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------------------
# logo: heart outline with a heartbeat line inside
# ---------------------------------------------------------------------------
def make_logo(size=256, color=RAPHA_GREEN, stroke=None):
    """Return an RGBA image of the RAPHA heart-with-pulse logo."""
    if not AVAILABLE:
        return None
    stroke = stroke or max(2, round(size / 20.0))
    big = size * SUPERSAMPLE
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    width = int(stroke * SUPERSAMPLE)
    # classic heart curve, scaled to fit with a margin for the stroke
    margin = big * 0.12 + width / 2.0
    scale = (big - 2 * margin) / 32.0
    points = []
    steps = 360
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        points.append((big / 2 + x * scale, margin + (13.5 - y) * scale + 0.5 * scale))
    _line(draw, points, width, color)
    # heartbeat line across the middle of the heart
    cx, cy = big / 2, big * 0.47
    pulse = [(-11, 1), (-5, 1), (-2.5, -4.5), (1, 6.5), (4, -2), (6, 1), (11, 1)]
    _line(draw, [(cx + x * scale, cy + y * scale) for x, y in pulse], width, color)
    return _finish(image, size)


# ---------------------------------------------------------------------------
# icon set (24-unit grid)
# ---------------------------------------------------------------------------
def _draw_icon(name, draw, k, width, color):
    def p(*pts):
        return [(x * k, y * k) for x, y in zip(pts[::2], pts[1::2])]

    def box(x0, y0, x1, y1):
        return (x0 * k, y0 * k, x1 * k, y1 * k)

    def rrect(x0, y0, x1, y1, r=2):
        draw.rounded_rectangle(box(x0, y0, x1, y1), radius=r * k, outline=color, width=width)

    def circle(cx, cy, r):
        draw.ellipse(box(cx - r, cy - r, cx + r, cy + r), outline=color, width=width)

    def stroke(*pts):
        _line(draw, p(*pts), width, color)

    if name == "dashboard":
        for x0, y0 in ((3, 3), (14, 3), (3, 14), (14, 14)):
            rrect(x0, y0, x0 + 7, y0 + 7)
    elif name == "patients":
        circle(9, 8, 3.5)
        draw.arc(box(2.5, 14, 15.5, 27), 180, 360, fill=color, width=width)
        circle(17.5, 9, 2.6)
        draw.arc(box(14.5, 14.5, 22.5, 22.5), 200, 340, fill=color, width=width)
    elif name == "add":
        circle(12, 12, 9)
        stroke(12, 8, 12, 16)
        stroke(8, 12, 16, 12)
    elif name == "lookup":
        circle(10, 10, 6.5)
        stroke(15, 15, 20.5, 20.5)
    elif name == "range":
        stroke(4, 12, 20, 12)
        stroke(4, 7, 4, 17)
        stroke(20, 7, 20, 17)
        stroke(9, 9, 12, 12, 9, 15)
    elif name == "report":
        rrect(5, 3, 19, 21)
        stroke(8.5, 9, 15.5, 9)
        stroke(8.5, 13, 15.5, 13)
        stroke(8.5, 17, 12.5, 17)
    elif name == "hash":
        stroke(9.5, 4, 7.5, 20)
        stroke(16.5, 4, 14.5, 20)
        stroke(4, 9, 20, 9)
        stroke(4, 15, 20, 15)
    elif name == "tree":
        circle(12, 5.5, 2.6)
        circle(5.5, 18, 2.6)
        circle(18.5, 18, 2.6)
        stroke(11, 8, 6.5, 15.5)
        stroke(13, 8, 17.5, 15.5)
    elif name == "about":
        circle(12, 12, 9)
        stroke(12, 11, 12, 17)
        stroke(12, 7.5, 12, 7.6)
    elif name == "calendar":
        rrect(4, 5, 20, 20)
        stroke(4, 10, 20, 10)
        stroke(8.5, 3, 8.5, 7)
        stroke(15.5, 3, 15.5, 7)
    elif name == "building":
        rrect(5, 3.5, 19, 21)
        stroke(9, 8, 9, 8.1)
        stroke(15, 8, 15, 8.1)
        stroke(9, 12, 9, 12.1)
        stroke(15, 12, 15, 12.1)
        stroke(10, 21, 10, 17, 14, 17, 14, 21)
    elif name == "gauge":
        draw.arc(box(3, 5, 21, 23), 180, 360, fill=color, width=width)
        stroke(4, 14, 20, 14)
        stroke(12, 14, 16, 9)
    elif name == "export":
        stroke(12, 4, 12, 15)
        stroke(7.5, 10.5, 12, 15, 16.5, 10.5)
        stroke(5, 15, 5, 20, 19, 20, 19, 15)
    elif name == "play":
        stroke(8, 5, 8, 19, 19, 12, 8, 5)


def make_icon(name, color, px=60):
    """RGBA image of one icon (px x px)."""
    if not AVAILABLE:
        return None
    key = (name, color, px)
    if key not in _cache:
        big = px * SUPERSAMPLE
        image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        k = big / 24.0
        _draw_icon(name, draw, k, max(1, int(round(2 * k))), color)
        _cache[key] = _finish(image, px)
    return _cache[key]


def ctk_icon(name, role="text", size=18):
    """CTkImage with light and dark variants, or None without Pillow.

    role picks the colour from the palette: text, muted, primary, white.
    """
    if not AVAILABLE:
        return None
    import customtkinter as ctk
    key = ("ctk", name, role, size)
    if key not in _cache:
        keys = {"text": "sidebar_text", "muted": "muted", "primary": "primary_text",
                "white": None}
        palette_key = keys[role]
        light = "#FFFFFF" if palette_key is None else LIGHT[palette_key]
        dark = "#FFFFFF" if palette_key is None else DARK[palette_key]
        px = size * 3
        _cache[key] = ctk.CTkImage(light_image=make_icon(name, light, px),
                                   dark_image=make_icon(name, dark, px),
                                   size=(size, size))
    return _cache[key]


def logo_image(size, role="light"):
    """CTkImage of the logo (same green in both modes)."""
    if not AVAILABLE:
        return None
    import customtkinter as ctk
    key = ("logo", size)
    if key not in _cache:
        image = make_logo(size * 3)
        _cache[key] = ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
    return _cache[key]


def ensure_assets(folder):
    """Create assets/rapha.png and assets/rapha.ico if they do not exist yet.

    Returns the path of the .ico file (or None when it could not be created).
    """
    if not AVAILABLE:
        return None
    try:
        os.makedirs(folder, exist_ok=True)
        png_path = os.path.join(folder, "rapha.png")
        ico_path = os.path.join(folder, "rapha.ico")
        if not os.path.exists(png_path) or not os.path.exists(ico_path):
            make_logo(256).save(png_path)
            make_logo(256).save(ico_path, sizes=[(16, 16), (24, 24), (32, 32),
                                                 (48, 48), (64, 64), (128, 128), (256, 256)])
        return ico_path
    except Exception:
        return None
