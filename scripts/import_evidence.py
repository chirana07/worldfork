"""Create a new replay database from verified exports without model calls."""

import argparse
import json
from pathlib import Path

from verify_evidence import verify_export, verify_manifest
from worldfork.store import Store

ROOT = Path(__file__).resolve().parents[1]


def load_recorded_runs(manifest_path, *, team_demo=False, evaluation=False):
    if evaluation:
        from evaluate_team import verify

        verify(manifest_path)
        manifest = json.loads(manifest_path.read_text())
        return [
            json.loads((manifest_path.parent / entry["trace"]).read_text())
            for entry in manifest["runs"]
        ]
    if team_demo:
        payloads = []
        for prefix, fault in (("", "none"), ("timeout-", "tool_timeout")):
            pair = [
                json.loads(
                    (ROOT / "evidence/team-demo" / f"{prefix}{name}.json").read_text()
                )
                for name in ("solo", "team")
            ]
            configs = []
            for payload in pair:
                result = verify_export(payload, strict_attempt_links=True)
                if result["fault"] != fault or result["fault_delivered"] != (
                    fault != "none"
                ):
                    raise ValueError(
                        "Recorded team demo fault differs from expected condition"
                    )
                configs.append(dict(payload["run"]["config"]))
            if [config.pop("strategy") for config in configs] != [
                "coordinated",
                "team",
            ] or configs[0] != configs[1]:
                raise ValueError(
                    "Team demo does not contain a matched solo and team comparison"
                )
            payloads.extend(pair)
        if len({payload["run"]["id"] for payload in payloads}) != len(payloads):
            raise ValueError("Team demo contains duplicate run IDs")
        return payloads
    verify_manifest(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    return [
        json.loads((ROOT / entry["trace"]).read_text()) for entry in manifest["runs"]
    ]


def import_evidence(manifest_path, database_path, *, team_demo=False, evaluation=False):
    if database_path.exists():
        raise ValueError("Destination exists; choose a new database path")
    payloads = load_recorded_runs(
        manifest_path, team_demo=team_demo, evaluation=evaluation
    )
    store = Store(database_path)
    try:
        with store.db:
            for payload in payloads:
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
        for original in payloads:
            run_id = original["run"]["id"]
            if (
                store.get(run_id) != original["run"]
                or store.events(run_id) != original["events"]
            ):
                raise ValueError("Imported data differs from source export")
    finally:
        store.db.close()
    return {
        "database": str(database_path),
        "imported_runs": len(payloads),
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
