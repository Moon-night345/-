
"""Durable triage cases and redacted agent traces for a multi-process deployment."""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

RULES_VERSION = "triage-rules-v1.2"
TTL_HOURS = int(os.getenv("BOTTLESAFE_CASE_TTL_HOURS", "24"))
DB_PATH = Path(os.getenv("BOTTLESAFE_TRIAGE_DB", str(Path(__file__).resolve().parent.parent / "data" / "triage_cases.sqlite3")))

def _now(): return datetime.now(timezone.utc)
def _iso(dt): return dt.isoformat(timespec="seconds")
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
      CREATE TABLE IF NOT EXISTS cases(
        case_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, lang TEXT NOT NULL,
        mode TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
        expires_at TEXT NOT NULL, answers_json TEXT NOT NULL,
        analysis_json TEXT, result_json TEXT);
      CREATE INDEX IF NOT EXISTS idx_cases_expiry ON cases(expires_at);
      CREATE TABLE IF NOT EXISTS trace_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT NOT NULL,
        case_id TEXT NOT NULL, event_type TEXT NOT NULL, payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL);
      CREATE INDEX IF NOT EXISTS idx_trace_events ON trace_events(trace_id, id);
    """)
    return c

def _redact(value, key=""):
    k = key.lower()
    if any(x in k for x in ("phone", "email", "address", "path", "photo", "image", "filename", "raw")):
        return "[redacted]"
    if k in {"product_or_mix", "symptoms_text", "free_text"}:
        return "[redacted_free_text]"
    if isinstance(value, dict): return {str(a): _redact(b, str(a)) for a,b in value.items()}
    if isinstance(value, list): return [_redact(x, key) for x in value]
    return value

def purge_expired():
    c = _conn(); c.execute("DELETE FROM cases WHERE expires_at < ?", (_iso(_now()),)); c.commit(); c.close()

def save_case(case):
    c = _conn(); now = _now(); expires = now + timedelta(hours=TTL_HOURS)
    c.execute("""INSERT INTO cases(case_id,trace_id,lang,mode,created_at,updated_at,expires_at,answers_json,analysis_json,result_json)
                 VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(case_id) DO UPDATE SET
                 updated_at=excluded.updated_at, expires_at=excluded.expires_at, answers_json=excluded.answers_json,
                 analysis_json=excluded.analysis_json, result_json=excluded.result_json""",
              (case.case_id, case.trace_id, case.lang, case.mode, case.created_at, _iso(now), _iso(expires),
               json.dumps(case.answers, ensure_ascii=False), json.dumps(case.analysis, ensure_ascii=False) if case.analysis is not None else None,
               json.dumps(case.result, ensure_ascii=False) if case.result is not None else None))
    c.commit(); c.close()

def load_case(case_id):
    purge_expired(); c = _conn(); row = c.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone(); c.close()
    if not row: return None
    return dict(row, answers=json.loads(row["answers_json"]), analysis=json.loads(row["analysis_json"]) if row["analysis_json"] else None,
                result=json.loads(row["result_json"]) if row["result_json"] else None)

def delete_case(case_id):
    c = _conn(); row = c.execute("SELECT trace_id FROM cases WHERE case_id=?", (case_id,)).fetchone()
    if row: c.execute("DELETE FROM trace_events WHERE trace_id=?", (row["trace_id"],))
    c.execute("DELETE FROM cases WHERE case_id=?", (case_id,)); c.commit(); deleted = c.total_changes > 0; c.close(); return deleted

def append_trace(trace_id, case_id, event_type, payload):
    c = _conn(); c.execute("INSERT INTO trace_events(trace_id,case_id,event_type,payload_json,created_at) VALUES(?,?,?,?,?)",
                           (trace_id, case_id, event_type, json.dumps(_redact(payload), ensure_ascii=False), _iso(_now())))
    c.commit(); c.close()

def trace_view(trace_id):
    c = _conn(); rows = c.execute("SELECT event_type,payload_json,created_at FROM trace_events WHERE trace_id=? ORDER BY id", (trace_id,)).fetchall(); c.close()
    return [{"event": r["event_type"], "payload": json.loads(r["payload_json"]), "created_at": r["created_at"]} for r in rows]
