"""Create a new replay database from verified exports without model calls."""

import argparse
import json
from pathlib import Path

from verify_evidence import verify_manifest
from worldfork.store import Store

ROOT = Path(__file__).resolve().parents[1]


def import_evidence(manifest_path, database_path):
    if database_path.exists():
        raise ValueError("Destination exists; choose a new database path")
    verify_manifest(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    store = Store(database_path)
    try:
        with store.db:
            for entry in manifest["runs"]:
                payload = json.loads((ROOT / entry["trace"]).read_text())
                run = payload["run"]
                # Preserve original timestamps, statuses, receipts and identities.
                store.db.execute(
                    "INSERT INTO runs VALUES(?,?,?,?,?,?)",
                    (
                        run["id"],
                        run["created_at"],
                        run["status"],
                        json.dumps(run["config"]),
                        json.dumps(run["snapshot"]),
                        json.dumps(run["result"]),
                    ),
                )
                store.db.executemany(
                    "INSERT INTO events VALUES(?,?,?)",
                    [
                        (run["id"], event["seq"], json.dumps(event))
                        for event in payload["events"]
                    ],
                )
        for entry in manifest["runs"]:
            original = json.loads((ROOT / entry["trace"]).read_text())
            if (
                store.get(entry["id"]) != original["run"]
                or store.events(entry["id"]) != original["events"]
            ):
                raise ValueError("Imported data differs from source export")
    finally:
        store.db.close()
    return {
        "database": str(database_path),
        "imported_runs": len(manifest["runs"]),
        "model_calls_sent": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest", type=Path, nargs="?", default=ROOT / "evidence/pilot-manifest.json"
    )
    parser.add_argument(
        "--database", type=Path, default=ROOT / "artifacts/replay.sqlite"
    )
    args = parser.parse_args()
    print(json.dumps(import_evidence(args.manifest, args.database), indent=2))
