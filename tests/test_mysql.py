"""Tests against a REAL MySQL server.  Skipped automatically when db_config.ini is
missing or the server cannot be reached.  They use a separate throw-away database
(rapha_hospital_test), never the real rapha_hospital data."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import DatabaseError, MySQLDatabase
from db_setup import ConfigMissing, load_config
from patient import Patient
from patient_manager import PatientManager
from seed_data import seed_if_empty

TEST_DB = "rapha_hospital_test"
ROOT = os.path.join(os.path.dirname(__file__), "..")


def make(pid, date="2026-10-21", age=30):
    return Patient(pid, "P%d" % pid, age, "Male", "ENT", "Flu", "Dr. X", date)


class RealMySQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.config = load_config(ROOT)
            cls.admin = MySQLDatabase(cls.config["host"], cls.config["port"], cls.config["user"],
                                      cls.config["password"], TEST_DB)
        except (ConfigMissing, DatabaseError) as problem:
            raise unittest.SkipTest("MySQL not available: %s" % str(problem).splitlines()[0])

    @classmethod
    def tearDownClass(cls):
        cursor = cls.admin.connection.cursor()
        cursor.execute("DROP DATABASE IF EXISTS " + TEST_DB)       # fixed test name
        cursor.close()
        cls.admin.close()

    def setUp(self):
        self.db = MySQLDatabase(self.config["host"], self.config["port"], self.config["user"],
                                self.config["password"], TEST_DB)
        self.db.create_table()
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM patients")
        self.db.connection.commit()
        cursor.close()

    def tearDown(self):
        self.db.close()

    def test_roundtrip(self):
        self.db.insert(make(1005, "2026-10-23"))
        loaded = self.db.load_all()
        self.assertEqual(loaded, [make(1005, "2026-10-23")])
        self.assertIsInstance(loaded[0].admission_date, str)

    def test_update_delete_duplicate(self):
        self.db.insert(make(1))
        with self.assertRaises(DatabaseError):
            self.db.insert(make(1))
        changed = make(1, age=60)
        changed.name = "Changed"
        self.db.update(changed)
        self.assertEqual(self.db.load_all()[0].name, "Changed")
        self.db.delete(1)
        self.assertEqual(self.db.count(), 0)

    def test_check_constraint_on_age(self):
        with self.assertRaises(DatabaseError):
            self.db.insert(make(2, age=150))      # needs MySQL 8.0.16+ to be enforced

    def test_manager_with_real_mysql(self):
        seed_if_empty(self.db)
        manager = PatientManager(self.db)
        self.assertEqual(manager.count(), 30)
        manager.add_patient(make(1101))
        reopened = PatientManager(MySQLDatabase(self.config["host"], self.config["port"],
                                                self.config["user"], self.config["password"], TEST_DB))
        self.assertEqual(reopened.count(), 31)
        self.assertIsNotNone(reopened.get_patient(1101))
        reopened.database.close()


if __name__ == "__main__":
    unittest.main()
