"""Reusable GUI components: cards, KPI cards, styled table, toast, badge,
tooltip, algorithm-info panel, help button, date picker, profile card.

RESTYLE: appearance only (frosted-glass look, RAPHA palette).  The behaviour
of every component is unchanged.
"""
import calendar
import datetime
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from algorithm_info import ALGORITHM_INFO
from gui import icons, theme
from gui.theme import font, mono, pair, pal

# text colours need darker shades than fills to stay AA-readable
TEXT_ROLE = {"primary": "primary_text", "success": "success_text", "danger": "danger_text"}


# ---------------------------------------------------------------------------
# Basic building blocks
# ---------------------------------------------------------------------------
class Card(ctk.CTkFrame):
    """Glass card: light surface, 1px soft border and a faint top highlight."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color", pair("card"))
        kwargs.setdefault("border_color", pair("border"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", theme.RADIUS)
        super().__init__(parent, **kwargs)
        # faint highlight along the top edge (inside the rounded corners)
        highlight = ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=pair("highlight"))
        highlight.place(relx=0.03, y=1, relwidth=0.94)


def label(parent, text="", size=12, weight="normal", color="text", **kwargs):
    """CTkLabel with the theme font and a palette colour name."""
    kwargs.setdefault("justify", "left")
    return ctk.CTkLabel(parent, text=text, font=font(size, weight),
                        text_color=pair(TEXT_ROLE.get(color, color)), **kwargs)


def button(parent, text, command, kind="primary", width=110, icon=None, **kwargs):
    """Themed CTkButton. kind: primary (teal) | secondary (glass) | danger (red)."""
    colors = {
        "primary": (pair("primary"), pair("primary_hover"), "#FFFFFF", 0),
        "secondary": (pair("chip"), pair("row_hover"), pair("text"), 1),
        "danger": (pair("danger"), pair("danger_hover"), "#FFFFFF", 0),
    }[kind]
    if icon is not None:
        kwargs["image"] = icon
        kwargs["compound"] = "left"
    return ctk.CTkButton(parent, text=text, command=command, width=width,
                         height=32, corner_radius=theme.gui_theme.RADIUS_INPUT,
                         fg_color=colors[0], hover_color=colors[1], text_color=colors[2],
                         border_width=colors[3], border_color=pair("border"),
                         font=font(12, "bold"), **kwargs)


def set_border(widget, color):
    """Set an entry's idle border colour (restored when it loses focus)."""
    widget._idle_border = color
    widget.configure(border_color=color)


def entry(parent, placeholder="", width=200, **kwargs):
    """White-glass input with a 1px border that turns green on focus."""
    field = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                         height=32, corner_radius=theme.gui_theme.RADIUS_INPUT,
                         border_width=1, fg_color=pair("input"),
                         border_color=pair("border"), text_color=pair("text"),
                         font=font(12), placeholder_text_color=pair("muted"), **kwargs)
    field._idle_border = pair("border")
    field.bind("<FocusIn>", lambda e: field.configure(border_color=pair("accent")), add="+")
    field.bind("<FocusOut>", lambda e: field.configure(border_color=field._idle_border), add="+")
    return field


def dropdown(parent, values, variable=None, width=170, command=None):
    return ctk.CTkOptionMenu(parent, values=values, variable=variable, width=width,
                             height=32, corner_radius=theme.gui_theme.RADIUS_INPUT,
                             font=font(12), fg_color=pair("input"),
                             button_color=pair("chip"), button_hover_color=pair("row_hover"),
                             text_color=pair("text"), dropdown_font=font(12),
                             dropdown_fg_color=pair("card"), dropdown_text_color=pair("text"),
                             dropdown_hover_color=pair("row_hover"), command=command)


class Badge(ctk.CTkLabel):
    """Small coloured tag, e.g. the department name."""

    def __init__(self, parent, text, color):
        super().__init__(parent, text=" %s " % text, fg_color=color,
                         text_color="#FFFFFF", corner_radius=8,
                         font=font(11, "bold"), height=24)


class Chip(ctk.CTkFrame):
    """Summary chip: value over a small caption (numbers in Consolas)."""

    def __init__(self, parent, caption, value="-"):
        super().__init__(parent, fg_color=pair("chip"), corner_radius=theme.RADIUS,
                         border_width=1, border_color=pair("border"))
        self.value = ctk.CTkLabel(self, text=str(value), font=mono(16, "bold"),
                                  text_color=pair("primary_text"))
        self.value.pack(padx=16, pady=(8, 0))
        label(self, caption, 11, color="muted").pack(padx=16, pady=(0, 8))

    def set(self, value):
        self.value.configure(text=str(value))


class KPICard(Card):
    """Dashboard tile: thin green accent line, line icon, value, title, sub-text
    and an optional progress bar."""

    def __init__(self, parent, icon, title, color="primary"):
        super().__init__(parent)
        accent = ctk.CTkFrame(self, height=2, corner_radius=0, fg_color=pair("accent"))
        accent.place(relx=0.05, y=0, relwidth=0.9)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 0))
        badge = ctk.CTkLabel(top, text="" if icons.AVAILABLE else icon[:1].upper(),
                             image=icons.ctk_icon(icon, "primary", 20), width=40, height=40,
                             corner_radius=20, fg_color=pair("chip"),
                             text_color=pair("primary_text"), font=font(14, "bold"))
        badge.pack(side="left")
        self.value = ctk.CTkLabel(top, text="-", font=mono(22, "bold"), text_color=pair("text"))
        self.value.pack(side="right")
        label(self, title, 11, "bold", "muted").pack(anchor="w", padx=16, pady=(8, 0))
        self.sub = label(self, "", 11, color="muted", wraplength=168)
        self.sub.pack(anchor="w", padx=16, pady=(0, 8))
        self.bar = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                      progress_color=pair("accent"), fg_color=pair("border"))
        self.bar_shown = False

    def set(self, value, sub="", progress=None, bar_color=None):
        self.value.configure(text=str(value))
        self.sub.configure(text=sub)
        if progress is not None:
            if not self.bar_shown:
                self.bar.pack(fill="x", padx=16, pady=(0, 16))
                self.bar_shown = True
            self.bar.set(max(0.0, min(1.0, progress)))
            if bar_color:
                self.bar.configure(progress_color=bar_color)
        elif not self.bar_shown:
            ctk.CTkFrame(self, height=8, fg_color="transparent").pack()


# ---------------------------------------------------------------------------
# ttk styling + styled table
# ---------------------------------------------------------------------------
def apply_ttk_styles(root):
    """(Re)configure ttk styles for the current light/dark palette."""
    colors = pal()
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Med.Treeview", background=colors["card"],
                    fieldbackground=colors["card"], foreground=colors["text"],
                    rowheight=theme.S(32), borderwidth=0, font=font(10),
                    bordercolor=colors["card"], lightcolor=colors["card"],
                    darkcolor=colors["card"])
    style.map("Med.Treeview", background=[("selected", colors["row_sel"])],
              foreground=[("selected", colors["row_sel_text"])])
    style.configure("Med.Treeview.Heading", background=colors["header"],
                    foreground=colors["header_text"], font=font(10, "bold"),
                    relief="flat", padding=(8, 8), borderwidth=0,
                    bordercolor=colors["header"], lightcolor=colors["header"],
                    darkcolor=colors["header"])
    style.map("Med.Treeview.Heading", background=[("active", colors["row_hover"])])


class StyledTable(ctk.CTkFrame):
    """Treeview with alternating rows, hover, clickable sortable headers and a
    row counter.  Sorting itself is done by the page (merge sort)."""

    def __init__(self, parent, columns, widths, height=12, on_sort=None,
                 on_double_click=None):
        super().__init__(parent, fg_color="transparent")
        self.columns = columns
        self.on_sort = on_sort
        self.sort_column = None
        self.sort_desc = False
        self.row_index = 0
        self.base_tags = {}
        self.hover_item = None
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 height=height, style="Med.Treeview")
        for column, width in zip(columns, widths):
            self.tree.heading(column, text=column,
                              command=lambda c=column: self._header_click(c))
            self.tree.column(column, width=width, minwidth=40, anchor="w",
                             stretch=True)
        scroll = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.count_label = label(self, "0 rows", 11, color="muted")
        self.count_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda e: self._set_hover(None))
        if on_double_click:
            self.tree.bind("<Double-1>", lambda e: on_double_click())
        self.restyle()

    def restyle(self):
        """Apply palette colours to tags (call after a theme switch)."""
        colors = pal()
        self.tree.tag_configure("even", background=colors["card"])
        self.tree.tag_configure("odd", background=colors["row_alt"])
        self.tree.tag_configure("hover", background=colors["row_hover"])
        self.tree.tag_configure("group", background=colors["chip"],
                                foreground=colors["primary_text"], font=font(10, "bold"))

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self.row_index = 0
        self.base_tags = {}
        self.hover_item = None

    def add_row(self, values, parent="", group=False, open_=True):
        """Insert a row (or a group heading row) and return its item id."""
        if group:
            tags = ("group",)
        else:
            tags = ("even" if self.row_index % 2 == 0 else "odd",)
            self.row_index += 1
        item = self.tree.insert(parent, "end", values=values, tags=tags, open=open_)
        self.base_tags[item] = tags
        return item

    def set_rows(self, rows):
        self.clear()
        for row in rows:
            self.add_row(row)
        self.finish()

    def finish(self, noun="rows"):
        self.count_label.configure(text="%d %s" % (self.row_index, noun))

    def selected(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])["values"]

    # -- hover --
    def _on_motion(self, event):
        self._set_hover(self.tree.identify_row(event.y) or None)

    def _set_hover(self, item):
        if item == self.hover_item:
            return
        if self.hover_item in self.base_tags and self.tree.exists(self.hover_item):
            self.tree.item(self.hover_item, tags=self.base_tags[self.hover_item])
        self.hover_item = item
        if item in self.base_tags and "group" not in self.base_tags[item]:
            self.tree.item(item, tags=self.base_tags[item] + ("hover",))

    # -- sorting --
    def _header_click(self, column):
        if not self.on_sort:
            return
        if self.sort_column == column:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_column, self.sort_desc = column, False
        for name in self.columns:
            arrow = ""
            if name == self.sort_column:
                arrow = "  ▼" if self.sort_desc else "  ▲"
            self.tree.heading(name, text=name + arrow)
        self.on_sort(self.columns.index(column), self.sort_desc)

    def reset_sort_marks(self):
        self.sort_column = None
        for name in self.columns:
            self.tree.heading(name, text=name)


# ---------------------------------------------------------------------------
# Toast, tooltip
# ---------------------------------------------------------------------------
class Toast:
    """Small pop-up in the bottom-right corner of the window that fades out."""

    def __init__(self, root):
        self.root = root
        self.active = []

    def show(self, message, kind="success"):
        colors = {"success": "#237F3C", "error": "#B03226", "info": "#0B5E6E"}
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        try:
            window.attributes("-alpha", 0.0)
        except tk.TclError:
            pass
        frame = tk.Frame(window, bg=colors[kind])
        frame.pack()
        tk.Label(frame, text=message, bg=colors[kind], fg="white",
                 font=font(12, "bold"), padx=24, pady=16).pack()
        window.update_idletasks()
        self.active.append(window)
        index = len(self.active) - 1
        x = self.root.winfo_rootx() + self.root.winfo_width() - window.winfo_width() - 32
        y = self.root.winfo_rooty() + self.root.winfo_height() - 96 - index * (window.winfo_height() + 8)
        window.geometry("+%d+%d" % (x, y))
        self._fade(window, 0.0, 1)

    def _fade(self, window, alpha, direction):
        try:
            if not window.winfo_exists():
                return
            if direction == 1:
                alpha = min(0.95, alpha + 0.15)
                window.attributes("-alpha", alpha)
                if alpha >= 0.95:
                    window.after(2400, lambda: self._fade(window, alpha, -1))
                else:
                    window.after(25, lambda: self._fade(window, alpha, 1))
            else:
                alpha -= 0.1
                if alpha <= 0:
                    self._close(window)
                else:
                    window.attributes("-alpha", alpha)
                    window.after(30, lambda: self._fade(window, alpha, -1))
        except tk.TclError:
            self._close(window)

    def _close(self, window):
        if window in self.active:
            self.active.remove(window)
        try:
            window.destroy()
        except tk.TclError:
            pass


class Tooltip:
    """Floating text label shown near the mouse (used on canvases)."""

    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.label = tk.Label(self.window, bg="#1B2B2E", fg="white",
                              font=font(11), padx=8, pady=8, justify="left")
        self.label.pack()
        self.window.withdraw()

    def show(self, text, x_root, y_root):
        self.label.configure(text=text)
        self.window.geometry("+%d+%d" % (x_root + 16, y_root + 16))
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()


# ---------------------------------------------------------------------------
# Algorithm info panel and "?" help button
# ---------------------------------------------------------------------------
class InfoPanel(ctk.CTkScrollableFrame):
    """Right-hand glass panel with the 6 explanation sections for the current page."""

    def __init__(self, parent, width=340):
        super().__init__(parent, fg_color=pair("sidebar"), corner_radius=theme.RADIUS,
                         border_width=1, border_color=pair("border"), width=width)
        self.trace_label = None
        self.key = None

    def show(self, key, trace_text=None):
        """Rebuild the panel for a page key; trace_text fills 'Live Trace'."""
        for child in self.winfo_children():
            child.destroy()
        self.key = key
        info = ALGORITHM_INFO[key]
        label(self, "Algorithm Info", 16, "bold", "primary").pack(
            anchor="w", padx=16, pady=(16, 0))
        label(self, info["title"], 12, "bold", "muted", wraplength=290).pack(
            anchor="w", padx=16, pady=(0, 8))
        self._section("Algorithm Used", info["algorithm"])
        steps = "\n".join("%d. %s" % (i + 1, s) for i, s in enumerate(info["steps"]))
        self._section("How It Works", steps)
        self._section("Why This Algorithm?", info["why"])
        self._comparison(info["comparison"])
        self._section("Complexity", info["complexity"])
        self.trace_label = self._section("Live Trace", trace_text or info["trace"],
                                         mono_font=True)

    def set_trace(self, text):
        if self.trace_label is not None and self.trace_label.winfo_exists():
            self.trace_label.configure(text=text)

    def _heading(self, text):
        label(self, text.upper(), 11, "bold", "primary").pack(
            anchor="w", padx=16, pady=(16, 4))

    def _section(self, heading, text, mono_font=False):
        self._heading(heading)
        box = ctk.CTkFrame(self, fg_color=pair("chip") if mono_font else "transparent",
                           corner_radius=8)
        box.pack(fill="x", padx=16)
        body = ctk.CTkLabel(box, text=text, justify="left", anchor="w",
                            wraplength=288, text_color=pair("text"),
                            font=theme.mono(10) if mono_font else font(11))
        body.pack(fill="x", padx=8 if mono_font else 0, pady=8 if mono_font else 0)
        return body

    def _comparison(self, data):
        self._heading("Comparison")
        table = ctk.CTkFrame(self, fg_color=pair("chip"), corner_radius=8)
        table.pack(fill="x", padx=16)
        columns = len(data["headers"])
        for column in range(columns):
            table.grid_columnconfigure(column, weight=1, uniform="c")
        for column, header in enumerate(data["headers"]):
            label(table, header, 11, "bold", "primary", wraplength=84).grid(
                row=0, column=column, sticky="w", padx=8, pady=(8, 4))
        for r, row in enumerate(data["rows"], start=1):
            for column, cell in enumerate(row):
                label(table, cell, 11, "bold" if column == 0 else "normal",
                      wraplength=84).grid(row=r, column=column, sticky="nw",
                                           padx=8, pady=4)
        label(table, data["note"], 11, color="muted", wraplength=270).grid(
            row=len(data["rows"]) + 1, column=0, columnspan=columns,
            sticky="w", padx=8, pady=(8, 8))


class HelpButton(ctk.CTkButton):
    """Small '?' button that pops up a summary of the algorithm used."""

    def __init__(self, parent, info_key):
        super().__init__(parent, text="?", width=28, height=28, corner_radius=14,
                         fg_color=pair("chip"), hover_color=pair("row_hover"),
                         text_color=pair("primary_text"), border_width=1,
                         border_color=pair("border"), font=font(12, "bold"),
                         command=lambda: self.popup(info_key))

    def popup(self, info_key):
        info = ALGORITHM_INFO[info_key]
        window = ctk.CTkToplevel(self.winfo_toplevel())
        window.title("Quick help")
        window.geometry("440x280")
        window.transient(self.winfo_toplevel())
        window.configure(fg_color=pair("card"))
        label(window, info["title"], 15, "bold", "primary", wraplength=400).pack(
            anchor="w", padx=24, pady=(24, 8))
        label(window, "Algorithm: " + info["algorithm"], 12, "bold",
              wraplength=400).pack(anchor="w", padx=24, pady=4)
        label(window, info["summary"], 12, wraplength=400).pack(
            anchor="w", padx=24, pady=4)
        label(window, "Complexity: " + info["complexity"], 11, color="muted",
              wraplength=400).pack(anchor="w", padx=24, pady=4)
        button(window, "Close", window.destroy, width=88).pack(
            anchor="e", padx=24, pady=16)
        window.after(100, window.focus)


# ---------------------------------------------------------------------------
# Date picker
# ---------------------------------------------------------------------------
class DateEntry(ctk.CTkFrame):
    """Entry showing YYYY-MM-DD plus a button that opens a small calendar."""

    def __init__(self, parent, variable, width=170):
        super().__init__(parent, fg_color="transparent")
        self.variable = variable
        self.entry = entry(self, "YYYY-MM-DD", width=width - 48, textvariable=variable)
        self.entry.pack(side="left")
        ctk.CTkButton(self, text="" if icons.AVAILABLE else "Pick", width=40, height=32,
                      corner_radius=theme.gui_theme.RADIUS_INPUT,
                      image=icons.ctk_icon("calendar", "white", 18),
                      fg_color=pair("primary"), hover_color=pair("primary_hover"),
                      command=self.open_calendar).pack(side="left", padx=(8, 0))

    def open_calendar(self):
        try:
            current = datetime.datetime.strptime(self.variable.get(), "%Y-%m-%d").date()
        except ValueError:
            current = datetime.date.today()
        CalendarPopup(self, current, self.variable.set)


class CalendarPopup(ctk.CTkToplevel):
    """Month grid; click a day to choose it."""

    def __init__(self, anchor, start_date, on_pick):
        super().__init__(anchor.winfo_toplevel())
        self.title("Pick a date")
        self.resizable(False, False)
        self.transient(anchor.winfo_toplevel())
        self.configure(fg_color=pair("card"))
        self.on_pick = on_pick
        self.year, self.month = start_date.year, start_date.month
        self.selected = start_date
        self.geometry("+%d+%d" % (anchor.winfo_rootx(), anchor.winfo_rooty() + 48))
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=16, pady=(16, 8))
        button(self.header, "<", lambda: self.shift(-1), "secondary", width=32).pack(side="left")
        self.title_label = label(self.header, "", 13, "bold")
        self.title_label.pack(side="left", expand=True)
        button(self.header, ">", lambda: self.shift(1), "secondary", width=32).pack(side="right")
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(padx=16, pady=(0, 16))
        self.draw()
        self.after(100, self.focus)

    def shift(self, step):
        self.month += step
        if self.month < 1:
            self.month, self.year = 12, self.year - 1
        elif self.month > 12:
            self.month, self.year = 1, self.year + 1
        self.draw()

    def draw(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.title_label.configure(text="%s %d" % (calendar.month_name[self.month], self.year))
        for column, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            label(self.grid_frame, name, 11, "bold", "muted", width=36).grid(row=0, column=column)
        for r, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for column, day in enumerate(week):
                if day == 0:
                    continue
                picked = datetime.date(self.year, self.month, day) == self.selected
                ctk.CTkButton(
                    self.grid_frame, text=str(day), width=36, height=32, corner_radius=8,
                    fg_color=pair("primary") if picked else "transparent",
                    text_color="#FFFFFF" if picked else pair("text"),
                    hover_color=pair("row_hover"), font=mono(11),
                    command=lambda d=day: self.pick(d)).grid(row=r, column=column, padx=1, pady=1)

    def pick(self, day):
        self.on_pick(datetime.date(self.year, self.month, day).isoformat())
        self.destroy()


# ---------------------------------------------------------------------------
# Patient profile card
# ---------------------------------------------------------------------------
class ProfileCard(Card):
    """Neat display of every field of one patient plus DSA locations."""

    def __init__(self, parent, manager, patient):
        super().__init__(parent)
        slot, position = manager.hash_table.chain_position(patient.patient_id)
        depth = manager.bst.depth_of(patient.patient_id)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(24, 8))
        ctk.CTkLabel(head, text=patient.name[:1].upper(), width=56, height=56,
                     corner_radius=28, fg_color=pair("primary"), text_color="#FFFFFF",
                     font=font(22, "bold")).pack(side="left")
        names = ctk.CTkFrame(head, fg_color="transparent")
        names.pack(side="left", padx=16)
        label(names, patient.name, 17, "bold").pack(anchor="w")
        names_sub = ctk.CTkLabel(names, font=mono(12), text_color=pair("muted"),
                                 text="Patient ID %d  •  %d yrs  •  %s" % (
                                     patient.patient_id, patient.age, patient.gender))
        names_sub.pack(anchor="w")
        Badge(head, patient.department, theme.dept_color(patient.department)).pack(side="right")
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=24, pady=8)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="p")
        fields = [("Diagnosis", patient.diagnosis), ("Doctor", patient.doctor),
                  ("Admission date", patient.admission_date),
                  ("Department", patient.department)]
        for index, (name, value) in enumerate(fields):
            cell = ctk.CTkFrame(grid, fg_color=pair("chip"), corner_radius=8)
            cell.grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)
            label(cell, name, 11, color="muted").pack(anchor="w", padx=16, pady=(8, 0))
            label(cell, value, 12, "bold", wraplength=230).pack(anchor="w", padx=16, pady=(0, 8))
        label(self, "Stored at hash slot %d, chain position %d     •     BST depth: %d" % (
            slot, position, depth), 12, "bold", "primary").pack(
                anchor="w", padx=24, pady=(8, 24))


def open_profile_window(app, patient_id):
    """Open a window with the profile of patient_id (if it still exists)."""
    patient = app.manager.get_patient(patient_id)
    if patient is None:
        return
    window = ctk.CTkToplevel(app)
    window.title("Patient %d" % patient_id)
    window.geometry("576x344")
    window.transient(app)
    window.configure(fg_color=pair("bg"))
    ProfileCard(window, app.manager, patient).pack(fill="both", expand=True, padx=16, pady=16)
    window.after(100, window.focus)
