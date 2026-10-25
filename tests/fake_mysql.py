"""A tiny stand-in for mysql.connector so the MySQL code can be tested without a server.

It is backed by an in-memory SQLite database: %s placeholders are translated to ?,
DATE values come back as datetime.date (like the real driver), and failures can
be injected (server down, wrong password, a failing statement).
"""
import datetime
import sqlite3
import sys
import types


class Error(Exception):
    def __init__(self, msg="", errno=None):
        Exception.__init__(self, msg)
        self.errno = errno


class FakeServer:
    def __init__(self):
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.log = []                # (sql, params) for every statement
        self.refuse = None           # errno to raise on connect()
        self.fail_next = None        # an Error raised by the next INSERT/UPDATE/DELETE
        self.ping_fails = False
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0


class FakeCursor:
    def __init__(self, server):
        self.server = server
        self.rows = []

    def execute(self, sql, params=()):
        server = self.server
        server.log.append((sql, tuple(params)))
        head = sql.strip().upper()
        if head.startswith("CREATE DATABASE"):
            return
        if head.startswith("CREATE TABLE"):
            server.db.execute(
                "CREATE TABLE IF NOT EXISTS patients (patient_id INTEGER PRIMARY KEY, "
                "name TEXT NOT NULL, age INTEGER, gender TEXT, department TEXT, "
                "diagnosis TEXT, doctor TEXT, admission_date TEXT NOT NULL, "
                "created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            return
        if head.split()[0] in ("INSERT", "UPDATE", "DELETE") and server.fail_next is not None:
            error, server.fail_next = server.fail_next, None
            raise error
        try:
            cursor = server.db.execute(sql.replace("%s", "?"), tuple(params))
        except sqlite3.IntegrityError as error:
            raise Error(str(error), errno=1062)
        if head.startswith("SELECT"):
            self.rows = []
            for row in cursor.fetchall():
                row = list(row)
                row[7] = datetime.date.fromisoformat(row[7])      # DATE column
                self.rows.append(tuple(row))

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, server):
        self.server = server

    def cursor(self):
        return FakeCursor(self.server)

    def commit(self):
        self.server.commits += 1
        self.server.db.commit()

    def rollback(self):
        self.server.rollbacks += 1
        self.server.db.rollback()

    def ping(self, reconnect=False, attempts=1, delay=0):
        if self.server.ping_fails:
            raise Error("server gone", errno=2013)

    def close(self):
        self.server.closed += 1


def install():
    """Put a fake `mysql.connector` into sys.modules; returns (FakeServer, restore_function)."""
    server = FakeServer()
    connector = types.ModuleType("mysql.connector")
    connector.Error = Error

    def connect(**settings):
        if server.refuse:
            raise Error("cannot connect", errno=server.refuse)
        return FakeConnection(server)

    connector.connect = connect
    package = types.ModuleType("mysql")
    package.connector = connector
    saved = {name: sys.modules.get(name) for name in ("mysql", "mysql.connector")}
    sys.modules["mysql"], sys.modules["mysql.connector"] = package, connector

    def restore():
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    return server, restore
