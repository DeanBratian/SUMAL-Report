"""SQLite storage: data/sumal.db.

Holds the SUMAL reference catalog (species, sortiments, operation types) synced
from the live site, and later the persistent pieces of the monthly workflow
(deposit prices, stock ledger). Plain sqlite3, no ORM.
"""

import os
import sqlite3

DB_RELATIVE_PATH = os.path.join("data", "sumal.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_sortiment (
    id_sortiment   INTEGER PRIMARY KEY,
    nume           TEXT    NOT NULL,
    cod            TEXT,
    status         INTEGER NOT NULL DEFAULT 1,
    synced_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_specie (
    id_specie      INTEGER PRIMARY KEY,
    nume           TEXT    NOT NULL,
    cod            TEXT,
    id_parinte     INTEGER,
    nume_parinte   TEXT,
    nivel          INTEGER,
    status         INTEGER NOT NULL DEFAULT 1,
    synced_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_tip_operatiune (
    cod            INTEGER PRIMARY KEY,
    nume           TEXT    NOT NULL,
    are_iesiri     INTEGER NOT NULL DEFAULT 0,
    status         INTEGER NOT NULL DEFAULT 1,
    synced_at      TEXT    NOT NULL
);
"""

# ---------------------------------------------------------------------- #

def get_connection(project_root: str) -> sqlite3.Connection:
    """Open (and initialize if needed) the project database."""
    path = os.path.join(project_root, DB_RELATIVE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
