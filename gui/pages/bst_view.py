"""BST view: drawing, animated search path and animated traversals."""
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.base import Page
from gui.utils import best_height
from gui.visualizers.bst_canvas import BSTCanvas
from gui.widgets import Card, Chip, HelpButton, button, entry, label

STEP_MS = 550


class BSTViewPage(Page):
    key = "bst_view"
    title = "BST View"
    subtitle = "Binary Search Tree • search O(log n) avg • traversals O(n)"

    def __init__(self, app):
        super().__init__(app)
        self.job = None
        chips = ctk.CTkFrame(self, fg_color="transparent")
        chips.pack(fill="x")
        self.chips = {}
        for key, caption in (("height", "Height"), ("best", "Best possible"),
                             ("worst", "Worst case"), ("nodes", "Nodes"), ("leaves", "Leaves")):
            chip = Chip(chips, caption)
            chip.pack(side="left", padx=(0, 8))
            self.chips[key] = chip

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 4))
        self.search_var = ctk.StringVar()
        search = entry(bar, "Patient ID", width=96, textvariable=self.search_var)
        search.pack(side="left")
        search.bind("<Return>", lambda e: self.animate_search())
        button(bar, "Animate Search", self.animate_search, width=112).pack(side="left", padx=4)
        for text, order in (("In-order", "in"), ("Pre-order", "pre"), ("Post-order", "post")):
            button(bar, text, lambda o=order: self.animate_traversal(o), "secondary",
                   width=70).pack(side="left", padx=2)
        HelpButton(bar, "bst_view").pack(side="left", padx=4)
        button(bar, "+", lambda: self.view.zoom(1.25), "secondary", width=32).pack(side="right", padx=2)
        button(bar, "-", lambda: self.view.zoom(0.8), "secondary", width=32).pack(side="right")
        label(bar, "Zoom:", 11, color="muted").pack(side="right", padx=8)

        self.message = label(self, " ", 12, "bold", "primary", wraplength=800)
        self.message.pack(anchor="w", pady=(2, 4))
        card = Card(self)
        card.pack(fill="both", expand=True)
        self.view = BSTCanvas(card, app, height=300)
        self.view.pack(fill="both", expand=True, padx=8, pady=8)
        self.sequence = label(self, " ", 11, wraplength=800, color="muted")
        self.sequence.pack(anchor="w", pady=(8, 0))

    def stop(self):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None

    def refresh(self):
        self.stop()
        tree = self.manager.bst
        n = tree.size()
        self.chips["height"].set(tree.height())
        self.chips["best"].set(best_height(n))
        self.chips["worst"].set(n)
        self.chips["nodes"].set(n)
        self.chips["leaves"].set(tree.leaf_count())
        self.view.clear_states()
        self.message.configure(text="Tree height %d (best possible %d, worst case %d)." % (
            tree.height(), best_height(n), n))
        self.sequence.configure(text=" ")
        self.trace("height %d | best %d | worst %d\nnodes %d | leaves %d\n"
                   "root = %s (first node inserted after shuffle)" % (
                       tree.height(), best_height(n), n, n, tree.leaf_count(),
                       tree.root.key if tree.root else "none"))

    # ---------- animated search ----------
    def animate_search(self):
        text = self.search_var.get().strip()
        if not text.isdigit():
            messagebox.showerror("Invalid ID", "Please enter a numeric patient ID.")
            return
        key = int(text)
        self.stop()
        found, steps = self.manager.bst.search_steps(key)
        self.sequence.configure(text=" ")
        self.view.clear_states()
        compared = len(steps) if found else len(steps) - 1
        self.app.set_status("BST search %d • %d comparison%s%s" % (
            key, compared, "" if compared == 1 else "s",
            "" if found else " • not found"))
        self.trace("\n".join(text for _, text in steps) +
                   ("\nfound after %d node(s)" % len(steps) if found else "\nnot found"))
        self._search_step(key, found, steps, 0, {})

    def _search_step(self, key, found, steps, index, states):
        node_key, text = steps[index]
        self.message.configure(text="Step %d: %s" % (index + 1, text))
        if node_key is not None:
            last = index == len(steps) - 1 and found
            states[node_key] = "found" if last else "path"
            self.view.set_states(dict(states))
            self.view.canvas.update_idletasks()
        if index + 1 < len(steps):
            self.job = self.after(STEP_MS, lambda: self._search_step(key, found, steps, index + 1, states))
        else:
            self.job = None
            if not found:
                self.message.configure(text=self.message.cget("text"))

    # ---------- animated traversals ----------
    def animate_traversal(self, order):
        self.stop()
        tree = self.manager.bst
        keys = {"in": tree.inorder_keys, "pre": tree.preorder_keys,
                "post": tree.postorder_keys}[order]()
        names = {"in": ("In-order", "Left → Root → Right (sorted IDs)"),
                 "pre": ("Pre-order", "Root → Left → Right"),
                 "post": ("Post-order", "Left → Right → Root")}[order]
        self.message.configure(text="%s traversal: %s" % names)
        self.view.clear_states()
        self.sequence.configure(text="Sequence: ")
        self.app.set_status("%s traversal • BST • %d nodes" % (names[0], len(keys)))
        self.trace("%s: %s\n%s" % (names[0], names[1], ", ".join(map(str, keys))))
        self._traversal_step(keys, 0, {}, {})

    def _traversal_step(self, keys, index, states, badges):
        if index >= len(keys):
            self.job = None
            return
        states[keys[index]] = "order"
        badges[keys[index]] = index + 1
        self.view.set_states(dict(states), dict(badges))
        self.sequence.configure(text="Sequence: " + ", ".join(map(str, keys[: index + 1])))
        self.job = self.after(260, lambda: self._traversal_step(keys, index + 1, states, badges))
