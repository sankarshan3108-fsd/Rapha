"""Daily admission report sorted by merge sort, with exports and animation."""
import csv
import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from gui.gui_theme import BRAND_FULL, TAGLINE
from gui.pages.base import Page
from gui.utils import bubble_worst, n_log2_n
from gui.visualizers.merge_sort_animation import MergeSortWindow
from gui.widgets import Card, Chip, HelpButton, StyledTable, button, dropdown, label
from merge_sort import recursion_depth

COLUMNS = ("ID", "Name", "Age", "Gender", "Department", "Diagnosis", "Doctor", "Admitted")
WIDTHS = (50, 106, 36, 62, 110, 100, 90, 88)
TITLE = BRAND_FULL          # RAPHA header (title + tagline) replaces the old header text


class ReportPage(Page):
    key = "report"
    title = "Daily Admission Report"
    subtitle = "Merge Sort (Divide & Conquer, stable) • O(n log n)"

    def __init__(self, app):
        super().__init__(app)
        self.shown = []              # patients currently in the table (for export)
        self.comparisons = 0
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        bar = ctk.CTkFrame(body, fg_color="transparent")
        bar.pack(fill="x")
        self.date_var = ctk.StringVar(value="All dates")
        self.dept_var = ctk.StringVar(value="All departments")
        self.date_menu = dropdown(bar, ["All dates"], self.date_var, 150, lambda v: self.refresh())
        self.date_menu.pack(side="left")
        self.dept_menu = dropdown(bar, ["All departments"], self.dept_var, 170, lambda v: self.refresh())
        self.dept_menu.pack(side="left", padx=8)
        HelpButton(bar, "report").pack(side="left", padx=4)
        button(bar, "Visualize Merge Sort", self.visualize, width=190).pack(side="right")

        exports = ctk.CTkFrame(body, fg_color="transparent")
        exports.pack(fill="x", pady=8)
        label(exports, "Export:", 11, "bold", "muted").pack(side="left", padx=(0, 8))
        for kind in ("txt", "csv", "pdf"):
            button(exports, ".%s" % kind, lambda k=kind: self.export(k), "secondary",
                   width=60).pack(side="left", padx=4)

        chips = ctk.CTkFrame(body, fg_color="transparent")
        chips.pack(fill="x", pady=(0, 8))
        self.chip_total = Chip(chips, "Total patients")
        self.chip_cmp = Chip(chips, "Merge sort comparisons")
        self.chip_nlogn = Chip(chips, "n log₂ n (reference)")
        self.chip_bubble = Chip(chips, "Bubble sort worst case")
        for chip in (self.chip_total, self.chip_cmp, self.chip_nlogn, self.chip_bubble):
            chip.pack(side="left", padx=(0, 8))

        card = Card(body)
        card.pack(fill="x")
        self.table = StyledTable(card, COLUMNS, WIDTHS, height=16)
        self.table.pack(fill="x", padx=16, pady=16)

    def restyle(self):
        self.table.restyle()

    def refresh(self):
        report, comparisons = self.manager.daily_report()        # merge sort
        self.comparisons = comparisons
        dates, departments = [], []
        for patient in report:
            if patient.admission_date not in dates:
                dates.append(patient.admission_date)
            if patient.department not in departments:
                departments.append(patient.department)
        self.date_menu.configure(values=["All dates"] + dates)
        self.dept_menu.configure(values=["All departments"] + departments)
        if self.date_var.get() not in dates:
            self.date_var.set("All dates")
        if self.dept_var.get() not in departments:
            self.dept_var.set("All departments")
        chosen_date, chosen_dept = self.date_var.get(), self.dept_var.get()
        self.shown = [p for p in report
                      if (chosen_date == "All dates" or p.admission_date == chosen_date)
                      and (chosen_dept == "All departments" or p.department == chosen_dept)]
        self.table.clear()
        parent, current = "", None
        for patient in self.shown:
            if patient.admission_date != current:
                current = patient.admission_date
                day_count = sum(1 for p in self.shown if p.admission_date == current)
                parent = self.table.add_row(
                    ("", "%s" % current, "", "",
                     "%d admission%s" % (day_count, "" if day_count == 1 else "s"),
                     "", "", ""),
                    group=True)
            row = list(patient.as_row())
            self.table.add_row(row, parent=parent)
        self.table.finish("patients")
        n = len(report)
        self.chip_total.set(len(self.shown))
        self.chip_cmp.set(comparisons)
        self.chip_nlogn.set(n_log2_n(n))
        self.chip_bubble.set(bubble_worst(n))
        self.trace("records sorted: %d\ncomparisons made: %d\nrecursion depth: %d levels\n"
                   "n log2 n = %d (reference)\nbubble sort worst case: n(n-1)/2 = %d\n"
                   "dates in report: %d" % (
                       n, comparisons, recursion_depth(n), n_log2_n(n), bubble_worst(n), len(dates)))
        self.app.set_status("Daily report • Merge sort • %d comparisons" % comparisons)

    def visualize(self):
        report, _ = self.manager.daily_report()
        if not report:
            messagebox.showinfo("Nothing to show", "There are no patients to sort.")
            return
        MergeSortWindow(self.app, self.manager.all_patients())

    # ---------- exports ----------
    def report_lines(self):
        """Plain-text report lines (used by .txt and .pdf)."""
        now = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
        lines = [TITLE, TAGLINE, "Daily Admission Report", "Generated: " + now,
                 "Filter: %s | %s" % (self.date_var.get(), self.dept_var.get()),
                 "Patients: %d | Merge sort comparisons: %d" % (len(self.shown), self.comparisons),
                 "=" * 86]
        current = None
        for patient in self.shown:
            if patient.admission_date != current:
                current = patient.admission_date
                count = sum(1 for p in self.shown if p.admission_date == current)
                lines += ["", "%s  (%d admission%s)" % (current, count, "" if count == 1 else "s"),
                          "-" * 86]
            lines.append("%-6d %-22s %3d  %-7s %-17s %-18s %s" % (
                patient.patient_id, patient.name[:22], patient.age, patient.gender,
                patient.department[:17], patient.diagnosis[:18], patient.doctor))
        return lines

    def export(self, kind):
        if not self.shown:
            messagebox.showinfo("Nothing to export", "The report is empty.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension="." + kind, filetypes=[(kind.upper() + " file", "*." + kind)],
            title="Save daily admission report",
            initialfile="daily_admission_report." + kind)
        if not path:
            return
        try:
            if kind == "csv":
                with open(path, "w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(COLUMNS)
                    for patient in self.shown:
                        writer.writerow(patient.as_row())
            elif kind == "txt":
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(self.report_lines()) + "\n")
            else:
                self.write_pdf(path)
        except Exception as error:
            messagebox.showerror("Export failed", str(error))
            return
        self.app.toast.show("Report exported (%s)" % kind.upper())
        self.app.set_status("Export report .%s • %d patients" % (kind, len(self.shown)))

    def write_pdf(self, path):
        """Simple printable PDF made with matplotlib (A4, monospaced text)."""
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.figure import Figure
        lines = self.report_lines()
        per_page = 52
        with PdfPages(path) as pdf:
            for start in range(0, len(lines), per_page):
                figure = Figure(figsize=(8.27, 11.69))
                if start == 0:
                    figure.text(0.06, 0.96, TITLE, fontsize=13, fontweight="bold", color="#0B5E6E")
                    top = 0.93
                    chunk = lines[1:per_page] if start == 0 else lines[start:start + per_page]
                else:
                    top = 0.96
                    chunk = lines[start:start + per_page]
                for index, line in enumerate(chunk):
                    figure.text(0.06, top - index * 0.0175, line, fontsize=6.4, family="monospace")
                figure.text(0.5, 0.02, "Page %d" % (start // per_page + 1), ha="center", fontsize=7)
                pdf.savefig(figure)
