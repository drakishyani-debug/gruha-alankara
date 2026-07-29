"""
database/db.py
---------------
Lightweight SQLite data-access layer.

ASSUMPTION: The prerequisites list mentions "Flask-SQLAlchemy" and
"SQLAlchemy ORM". This environment does not have SQLAlchemy pre-installed
and the app is meant to run with zero external services, so we implement
the same responsibilities (models, relationships, CRUD) using Python's
built-in `sqlite3` module instead. The public API below (get_db,
init_db) mirrors what Flask-SQLAlchemy would give you, so swapping to a
real ORM later only touches this file and models.py.
"""

import sqlite3
import os
from flask import g, current_app


def get_db():
    """Return a SQLite connection for the current Flask app context,
    creating one if it does not already exist (connection reuse per request).
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create all tables from schema.sql if they do not already exist,
    and register the connection teardown handler.
    """
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    with app.app_context():
        db = sqlite3.connect(app.config["DATABASE_PATH"])
        with open(schema_path, "r") as f:
            db.executescript(f.read())
        db.commit()
        db.close()

    app.teardown_appcontext(close_db)
