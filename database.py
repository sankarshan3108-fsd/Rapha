"""Storage layer: SQLite (Database) and MySQL (MySQLDatabase).

Both classes have the same methods (create_table, insert, update, delete,
load_all, count, close) and are used ONLY for permanent storage:
plain INSERT / UPDATE / DELETE and a plain SELECT * to load everything.
Searching, ordering and sorting are done by our own hash table, BST and
merge sort - never by SQL.
"""
import re
import sqlite3

from patient import Patient


class DatabaseError(Exception):
    """A storage problem with a message that is safe to show to the user."""


class Database:
    """SQLite storage (patients.db). Also used as the offline fallback."""

    status_kind = "sqlite"
    status_text = "SQLite (offline mode)"

    def __init__(self, path="patients.db"):
        self.connection = sqlite3.connect(path)

    def create_table(self):
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                department TEXT,
                diagnosis TEXT,
                doctor TEXT,
                admission_date TEXT)""")
        self.connection.commit()

    def insert(self, patient):
        self.connection.execute(
            "INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", patient.as_row())
        self.connection.commit()

    def update(self, patient):
        row = patient.as_row()
        self.connection.execute(
            "UPDATE patients SET name=?, age=?, gender=?, department=?, "
            "diagnosis=?, doctor=?, admission_date=? WHERE patient_id=?",
            row[1:] + (row[0],))
        self.connection.commit()

    def delete(self, patient_id):
        self.connection.execute(
            "DELETE FROM patients WHERE patient_id=?", (patient_id,))
        self.connection.commit()

    def load_all(self):
        """Plain SELECT * - ordering is done by our own data structures."""
        cursor = self.connection.execute("SELECT * FROM patients")
        return [Patient(*row) for row in cursor.fetchall()]

    def count(self):
        return len(self.connection.execute("SELECT * FROM patients").fetchall())

    def close(self):
        self.connection.close()


# ---------------------------------------------------------------------------
# MySQL
# ---------------------------------------------------------------------------
# Kept identical to schema.sql so it can also be run by hand in MySQL Workbench.
MYSQL_CREATE_TABLE = """CREATE TABLE IF NOT EXISTS patients (
    patient_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT CHECK (age BETWEEN 0 AND 120),
    gender VARCHAR(10),
    department VARCHAR(50),
    diagnosis VARCHAR(150),
    doctor VARCHAR(100),
    admission_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,64}$")


def _friendly(error):
    """Turn a mysql.connector error into a short, readable sentence."""
    code = getattr(error, "errno", None)
    if code == 1045:
        return "MySQL rejected the user name or password (check db_config.ini)."
    if code in (2002, 2003, 2005, 2013):
        return "The MySQL server could not be reached (is the MySQL service running?)."
    if code == 1049:
        return "The MySQL database does not exist."
    if code == 1062:
        return "A patient with this ID already exists in the database."
    if code == 3819:
        return "A value is outside the allowed range (age must be 0 to 120)."
    return "MySQL reported: %s" % error


class MySQLDatabase:
    """MySQL storage using mysql-connector-python and parameterized queries (%s).

    Every change is committed immediately and rolled back if it fails.
    """

    status_kind = "mysql"

    def __init__(self, host="localhost", port=3306, user="root", password="",
                 database="rapha_hospital", connect_timeout=5):
        if not _NAME_PATTERN.match(database):
            raise DatabaseError("The database name may only contain letters, digits and _.")
        try:
            import mysql.connector
        except ImportError:
            raise DatabaseError("The MySQL driver is not installed.\n"
                                "Please run:  pip install mysql-connector-python")
        self._mysql = mysql.connector
        self.database_name = database
        settings = dict(host=host, port=int(port), user=user, password=password,
                        connection_timeout=connect_timeout, charset="utf8mb4")
        try:
            server = mysql.connector.connect(**settings)
            cursor = server.cursor()
            # An identifier cannot be a %s parameter; the name was checked above
            # (letters, digits and _ only), so this is safe.
            cursor.execute("CREATE DATABASE IF NOT EXISTS `" + database +
                           "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            server.commit()
            cursor.close()
            server.close()
            self.connection = mysql.connector.connect(database=database, **settings)
        except mysql.connector.Error as error:
            raise DatabaseError(_friendly(error))

    @property
    def status_text(self):
        return "MySQL connected · %s" % self.database_name

    # -- helpers --
    def _ensure_connected(self):
        """Reconnect if the server closed an idle connection."""
        try:
            self.connection.ping(reconnect=True, attempts=2, delay=1)
        except self._mysql.Error as error:
            raise DatabaseError(_friendly(error))

    def _change(self, sql, params=()):
        """Run one INSERT / UPDATE / DELETE, commit, or roll back on error."""
        self._ensure_connected()
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            self.connection.commit()
        except self._mysql.Error as error:
            try:
                self.connection.rollback()
            except self._mysql.Error:
                pass
            raise DatabaseError("The change was not saved. " + _friendly(error))
        finally:
            cursor.close()

    # -- same interface as the SQLite Database --
    def create_table(self):
        self._change(MYSQL_CREATE_TABLE)

    def insert(self, patient):
        self._change(
            "INSERT INTO patients (patient_id, name, age, gender, department, "
            "diagnosis, doctor, admission_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            patient.as_row())

    def update(self, patient):
        row = patient.as_row()
        self._change(
            "UPDATE patients SET name=%s, age=%s, gender=%s, department=%s, "
            "diagnosis=%s, doctor=%s, admission_date=%s WHERE patient_id=%s",
            row[1:] + (row[0],))

    def delete(self, patient_id):
        self._change("DELETE FROM patients WHERE patient_id=%s", (patient_id,))

    def load_all(self):
        """Plain SELECT * - ordering is done by our own data structures.

        The first 8 columns are the patient fields (created_at / updated_at are
        ignored); the DATE column is converted back to a 'YYYY-MM-DD' string.
        """
        self._ensure_connected()
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT * FROM patients")
            rows = cursor.fetchall()
        except self._mysql.Error as error:
            raise DatabaseError("The patients could not be loaded. " + _friendly(error))
        finally:
            cursor.close()
        patients = []
        for row in rows:
            admitted = row[7]
            admitted = admitted.isoformat() if hasattr(admitted, "isoformat") else str(admitted)
            patients.append(Patient(row[0], row[1], row[2], row[3], row[4], row[5],
                                    row[6], admitted))
        return patients

    def count(self):
        # plain SELECT * as well, to keep to the "no extra SQL" rule
        return len(self.load_all())

    def close(self):
        try:
            self.connection.close()
        except Exception:
            pass
