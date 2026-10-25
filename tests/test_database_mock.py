"""Database-layer tests that need no MySQL server (a fake connector is used)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fake_mysql
from database import Database, DatabaseError, MySQLDatabase
from db_setup import BackendProblem, ConfigMissing, load_config, open_database
from migrate_sqlite_to_mysql import migrate
from patient import Patient
from patient_manager import PatientManager
from seed_data import SEED_ROWS, seed_if_empty

ROOT = os.path.join(os.path.dirname(__file__), "..")


def make(pid, date="2026-10-21", age=30):
    return Patient(pid, "P%d" % pid, age, "Male", "ENT", "Flu", "Dr. X", date)


class MySQLWithFakeConnector(unittest.TestCase):
    def setUp(self):
        self.server, self.restore = fake_mysql.install()
        self.db = MySQLDatabase("localhost", 3306, "root", "pw", "rapha_hospital")
        self.db.create_table()

    def tearDown(self):
        self.restore()

    def test_roundtrip_and_date_string(self):
        self.db.insert(make(1005, "2026-10-23"))
        loaded = self.db.load_all()
        self.assertEqual(loaded, [make(1005, "2026-10-23")])
        self.assertIsInstance(loaded[0].admission_date, str)      # not a datetime.date
        self.assertEqual(self.db.count(), 1)

    def test_update_delete(self):
        self.db.insert(make(1))
        changed = make(1, age=44)
        changed.name = "New"
        self.db.update(changed)
        self.assertEqual(self.db.load_all()[0].name, "New")
        self.db.delete(1)
        self.assertEqual(self.db.load_all(), [])

    def test_all_queries_are_parameterized_and_storage_only(self):
        self.db.insert(make(7))
        self.db.update(make(7, age=31))
        self.db.delete(7)
        self.db.load_all()
        for sql, params in self.server.log:
            upper = sql.upper()
            self.assertNotIn("ORDER BY", upper)
            if not upper.startswith("CREATE"):
                self.assertNotIn("BETWEEN", upper)
            if upper.startswith(("INSERT", "UPDATE", "DELETE")):
                self.assertIn("%s", sql)
                self.assertTrue(params)
            if upper.startswith("SELECT"):
                self.assertEqual(upper.strip(), "SELECT * FROM PATIENTS")
        for sql, _ in self.server.log:          # values never end up inside the SQL text
            self.assertNotIn("P7", sql)

    def test_commit_after_each_change(self):
        before = self.server.commits
        self.db.insert(make(1))
        self.db.update(make(1, age=40))
        self.db.delete(1)
        self.assertEqual(self.server.commits - before, 3)

    def test_failed_change_rolls_back_with_friendly_message(self):
        self.server.fail_next = fake_mysql.Error("boom", errno=3819)
        with self.assertRaises(DatabaseError) as raised:
            self.db.insert(make(2, age=150))
        self.assertIn("0 to 120", str(raised.exception))
        self.assertEqual(self.server.rollbacks, 1)
        self.assertEqual(self.db.load_all(), [])

    def test_duplicate_id_message(self):
        self.db.insert(make(3))
        with self.assertRaises(DatabaseError) as raised:
            self.db.insert(make(3))
        self.assertIn("already exists", str(raised.exception))

    def test_lost_connection_is_reported(self):
        self.server.ping_fails = True
        with self.assertRaises(DatabaseError):
            self.db.load_all()

    def test_close(self):
        self.db.close()
        self.assertGreaterEqual(self.server.closed, 1)

    def test_status_text(self):
        self.assertEqual(self.db.status_kind, "mysql")
        self.assertEqual(self.db.status_text, "MySQL connected · rapha_hospital")
        self.assertEqual(Database(":memory:").status_text, "SQLite (offline mode)")

    def test_manager_sync_with_mysql_backend(self):
        seed_if_empty(self.db)
        manager = PatientManager(self.db)
        self.assertEqual(manager.count(), 30)
        ids = [p.patient_id for p in manager.all_patients()]
        self.assertEqual(ids, sorted(ids))
        manager.add_patient(make(1101))
        self.assertEqual(self.db.count(), 31)
        manager.update_patient(make(1101, age=50))
        self.assertEqual(manager.get_patient(1101).age, 50)
        manager.delete_patient(1101)
        self.assertEqual(self.db.count(), 30)
        report, comparisons = manager.daily_report()           # merge sort on string dates
        dates = [p.admission_date for p in report]
        self.assertTrue(all(a <= b for a, b in zip(dates, dates[1:])))
        self.assertGreater(comparisons, 0)

    def test_failed_insert_leaves_structures_unchanged(self):
        manager = PatientManager(self.db)
        self.server.fail_next = fake_mysql.Error("down", errno=2013)
        with self.assertRaises(DatabaseError):
            manager.add_patient(make(9))
        self.assertEqual(manager.count(), 0)
        self.assertIsNone(manager.get_patient(9))


class ConnectionProblems(unittest.TestCase):
    def setUp(self):
        self.server, self.restore = fake_mysql.install()

    def tearDown(self):
        self.restore()

    def test_wrong_password(self):
        self.server.refuse = 1045
        with self.assertRaises(DatabaseError) as raised:
            MySQLDatabase("localhost", 3306, "root", "bad", "rapha_hospital")
        self.assertIn("password", str(raised.exception))

    def test_server_down(self):
        self.server.refuse = 2003
        with self.assertRaises(DatabaseError) as raised:
            MySQLDatabase("localhost", 3306, "root", "pw", "rapha_hospital")
        self.assertIn("could not be reached", str(raised.exception))

    def test_bad_database_name(self):
        with self.assertRaises(DatabaseError):
            MySQLDatabase("localhost", 3306, "root", "pw", "x`; DROP DATABASE y; --")


class ConfigAndStartup(unittest.TestCase):
    def setUp(self):
        self.server, self.restore = fake_mysql.install()
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        self.restore()

    def write_config(self, backend="mysql", password="pw"):
        with open(os.path.join(self.folder, "db_config.ini"), "w") as handle:
            handle.write("[mysql]\nhost = localhost\nport = 3306\nuser = root\n"
                         "password = %s\ndatabase = rapha_hospital\n[app]\nbackend = %s\n"
                         % (password, backend))

    def test_missing_config(self):
        with self.assertRaises(ConfigMissing):
            load_config(self.folder)
        with self.assertRaises(BackendProblem) as raised:
            open_database(self.folder)
        self.assertIn("db_config.example.ini", raised.exception.message)

    def test_example_file_parses(self):
        import shutil
        shutil.copy(os.path.join(ROOT, "db_config.example.ini"),
                    os.path.join(self.folder, "db_config.ini"))
        config = load_config(self.folder)
        self.assertEqual(config["database"], "rapha_hospital")
        self.assertEqual(config["backend"], "mysql")
        self.assertEqual(config["password"], "your_password_here")

    def test_mysql_first_run_seeds_when_no_sqlite_file(self):
        self.write_config()
        database = open_database(self.folder)
        self.assertEqual(database.status_kind, "mysql")
        self.assertEqual(database.count(), len(SEED_ROWS))

    def test_mysql_not_seeded_when_patients_db_exists(self):
        self.write_config()
        Database(os.path.join(self.folder, "patients.db")).close()
        database = open_database(self.folder)
        self.assertEqual(database.count(), 0)          # waiting for the migration script

    def test_unreachable_mysql_gives_backend_problem(self):
        self.write_config()
        self.server.refuse = 2003
        with self.assertRaises(BackendProblem) as raised:
            open_database(self.folder)
        self.assertIn("could not be reached", raised.exception.message)

    def test_sqlite_backend_setting(self):
        self.write_config(backend="sqlite")
        database = open_database(self.folder)
        self.assertEqual(database.status_kind, "sqlite")
        self.assertEqual(database.count(), len(SEED_ROWS))
        database.close()

    def test_migration_copies_then_skips(self):
        source = Database(":memory:")
        source.create_table()
        seed_if_empty(source)
        target = MySQLDatabase("localhost", 3306, "root", "pw", "rapha_hospital")
        target.create_table()
        self.assertEqual(migrate(source, target), (30, 0, 0))
        self.assertEqual(migrate(source, target), (0, 30, 0))
        self.assertEqual(target.count(), 30)
        self.assertEqual([p.admission_date for p in target.load_all()][:1],
                         [p.admission_date for p in source.load_all()][:1])


if __name__ == "__main__":
    unittest.main()
