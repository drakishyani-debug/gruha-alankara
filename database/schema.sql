-- schema.sql
-- SQLite schema for Gruha Alankara
-- Four core entities as described in the project document:
--   Users -> Designs (one to many)
--   Designs -> Furniture (one to many)
--   Designs -> Bookings (one to many)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS designs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    room_type     TEXT,
    style         TEXT,
    budget        REAL,
    image_path    TEXT,
    analysis_data TEXT,     -- JSON blob: room analyzer output
    design_data   TEXT,     -- JSON blob: AI-generated design (style, furniture, budget)
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS furniture (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id   INTEGER NOT NULL,
    name        TEXT NOT NULL,
    category    TEXT,
    quantity    INTEGER DEFAULT 1,
    price_min   REAL,
    price_max   REAL,
    priority    TEXT,      -- high / medium / low
    image_url   TEXT,
    FOREIGN KEY (design_id) REFERENCES designs (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id      INTEGER NOT NULL,
    furniture_name TEXT NOT NULL,
    status         TEXT DEFAULT 'pending',   -- pending / confirmed / cancelled
    language       TEXT DEFAULT 'en',
    booking_date   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (design_id) REFERENCES designs (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_designs_user ON designs(user_id);
CREATE INDEX IF NOT EXISTS idx_furniture_design ON furniture(design_id);
CREATE INDEX IF NOT EXISTS idx_bookings_design ON bookings(design_id);
