"""Scrollable, zoomable canvas that draws the BST.

Layout rule (no overlaps): x = position of the node in the in-order sequence
(every node gets its own column), y = depth of the node.
"""
import tkinter as tk

import customtkinter as ctk

from gui import theme
from gui.theme import S, font, mono, pal
from gui.widgets import open_profile_window


class BSTCanvas(ctk.CTkFrame):
    HIGHLIGHT_STATES = ("path", "found", "included", "visited", "order")

    def __init__(self, parent, app, height=320):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.zoom_level = 1.0
        self.states = {}        # node key -> "path" | "found" | "visited" | ...
        self.badges = {}        # node key -> small text drawn above the node
        self.canvas = tk.Canvas(self, height=height, highlightthickness=1,
                                bg=pal()["canvas_bg"])
        vbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        hbar = ctk.CTkScrollbar(self, orientation="horizontal",
                                command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        self.canvas.bind("<Shift-MouseWheel>",
                         lambda e: self.canvas.xview_scroll(-1 * (e.delta // 120), "units"))

    def zoom(self, factor):
        self.zoom_level = max(0.5, min(2.5, self.zoom_level * factor))
        self.redraw()

    def set_states(self, states, badges=None):
        self.states = states
        self.badges = badges or {}
        self.redraw()

    def clear_states(self):
        self.set_states({}, {})

    def _fill_for(self, state):
        colors = pal()
        return {
            "path": (colors["node_hot"], colors["node_hot"]),
            "found": (colors["node_found"], colors["node_found"]),
            "included": (colors["node_found"], colors["node_found"]),
            "visited": (colors["visited"], colors["node_line"]),
            "order": (colors["node_hot"], colors["node_hot"]),
            "pruned": (colors["pruned"], colors["faint"]),
        }.get(state, (colors["node"], colors["node_line"]))

    def redraw(self):
        colors = pal()
        canvas = self.canvas
        canvas.delete("all")
        canvas.configure(bg=colors["canvas_bg"], highlightbackground=colors["border"])
        tree = self.app.manager.bst
        z = self.zoom_level
        step_x, step_y, radius = S(46) * z, S(66) * z, S(17) * z
        positions = {}
        counter = [0]

        def place(node, depth):
            if node is None:
                return
            place(node.left, depth + 1)
            positions[node.key] = (S(36) + counter[0] * step_x, S(40) + depth * step_y)
            counter[0] += 1
            place(node.right, depth + 1)

        place(tree.root, 0)
        if not positions:
            canvas.create_text(S(20), S(20), anchor="nw", fill=colors["muted"],
                               text="The tree is empty.", font=font(12))
            return

        def edges(node):
            if node is None:
                return
            for child in (node.left, node.right):
                if child is None:
                    continue
                x1, y1 = positions[node.key]
                x2, y2 = positions[child.key]
                hot = (self.states.get(node.key) in self.HIGHLIGHT_STATES
                       and self.states.get(child.key) in self.HIGHLIGHT_STATES)
                canvas.create_line(x1, y1, x2, y2,
                                   fill=colors["node_hot"] if hot else colors["arrow"],
                                   width=2 if hot else 1)
                edges(child)

        edges(tree.root)
        text_size = max(6, int(8 * z))
        for key, (x, y) in positions.items():
            state = self.states.get(key)
            fill, outline = self._fill_for(state)
            tag = "n%d" % key
            canvas.create_oval(x - radius, y - radius * 0.8, x + radius, y + radius * 0.8,
                               fill=fill, outline=outline, width=1, tags=(tag,))
            ink = colors["on_fill"] if state in ("path", "found", "included", "order") else colors["text"]
            canvas.create_text(x, y, text=str(key), tags=(tag,),
                               fill=colors["muted"] if state == "pruned" else ink,
                               font=mono(text_size, "bold"))
            if key in self.badges:
                canvas.create_text(x, y - radius - S(8), text=str(self.badges[key]),
                                   fill=colors["primary_text"], font=mono(text_size, "bold"))
            canvas.tag_bind(tag, "<Enter>", lambda e, k=key: self._tip(e, k))
            canvas.tag_bind(tag, "<Leave>", lambda e: self.app.tooltip.hide())
            canvas.tag_bind(tag, "<Button-1>", lambda e, k=key: open_profile_window(self.app, k))
        canvas.configure(scrollregion=(0, 0, S(72) + counter[0] * step_x,
                                       S(80) + tree.height() * step_y))

    def _tip(self, event, key):
        patient = self.app.manager.get_patient(key)
        if patient:
            self.app.tooltip.show("%d  %s  (%s)\nDepth %d" % (
                key, patient.name, patient.department,
                self.app.manager.bst.depth_of(key)), event.x_root, event.y_root)
