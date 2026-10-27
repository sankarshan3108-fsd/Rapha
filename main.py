"""Entry point: python main.py

Opens MySQL (see db_config.ini).  If MySQL cannot be used, the user is asked
whether to continue with the local SQLite file (offline mode) instead.
"""
import os
import sys

from db_setup import BackendProblem, open_database, open_sqlite
from gui import run_app
from patient_manager import PatientManager


def ask_use_offline(problem):
    """Show the problem and ask whether to continue with SQLite."""
    message = problem.message + "\n\nContinue in offline mode (local SQLite file)?"
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        answer = messagebox.askyesno(problem.title, message)
        root.destroy()
        return answer
    except Exception:
        print(problem.title + "\n" + message)
        return False


def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    try:
        database = open_database(folder)
    except BackendProblem as problem:
        if not ask_use_offline(problem):
            sys.exit(1)
        database = open_sqlite(folder)
    run_app(PatientManager(database))


if __name__ == "__main__":
    main()
