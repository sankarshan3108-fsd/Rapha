"""Add / Edit patient with live validation and an 'insertion result' card."""
import datetime
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.base import Page
from gui.theme import pair, pal
from gui.utils import bst_compare_text
from gui.widgets import (Card, DateEntry, HelpButton, button, dropdown, entry, label)
from patient import Patient

GENDERS = ["Male", "Female", "Other"]
DEPARTMENTS = ["Cardiology", "Orthopedics", "Pediatrics", "General Medicine",
               "Neurology", "ENT"]
PLACEHOLDER_CHOICE = "Select..."


class FormField:
    """One labelled input with its own inline error message."""

    def __init__(self, parent, text, row, column, kind="entry", options=None,
                 placeholder="", on_change=None, extra=None):
        self.var = ctk.StringVar(value=PLACEHOLDER_CHOICE if kind == "menu" else "")
        self.kind = kind
        self.touched = False
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.grid(row=row, column=column, sticky="ew", padx=16, pady=8)
        label(self.frame, text, 11, "bold", "muted").pack(anchor="w")
        if kind == "menu":
            self.widget = dropdown(self.frame, [PLACEHOLDER_CHOICE] + options, self.var, 250,
                                   lambda v: on_change())
            self.widget.pack(anchor="w", pady=(2, 0))
            self.border_target = None
        elif kind == "date":
            self.widget = DateEntry(self.frame, self.var, width=250)
            self.widget.pack(anchor="w", pady=(2, 0))
            self.border_target = self.widget.entry
        elif kind == "id":
            holder = ctk.CTkFrame(self.frame, fg_color="transparent")
            holder.pack(anchor="w", pady=(2, 0))
            self.widget = entry(holder, placeholder, width=120, textvariable=self.var)
            self.widget.pack(side="left")
            self.suggest_button = button(holder, "Suggest free ID", extra, "secondary", width=122)
            self.suggest_button.pack(side="left", padx=(8, 0))
            self.border_target = self.widget
        else:
            self.widget = entry(self.frame, placeholder, width=250, textvariable=self.var)
            self.widget.pack(anchor="w", pady=(2, 0))
            self.border_target = self.widget
        self.error = label(self.frame, " ", 11, color="danger")
        self.error.pack(anchor="w")
        self.var.trace_add("write", lambda *a: on_change())

    def get(self):
        value = self.var.get().strip()
        return "" if value == PLACEHOLDER_CHOICE else value

    def show(self, message):
        """Show an error (or green border when message == '')."""
        self.error.configure(text=message or " ")
        if self.border_target is not None:
            colour = pair("danger") if message else (pair("success") if self.get() else pair("border"))
            self.border_target.configure(border_color=colour)


class AddPatientPage(Page):
    key = "add"
    title = "Add / Edit Patient"
    subtitle = "Hashing with Separate Chaining (id % size) • BST insertion • O(1) avg / O(log n) avg"

    def __init__(self, app):
        super().__init__(app)
        self.editing_id = None
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self.form_card = Card(body)
        self.form_card.pack(fill="x")
        self.heading = label(self.form_card, "Register a new patient", 16, "bold")
        self.heading.pack(anchor="w", padx=16, pady=(16, 0))
        grid = ctk.CTkFrame(self.form_card, fg_color="transparent")
        grid.pack(fill="x", padx=4, pady=4)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="f")
        check = self.live_validate
        self.fields = {
            "id": FormField(grid, "Patient ID", 0, 0, "id", placeholder="e.g. 1101",
                            on_change=check, extra=self.suggest_id),
            "name": FormField(grid, "Full name", 1, 0, placeholder="e.g. Anita Rao", on_change=check),
            "age": FormField(grid, "Age (0-120)", 2, 0, placeholder="e.g. 34", on_change=check),
            "gender": FormField(grid, "Gender", 3, 0, "menu", GENDERS, on_change=check),
            "department": FormField(grid, "Department", 0, 1, "menu", DEPARTMENTS, on_change=check),
            "diagnosis": FormField(grid, "Diagnosis", 1, 1, placeholder="e.g. Asthma", on_change=check),
            "doctor": FormField(grid, "Doctor", 2, 1, placeholder="e.g. Dr. K. Rao", on_change=check),
            "date": FormField(grid, "Admission date", 3, 1, "date", on_change=check),
        }
        self.suggest_button = self.fields["id"].suggest_button
        buttons = ctk.CTkFrame(self.form_card, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=(4, 16))
        self.save_button = button(buttons, "Save Patient", self.save, width=140)
        self.save_button.pack(side="left")
        HelpButton(buttons, "add").pack(side="left", padx=8)
        button(buttons, "Clear", self.reset_form, "secondary", width=80).pack(side="left")
        self.cancel_button = button(buttons, "Cancel edit", self.cancel_edit, "secondary", width=110)

        self.result_card = Card(body)
        self.result_title = label(self.result_card, "Insertion result", 14, "bold", "primary")
        self.result_title.pack(anchor="w", padx=16, pady=(16, 4))
        self.result_text = label(self.result_card, "", 12, wraplength=560)
        self.result_text.pack(anchor="w", padx=16, pady=(0, 16))
        self.reset_form()

    # ---------- form state ----------
    def on_show(self):
        if self.editing_id is None and not self.fields["id"].get():
            self.suggest_id()

    def suggest_id(self):
        if self.editing_id is None:
            self.fields["id"].var.set(str(self.manager.next_free_id()))

    def reset_form(self):
        self.editing_id = None
        self.heading.configure(text="Register a new patient")
        self.save_button.configure(text="Save Patient")
        self.cancel_button.pack_forget()
        self.fields["id"].widget.configure(state="normal")
        self.suggest_button.pack(side="left", padx=(8, 0))
        for field in self.fields.values():
            field.var.set(PLACEHOLDER_CHOICE if field.kind == "menu" else "")
            field.touched = False
            field.show("")
        self.fields["date"].var.set(datetime.date.today().isoformat())
        self.fields["id"].show("")
        self.fields["date"].show("")
        self.fields["id"].var.set(str(self.manager.next_free_id()))

    def load_for_edit(self, patient):
        self.reset_form()
        self.editing_id = patient.patient_id
        self.heading.configure(text="Edit patient %d" % patient.patient_id)
        self.save_button.configure(text="Update Patient")
        self.cancel_button.pack(side="left", padx=8)
        self.suggest_button.pack_forget()
        values = {"id": str(patient.patient_id), "name": patient.name, "age": str(patient.age),
                  "gender": patient.gender, "department": patient.department,
                  "diagnosis": patient.diagnosis, "doctor": patient.doctor,
                  "date": patient.admission_date}
        for key, value in values.items():
            self.fields[key].var.set(value)
        self.fields["id"].widget.configure(state="disabled")
        self.result_card.pack_forget()

    def cancel_edit(self):
        self.reset_form()
        self.app.navigate("patients")

    # ---------- validation ----------
    def error_for(self, key, value):
        """Return an error message for one field or '' when valid."""
        if key == "id":
            if not value:
                return "Patient ID is required."
            if not value.isdigit() or int(value) <= 0:
                return "ID must be a positive whole number."
            if self.editing_id is None and self.manager.get_patient(int(value)) is not None:
                return "ID %s already exists (found by hash lookup)." % value
        elif key == "name":
            if not value:
                return "Name is required."
            if len(value) < 2:
                return "Name is too short."
        elif key == "age":
            if not value:
                return "Age is required."
            if not value.isdigit() or not 0 <= int(value) <= 120:
                return "Age must be a number from 0 to 120."
        elif key == "date":
            if not value:
                return "Admission date is required."
            try:
                parsed = datetime.datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return "Use a valid date like 2026-10-25."
            if parsed.strftime("%Y-%m-%d") != value:
                return "Use the format YYYY-MM-DD."
        elif not value:
            return "%s is required." % key.capitalize()
        return ""

    def live_validate(self):
        """Colour borders / messages while typing (only for touched fields)."""
        for key, field in self.fields.items():
            value = field.get()
            if value or field.touched:
                field.touched = True
                field.show(self.error_for(key, value))

    def validate_all(self):
        first_error = ""
        for key, field in self.fields.items():
            field.touched = True
            message = self.error_for(key, field.get())
            field.show(message)
            first_error = first_error or message
        return first_error

    # ---------- saving ----------
    def save(self):
        if self.validate_all():
            messagebox.showerror("Please fix the form", "Some fields are invalid - see the red messages.")
            return
        values = {key: field.get() for key, field in self.fields.items()}
        patient = Patient(int(values["id"]), values["name"], int(values["age"]),
                          values["gender"], values["department"], values["diagnosis"],
                          values["doctor"], values["date"])
        try:
            if self.editing_id is not None:
                self.manager.update_patient(patient)
                self.after_update(patient)
            else:
                slot = self.manager.add_patient(patient)
                self.after_insert(patient, slot)
        except Exception as error:
            messagebox.showerror("Could not save", str(error))

    def after_update(self, patient):
        self.app.toast.show("Patient %d updated" % patient.patient_id)
        self.app.set_status("Update %d • Hash + BST + SQLite" % patient.patient_id)
        self.app.notify_change()
        self.reset_form()
        self.app.navigate("patients")

    def after_insert(self, patient, slot):
        info = self.manager.last_add_info
        size = info["size_after"]
        lines = ["Hash: %d %% %d = %d" % (patient.patient_id, info["size_before"], info["slot_before"])]
        if info["chain_before"]:
            lines.append("Slot %d already held %s → collision, appended to the chain" % (
                info["slot_before"], " → ".join(map(str, info["chain_before"]))))
        else:
            lines.append("Slot %d was empty → became the first node" % info["slot_before"])
        lines.append("Chain at slot %d: %s" % (info["slot"], " → ".join(map(str, info["chain"]))))
        path = info["bst_path"]
        if path:
            lines.append("BST path: " + " → ".join(map(str, path)))
            lines.append("Inserted as %s child of %d" % (info["bst_side"], info["bst_parent"]))
        else:
            lines.append("BST was empty → became the root")
        count_before = self.manager.hash_table.count - 1
        if info["rehashed"]:
            lines.append("Rehash: YES - load factor %.2f exceeded 0.75, size %d → %d (new slot %d)" % (
                (count_before + 1) / info["size_before"], info["size_before"], size, info["slot"]))
        else:
            lines.append("Rehash: No (load factor %.2f ≤ 0.75)" % info["load_factor"])
        self.result_text.configure(text="\n".join(lines))
        self.result_card.pack(fill="x", pady=(16, 0))
        # live trace in the algorithm panel
        compare = "; ".join(bst_compare_text(patient.patient_id, path)) if path else "tree was empty"
        self.trace("%d %% %d = %d → slot %d %s.\nBST: %s → inserted as %s child of %s.\nRehash: %s (%.2f %s 0.75)." % (
            patient.patient_id, info["size_before"], info["slot_before"], info["slot_before"],
            "occupied → collision, appended" if info["chain_before"] else "empty → inserted",
            compare, info["bst_side"], info["bst_parent"],
            "Yes" if info["rehashed"] else "No", info["load_factor"],
            ">" if info["rehashed"] else "<"))
        comparisons = len(info["chain_before"]) + len(path)
        self.app.toast.show("Patient %d added • hash slot %d" % (patient.patient_id, slot))
        self.app.set_status("Insert %d • Hashing + BST • %d comparisons" % (
            patient.patient_id, comparisons))
        self.app.notify_change()
        self.fields["name"].var.set("")
        for key in ("name", "age", "diagnosis", "doctor"):
            self.fields[key].var.set("")
            self.fields[key].touched = False
            self.fields[key].show("")
        for key in ("gender", "department"):
            self.fields[key].var.set(PLACEHOLDER_CHOICE)
            self.fields[key].touched = False
            self.fields[key].show("")
        self.fields["id"].touched = False
        self.fields["id"].var.set(str(self.manager.next_free_id()))
        self.fields["id"].show("")
