"""Chooses and opens the storage backend (MySQL, or SQLite as the fallback).

Reads db_config.ini.  Nothing here searches or sorts data - it only opens the
database and seeds sample data on a first run.
"""
import configparser
import os

from database import Database, DatabaseError, MySQLDatabase
from seed_data import seed_if_empty

CONFIG_NAME = "db_config.ini"
SQLITE_NAME = "patients.db"

MISSING_CONFIG_HELP = (
    "The database settings file db_config.ini was not found.\n\n"
    "To create it:\n"
    "  1. Copy db_config.example.ini to db_config.ini (same folder as main.py).\n"
    "  2. Open db_config.ini and replace your_password_here with your MySQL password.\n"
    "  3. Start the app again.")


class BackendProblem(Exception):
    """MySQL cannot be used. Carries a title and a friendly message for a dialog."""

    def __init__(self, title, message):
        Exception.__init__(self, message)
        self.title = title
        self.message = message


class ConfigMissing(Exception):
    pass


def load_config(folder):
    """Read db_config.ini into a dict. Raises ConfigMissing if the file is absent."""
    path = os.path.join(folder, CONFIG_NAME)
    if not os.path.exists(path):
        raise ConfigMissing(MISSING_CONFIG_HELP)
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    section = parser["mysql"] if parser.has_section("mysql") else {}
    app_section = parser["app"] if parser.has_section("app") else {}
    try:
        port = int(section.get("port", "3306"))
    except ValueError:
        port = 3306
    return {
        "host": section.get("host", "localhost"),
        "port": port,
        "user": section.get("user", "root"),
        "password": section.get("password", ""),
        "database": section.get("database", "rapha_hospital"),
        "backend": app_section.get("backend", "mysql").strip().lower(),
    }


def open_sqlite(folder):
    """Open (and create / seed if needed) the local SQLite database."""
    database = Database(os.path.join(folder, SQLITE_NAME))
    database.create_table()
    seed_if_empty(database)
    return database


def open_database(folder):
    """Open the configured backend.

    Returns a Database / MySQLDatabase.  Raises BackendProblem when MySQL was
    requested but cannot be used (missing settings, server down, wrong password).
    """
    try:
        config = load_config(folder)
    except ConfigMissing as problem:
        raise BackendProblem("Database settings not found", str(problem))
    if config["backend"] == "sqlite":
        return open_sqlite(folder)
    sqlite_existed = os.path.exists(os.path.join(folder, SQLITE_NAME))
    try:
        database = MySQLDatabase(config["host"], config["port"], config["user"],
                                 config["password"], config["database"])
        database.create_table()
        # first run: seed only when there is nothing to migrate from patients.db
        if not sqlite_existed and database.count() == 0:
            seed_if_empty(database)
    except DatabaseError as error:
        raise BackendProblem("MySQL is not available", str(error))
    return database
