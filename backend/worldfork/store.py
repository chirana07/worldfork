import json
import sqlite3
import threading
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path


def now():
    return datetime.now(UTC).isoformat()


def serialized(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)

    return wrapped


class Store:
    def __init__(self, path):
        self.lock = threading.RLock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created_at TEXT, status TEXT, config TEXT, snapshot TEXT, result TEXT);
        CREATE TABLE IF NOT EXISTS events(run_id TEXT REFERENCES runs(id), seq INTEGER, event TEXT, PRIMARY KEY(run_id,seq));
        CREATE TABLE IF NOT EXISTS comparisons(id TEXT PRIMARY KEY, created_at TEXT, config TEXT, run_ids TEXT);
        """)
        self.db.commit()

    @serialized
    def recover_interrupted(self):
        self.db.execute(
            "UPDATE runs SET status='interrupted' WHERE status IN ('queued','running')"
        )
        self.db.commit()

    @serialized
    def create(self, rid, config, snapshot):
        self.db.execute(
            "INSERT INTO runs VALUES(?,?,?,?,?,?)",
            (rid, now(), "queued", json.dumps(config), json.dumps(snapshot), None),
        )
        self.db.commit()

    @serialized
    def update(self, rid, status=None, snapshot=None, result=None):
        for key, value in [
            ("status", status),
            ("snapshot", json.dumps(snapshot) if snapshot is not None else None),
            ("result", json.dumps(result) if result is not None else None),
        ]:
            if value is not None:
                self.db.execute(f"UPDATE runs SET {key}=? WHERE id=?", (value, rid))
        self.db.commit()

    @serialized
    def enrich_manifest(self, rid, fields):
        current = self.get(rid)
        if current is None:
            raise KeyError(rid)
        merged = {**current["config"], **fields}
        self.db.execute(
            "UPDATE runs SET config=? WHERE id=?", (json.dumps(merged), rid)
        )
        self.db.commit()

    @serialized
    def append(self, rid, event, snapshot, *, terminal=None):
        with self.db:
            seq = self.db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE run_id=?", (rid,)
            ).fetchone()[0]
            event = {
                **event,
                "seq": seq,
                "run_id": rid,
                "timestamp_utc": now(),
                "snapshot": snapshot,
            }
            self.db.execute(
                "INSERT INTO events VALUES(?,?,?)", (rid, seq, json.dumps(event))
            )
            if terminal is None:
                self.db.execute(
                    "UPDATE runs SET snapshot=? WHERE id=?", (json.dumps(snapshot), rid)
                )
            else:
                self.db.execute(
                    "UPDATE runs SET snapshot=?, status=?, result=? WHERE id=?",
                    (json.dumps(snapshot), terminal, json.dumps(event["result"]), rid),
                )
        return event

    @serialized
    def get(self, rid):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (rid,)).fetchone()
        if not row:
            return None
        return self.decode_run(row)

    @staticmethod
    def decode_run(row):
        d = dict(row)
        for k in ["config", "snapshot", "result"]:
            if k in d:
                d[k] = json.loads(d[k]) if d[k] else None
        return d

    @serialized
    def list(self, *, summary=False):
        columns = "*"
        if summary:
            columns = """id, created_at, status, config,
                CASE WHEN result IS NOT NULL THEN json_object(
                    'satisfied_people', json_extract(result, '$.satisfied_people'),
                    'total_people', json_extract(result, '$.total_people')
                ) END AS result"""
        return [
            self.decode_run(row)
            for row in self.db.execute(
                f"SELECT {columns} FROM runs ORDER BY created_at DESC LIMIT 100"
            )
        ]

    @serialized
    def events(self, rid, after=0):
        return [
            json.loads(r[0])
            for r in self.db.execute(
                "SELECT event FROM events WHERE run_id=? AND seq>? ORDER BY seq",
                (rid, after),
            )
        ]

    @serialized
    def comparison(self, cid, config=None, run_ids=None):
        if config is not None:
            self.db.execute(
                "INSERT INTO comparisons VALUES(?,?,?,?)",
                (cid, now(), json.dumps(config), json.dumps(run_ids)),
            )
            self.db.commit()
        row = self.db.execute("SELECT * FROM comparisons WHERE id=?", (cid,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "config": json.loads(row["config"]),
            "run_ids": json.loads(row["run_ids"]),
        }
