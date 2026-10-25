"""One-off copy of every record from patients.db (SQLite) into MySQL.

Usage:  python migrate_sqlite_to_mysql.py
Records whose ID already exists in MySQL are skipped; patients.db is not changed.
"""
import os
import sys

from database import Database, DatabaseError, MySQLDatabase
from db_setup import ConfigMissing, SQLITE_NAME, load_config

FOLDER = os.path.dirname(os.path.abspath(__file__))


def migrate(source, target):
    """Copy patients from `source` to `target` (both have load_all / insert).

    Returns (copied, skipped, failed).  The existing IDs are collected from one
    plain load of the target table - no per-ID SQL lookups.
    """
    existing = [patient.patient_id for patient in target.load_all()]
    copied = skipped = failed = 0
    for patient in source.load_all():
        if patient.patient_id in existing:
            skipped += 1
            continue
        try:
            target.insert(patient)
            existing.append(patient.patient_id)
            copied += 1
        except DatabaseError as error:
            failed += 1
            print("  could not copy patient %d: %s" % (patient.patient_id, error))
    return copied, skipped, failed


def main():
    sqlite_path = os.path.join(FOLDER, SQLITE_NAME)
    if not os.path.exists(sqlite_path):
        print("%s was not found - nothing to migrate." % SQLITE_NAME)
        return 1
    try:
        config = load_config(FOLDER)
    except ConfigMissing as problem:
        print(problem)
        return 1
    try:
        target = MySQLDatabase(config["host"], config["port"], config["user"],
                               config["password"], config["database"])
        target.create_table()
    except DatabaseError as error:
        print("Cannot connect to MySQL: %s" % error)
        return 1
    source = Database(sqlite_path)
    try:
        copied, skipped, failed = migrate(source, target)
    finally:
        source.close()
        target.close()
    print("Migration finished: %d record(s) copied, %d already in MySQL (skipped), %d failed."
          % (copied, skipped, failed))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
