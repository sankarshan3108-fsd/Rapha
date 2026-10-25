"""Frosted-glass helpers: blurred backdrop, glass colours and the splash screen.

Tk widgets cannot be translucent, so glass is simulated:
  * the window shows a blurred, low-contrast backdrop generated with Pillow;
  * panels use solid colours that are a white tint blended over the backdrop's
    average colour (see gui_theme.py), with a 1px border and a top highlight.
Without Pillow every function degrades to the same design in flat colours.
"""
import os
import tkinter as tk

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk
    AVAILABLE = True
except ImportError:          # pragma: no cover
    AVAILABLE = False

from gui.gui_theme import BACKDROP, BRAND, DARK, LIGHT, RAPHA_GREEN, TAGLINE
from gui import icons


# ---------------------------------------------------------------------------
# colour helpers
# ---------------------------------------------------------------------------
def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


def blend(tint, base, alpha):
    """Colour of `tint` at `alpha` (0-1) laid over `base` (both hex)."""
    t, b = hex_to_rgb(tint), hex_to_rgb(base)
    return rgb_to_hex(tuple(alpha * t[i] + (1 - alpha) * b[i] for i in range(3)))


def glass_color(mode, alpha=0.6, tint="#FFFFFF"):
    """Solid colour that reads as `alpha` white glass over the backdrop average."""
    base = BACKDROP[mode]["base"]
    if mode == "dark":
        tint = "#9FC4C8" if tint == "#FFFFFF" else tint
        alpha = alpha * 0.22
    return blend(tint, base, alpha)


# ---------------------------------------------------------------------------
# backdrop
# ---------------------------------------------------------------------------
BLOBS = [(0.12, 0.18, 0.42), (0.88, 0.12, 0.38), (0.78, 0.92, 0.46),
         (0.08, 0.90, 0.30), (0.50, 0.50, 0.28)]


def make_backdrop(width, height, mode="light"):
    """Blurred abstract blobs (muted teal, sage, off-white). Built at 1/6 size
    and scaled up, which is fast and keeps the look soft."""
    if not AVAILABLE:
        return None
    spec = BACKDROP[mode]
    small_w, small_h = max(8, width // 6), max(8, height // 6)
    image = Image.new("RGB", (small_w, small_h), spec["base"])
    draw = ImageDraw.Draw(image)
    colors = spec["blobs"]
    for index, (fx, fy, fr) in enumerate(BLOBS):
        radius = fr * min(small_w, small_h) * 1.4
        cx, cy = fx * small_w, fy * small_h
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                     fill=colors[index % len(colors)])
    image = image.filter(ImageFilter.GaussianBlur(min(small_w, small_h) * 0.18))
    return image.resize((width, height), Image.BICUBIC)


class Backdrop:
    """Keeps a backdrop label behind everything in the root window.

    Regenerates (debounced) when the window is resized or the mode changes.
    """

    DEBOUNCE_MS = 150

    def __init__(self, root, mode="light"):
        self.root = root
        self.mode = mode
        self.job = None
        self.size = None
        self.photo = None
        self.label = tk.Label(root, bd=0, highlightthickness=0, bg=BACKDROP[mode]["base"])
        self.label.place(x=0, y=0, relwidth=1, relheight=1)
        self.label.lower()
        root.bind("<Configure>", self._on_configure, add="+")

    def _on_configure(self, event):
        if event.widget is not self.root or not AVAILABLE:
            return
        if self.job is not None:
            self.root.after_cancel(self.job)
        self.job = self.root.after(self.DEBOUNCE_MS, self.apply)

    def set_mode(self, mode):
        self.mode = mode
        self.size = None
        self.label.configure(bg=BACKDROP[mode]["base"])
        self.apply()

    def apply(self):
        self.job = None
        if not AVAILABLE:
            return
        width, height = self.root.winfo_width(), self.root.winfo_height()
        if width < 50 or height < 50 or (width, height, self.mode) == self.size:
            return
        try:
            self.photo = ImageTk.PhotoImage(make_backdrop(width, height, self.mode))
            self.label.configure(image=self.photo)
            self.label.lower()
            self.size = (width, height, self.mode)
        except Exception:        # never let decoration break the app
            pass


# ---------------------------------------------------------------------------
# splash screen
# ---------------------------------------------------------------------------
FONT_FILES = {
    "regular": ["segoeui.ttf", "arial.ttf"],
    "semibold": ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"],
    "italic": ["segoeuii.ttf", "ariali.ttf"],
}


def _font(kind, size):
    folder = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for name in FONT_FILES[kind]:
        try:
            return ImageFont.truetype(os.path.join(folder, name), size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def make_splash_image(width, height, scale=1.0):
    """Backdrop plus a centred frosted-glass card with logo, name and tagline."""
    base = make_backdrop(width, height, "light")
    image = base.convert("RGBA")
    card_w, card_h = int(400 * scale), int(250 * scale)
    x0, y0 = (width - card_w) // 2, (height - card_h) // 2
    box = (x0, y0, x0 + card_w, y0 + card_h)
    radius = int(14 * scale)
    # frost: blur the backdrop behind the card, then lay white glass on it
    frosted = base.crop(box).filter(ImageFilter.GaussianBlur(8 * scale)).convert("RGBA")
    frosted = Image.alpha_composite(frosted, Image.new("RGBA", frosted.size, (255, 255, 255, 158)))
    mask = Image.new("L", frosted.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, fill=255)
    image.paste(frosted, (x0, y0), mask)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=radius, outline=(255, 255, 255, 230), width=max(1, int(scale)))
    draw.rounded_rectangle((x0 - 1, y0 - 1, x0 + card_w, y0 + card_h), radius=radius + 1,
                           outline=(190, 208, 204, 255), width=1)
    draw.line((x0 + radius, y0 + 2, x0 + card_w - radius, y0 + 2), fill=(255, 255, 255, 255), width=1)

    cx = width // 2
    logo = icons.make_logo(int(64 * scale))
    image.alpha_composite(logo, (cx - logo.width // 2, y0 + int(24 * scale)))
    # name in bold capitals with a little letter spacing
    name_font = _font("semibold", int(28 * scale))
    spacing = int(5 * scale)
    widths = [draw.textlength(ch, font=name_font) for ch in BRAND]
    total = sum(widths) + spacing * (len(BRAND) - 1)
    x = cx - total / 2
    y = y0 + int(100 * scale)
    for ch, w in zip(BRAND, widths):
        draw.text((x, y), ch, font=name_font, fill=hex_to_rgb(LIGHT["text"]))
        x += w + spacing
    sub = "Hospital Management System"
    sub_font = _font("regular", int(13 * scale))
    draw.text((cx, y0 + int(148 * scale)), sub, font=sub_font, fill=hex_to_rgb(LIGHT["muted"]), anchor="mt")
    draw.line((cx - int(36 * scale), y0 + int(182 * scale), cx + int(36 * scale), y0 + int(182 * scale)),
              fill=hex_to_rgb(RAPHA_GREEN), width=max(1, int(scale)))
    tag_font = _font("italic", int(12 * scale))
    draw.text((cx, y0 + int(200 * scale)), TAGLINE, font=tag_font, fill=hex_to_rgb(LIGHT["muted"]), anchor="mt")
    return image.convert("RGB")


class Splash:
    """Borderless splash window shown while the data loads, then fades out.

    run(loader) calls loader() once (after the splash is painted), keeps the
    splash up for at least `min_ms`, fades it out and returns loader's result.
    Only decoration - the loader does exactly what it did before.
    """

    LOGICAL_SIZE = (560, 340)

    def __init__(self, icon_path=None):
        import customtkinter as ctk      # CTk root keeps DPI behaviour identical to the app
        self.root = ctk.CTk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.title("RAPHA")
        scale = ctk.ScalingTracker.get_window_scaling(self.root)
        logical_w, logical_h = self.LOGICAL_SIZE
        pixel_w, pixel_h = int(logical_w * scale), int(logical_h * scale)
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = max(0, int((screen_w - logical_w) / 2))
        y = max(0, int((screen_h - logical_h) / 2) - 20)
        self.root.geometry("%dx%d+%d+%d" % (logical_w, logical_h, x, y))
        self.photo = None
        self.label = tk.Label(self.root, bd=0, highlightthickness=0, bg="#E3EBE8")
        if AVAILABLE:
            try:
                self.photo = ImageTk.PhotoImage(make_splash_image(pixel_w, pixel_h, scale))
                self.label.configure(image=self.photo)
            except Exception:
                self.photo = None
        if self.photo is None:       # solid-colour fallback with the same text
            self.label.configure(text="RAPHA\nHospital Management System\n\n" + TAGLINE,
                                 fg=LIGHT["text"], font=("Segoe UI", 14), justify="center")
        self.label.place(x=0, y=0, relwidth=1, relheight=1)
        self.result = None
        self.error = None
        self.loaded = False
        self.time_up = False
        self.root.attributes("-alpha", 0.0)
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def run(self, loader, min_ms=2000):
        self.root.after(80, lambda: self._load(loader))
        self.root.after(min_ms, self._mark_time_up)
        self._fade(0.0, 1, 40)
        self.root.mainloop()
        if self.error is not None:
            raise self.error
        return self.result

    def _load(self, loader):
        try:
            self.result = loader()
        except Exception as error:      # re-raised after the splash closes
            self.error = error
        self.loaded = True
        self._maybe_close()

    def _mark_time_up(self):
        self.time_up = True
        self._maybe_close()

    def _maybe_close(self):
        if self.loaded and self.time_up:
            self._fade(1.0, -1, 30)

    def _fade(self, alpha, direction, delay):
        alpha = min(1.0, alpha + 0.12) if direction == 1 else alpha - 0.1
        try:
            self.root.attributes("-alpha", max(0.0, alpha))
        except tk.TclError:
            return
        if direction == 1 and alpha < 1.0:
            self.root.after(delay, lambda: self._fade(alpha, 1, delay))
        elif direction == -1:
            if alpha > 0:
                self.root.after(delay, lambda: self._fade(alpha, -1, delay))
            else:
                # cancel CustomTkinter's own pending callbacks so nothing fires after destroy
                for job in self.root.tk.call("after", "info"):
                    try:
                        self.root.after_cancel(job)
                    except Exception:
                        pass
                self.root.quit()
                self.root.destroy()
