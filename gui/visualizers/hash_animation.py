"""Canvas drawings for the hash table: the full table view and the animated
lookup (formula -> slot -> walk the chain)."""
import tkinter as tk

import customtkinter as ctk

from gui.theme import S, font, mono, pal
from gui.widgets import open_profile_window


class HashCanvas(ctk.CTkFrame):
    """Every slot as an indexed box with its chain drawn as linked boxes."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.zoom_level = 1.0
        self.canvas = tk.Canvas(self, highlightthickness=1, bg=pal()["canvas_bg"])
        vbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        hbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def zoom(self, factor):
        self.zoom_level = max(0.6, min(2.0, self.zoom_level * factor))
        self.redraw()

    def redraw(self):
        colors = pal()
        canvas = self.canvas
        canvas.delete("all")
        canvas.configure(bg=colors["canvas_bg"], highlightbackground=colors["border"])
        manager = self.app.manager
        table = manager.hash_table
        z = self.zoom_level
        row_h, box_h = S(34) * z, S(26) * z
        index_w, node_w, gap = S(54) * z, S(66) * z, S(30) * z
        text_size = max(7, int(10 * z))
        widest = 1
        for slot, chain in enumerate(table.get_slots()):
            y = S(10) + slot * row_h
            fill = colors["faint"] if not chain else colors["primary"]
            canvas.create_rectangle(S(10), y, S(10) + index_w, y + box_h,
                                    fill=fill, outline="")
            canvas.create_text(S(10) + index_w / 2, y + box_h / 2, text=str(slot),
                               fill=colors["muted"] if not chain else "#FFFFFF",
                               font=mono(text_size, "bold"))
            if not chain:
                canvas.create_text(S(10) + index_w + S(10), y + box_h / 2, anchor="w",
                                   text="empty", fill=colors["faint"], font=font(text_size))
                continue
            x = S(10) + index_w
            for key in chain:
                canvas.create_line(x, y + box_h / 2, x + gap, y + box_h / 2, arrow="last",
                                   fill=colors["arrow"], width=1)
                color = colors["node"] if len(chain) == 1 else colors["collide"]
                tag = "k%d" % key
                canvas.create_rectangle(x + gap, y, x + gap + node_w, y + box_h, fill=color,
                                        outline=colors["faint"], tags=(tag,))
                canvas.create_text(x + gap + node_w / 2, y + box_h / 2, text=str(key),
                                   fill=colors["text"], font=mono(text_size), tags=(tag,))
                canvas.tag_bind(tag, "<Enter>", lambda e, k=key: self._tip(e, k))
                canvas.tag_bind(tag, "<Leave>", lambda e: self.app.tooltip.hide())
                canvas.tag_bind(tag, "<Button-1>",
                                lambda e, k=key: open_profile_window(self.app, k))
                x += gap + node_w
            widest = max(widest, len(chain))
        canvas.configure(scrollregion=(0, 0, S(40) + index_w + widest * (gap + node_w),
                                       S(30) + table.size * row_h))

    def _tip(self, event, key):
        patient = self.app.manager.get_patient(key)
        if patient:
            self.app.tooltip.show("%d  %s\n%s" % (key, patient.name, patient.department),
                                  event.x_root, event.y_root)


class LookupCanvas(tk.Canvas):
    """Animated lookup: formula, slot highlight, then chain nodes one by one."""

    STEP_MS = 400

    def __init__(self, parent):
        super().__init__(parent, height=S(190), highlightthickness=0, bg=pal()["canvas_bg"])
        self.job = None
        self.data = None
        self.stage = 0
        self.on_done = None
        self.bind("<Configure>", lambda e: self.render())

    def stop(self):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None

    def idle(self, text):
        self.stop()
        self.data = None
        self.delete("all")
        self.configure(bg=pal()["canvas_bg"])
        self.create_text(S(20), S(30), anchor="w", text=text, fill=pal()["muted"],
                         font=font(12))

    def play(self, key, slot, size, steps, on_done=None):
        """Start the animation. steps = [(chain_key, matched), ...]."""
        self.stop()
        self.data = (key, slot, size, steps)
        self.stage = 0
        self.on_done = on_done
        self.render()
        self.job = self.after(self.STEP_MS, self._advance)

    def _advance(self):
        key, slot, size, steps = self.data
        self.stage += 1
        self.render()
        if self.stage < 1 + len(steps) + 1:
            self.job = self.after(self.STEP_MS, self._advance)
        else:
            self.job = None
            if self.on_done:
                self.on_done()

    def _mark(self, cx, cy, ok, color):
        """Small tick (match) or cross (no match) drawn with lines."""
        r = S(4)
        if ok:
            self.create_line(cx - r, cy, cx - r / 3, cy + r * 0.8, cx + r, cy - r * 0.8,
                             fill=color, width=2, capstyle="round", joinstyle="round")
        else:
            self.create_line(cx - r, cy - r, cx + r, cy + r, fill=color, width=2, capstyle="round")
            self.create_line(cx - r, cy + r, cx + r, cy - r, fill=color, width=2, capstyle="round")

    def render(self):
        """Draw the current stage: 0 formula, 1 slot, 2.. chain steps, last result."""
        colors = pal()
        self.delete("all")
        self.configure(bg=colors["canvas_bg"])
        if self.data is None:
            return
        key, slot, size, steps = self.data
        self.create_text(S(20), S(26), anchor="w", fill=colors["text"],
                         font=font(15, "bold"),
                         text="h(%d) = %d %% %d%s" % (
                             key, key, size, ("  =  %d" % slot) if self.stage >= 1 else "  = ?"))
        # the slot box
        sx, sy, sw, sh = S(20), S(60), S(96), S(48)
        active = self.stage >= 1
        self.create_rectangle(sx, sy, sx + sw, sy + sh,
                              fill=colors["primary"] if active else colors["faint"],
                              outline="", width=1)
        self.create_text(sx + sw / 2, sy + sh / 2, text="slot %d" % slot,
                         fill="#FFFFFF" if active else colors["muted"], font=mono(12, "bold"))
        revealed = max(0, min(len(steps), self.stage - 1))
        if not steps and self.stage >= 2:
            self.create_text(sx + sw + S(20), sy + sh / 2, anchor="w",
                             text="empty slot → nothing to compare",
                             fill=colors["muted"], font=font(12, "bold"))
        x = sx + sw
        for index in range(revealed):
            chain_key, matched = steps[index]
            self.create_line(x, sy + sh / 2, x + S(34), sy + sh / 2, arrow="last",
                             fill=colors["arrow"], width=1)
            fill = colors["node_found"] if matched else colors["node"]
            ink = colors["on_fill"] if matched else colors["text"]
            left = x + S(34)
            self.create_rectangle(left, sy, left + S(88), sy + sh, fill=fill,
                                  outline=colors["faint"] if not matched else colors["success"],
                                  width=1)
            self.create_text(left + S(44), sy + sh / 2 - S(8), text=str(chain_key),
                             fill=ink, font=mono(12, "bold"))
            self._mark(left + S(22), sy + sh / 2 + S(12), matched, ink)
            self.create_text(left + S(32), sy + sh / 2 + S(12), anchor="w",
                             text="match" if matched else "no match",
                             fill=ink, font=font(10, "bold"))
            x = left + S(88)
        if self.stage >= 1 + len(steps) + 1:
            found = bool(steps) and steps[-1][1]
            message = ("Found after %d comparison(s)" if found
                       else "Not found after %d comparison(s)") % len(steps)
            self.create_text(S(20), S(150), anchor="w", text=message, font=font(13, "bold"),
                             fill=colors["success_text"] if found else colors["danger_text"])
