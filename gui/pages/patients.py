"""All Patients: BST in-order list, search/filter, merge-sort column sorting."""
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.base import Page
from gui.widgets import (Card, HelpButton, StyledTable, button, dropdown, entry,
                         open_profile_window)

COLUMNS = ("ID", "Name", "Age", "Gender", "Department", "Diagnosis", "Doctor", "Admitted")
WIDTHS = (50, 106, 36, 62, 110, 100, 90, 88)


class PatientsPage(Page):
    key = "patients"
    title = "All Patients"
    subtitle = "BST In-order Traversal • O(n) sorted listing • Merge-sort column sorting"

    def __init__(self, app):
        super().__init__(app)
        self.sort_info = None        # (column index, descending) when a header was clicked
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x")
        self.search_var = ctk.StringVar()
        self.dept_var = ctk.StringVar(value="All departments")
        self.gender_var = ctk.StringVar(value="All genders")
        self.search_entry = entry(bar, "Search name, ID, doctor, diagnosis...",
                                  width=250, textvariable=self.search_var)
        self.search_entry.pack(side="left")
        self.dept_menu = dropdown(bar, ["All departments"], self.dept_var, 150,
                                  lambda v: self.refresh())
        self.dept_menu.pack(side="left", padx=8)
        dropdown(bar, ["All genders", "Male", "Female", "Other"], self.gender_var, 110,
                 lambda v: self.refresh()).pack(side="left")
        button(bar, "Clear", self.clear_filters, "secondary", width=60).pack(side="left", padx=8)
        self.search_var.trace_add("write", lambda *a: self.refresh())

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=8)
        button(actions, "View Details", self.view_details, width=110).pack(side="left")
        button(actions, "Edit", self.edit, "secondary", width=70).pack(side="left", padx=8)
        button(actions, "Delete", self.delete, "danger", width=80).pack(side="left")
        HelpButton(actions, "patients").pack(side="left", padx=8)

        card = Card(self)
        card.pack(fill="both", expand=True)
        self.table = StyledTable(card, COLUMNS, WIDTHS, height=14, on_sort=self.on_sort,
                                 on_double_click=self.view_details)
        self.table.pack(fill="both", expand=True, padx=16, pady=16)

    def restyle(self):
        self.table.restyle()

    def clear_filters(self):
        self.search_var.set("")
        self.dept_var.set("All departments")
        self.gender_var.set("All genders")
        self.sort_info = None
        self.table.reset_sort_marks()
        self.refresh()

    def on_sort(self, column, descending):
        self.sort_info = (column, descending)
        self.refresh()

    def refresh(self):
        patients = self.manager.all_patients()         # BST in-order = sorted by ID
        departments = []
        for patient in patients:
            if patient.department not in departments:
                departments.append(patient.department)
        self.dept_menu.configure(values=["All departments"] + departments)
        needle = self.search_var.get().strip().lower()
        dept, gender = self.dept_var.get(), self.gender_var.get()
        matches = []
        for patient in patients:                        # linear search O(n)
            if dept != "All departments" and patient.department != dept:
                continue
            if gender != "All genders" and patient.gender != gender:
                continue
            if needle and not any(needle in str(cell).lower() for cell in patient.as_row()):
                continue
            matches.append(patient)
        comparisons = 0
        if self.sort_info is not None:
            matches, comparisons = self.manager.sort_patients(matches, *self.sort_info)
        self.table.clear()
        for patient in matches:
            row = list(patient.as_row())
            self.table.add_row(row)
        self.table.finish("patients")
        if self.sort_info is not None:
            self.trace("sorted %d rows by '%s' (%s)\nmerge sort: %d comparisons" % (
                len(matches), COLUMNS[self.sort_info[0]],
                "descending" if self.sort_info[1] else "ascending", comparisons))
            self.app.set_status("Sort by %s • Merge sort • %d comparisons" % (
                COLUMNS[self.sort_info[0]], comparisons))
        else:
            self.trace("BST in-order traversal visited %d nodes\nfilter scanned %d records "
                       "(linear search), %d matched" % (len(patients), len(patients), len(matches)))

    def _selected_id(self):
        row = self.table.selected()
        if not row:
            messagebox.showinfo("Select a patient", "Please select a row first.")
            return None
        return int(row[0])

    def view_details(self):
        patient_id = self._selected_id()
        if patient_id is not None:
            open_profile_window(self.app, patient_id)

    def edit(self):
        patient_id = self._selected_id()
        if patient_id is not None:
            self.app.edit_patient(patient_id)

    def delete(self):
        patient_id = self._selected_id()
        if patient_id is None:
            return
        patient = self.manager.get_patient(patient_id)
        if not messagebox.askyesno(
                "Confirm delete", "Delete patient %d (%s) permanently?" % (
                    patient_id, patient.name if patient else "?")):
            return
        try:
            self.manager.delete_patient(patient_id)
        except Exception as error:
            messagebox.showerror("Delete failed", str(error))
            return
        self.app.set_status("Delete %d • Hash + BST delete" % patient_id)
        self.app.toast.show("Patient %d deleted" % patient_id, "info")
        self.app.notify_change()
