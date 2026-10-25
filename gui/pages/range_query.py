"""Range query on the BST with visited / included / pruned visualisation."""
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.base import Page
from gui.visualizers.bst_canvas import BSTCanvas
from gui.widgets import Card, Chip, HelpButton, StyledTable, button, entry, label

COLUMNS = ("ID", "Name", "Age", "Gender", "Department", "Diagnosis", "Doctor", "Admitted")
WIDTHS = (50, 106, 36, 62, 110, 100, 90, 88)
PRESETS = [(1001, 1025), (1026, 1050), (1040, 1060), (1061, 1100)]


class RangeQueryPage(Page):
    key = "range"
    title = "Range Query"
    subtitle = "BST Pruned In-order Traversal • O(h + k)"

    def __init__(self, app):
        super().__init__(app)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        controls = Card(body)
        controls.pack(fill="x")
        row = ctk.CTkFrame(controls, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(16, 8))
        self.low_var, self.high_var = ctk.StringVar(), ctk.StringVar()
        label(row, "Low ID", 11, "bold", "muted").pack(side="left")
        entry(row, "1001", width=100, textvariable=self.low_var).pack(side="left", padx=(8, 16))
        label(row, "High ID", 11, "bold", "muted").pack(side="left")
        high_entry = entry(row, "1050", width=100, textvariable=self.high_var)
        high_entry.pack(side="left", padx=(8, 16))
        high_entry.bind("<Return>", lambda e: self.search())
        button(row, "Search Range", self.search, width=120).pack(side="left")
        HelpButton(row, "range").pack(side="left", padx=8)
        presets = ctk.CTkFrame(controls, fg_color="transparent")
        presets.pack(fill="x", padx=16, pady=(0, 16))
        label(presets, "Quick ranges:", 11, color="muted").pack(side="left", padx=(0, 8))
        for low, high in PRESETS:
            button(presets, "%d–%d" % (low, high), lambda l=low, h=high: self.preset(l, h),
                   "secondary", width=100).pack(side="left", padx=4)

        chips = ctk.CTkFrame(body, fg_color="transparent")
        chips.pack(fill="x", pady=8)
        self.chip_found = Chip(chips, "Results found")
        self.chip_visited = Chip(chips, "Nodes visited")
        self.chip_pruned = Chip(chips, "Nodes skipped (pruned)")
        for chip in (self.chip_found, self.chip_visited, self.chip_pruned):
            chip.pack(side="left", padx=(0, 8))

        table_card = Card(body)
        table_card.pack(fill="x")
        self.table = StyledTable(table_card, COLUMNS, WIDTHS, height=8)
        self.table.pack(fill="x", padx=16, pady=16)

        tree_card = Card(body)
        tree_card.pack(fill="x", pady=(16, 0))
        label(tree_card, "BST traversal (green = included, teal = visited only, grey = pruned)",
              12, "bold").pack(anchor="w", padx=16, pady=(8, 0))
        self.tree_view = BSTCanvas(tree_card, app, height=250)
        self.tree_view.pack(fill="x", padx=16, pady=8)
        self.last_range = None

    def restyle(self):
        self.table.restyle()

    def refresh(self):
        if self.last_range:
            self.run(*self.last_range, announce=False)
        else:
            self.tree_view.redraw()

    def preset(self, low, high):
        self.low_var.set(str(low))
        self.high_var.set(str(high))
        self.search()

    def search(self):
        low_text, high_text = self.low_var.get().strip(), self.high_var.get().strip()
        if not (low_text.isdigit() and high_text.isdigit()):
            messagebox.showerror("Invalid input", "Low and High must both be numeric IDs.")
            return
        low, high = int(low_text), int(high_text)
        if low > high:
            messagebox.showerror("Invalid range", "Low ID must not be larger than High ID.")
            return
        self.run(low, high)

    def run(self, low, high, announce=True):
        self.last_range = (low, high)
        results, visited_count = self.manager.range_query(low, high)    # pruned in-order walk
        visited, included, pruned = self.manager.bst.range_trace(low, high)
        total = self.manager.bst.size()
        self.table.clear()
        for patient in results:
            self.table.add_row(patient.as_row())
        self.table.finish("results")
        skipped = total - visited_count
        self.chip_found.set(len(results))
        self.chip_visited.set("%d of %d" % (visited_count, total))
        self.chip_pruned.set(skipped)
        states = {}
        for key in self.manager.bst.inorder_keys():
            states[key] = "pruned"
        for key in visited:
            states[key] = "visited"
        for key in included:
            states[key] = "included"
        self.tree_view.set_states(states)
        self.trace("range [%d, %d]\nvisited (%d): %s\nincluded (%d): %s\npruned subtrees rooted at: %s\n"
                   "skipped %d of %d nodes" % (
                       low, high, len(visited), ", ".join(map(str, visited)),
                       len(included), ", ".join(map(str, included)) or "none",
                       ", ".join(map(str, pruned)) or "none", skipped, total))
        if announce:
            self.app.set_status("Range %d–%d • BST • %d nodes visited, %d results" % (
                low, high, visited_count, len(results)))
