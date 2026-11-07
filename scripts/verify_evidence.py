"""Replay exported scripted episodes without any model calls or service access."""

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

from worldfork.agents import PythonAgent
from worldfork.engine import Action, World, digest, score
from worldfork.gateway import unwrap_json_reply

ROOT = Path(__file__).resolve().parents[1]
LEGACY_ENGINE = "7b9aed1bc23dc5a8d8f1fa31d60b80ce12c979cb1334996b40f733c2e8ec91ca"
LEGACY_GATEWAY = "4b897ddf1de418afa24eab6a96c2abbe1471995869c4721072e10ab14219ca16"
JSON_FENCE_GATEWAY = "9f18aab1139c49cff198f47c3a63c1b819c0fb980ab9ae152e10dccd0fec817c"
VALIDATED_USAGE_GATEWAY = (
    "90659c040808e75ffc66493f526f2a007c27c1db288efd6f6b7a69885c0ead49"
)
LEGACY_RUNNER = "2cdf596d46e787481d3305d1b3cd8045b3fa3175a21e69729b468c6f4923fc05"
ATOMIC_RUNNER = "dddb4918c6c10e20e5277371f4067fa214ba86e1c0847ce3e10ba982bfb86237"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_export(payload, *, strict_attempt_links=False):
    run, events = payload["run"], payload["events"]
    require(
        run["config"]["passenger_mode"] == "scripted",
        "This replay verifier handles scripted contracts only",
    )
    require(run["status"] not in ["running", "queued"], "Episode is unfinished")
    require(
        [e["seq"] for e in events] == list(range(1, len(events) + 1)),
        "Event sequence has a gap",
    )
    require(
        bool(events)
        and events[0]["type"] == "started"
        and events[-1]["type"] == "finished",
        "Missing episode boundaries",
    )
    require(
        all(event["run_id"] == run["id"] for event in events),
        "Event run identity differs",
    )
    result = run["result"]
    require(events[-1]["result"] == result, "Finished event result differs")
    max_steps = run["config"]["max_steps"]
    require(type(max_steps) is int and 1 <= max_steps <= 64, "Invalid step budget")
    require(
        all(
            type(event["tick"]) is int and 0 <= event["tick"] <= max_steps
            for event in events
        ),
        "Event tick outside step budget",
    )
    require(
        set(run["config"]["source_hashes"])
        == {"engine", "agents", "gateway", "runner"},
        "Required source hashes differ",
    )
    world = World(payload["scenario"])
    strategy = run["config"]["strategy"]
    agent = PythonAgent(None, run["id"], world.fixture["policy"], strategy)
    require(
        digest(payload["scenario"]) == run["config"]["scenario_hash"],
        "Scenario hash mismatch",
    )
    for name, expected in run["config"]["source_hashes"].items():
        current = (ROOT / "backend/worldfork" / (name + ".py")).read_text()
        if (
            digest(current) != expected
            and name == "engine"
            and expected == LEGACY_ENGINE
        ):
            old = (ROOT / "evidence/frozen-source/engine.py").read_text()
            require(digest(old) == expected, "Frozen engine snapshot differs")
            require(
                current
                == old.replace(
                    '"cases": self.cases(),', '"cases": copy.deepcopy(self.cases()),', 1
                ),
                "Engine changed beyond the observation-copy correction",
            )
        elif name == "gateway" and expected == LEGACY_GATEWAY:
            old = (ROOT / "evidence/frozen-source/gateway.py").read_text()
            require(digest(old) == expected, "Frozen gateway snapshot differs")
            require(
                digest(current)
                in {expected, JSON_FENCE_GATEWAY, VALIDATED_USAGE_GATEWAY},
                "Unknown gateway revision",
            )
        elif name == "gateway" and expected == JSON_FENCE_GATEWAY:
            old = (ROOT / "evidence/frozen-source/gateway-json-fence.py").read_text()
            require(digest(old) == expected, "Frozen gateway snapshot differs")
            require(
                digest(current) in {expected, VALIDATED_USAGE_GATEWAY},
                "Unknown gateway revision",
            )
        elif name == "runner" and expected == LEGACY_RUNNER:
            old = (ROOT / "evidence/frozen-source/runner.py").read_text()
            require(digest(old) == expected, "Frozen runner snapshot differs")
            require(
                digest(current) in {expected, ATOMIC_RUNNER}, "Unknown runner revision"
            )
        else:
            require(digest(current) == expected, "Frozen source differs: " + name)
    timeout_ticks = {
        e["tick"]
        for e in events
        if e["type"] == "fault" and e.get("fault") == "tool_timeout"
    }
    misleading = {
        e["tick"]: e["shown"]
        for e in events
        if e["type"] == "fault" and e.get("fault") == "misleading_observation"
    }
    legacy_observation_events = 0
    for event in events:
        require(event["tick"] >= world.tick, "Logical time moved backward")
        while world.tick < event["tick"]:
            world.advance()
        if event["type"] == "fault" and event["fault"] == "misleading_observation":
            truth = world.option_view()
            shown = copy.deepcopy(truth)
            shown[0]["available"] += 1
            require(
                event["truth"] == truth and event["shown"] == shown,
                "Injected inventory differs",
            )
        if event["type"] == "action":
            action = Action.model_validate(event["action"])
            expected_observation = copy.deepcopy(world.observation())
            if event["tick"] in misleading:
                expected_observation["options"] = misleading[event["tick"]]
            menu = [
                {"id": i, **option.model_dump()}
                for i, option in enumerate(agent.action_menu(expected_observation))
            ]
            require(event["candidate_actions"] == menu, "Public action menu differs")
            if strategy == "case_by_case":
                pending = (
                    c["id"]
                    for c in expected_observation["cases"]
                    if not c["booking"] and agent.failures.get(c["id"], 0) < 2
                )
                expected_observation["queue_guidance"] = {
                    "focus": next(pending, None),
                    "deferred": [p for p, n in agent.failures.items() if n >= 2],
                    "rule": "Public bookings and bounded failures only; already-booked parties remain contactable.",
                }
            observed = event["observation"]
            if (
                observed != expected_observation
                and run["config"]["source_hashes"]["engine"] == LEGACY_ENGINE
                and action.tool == "ask_question"
                and event["result"].get("ok")
            ):
                case = next(
                    c
                    for c in expected_observation["cases"]
                    if c["id"] == action.arguments["party_id"]
                )
                case["known"][action.arguments["topic"]] = event["result"]["answer"]
                legacy_observation_events += 1
            require(
                observed == expected_observation,
                f"Public observation differs at tick {world.tick}",
            )
            raw = event["attempts"][-1]["raw_response"]
            if run["config"]["source_hashes"]["gateway"] != LEGACY_GATEWAY:
                raw = unwrap_json_reply(raw)
            selected = json.loads(raw)["action_id"]
            candidate = next(
                (a for a in event["candidate_actions"] if a["id"] == selected), None
            )
            require(
                candidate is not None
                and {k: v for k, v in candidate.items() if k != "id"}
                == event["action"],
                "Recorded choice differs from the measured model reply",
            )
            if event["tick"] in timeout_ticks:
                require(
                    event["result"].get("code") == "timeout",
                    "Timeout event did not produce a timeout receipt",
                )
                world.last_result = event["result"]
            else:
                actual = world.execute(action)
                require(
                    actual == event["result"], f"Receipt differs at tick {world.tick}"
                )
            agent.observe_tool_result(action, event["result"])
        world.assert_invariants()
        require(
            world.snapshot() == event["snapshot"],
            f"World differs at event {event['seq']}",
        )
    for key, value in score(world).items():
        require(result[key] == value, "Terminal score differs: " + key)
    require(run["snapshot"] == world.snapshot(), "Run terminal snapshot differs")
    require(
        result["steps"] == world.tick <= run["config"]["max_steps"],
        "Step budget mismatch",
    )
    require(
        result["tool_calls"] == sum(e["type"] == "action" for e in events),
        "Tool count mismatch",
    )
    attempts = result["attempts"]
    require(result["model_calls"] == len(attempts), "Model-attempt count mismatch")
    require(
        len({a["id"] for a in attempts}) == len(attempts), "Duplicate attempt identity"
    )
    linked = [attempt for event in events for attempt in event.get("attempts", [])]
    measured = [attempt for attempt in attempts if not attempt["injected"]]
    require(
        linked == measured[: len(linked)],
        "Event attempts differ from aggregate attempts",
    )
    if strict_attempt_links or run["status"] in {"completed", "stopped"}:
        require(len(linked) == len(measured), "Terminal run has unlinked attempts")
    for key in ["input_tokens", "output_tokens"]:
        expected = (
            sum(a[key] for a in attempts)
            if all(a[key] is not None for a in attempts)
            else None
        )
        require(result[key] == expected, "Token accounting differs: " + key)
    faults = [e for e in events if e["type"] == "fault"]
    require(bool(faults) == result["fault_delivered"], "Fault exposure flag differs")
    require(len(faults) <= 1, "More than one fault delivered")
    require(
        result["fault_configured"] == run["config"]["fault"]
        and all(fault["fault"] == result["fault_configured"] for fault in faults),
        "Configured and recorded fault identities differ",
    )
    require(result["terminal"] == run["status"], "Terminal status differs")
    return {
        "id": run["id"],
        "events": len(events),
        "actions": result["tool_calls"],
        "attempts": len(attempts),
        "status": run["status"],
        "satisfied_people": result["satisfied_people"],
        "fault": run["config"]["fault"],
        "fault_delivered": result["fault_delivered"],
        "model_digest": run["config"]["model_manifest"]["digest"],
        "legacy_observation_events": legacy_observation_events,
    }


def verify_manifest(filename):
    manifest = json.loads(filename.read_text())
    require(
        manifest["matrix"] == "full30" and len(manifest["runs"]) == 30,
        "Expected the complete full30 pilot",
    )
    require(
        not manifest["tracked_changes_at_start"],
        "Pilot started with tracked source changes",
    )
    records = []
    for entry in manifest["runs"]:
        trace = Path(entry.get("trace", ""))
        if not trace.is_absolute():
            trace = ROOT / trace
        require(trace.is_file(), "Missing full trace for " + entry["id"])
        payload = json.loads(trace.read_text())
        require(payload["run"]["id"] == entry["id"], "Trace identity mismatch")
        require(payload["run"]["status"] == entry["status"], "Trace status mismatch")
        require(
            payload["run"]["config"] == entry["config"], "Trace configuration mismatch"
        )
        require(
            payload["run"]["result"] == entry["result"],
            "Manifest and trace result differ",
        )
        records.append(verify_export(payload, strict_attempt_links=True))
    require(len({r["id"] for r in records}) == 30, "Duplicate episode identity")
    digests = {r["model_digest"] for r in records}
    require(
        len(digests) == 1 and None not in digests,
        "Model identity drift or missing digest",
    )
    cells = Counter(
        (e["config"]["framework"], e["config"]["strategy"], e["config"]["fault"])
        for e in manifest["runs"]
    )
    require(
        len(cells) == 10 and all(n == 3 for n in cells.values()),
        "Matrix cell counts differ",
    )
    for cell in cells:
        seeds = {
            e["config"]["seed"]
            for e in manifest["runs"]
            if (e["config"]["framework"], e["config"]["strategy"], e["config"]["fault"])
            == cell
        }
        require(seeds == {11, 29, 47}, "Unexpected seeds in matrix cell")
    common = {
        tuple(
            e["config"][k]
            for k in [
                "scenario_hash",
                "model",
                "passenger_mode",
                "temperature",
                "max_steps",
                "max_tokens",
                "wall_seconds",
            ]
        )
        for e in manifest["runs"]
    }
    require(len(common) == 1, "A shared experiment condition drifted")
    return {
        "verified_episodes": len(records),
        "events": sum(r["events"] for r in records),
        "actions": sum(r["actions"] for r in records),
        "model_attempts": sum(r["attempts"] for r in records),
        "statuses": dict(Counter(r["status"] for r in records)),
        "model_digest": next(iter(digests)),
        "legacy_observation_events": sum(
            r["legacy_observation_events"] for r in records
        ),
        "runs": records,
        "scope": "Deterministic scripted-world replay, receipts, scores, measured choices, identities and token sums. Archived disclosure alias is explicitly checked and counted; originals are unchanged. No model calls or human-realism claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify_manifest(args.manifest)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered)
