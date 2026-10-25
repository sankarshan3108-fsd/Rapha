"""GUI package. run_app(manager) starts the application."""
import sys


def run_app(manager):
    try:
        import customtkinter  # noqa: F401
        import matplotlib     # noqa: F401
    except ImportError as error:
        message = ("A required library is missing (%s).\n\n"
                   "Please run:  pip install -r requirements.txt" % error)
        print(message)
        try:
            import tkinter
            from tkinter import messagebox
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror("Missing libraries", message)
        except Exception:
            pass
        sys.exit(1)
    from gui.app import run_app as start
    start(manager)
