import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
verify_export = runpy.run_path(str(ROOT / "scripts/verify_evidence.py"))[
    "verify_export"
]


@pytest.fixture
def trace():
    manifest = json.loads((ROOT / "evidence/pilot-manifest.json").read_text())
    return json.loads((ROOT / manifest["runs"][0]["trace"]).read_text())


def test_original_trace_verifies(trace):
    assert verify_export(trace)["id"] == trace["run"]["id"]


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("identity", "Event run identity"),
        ("result", "Finished event result"),
        ("hashes", "Required source hashes"),
        ("tick", "Event tick outside"),
        ("attempt", "Event attempts differ"),
        ("menu", "Public action menu differs"),
        ("guidance", "Public observation differs"),
    ],
)
def test_replay_rejects_tampered_trace(trace, field, message):
    if field == "identity":
        trace["events"][1]["run_id"] = "other-run"
    elif field == "result":
        trace["events"][-1]["result"]["satisfied_people"] = -1
    elif field == "hashes":
        del trace["run"]["config"]["source_hashes"]["runner"]
    elif field == "tick":
        trace["events"][1]["tick"] = 10**9
    elif field == "attempt":
        action = next(e for e in trace["events"] if e["type"] == "action")
        action["attempts"][-1]["id"] = "forged"
    elif field == "menu":
        action = next(e for e in trace["events"] if e["type"] == "action")
        action["candidate_actions"].pop()
    elif field == "guidance":
        action = next(e for e in trace["events"] if e["type"] == "action")
        action["observation"]["queue_guidance"]["focus"] = "forged"
    with pytest.raises(ValueError, match=message):
        verify_export(trace)
