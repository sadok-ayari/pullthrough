from __future__ import annotations

import os
import sqlite3
from typing import Dict, List, Tuple

from .models import Reading

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    day         TEXT NOT NULL,
    narrative   TEXT NOT NULL,
    article_key TEXT NOT NULL,
    state       TEXT NOT NULL,
    in_title    INTEGER NOT NULL DEFAULT 0,
    outlet      TEXT,
    title       TEXT,
    url         TEXT,
    PRIMARY KEY (day, narrative, article_key)
);
CREATE TABLE IF NOT EXISTS runs (
    day       TEXT PRIMARY KEY,
    articles  INTEGER NOT NULL,
    conveyed  INTEGER NOT NULL,
    mentioned INTEGER NOT NULL,
    distorted INTEGER NOT NULL,
    absent    INTEGER NOT NULL
);
"""


class Store:
    def __init__(self, path: str = "pullthrough.db"):
        directory = os.path.dirname(os.path.abspath(path))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def save(self, day: str, readings: List[Reading]) -> None:
        rows = [
            (day, r.narrative, r.article.key, r.state, 1 if r.in_title else 0,
             r.article.outlet, r.article.title, r.article.url)
            for r in readings
        ]
        self.conn.executemany(
            "INSERT OR REPLACE INTO readings "
            "(day, narrative, article_key, state, in_title, outlet, title, url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        counts = {state: 0 for state in ("conveyed", "mentioned", "distorted", "absent")}
        for r in readings:
            counts[r.state] = counts.get(r.state, 0) + 1
        self.conn.execute(
            "INSERT OR REPLACE INTO runs (day, articles, conveyed, mentioned, distorted, absent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (day, len({r.article.key for r in readings}), counts["conveyed"],
             counts["mentioned"], counts["distorted"], counts["absent"]))
        self.conn.commit()

    def history(self, narrative: str, limit: int = 14) -> List[Tuple[str, Dict[str, int]]]:
        rows = self.conn.execute(
            "SELECT day, state, COUNT(*) FROM readings WHERE narrative = ? "
            "GROUP BY day, state ORDER BY day DESC", (narrative,)).fetchall()
        days: Dict[str, Dict[str, int]] = {}
        for day, state, count in rows:
            days.setdefault(day, {})[state] = count
        out = sorted(days.items(), reverse=True)[:limit]
        return list(reversed(out))

    def close(self) -> None:
        self.conn.close()
