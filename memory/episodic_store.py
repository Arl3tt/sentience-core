# memory/episodic_store.py
"""
Simple episodic store backed by SQLite for events, task traces, and model summaries.
"""
import os, sqlite3, json, threading
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
DB_PATH = os.getenv("EPISODIC_DB", "./data/episodes.sqlite")
_lock = threading.Lock()

# ensure data dir
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_cur = _conn.cursor()
_cur.execute("""
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT,
    content TEXT,
    metadata TEXT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
_conn.commit()

def add_episode(kind: str, content: str, metadata: Dict[str, Any]=None):
    meta = json.dumps(metadata or {})
    with _lock:
        _cur.execute("INSERT INTO episodes (kind, content, metadata) VALUES (?, ?, ?)", (kind, content, meta))
        _conn.commit()
        return _cur.lastrowid

def query_recent(limit: int=50) -> List[Dict[str, Any]]:
    with _lock:
        _cur.execute("SELECT id, kind, content, metadata, ts FROM episodes ORDER BY id DESC LIMIT ?", (limit,))
        rows = _cur.fetchall()
    out = []
    for r in rows:
        out.append({"id": r[0], "kind": r[1], "content": r[2], "metadata": json.loads(r[3]) if r[3] else {}, "ts": r[4]})
    return out

def find_by_kind(kind: str, limit: int=50):
    with _lock:
        _cur.execute("SELECT id, kind, content, metadata, ts FROM episodes WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, limit))
        rows = _cur.fetchall()
    return [{"id":r[0],"content":r[2],"meta": json.loads(r[3]) if r[3] else {}, "ts": r[4]} for r in rows]