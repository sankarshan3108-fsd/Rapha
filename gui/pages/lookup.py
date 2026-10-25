"""Lookup by ID using the hash table, with a step-by-step animation."""
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.base import Page
from gui.theme import font, mono, pair
from gui.visualizers.hash_animation import LookupCanvas
from gui.widgets import Card, HelpButton, ProfileCard, button, entry, label


class LookupPage(Page):
    key = "lookup"
    title = "Lookup by ID"
    subtitle = "Hashing with Separate Chaining • O(1) average"

    def __init__(self, app):
        super().__init__(app)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        search = Card(body)
        search.pack(fill="x")
        label(search, "Enter a patient ID", 15, "bold").pack(pady=(16, 8))
        row = ctk.CTkFrame(search, fg_color="transparent")
        row.pack(pady=(0, 16))
        self.id_var = ctk.StringVar()
        self.entry = entry(row, "e.g. 1045", width=320, textvariable=self.id_var)
        self.entry.configure(height=48, font=mono(18))
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda e: self.lookup())
        big = button(row, "Lookup", self.lookup, width=120)
        big.configure(height=48)
        big.pack(side="left", padx=8)
        HelpButton(row, "lookup").pack(side="left")

        viz_card = Card(body)
        viz_card.pack(fill="x", pady=(16, 0))
        label(viz_card, "Hash computation", 13, "bold").pack(anchor="w", padx=16, pady=(16, 0))
        self.canvas = LookupCanvas(viz_card)
        self.canvas.pack(fill="x", padx=16, pady=8)
        self.canvas.idle("Type an ID and press Lookup to watch the hash function work.")
        self.result_holder = ctk.CTkFrame(body, fg_color="transparent")
        self.result_holder.pack(fill="x", pady=(16, 0))

    def restyle(self):
        self.canvas.render() if self.canvas.data else self.canvas.idle(
            "Type an ID and press Lookup to watch the hash function work.")

    def on_show(self):
        self.entry.focus_set()

    def clear_result(self):
        for child in self.result_holder.winfo_children():
            child.destroy()

    def lookup(self):
        text = self.id_var.get().strip()
        if not text.isdigit():
            messagebox.showerror("Invalid ID", "Please enter a numeric patient ID (digits only).")
            return
        key = int(text)
        patient, slot, steps, size = self.manager.lookup_trace(key)
        self.clear_result()
        comparisons = len(steps)
        walk = " → ".join("compare %d %s" % (k, "(match)" if hit else "(no match)") for k, hit in steps)
        self.trace("h(%d) = %d %% %d = %d%s\n%s\n%d comparison(s) (linear search could need %d)" % (
            key, key, size, slot, "" if steps else " → slot is empty",
            walk or "no nodes to compare → not found", comparisons, self.manager.count()))
        self.app.set_status("Lookup %d • Hashing • %d comparison%s%s" % (
            key, comparisons, "" if comparisons == 1 else "s",
            "" if patient else " • not found"))
        self.canvas.play(key, slot, size, steps, on_done=lambda: self.show_result(key, patient, slot, comparisons))

    def show_result(self, key, patient, slot, comparisons):
        self.clear_result()
        if patient is not None:
            ProfileCard(self.result_holder, self.manager, patient).pack(fill="x")
            return
        card = Card(self.result_holder)
        card.pack(fill="x")
        label(card, "No patient with ID %d" % key, 16, "bold", "danger").pack(
            anchor="w", padx=16, pady=(16, 2))
        label(card, "Slot %d was checked (%d comparison%s) and nothing matched.\n"
                    "Try another ID, or add this patient from the Add Patient page." % (
                        slot, comparisons, "" if comparisons == 1 else "s"),
              12, color="muted").pack(anchor="w", padx=16, pady=(0, 16))
