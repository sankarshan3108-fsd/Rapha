"""About page: project brief, architecture diagram, complexity table, team."""
import tkinter as tk

import customtkinter as ctk

from gui.pages.base import Page
from gui.theme import S, font, pair, pal
from gui.widgets import Card, HelpButton, label

SCOPE = ("Maintain at least 25 patient records in a hash table keyed by patient ID for "
         "direct access. Separately maintain the same records in a BST keyed by patient ID "
         "to support ordered operations (e.g., listing patients within an ID range). "
         "Implement merge sort to order patients by admission date for a daily report.")
EXPECTED = ("A program demonstrating record insertion/lookup via hashing, a range-query "
            "listing via the BST's in-order traversal, and a sorted daily admission report.")

COMPLEXITY = [
    ("Operation", "Average", "Worst", "Space"),
    ("Hash insert / search / delete", "O(1)", "O(n)", "O(n)"),
    ("Hash rehash", "O(n)", "O(n)", "O(n)"),
    ("BST insert / search / delete", "O(log n)", "O(n) skewed", "O(n)"),
    ("BST in-order traversal", "O(n)", "O(n)", "O(h)"),
    ("BST range query", "O(h + k)", "O(n)", "O(h)"),
    ("Merge sort (daily report)", "O(n log n)", "O(n log n)", "O(n)"),
    ("Linear text search", "O(n)", "O(n)", "O(1)"),
]

TEAM = [("J Asher", "URK25CS1035"), ("Priyadharshan N", "URK25CS1028"),
        ("Sankar S", "URK25CS1027")]


class AboutPage(Page):
    key = "about"
    title = "About Project"
    subtitle = "Why a hash table + BST + merge sort in a hospital system"

    def __init__(self, app):
        super().__init__(app)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        head = Card(body)
        head.pack(fill="x")
        row = ctk.CTkFrame(head, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(16, 4))
        label(row, "Micro Project – 07: Hospital Patient Record System", 20, "bold",
              "primary", wraplength=520).pack(side="left")
        HelpButton(row, "about").pack(side="right")
        label(head, "Industry Focus: Healthcare      Integrated COs: CO2, CO3, CO4", 12, "bold",
              "muted").pack(anchor="w", padx=16, pady=(0, 16))

        brief = Card(body)
        brief.pack(fill="x", pady=(16, 0))
        label(brief, "Project Scope", 14, "bold").pack(anchor="w", padx=16, pady=(16, 2))
        label(brief, SCOPE, 12, wraplength=560).pack(anchor="w", padx=16)
        label(brief, "Expected Output", 14, "bold").pack(anchor="w", padx=16, pady=(16, 2))
        label(brief, EXPECTED, 12, wraplength=560).pack(anchor="w", padx=16, pady=(0, 16))

        arch = Card(body)
        arch.pack(fill="x", pady=(16, 0))
        label(arch, "Architecture", 14, "bold").pack(anchor="w", padx=16, pady=(16, 0))
        self.diagram = tk.Canvas(arch, height=S(300), highlightthickness=0)
        self.diagram.pack(fill="x", padx=16, pady=8)
        self.diagram.bind("<Configure>", lambda e: self.draw_diagram())

        table = Card(body)
        table.pack(fill="x", pady=(16, 0))
        label(table, "Complexity Summary", 14, "bold").pack(anchor="w", padx=16, pady=(16, 8))
        grid = ctk.CTkFrame(table, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 16))
        grid.grid_columnconfigure(0, weight=3)
        for column in (1, 2, 3):
            grid.grid_columnconfigure(column, weight=1)
        for r, values in enumerate(COMPLEXITY):
            for c, text in enumerate(values):
                header = r == 0
                cell = ctk.CTkLabel(
                    grid, text=text, anchor="w", font=font(11, "bold" if header or c == 0 else "normal"),
                    text_color="#FFFFFF" if header else pair("text"),
                    fg_color=pair("primary") if header else (pair("chip") if r % 2 == 0 else "transparent"),
                    corner_radius=0)
                cell.grid(row=r, column=c, sticky="ew", ipadx=8, ipady=4)

        label(body, "Team", 16, "bold").pack(anchor="w", pady=(16, 8), padx=4)
        team = ctk.CTkFrame(body, fg_color="transparent")
        team.pack(fill="x")
        team.grid_columnconfigure((0, 1, 2), weight=1, uniform="t")
        for index, (name, register) in enumerate(TEAM):
            card = Card(team)
            card.grid(row=0, column=index, sticky="nsew", padx=4, pady=4)
            ctk.CTkLabel(card, text=name[:1], width=52, height=52, corner_radius=26,
                         fg_color=pair("primary"), text_color="#FFFFFF",
                         font=font(20, "bold")).pack(pady=(16, 8))
            label(card, name, 13, "bold", wraplength=150).pack()
            label(card, register, 11, color="muted").pack(pady=(0, 16))
        guide = Card(body)
        guide.pack(fill="x", pady=(16, 8))
        label(guide, "Guided by", 11, "bold", "muted").pack(anchor="w", padx=16, pady=(16, 0))
        label(guide, "Dr. J. A. M. Rexie, Assistant Professor", 15, "bold").pack(
            anchor="w", padx=16)
        label(guide, "Division of Computer Science and Engineering, Karunya University", 12,
              color="muted").pack(anchor="w", padx=16, pady=(0, 16))

    def refresh(self):
        self.draw_diagram()

    def restyle(self):
        self.draw_diagram()

    def draw_diagram(self):
        """GUI layer -> PatientManager -> (Hash Table, BST, Merge Sort) -> SQLite."""
        colors = pal()
        canvas = self.diagram
        canvas.delete("all")
        canvas.configure(bg=colors["card"])
        width = max(canvas.winfo_width(), S(500))

        def box(cx, cy, w, h, text, sub, fill, text_color="#FFFFFF"):
            canvas.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill=fill,
                                    outline="")
            canvas.create_text(cx, cy - S(7), text=text, fill=text_color, font=font(11, "bold"))
            canvas.create_text(cx, cy + S(10), text=sub, fill=text_color, font=font(8))

        def arrow(x1, y1, x2, y2):
            canvas.create_line(x1, y1, x2, y2, arrow="last", width=2, fill=colors["muted"])

        mid = width / 2
        bw, bh = S(180), S(44)
        box(mid, S(30), bw * 1.4, bh, "GUI Layer", "CustomTkinter pages", colors["primary"])
        arrow(mid, S(52), mid, S(78))
        box(mid, S(100), bw * 1.4, bh, "PatientManager", "keeps everything in sync", "#5B7083")
        spread = min(S(190), (width - S(160)) / 3)
        for offset, name, sub, colour in ((-spread, "Hash Table", "O(1) lookup", "#238041"),
                                          (0, "BST", "ordered / range", "#8A6D3B"),
                                          (spread, "Merge Sort", "daily report", "#2F7A76")):
            arrow(mid + offset * 0.3, S(122), mid + offset, S(168))
            box(mid + offset, S(190), spread * 0.85, bh, name, sub, colour)
            arrow(mid + offset, S(212), mid, S(246))
        box(mid, S(268), bw * 1.4, bh, "SQLite Database", "patients.db - storage only", "#44575A")
