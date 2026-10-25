"""Generate Report page: choose a report type, preview it, save it as a PDF.

All report data is built by reports/report_generator.py from our own DSA code
(through PatientManager); this page only collects the options and shows results.
"""
import os
import time
import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from gui import icons, theme
from gui.pages.base import Page
from gui.theme import font, mono, pair
from gui.widgets import Card, HelpButton, button, dropdown, entry, label
from reports import report_generator as rg

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "reports_output")
LOGO_PATH = os.path.join(PROJECT_DIR, "assets", "rapha.png")


class GenerateReportPage(Page):
    key = "reports"
    title = "Generate Report"
    subtitle = "Hash lookup • BST traversal and range query • Merge sort • PDF output"

    def __init__(self, app):
        super().__init__(app)
        self.last_pdf = None
        self.kind_var = ctk.StringVar(value="daily")
        self.dsa_var = ctk.BooleanVar(value=True)
        self.date_var = ctk.StringVar(value="All dates")
        self.dept_var = ctk.StringVar(value="All departments")
        self.low_var, self.high_var, self.id_var = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- left: report options ----------------
        options = Card(self, width=288)
        options.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        options.grid_propagate(False)
        head = ctk.CTkFrame(options, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(16, 8))
        label(head, "Report options", 15, "bold").pack(side="left")
        HelpButton(head, "reports").pack(side="right")
        label(options, "Report type", 11, "bold", "muted").pack(anchor="w", padx=16, pady=(8, 4))
        for kind, text in rg.KINDS:
            ctk.CTkRadioButton(
                options, text=text, value=kind, variable=self.kind_var, font=font(12),
                text_color=pair("text"), fg_color=pair("primary"), hover_color=pair("primary_hover"),
                border_color=pair("border"), radiobutton_width=18, radiobutton_height=18,
                command=self.on_kind_changed).pack(anchor="w", padx=16, pady=4)

        self.option_area = ctk.CTkFrame(options, fg_color="transparent")
        self.option_area.pack(fill="x", padx=16, pady=(16, 0))
        self.daily_box = self._option_box("Date")
        self.date_menu = dropdown(self.daily_box, ["All dates"], self.date_var, 240)
        self.date_menu.pack(anchor="w")
        self.dept_box = self._option_box("Department")
        self.dept_menu = dropdown(self.dept_box, ["All departments"], self.dept_var, 240)
        self.dept_menu.pack(anchor="w")
        self.range_box = self._option_box("ID range")
        row = ctk.CTkFrame(self.range_box, fg_color="transparent")
        row.pack(anchor="w")
        entry(row, "Low ID", width=112, textvariable=self.low_var).pack(side="left")
        entry(row, "High ID", width=112, textvariable=self.high_var).pack(side="left", padx=(8, 0))
        self.patient_box = self._option_box("Patient ID")
        entry(self.patient_box, "e.g. 1045", width=232, textvariable=self.id_var).pack(anchor="w")

        ctk.CTkCheckBox(options, text="Include DSA statistics", variable=self.dsa_var,
                        font=font(12), text_color=pair("text"), fg_color=pair("primary"),
                        hover_color=pair("primary_hover"), border_color=pair("border"),
                        checkbox_width=18, checkbox_height=18).pack(anchor="w", padx=16, pady=16)
        buttons = ctk.CTkFrame(options, fg_color="transparent")
        buttons.pack(fill="x", padx=16)
        button(buttons, "Preview", self.preview, "secondary", width=104).pack(side="left")
        button(buttons, "Generate PDF", self.generate, width=136).pack(side="left", padx=(8, 0))
        self.open_button = button(options, "Open report", self.open_last, "secondary", width=248,
                                  icon=icons.ctk_icon("report", "text", 16))
        self.saved_label = label(options, "", 11, color="muted", wraplength=248)

        # ---------------- right: preview ----------------
        preview = Card(self)
        preview.grid(row=0, column=1, sticky="nsew")
        label(preview, "Preview", 15, "bold").pack(anchor="w", padx=16, pady=(16, 8))
        self.text = ctk.CTkTextbox(preview, wrap="none", font=mono(11), corner_radius=8,
                                   fg_color=pair("input"), text_color=pair("text"),
                                   border_width=1, border_color=pair("border"))
        self.text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._set_preview("Choose a report type and press Preview to see the content here.")
        self.on_kind_changed()

    def _option_box(self, caption):
        box = ctk.CTkFrame(self.option_area, fg_color="transparent")
        label(box, caption, 11, "bold", "muted").pack(anchor="w", pady=(0, 4))
        return box

    # ---------------- behaviour ----------------
    def refresh(self):
        """Fill the date / department drop-downs from the current data."""
        ordered, _ = self.manager.daily_report()
        dates, departments = [], []
        for patient in ordered:
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

    def on_kind_changed(self):
        """Show only the option fields that belong to the chosen report type."""
        for box in (self.daily_box, self.dept_box, self.range_box, self.patient_box):
            box.pack_forget()
        box = {"daily": self.daily_box, "department": self.dept_box,
               "range": self.range_box, "patient": self.patient_box}.get(self.kind_var.get())
        if box is not None:
            box.pack(fill="x")

    def _set_preview(self, text):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.configure(state="disabled")

    def _collect_options(self):
        return {"date": self.date_var.get(), "department": self.dept_var.get(),
                "low": self.low_var.get(), "high": self.high_var.get(),
                "patient_id": self.id_var.get()}

    def _build(self):
        """Build the report data; shows a friendly dialog and returns None on input errors."""
        started = time.perf_counter()
        try:
            report = rg.build_report(self.manager, self.kind_var.get(), self._collect_options(),
                                     self.dsa_var.get())
        except rg.ReportError as error:
            messagebox.showerror("Cannot build report", str(error))
            return None
        except Exception as error:
            messagebox.showerror("Cannot build report", "Something went wrong:\n%s" % error)
            return None
        self.trace("%s\nblocks built: %d\nbuilt in %.1f ms\nsource: PatientManager "
                   "(hash table / BST / merge sort)" % (
                       report["title"], len(report["blocks"]), (time.perf_counter() - started) * 1000))
        return report

    def preview(self):
        report = self._build()
        if report is None:
            return None
        self._set_preview(rg.preview_text(report))
        self.app.set_status("Report preview • %s" % report["title"])
        return report

    def generate(self):
        report = self._build()
        if report is None:
            return
        self._set_preview(rg.preview_text(report))
        try:
            import reportlab  # noqa: F401
        except ImportError:
            messagebox.showerror("PDF library missing",
                                 "Creating PDF reports needs the reportlab library.\n\n"
                                 "Please run:  pip install reportlab")
            return
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Save report as", defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")],
            initialdir=OUTPUT_DIR, initialfile=rg.suggested_filename(report))
        if not path:
            return
        try:
            rg.write_pdf(report, path, LOGO_PATH)
        except Exception as error:
            messagebox.showerror("Could not save report", str(error))
            return
        self.last_pdf = path
        name = os.path.basename(path)
        self.saved_label.configure(text="Saved: " + name)
        self.saved_label.pack(anchor="w", padx=16, pady=(8, 0))
        self.open_button.pack(anchor="w", padx=16, pady=(8, 16))
        self.app.toast.show("Report saved: " + name)
        self.app.set_status("Generate report • %s • PDF saved" % report["title"])

    def open_last(self):
        if not self.last_pdf or not os.path.exists(self.last_pdf):
            messagebox.showinfo("Open report", "Generate a report first.")
            return
        try:
            os.startfile(self.last_pdf)          # default PDF viewer (Windows)
        except Exception as error:
            messagebox.showerror("Cannot open report", str(error))
