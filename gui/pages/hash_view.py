"""Hash table view: all slots and chains, colour-coded by chain length."""
import customtkinter as ctk

from gui.pages.base import Page
from gui.theme import pal
from gui.visualizers.hash_animation import HashCanvas
from gui.widgets import Card, Chip, HelpButton, button, label


class HashViewPage(Page):
    key = "hash_view"
    title = "Hash Table View"
    subtitle = "Separate Chaining • id % size • collisions form linked chains"

    def __init__(self, app):
        super().__init__(app)
        chips = ctk.CTkFrame(self, fg_color="transparent")
        chips.pack(fill="x")
        self.chips = {}
        for key, caption in (("size", "Table size"), ("records", "Records"),
                             ("load", "Load factor"), ("collisions", "Collisions"),
                             ("longest", "Longest chain"), ("empty", "Empty slots")):
            chip = Chip(chips, caption)
            chip.pack(side="left", padx=(0, 8))
            self.chips[key] = chip
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=8)
        self.legend_items = []
        for text, colour in (("empty", "faint"), ("1 node", "node"), ("2+ nodes (collision)", "collide")):
            swatch = ctk.CTkLabel(bar, text="  ", width=18, height=18, corner_radius=4,
                                  fg_color=pal()[colour])
            swatch.pack(side="left")
            self.legend_items.append((swatch, colour))
            label(bar, text, 11, color="muted").pack(side="left", padx=(4, 16))
        HelpButton(bar, "hash_view").pack(side="right")
        button(bar, "+", lambda: self.canvas.zoom(1.25), "secondary", width=40).pack(side="right", padx=4)
        button(bar, "-", lambda: self.canvas.zoom(0.8), "secondary", width=40).pack(side="right")
        label(bar, "Zoom:", 11, color="muted").pack(side="right", padx=8)
        card = Card(self)
        card.pack(fill="both", expand=True)
        self.canvas = HashCanvas(card, app)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

    def restyle(self):
        for swatch, colour in self.legend_items:
            swatch.configure(fg_color=pal()[colour])

    def refresh(self):
        table = self.manager.hash_table
        self.chips["size"].set(table.size)
        self.chips["records"].set(table.count)
        self.chips["load"].set("%.2f" % table.load_factor())
        self.chips["collisions"].set(table.collisions)
        self.chips["longest"].set(table.longest_chain())
        self.chips["empty"].set(table.empty_slots())
        self.canvas.redraw()
        self.trace("size %d | records %d | load %.2f\ncollisions %d (inserts that hit a used slot)\n"
                   "longest chain %d → worst lookup = %d comparisons\nempty slots %d of %d\n"
                   "rehashes so far: %d" % (
                       table.size, table.count, table.load_factor(), table.collisions,
                       table.longest_chain(), table.longest_chain(), table.empty_slots(),
                       table.size, table.rehash_count))
