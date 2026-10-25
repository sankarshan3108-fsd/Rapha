"""Main window: sidebar navigation, top bar, algorithm-info panel, status bar,
light/dark switching.  Pages live in gui/pages and only talk to the manager.

RAPHA restyle: branding, frosted-glass panels over a blurred backdrop, line
icons.  Navigation, page logic and data flow are unchanged.
"""
import datetime
import os
from tkinter import messagebox

import customtkinter as ctk

from gui import glass, icons, theme
from gui.gui_theme import BRAND, BRAND_FULL
from gui.pages.about import AboutPage
from gui.pages.add_patient import AddPatientPage
from gui.pages.bst_view import BSTViewPage
from gui.pages.dashboard import DashboardPage
from gui.pages.generate_report import GenerateReportPage
from gui.pages.hash_view import HashViewPage
from gui.pages.lookup import LookupPage
from gui.pages.patients import PatientsPage
from gui.pages.range_query import RangeQueryPage
from gui.pages.report import ReportPage
from gui.theme import font, mono, pair
from gui.widgets import InfoPanel, Toast, Tooltip, apply_ttk_styles, label, button

# (page key, icon name, sidebar label, page class)
NAV_ITEMS = [
    ("dashboard", "dashboard", "Dashboard", DashboardPage),
    ("patients", "patients", "All Patients", PatientsPage),
    ("add", "add", "Add Patient", AddPatientPage),
    ("lookup", "lookup", "Lookup by ID", LookupPage),
    ("range", "range", "Range Query", RangeQueryPage),
    ("report", "report", "Daily Report", ReportPage),
    ("hash_view", "hash", "Hash Table View", HashViewPage),
    ("bst_view", "tree", "BST View", BSTViewPage),
    ("about", "about", "About Project", AboutPage),
    # Generate Report page (PDF reports) - added last
    ("reports", "export", "Generate Report", GenerateReportPage),
]

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class RaphaApp(ctk.CTk):
    def __init__(self, manager):
        # Fixed 1:1 pixel scaling keeps CTk widgets, ttk tables and canvases
        # the same size on every screen DPI (and the window always fits).
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        super().__init__()
        self.attributes("-alpha", 0.0)          # RESTYLE: fades in once built
        self.manager = manager
        theme.set_mode("light")
        ctk.set_default_color_theme("blue")
        theme.init_fonts()
        self.title(BRAND_FULL)
        self._set_icon()
        self._place_window(1280, 780)
        self.minsize(1100, 700)
        self.configure(fg_color=pair("bg"))
        self.backdrop = glass.Backdrop(self, "light")     # blurred glass backdrop
        apply_ttk_styles(self)
        self.toast = Toast(self)
        self.tooltip = Tooltip(self)
        self.traces = {}
        self.nav_buttons = {}
        self.nav_indicators = {}
        self.pages = {}
        self.current = None
        self.info_visible = True
        self.user_toggled = False      # True once the user used the toggle button
        self.auto_hidden = False       # panel hidden automatically on narrow windows
        self.last_operation = "Application started"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_center()
        self.info_panel = InfoPanel(self, width=340)
        self.info_panel.grid(row=0, column=2, sticky="nsew", padx=(0, 16), pady=(16, 8))
        self._build_status_bar()
        for key, icon, title, page_class in NAV_ITEMS:
            page = page_class(self)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
            self.pages[key] = page
        self.navigate("dashboard")
        self._tick_clock()
        self.bind("<Configure>", self._on_resize, add="+")
        self.after(60, self._fade_in)

    # ---------------- construction ----------------
    def _set_icon(self):
        """Window / taskbar icon from assets/rapha.ico (created on first run)."""
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RAPHA.HospitalManagement")
        except Exception:
            pass
        path = icons.ensure_assets(ASSETS_DIR)
        if path:
            # CustomTkinter sets its own icon shortly after start-up, so set ours after that
            for delay in (0, 300):
                self.after(delay, lambda: self._apply_icon(path))

    def _apply_icon(self, path):
        try:
            self.iconbitmap(path)
        except Exception:
            pass

    def _fade_in(self, alpha=0.0):
        alpha = min(1.0, alpha + 0.2)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            return
        if alpha < 1.0:
            self.after(20, lambda: self._fade_in(alpha))

    def _place_window(self, width, height):
        """Centre the window on screen (sizes are in CTk logical pixels)."""
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        width, height = int(min(width, screen_w - 20)), int(min(height, screen_h - 80))
        x = max(0, int((screen_w - width) / 2))
        y = max(0, int((screen_h - height) / 2) - 20)
        self.geometry("%dx%d+%d+%d" % (width, height, x, y))

    def _glass_panel(self, **grid):
        panel = ctk.CTkFrame(self, corner_radius=theme.RADIUS, fg_color=pair("sidebar"),
                             border_width=1, border_color=pair("border"))
        panel.grid(**grid)
        return panel

    def _build_sidebar(self):
        sidebar = self._glass_panel(row=0, column=0, rowspan=2, sticky="nsew",
                                    padx=(16, 8), pady=16)
        sidebar.configure(width=232)
        sidebar.grid_propagate(False)
        # brand block: logo + RAPHA + subtitle + project caption
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(24, 0))
        ctk.CTkLabel(brand, text="" if icons.AVAILABLE else "+", image=icons.logo_image(40),
                     width=40, height=40).pack(side="left")
        ctk.CTkLabel(brand, text=BRAND, font=font(22, "bold"),
                     text_color=pair("text")).pack(side="left", padx=(8, 0))
        label(sidebar, "Hospital Management System", 12, "bold", "muted").pack(
            anchor="w", padx=16, pady=(8, 0))
        label(sidebar, "Hash Table • BST • Merge Sort", 11, color="muted").pack(
            anchor="w", padx=16, pady=(0, 16))
        ctk.CTkFrame(sidebar, height=1, fg_color=pair("border")).pack(fill="x", padx=16, pady=(0, 8))
        for key, icon, title, _ in NAV_ITEMS:
            row = ctk.CTkFrame(sidebar, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            indicator = ctk.CTkFrame(row, width=3, height=24, corner_radius=2, fg_color="transparent")
            indicator.pack(side="left", padx=(0, 4))
            nav = ctk.CTkButton(
                row, text=title, image=icons.ctk_icon(icon, "text", 18), compound="left",
                anchor="w", height=36, corner_radius=8, fg_color="transparent",
                text_color=pair("sidebar_text"), hover_color=pair("sidebar_hover"),
                font=font(12, "bold"), command=lambda k=key: self.navigate(k))
            nav.pack(side="left", fill="x", expand=True)
            self.nav_buttons[key] = nav
            self.nav_indicators[key] = indicator
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=24)
        self.mode_switch = ctk.CTkSwitch(bottom, text="Dark mode", text_color=pair("sidebar_text"),
                                         font=font(12), command=self.toggle_theme,
                                         progress_color=pair("accent"),
                                         button_color=pair("primary"),
                                         fg_color=pair("border"))
        self.mode_switch.pack(anchor="w", pady=(0, 16))
        label(bottom, "DSA Micro Project-07", 11, "bold", "muted").pack(anchor="w")

    def _build_center(self):
        self.center = ctk.CTkFrame(self, fg_color=pair("panel"), corner_radius=theme.RADIUS,
                                   border_width=1, border_color=pair("border"))
        self.center.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=(16, 8))
        center = self.center
        center.grid_rowconfigure(2, weight=1)
        center.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(center, fg_color="transparent", height=72)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        top.pack_propagate(False)
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left", padx=16, pady=8)
        self.title_label = label(titles, "", 22, "bold")
        self.title_label.pack(anchor="w")
        self.subtitle_label = label(titles, "", 11, color="primary")
        self.subtitle_label.pack(anchor="w")
        right = ctk.CTkFrame(top, fg_color="transparent")
        right.pack(side="right", padx=8)
        self.info_button = button(right, "Hide Algorithm Info", self.toggle_info,
                                  "secondary", width=152)
        self.info_button.configure(height=32)
        self.clock_label = ctk.CTkLabel(right, text="", font=mono(12), text_color=pair("muted"))
        self.clock_label.pack(anchor="e", pady=(8, 4))
        self.info_button.pack(anchor="e")
        ctk.CTkFrame(center, height=1, fg_color=pair("border")).grid(
            row=1, column=0, sticky="ew", padx=16)
        self.container = ctk.CTkFrame(center, fg_color="transparent")
        self.container.grid(row=2, column=0, sticky="nsew", padx=16, pady=16)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, height=32, corner_radius=theme.RADIUS, fg_color=pair("sidebar"),
                           border_width=1, border_color=pair("border"))
        bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 16), pady=(0, 16))
        self.status_records = label(bar, "", 11, "bold")
        self.status_records.pack(side="left", padx=(16, 16), pady=4)
        # connection indicator: green dot = MySQL connected, amber dot = SQLite offline mode
        database = self.manager.database
        online = getattr(database, "status_kind", "sqlite") == "mysql"
        ctk.CTkFrame(bar, width=8, height=8, corner_radius=4,
                     fg_color=pair("accent") if online else ("#D9A441", "#D9A441")).pack(side="left")
        label(bar, getattr(database, "status_text", "SQLite (offline mode)"), 11,
              color="muted").pack(side="left", padx=(8, 16))
        self.status_operation = label(bar, "", 11, color="muted")
        self.status_operation.pack(side="left")

    # ---------------- behaviour ----------------
    def report_callback_exception(self, exc, val, tb):
        """Never crash: show any unexpected error in a dialog."""
        messagebox.showerror("Unexpected error", "Something went wrong:\n%s" % val)

    def _tick_clock(self):
        self.clock_label.configure(
            text=datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def _mark_nav(self, key, active):
        """Active item: stronger glass, green indicator, teal text."""
        button_ = self.nav_buttons[key]
        icon = dict((k, i) for k, i, _, _ in NAV_ITEMS)[key]
        button_.configure(fg_color=pair("sidebar_active") if active else "transparent",
                          text_color=pair("primary_text") if active else pair("sidebar_text"),
                          image=icons.ctk_icon(icon, "primary" if active else "text", 18))
        self.nav_indicators[key].configure(fg_color=pair("accent") if active else "transparent")

    def navigate(self, key):
        """Show one page, highlight its sidebar button and refresh the info panel."""
        if self.current:
            self.pages[self.current].grid_remove()
            self._mark_nav(self.current, False)
        self.current = key
        page = self.pages[key]
        page.grid()
        self._mark_nav(key, True)
        self.title_label.configure(text=page.title)
        self.subtitle_label.configure(text=page.subtitle)
        self.info_panel.show(key, self.traces.get(key))
        if page.dirty:
            page.refresh()
            page.dirty = False
        page.on_show()
        self.refresh_status()

    def _on_resize(self, event):
        """Hide the info panel automatically on narrow windows (< 1180 px)."""
        if event.widget is not self or self.user_toggled:
            return
        width = event.width / ctk.ScalingTracker.get_window_scaling(self)
        if width < 1180 and self.info_visible:
            self.toggle_info(user=False)
            self.auto_hidden = True
        elif width >= 1180 and self.auto_hidden and not self.info_visible:
            self.toggle_info(user=False)
            self.auto_hidden = False

    def toggle_info(self, user=True):
        if user:
            self.user_toggled = True
        self.info_visible = not self.info_visible
        if self.info_visible:
            self.info_panel.grid()
            self.center.grid_configure(padx=(0, 8))
            self.info_button.configure(text="Hide Algorithm Info")
        else:
            self.info_panel.grid_remove()
            self.center.grid_configure(padx=(0, 16))
            self.info_button.configure(text="Show Algorithm Info")

    def toggle_theme(self):
        theme.set_mode("dark" if self.mode_switch.get() else "light")
        apply_ttk_styles(self)
        self.configure(fg_color=pair("bg"))
        self.backdrop.set_mode(theme.mode())
        for page in self.pages.values():
            page.on_theme()
        for key in self.nav_buttons:                 # icons follow the palette
            self._mark_nav(key, key == self.current)
        self.info_panel.show(self.current, self.traces.get(self.current))

    def set_trace(self, key, text):
        """Store the live-trace text for a page and show it if that page is open."""
        self.traces[key] = text
        if key == self.current:
            self.info_panel.set_trace(text)

    def set_status(self, operation):
        self.last_operation = operation
        self.refresh_status()

    def refresh_status(self):
        self.status_records.configure(text="Total records: %d" % self.manager.count())
        self.status_operation.configure(text="Last operation: " + self.last_operation)

    def notify_change(self):
        """Call after any add/update/delete: pages are refreshed lazily."""
        for key, page in self.pages.items():
            page.dirty = True
        page = self.pages[self.current]
        page.refresh()
        page.dirty = False
        self.refresh_status()

    def edit_patient(self, patient_id):
        """Open the Add/Edit page pre-filled with an existing patient."""
        patient = self.manager.get_patient(patient_id)
        if patient is None:
            messagebox.showerror("Not found", "That patient no longer exists.")
            return
        self.pages["add"].load_for_edit(patient)
        self.navigate("add")


MediTrackApp = RaphaApp          # old name kept so existing references still work


def run_app(manager):
    app = RaphaApp(manager)
    app.mainloop()
