"""Entry point: python main.py"""
import os
import sys

from db_setup import BackendProblem, open_database, open_sqlite
from gui import run_app
from patient_manager import PatientManager

FOLDER = os.path.dirname(os.path.abspath(__file__))


def load_data():
    """Open the database (MySQL by default), then load the hash table + BST.

    Returns a PatientManager, or a BackendProblem when MySQL cannot be used
    (the caller then offers the SQLite fallback).
    """
    try:
        database = open_database(FOLDER)
    except BackendProblem as problem:
        return problem
    return PatientManager(database)


def offer_sqlite_fallback(problem):
    """Explain the problem and offer to continue with local SQLite (patients.db).

    Returns a PatientManager, or None if the user declines.
    """
    import tkinter
    from tkinter import messagebox
    root = tkinter.Tk()
    root.withdraw()
    try:
        accept = messagebox.askyesno(
            problem.title,
            problem.message + "\n\nContinue with the local SQLite database (patients.db) instead?\n"
            "Changes made in this mode are NOT saved to MySQL.")
    finally:
        root.destroy()
    if not accept:
        return None
    try:
        return PatientManager(open_sqlite(FOLDER))
    except Exception as error:
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror("Cannot continue", "The local database could not be opened:\n%s" % error)
        root.destroy()
        return None


def main():
    # RAPHA splash (about 2 seconds) is shown only while the data loads.
    # If it cannot be created the data simply loads without it.
    splash = None
    try:
        from gui.glass import Splash
        splash = Splash()
    except Exception:
        splash = None
    manager = splash.run(load_data, min_ms=2000) if splash else load_data()
    if isinstance(manager, BackendProblem):
        manager = offer_sqlite_fallback(manager)
        if manager is None:
            sys.exit(0)
    try:
        run_app(manager)
    finally:
        manager.database.close()          # close the connection cleanly on exit


if __name__ == "__main__":
    main()
