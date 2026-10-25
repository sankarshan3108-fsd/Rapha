"""Dashboard: KPI cards, matplotlib charts, recent admissions, quick actions."""
import datetime

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gui import icons, theme
from gui.pages.base import Page
from gui.theme import font, pair, pal
from gui.utils import best_height, count_by, short_date
from gui.widgets import Card, KPICard, StyledTable, button, label


class DashboardPage(Page):
    key = "dashboard"
    title = "Dashboard"
    subtitle = "Hash table health & BST shape • Load factor, rehashing, height"

    def __init__(self, app):
        super().__init__(app)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self.cards = {}
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x")
        specs = [("total", "patients", "TOTAL PATIENTS", "primary"),
                 ("depts", "building", "DEPARTMENTS", "success"),
                 ("latest", "calendar", "LATEST-DAY ADMISSIONS", "accent"),
                 ("hash", "hash", "HASH TABLE SIZE", "primary"),
                 ("load", "gauge", "LOAD FACTOR", "success"),
                 ("height", "tree", "BST HEIGHT", "primary")]
        for index, (key, icon, title, color) in enumerate(specs):
            card = KPICard(grid, icon, title, color)
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=8, pady=8)
            grid.grid_columnconfigure(index % 3, weight=1, uniform="kpi")
            self.cards[key] = card

        charts = ctk.CTkFrame(body, fg_color="transparent")
        charts.pack(fill="x", pady=(8, 0))
        charts.grid_columnconfigure((0, 1), weight=1, uniform="chart")
        self.bar_figure, self.bar_canvas = self._make_chart(charts, 0)
        self.pie_figure, self.pie_canvas = self._make_chart(charts, 1)

        lower = ctk.CTkFrame(body, fg_color="transparent")
        lower.pack(fill="x", pady=(8, 0))
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=1)
        recent = Card(lower)
        recent.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        label(recent, "Recent admissions (merge sort, latest 5)", 13, "bold").pack(
            anchor="w", padx=16, pady=(16, 8))
        self.recent_table = StyledTable(recent, ("ID", "Name", "Department", "Admitted"),
                                        (60, 160, 130, 100), height=5)
        self.recent_table.pack(fill="x", padx=16, pady=(0, 16))
        actions = Card(lower)
        actions.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        label(actions, "Quick actions", 13, "bold").pack(anchor="w", padx=16, pady=(16, 8))
        for text, target, icon_name in (("Add Patient", "add", "add"), ("Lookup", "lookup", "lookup"),
                             ("Daily Report", "report", "report")):
            button(actions, text, lambda t=target: self.app.navigate(t), width=152,
                   icon=icons.ctk_icon(icon_name, "white", 16)).pack(
                padx=16, pady=4, anchor="w")

    def _make_chart(self, parent, column):
        card = Card(parent)
        card.grid(row=0, column=column, sticky="nsew", padx=8, pady=8)
        figure = Figure(figsize=(3.4, 2.7), dpi=100)
        canvas = FigureCanvasTkAgg(figure, master=card)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        return figure, canvas

    def restyle(self):
        self.recent_table.restyle()

    def refresh(self):
        manager, colors = self.manager, pal()
        table, tree = manager.hash_table, manager.bst
        patients = manager.all_patients()           # BST in-order
        report, _ = manager.daily_report()           # merge sort
        by_dept = count_by(patients, lambda p: p.department)
        by_day = count_by(report, lambda p: p.admission_date)
        n = len(patients)
        today = datetime.date.today().isoformat()
        today_count = sum(1 for p in patients if p.admission_date == today)
        if today_count:
            latest_value, latest_sub = today_count, "admitted today (%s)" % short_date(today)
        elif by_day:
            latest_value = by_day[-1][1]
            latest_sub = "on %s (latest day)" % short_date(by_day[-1][0])
        else:
            latest_value, latest_sub = 0, "no admissions yet"
        load = table.load_factor()
        load_color = "#2EAA4F" if load < 0.6 else ("#D9A441" if load <= 0.75 else "#C0392B")
        self.cards["total"].set(n, "records in hash table and BST")
        self.cards["depts"].set(len(by_dept), ", ".join(d for d, _ in by_dept[:3]) +
                                ("..." if len(by_dept) > 3 else ""))
        self.cards["latest"].set(latest_value, latest_sub)
        self.cards["hash"].set(table.size, "%d collisions • %d rehash(es)" % (
            table.collisions, table.rehash_count))
        self.cards["load"].set("%.2f" % load, "%d records / %d slots\n(limit 0.75)" % (
            table.count, table.size), progress=load / 0.75, bar_color=load_color)
        self.cards["height"].set(tree.height(), "best possible %d • worst %d" % (
            best_height(tree.size()), tree.size()))
        self._draw_charts(by_day, by_dept)
        self.recent_table.clear()
        for patient in report[-5:][::-1]:
            self.recent_table.add_row((patient.patient_id, patient.name,
                                       patient.department, patient.admission_date))
        self.recent_table.finish("recent admissions")
        self.trace(
            "load factor = n / size\n= %d / %d = %.2f (limit 0.75)\n"
            "rehashes so far: %d (table grew 31 -> %d)\n"
            "BST height: actual %d | best %d | worst %d\n"
            "records are shuffled (seed 42) before BST insertion" % (
                table.count, table.size, load, table.rehash_count, table.size,
                tree.height(), best_height(tree.size()), tree.size()))

    def _style_axes(self, figure, axes):
        colors = pal()
        figure.patch.set_facecolor(colors["card"])
        axes.set_facecolor(colors["card"])
        axes.tick_params(colors=colors["muted"], labelsize=8)
        for spine in axes.spines.values():
            spine.set_color(colors["border"])
        axes.title.set_color(colors["text"])

    def _draw_charts(self, by_day, by_dept):
        colors = pal()
        figure = self.bar_figure
        figure.clear()
        axes = figure.add_subplot(111)
        self._style_axes(figure, axes)
        labels = [short_date(d) for d, _ in by_day]
        values = [c for _, c in by_day]
        bars = axes.bar(labels, values, color=colors["primary"], width=0.6)
        axes.bar_label(bars, color=colors["text"], fontsize=8)
        axes.set_title("Admissions per day", fontsize=10, fontweight="bold")
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        figure.tight_layout()
        self.bar_canvas.draw_idle()

        figure = self.pie_figure
        figure.clear()
        axes = figure.add_subplot(111)
        self._style_axes(figure, axes)
        axes.set_title("Patients per department", fontsize=10, fontweight="bold")
        names = [d for d, _ in by_dept]
        counts = [c for _, c in by_dept]
        if counts:
            axes.pie(counts, colors=[theme.dept_color(d) for d in names],
                     wedgeprops=dict(width=0.42, edgecolor=colors["card"]),
                     startangle=90, autopct=lambda p: "%d" % round(p * sum(counts) / 100),
                     pctdistance=0.79, textprops=dict(color="white", fontsize=8))
            axes.legend(names, loc="center left", bbox_to_anchor=(0.92, 0.5), fontsize=7,
                        frameon=False, labelcolor=colors["text"])
        axes.axis("equal")
        figure.tight_layout()
        self.pie_canvas.draw_idle()
