"""Window that animates merge sort on the admission dates, level by level.

Frames come from merge_sort.merge_sort_frames(): first the 'divide' levels
(splitting every sub-array in half), then the 'merge' levels (merging pairs of
sorted halves) until the list is sorted.
"""
import tkinter as tk

import customtkinter as ctk

from gui.theme import S, font, pair, pal
from gui.widgets import button, label
from merge_sort import merge_sort_frames


class MergeSortWindow(ctk.CTkToplevel):
    SEGMENT_COLORS = ["#0B5E6E", "#8A6D3B", "#238041", "#5B7083", "#2F7A76", "#5E7230"]

    def __init__(self, app, patients):
        super().__init__(app)
        self.title("Merge Sort Visualisation")
        self.geometry("1180x640")
        self.configure(fg_color=pair("bg"))
        self.transient(app)
        self.frames = merge_sort_frames(patients)
        self.index = 0
        self.playing = False
        self.job = None
        self.count = len(patients)

        label(self, "Merge sort on admission dates (date over patient ID)", 15, "bold",
              "primary").pack(anchor="w", padx=16, pady=(16, 0))
        self.caption = label(self, "", 12, color="muted")
        self.caption.pack(anchor="w", padx=16, pady=(0, 8))
        holder = ctk.CTkFrame(self, fg_color="transparent")
        holder.pack(fill="both", expand=True, padx=16)
        self.canvas = tk.Canvas(holder, highlightthickness=1, bg=pal()["canvas_bg"],
                                highlightbackground=pal()["border"])
        vbar = ctk.CTkScrollbar(holder, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=16, pady=16)
        button(controls, "Reset", self.reset, "secondary", width=90).pack(side="left")
        button(controls, "Back", self.step_back, "secondary", width=90).pack(side="left", padx=8)
        self.play_button = button(controls, "Play", self.toggle_play, width=100)
        self.play_button.pack(side="left")
        button(controls, "Next", self.step_forward, "secondary", width=90).pack(side="left", padx=8)
        label(controls, "Speed:", 11, color="muted").pack(side="left", padx=(24, 8))
        self.speed = ctk.CTkSlider(controls, from_=150, to=1500, width=180)
        self.speed.set(700)
        self.speed.pack(side="left")
        label(controls, "(left = fast)", 11, color="muted").pack(side="left", padx=8)
        button(controls, "Close", self.destroy, "secondary", width=80).pack(side="right")
        self.draw()
        self.after(100, self.focus)

    # -- controls --
    def reset(self):
        self.stop()
        self.index = 0
        self.draw()

    def step_forward(self):
        if self.index < len(self.frames) - 1:
            self.index += 1
            self.draw()
        else:
            self.stop()

    def step_back(self):
        self.stop()
        if self.index > 0:
            self.index -= 1
            self.draw()

    def toggle_play(self):
        if self.playing:
            self.stop()
            return
        if self.index >= len(self.frames) - 1:
            self.index = 0
            self.draw()
        self.playing = True
        self.play_button.configure(text="Pause")
        self._tick()

    def stop(self):
        self.playing = False
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        try:
            self.play_button.configure(text="Play")
        except tk.TclError:
            pass

    def _tick(self):
        if not self.playing:
            return
        if self.index >= len(self.frames) - 1:
            self.stop()
            return
        self.step_forward()
        self.job = self.after(int(self.speed.get()), self._tick)

    def destroy(self):
        self.playing = False
        if self.job is not None:
            try:
                self.after_cancel(self.job)
            except tk.TclError:
                pass
        super().destroy()

    # -- drawing: every frame so far is drawn as one row (a history) --
    def draw(self):
        colors = pal()
        canvas = self.canvas
        canvas.delete("all")
        canvas.configure(bg=colors["canvas_bg"])
        width = max(canvas.winfo_width(), S(900))
        gap, margin, row_h = S(6), S(14), S(62)
        usable = width - 2 * margin - gap * max(0, self.count - 1)
        box_w = max(S(18), min(S(56), usable / max(1, self.count)))
        for row, (phase, name, segments) in enumerate(self.frames[: self.index + 1]):
            y = S(26) + row * row_h
            current = row == self.index
            canvas.create_text(margin, y - S(14), anchor="w", text=name,
                               font=font(9, "bold"),
                               fill=colors["primary"] if current else colors["muted"])
            x = margin
            for number, segment in enumerate(segments):
                if phase == "merge":
                    fill = colors["node_found"] if len(segment) > 1 else colors["node"]
                else:
                    fill = self.SEGMENT_COLORS[number % len(self.SEGMENT_COLORS)]
                for patient in segment:
                    canvas.create_rectangle(x, y, x + box_w, y + S(34), fill=fill, outline="")
                    short = patient.admission_date[5:] if box_w >= S(34) else patient.admission_date[8:]
                    canvas.create_text(x + box_w / 2, y + S(11), text=short,
                                       fill="#FFFFFF" if phase == "divide" else "#101010",
                                       font=font(8, "bold"))
                    canvas.create_text(x + box_w / 2, y + S(25), text=str(patient.patient_id)[-3:],
                                       fill="#FFFFFF" if phase == "divide" else "#101010",
                                       font=font(7))
                    x += box_w
                x += gap
        canvas.configure(scrollregion=(0, 0, width, S(40) + (self.index + 1) * row_h))
        canvas.yview_moveto(1.0)
        self.caption.configure(text="Step %d of %d  •  %s" % (
            self.index + 1, len(self.frames),
            "dividing: every sub-list is cut in half" if self.frames[self.index][0] == "divide"
            else "merging: two sorted halves are combined by repeatedly taking the smaller front item"))
