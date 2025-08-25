import sqlite3
import json
import os
import time
from pathlib import Path

DB_PATH = Path('data/sessions.db')
DB_PATH.parent.mkdir(exist_ok=True, parents=True)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  start_ts REAL,
  end_ts REAL,
  preset TEXT,
  key TEXT,
  bpm INTEGER,
  beats_per_chord INTEGER,
  adaptive INTEGER DEFAULT 0,
  arp_mode TEXT DEFAULT 'off',
  arp_rate REAL DEFAULT 1.0,
  density REAL DEFAULT 0.5
);
CREATE TABLE IF NOT EXISTS chords (
  session_id INTEGER,
  ts REAL,
  root INTEGER,
  quality TEXT,
  pitches TEXT,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE TABLE IF NOT EXISTS notes (
  session_id INTEGER,
  ts REAL,
  pitch INTEGER,
  velocity INTEGER,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE TABLE IF NOT EXISTS probs (
  session_id INTEGER,
  ts REAL,
  value REAL,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
"""

class SessionLogger:
    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        self.session_id = None
        self._ensure_columns()

    def _ensure_columns(self):
        # Add new columns if upgrading existing DB
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(sessions)")
        cols = {row[1] for row in cur.fetchall()}
        alter_stmts = []
        if 'adaptive' not in cols:
            alter_stmts.append("ALTER TABLE sessions ADD COLUMN adaptive INTEGER DEFAULT 0")
        if 'arp_mode' not in cols:
            alter_stmts.append("ALTER TABLE sessions ADD COLUMN arp_mode TEXT DEFAULT 'off'")
        if 'arp_rate' not in cols:
            alter_stmts.append("ALTER TABLE sessions ADD COLUMN arp_rate REAL DEFAULT 1.0")
        if 'density' not in cols:
            alter_stmts.append("ALTER TABLE sessions ADD COLUMN density REAL DEFAULT 0.5")
        for stmt in alter_stmts:
            try:
                self.conn.execute(stmt)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def start_session(self, preset: str, key: str, bpm: int, beats_per_chord: int,
                      adaptive: int = 0, arp_mode: str = 'off', arp_rate: float = 1.0, density: float = 0.5):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO sessions (start_ts, preset, key, bpm, beats_per_chord, adaptive, arp_mode, arp_rate, density) VALUES (?,?,?,?,?,?,?,?,?)",
            (time.time(), preset, key, bpm, beats_per_chord, int(adaptive), arp_mode, float(arp_rate), float(density)),
        )
        self.session_id = cur.lastrowid
        self.conn.commit()
        return self.session_id

    def log_chord(self, root: int, quality: str, pitches):
        if self.session_id is None:
            return
        self.conn.execute(
            "INSERT INTO chords VALUES (?,?,?,?,?)",
            (self.session_id, time.time(), root, quality, json.dumps(pitches)),
        )

    def log_note(self, pitch: int, velocity: int):
        if self.session_id is None:
            return
        self.conn.execute(
            "INSERT INTO notes VALUES (?,?,?,?)",
            (self.session_id, time.time(), pitch, velocity),
        )
    
    def log_prob(self, value: float):
        if self.session_id is None:
            return
        self.conn.execute(
            "INSERT INTO probs VALUES (?,?,?)",
            (self.session_id, time.time(), float(value)),
        )

    def end_session(self):
        if self.session_id is None:
            return
        self.conn.execute(
            "UPDATE sessions SET end_ts=? WHERE id=?",
            (time.time(), self.session_id),
        )
        self.conn.commit()
        self.conn.close()
        self.session_id = None

    # ---------- Static helpers ----------

    @classmethod
    def list_sessions(cls, limit: int = 20):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, start_ts, end_ts, preset, key, bpm, beats_per_chord, adaptive, arp_mode, arp_rate, density FROM sessions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return rows 