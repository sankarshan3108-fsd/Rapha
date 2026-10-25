"""Base class for all pages."""
import customtkinter as ctk


class Page(ctk.CTkFrame):
    """A page shown in the main area.  Subclasses set key/title/subtitle and
    implement refresh() (redraw everything from the data structures)."""

    key = ""
    title = ""
    subtitle = ""

    def __init__(self, app):
        super().__init__(app.container, fg_color="transparent")
        self.app = app
        self.manager = app.manager
        self.dirty = True

    def refresh(self):
        """Redraw from the manager's data."""

    def on_show(self):
        """Called every time the page becomes visible."""

    def restyle(self):
        """Re-apply colours that CustomTkinter cannot switch itself."""

    def on_theme(self):
        self.restyle()
        self.dirty = True
        if self.app.current == self.key:
            self.refresh()
            self.dirty = False

    def trace(self, text):
        self.app.set_trace(self.key, text)
