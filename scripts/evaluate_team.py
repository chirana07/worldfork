"""Run or verify the fixed, resumable release comparison through the public API."""

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import httpx
from verify_evidence import verify_export
from worldfork.cli import build_provenance
from worldfork.runner import RunConfig


def planned_configs():
    configs = []
    for index, seed in enumerate([17, 43, 71]):
        for scenario in ["harbor-v1", "harbor-transfer-v1"]:
            for fault in ["none", "tool_timeout"]:
                strategies = ["coordinated", "team"]
                if (index + (fault == "tool_timeout")) % 2:
                    strategies.reverse()
                for strategy in strategies:
                    configs.append(
                        RunConfig(
                            scenario_id=scenario,
                            strategy=strategy,
                            seed=seed,
                            fault=fault,
                            temperature=0.2,
                            max_steps=16,
                            max_tokens=160000,
                            wall_seconds=900,
                        ).model_dump()
                    )
    return configs


def save(path, manifest):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary.replace(path)


def measurements(payload):
    actions = [event for event in payload["events"] if event["type"] == "action"]
    timeouts = [event for event in actions if event["result"].get("code") == "timeout"]
    after = [
        event for event in actions if timeouts and event["tick"] > timeouts[0]["tick"]
    ]
    result = payload["run"]["result"]
    return {
        "satisfied_people": result["satisfied_people"],
        "model_calls": result["model_calls"],
        "tool_calls": result["tool_calls"],
        "tokens": result["input_tokens"] + result["output_tokens"],
        "elapsed_ms": result["elapsed_ms"],
        "violations": result["committed_policy_violations"],
        "fault_delivered": result["fault_delivered"],
        "post_fault_actions": len(after),
        "successful_post_fault_actions": sum(
            event["result"].get("ok") is True for event in after
        ),
        "post_fault_bookings": sum(
            event["result"].get("receipt", {}).get("status") == "committed"
            for event in after
        ),
        "timed_out_action_succeeded_later": any(
            event["action"] == timeouts[0]["action"]
            and event["result"].get("ok") is True
            for event in after
        ),
        "advice_reuse_steps": sum(
            event.get("coordination", {}).get("consultation_reason") == "reuse_advice"
            for event in actions
        ),
    }


def verify(path, *, complete=True):
    manifest = json.loads(path.read_text())
    expected = planned_configs()
    if manifest["planned_configs"] != expected or len(manifest["runs"]) != len(
        expected
    ):
        raise ValueError("Release matrix differs from its fixed protocol")
    groups = defaultdict(dict)
    totals = defaultdict(list)
    identities = set()
    source_identities = set()
    model_identities = set()
    for entry, config in zip(manifest["runs"], expected, strict=True):
        if entry["config"] != config:
            raise ValueError("Planned configuration differs")
        if "trace" not in entry:
            if complete:
                raise ValueError("Release evaluation is incomplete")
            continue
        trace = path.parent / entry["trace"]
        if hashlib.sha256(trace.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Release trace checksum differs")
        payload = json.loads(trace.read_text())
        verify_export(payload, strict_attempt_links=True)
        run = payload["run"]
        if run["id"] != entry["id"] or run["id"] in identities:
            raise ValueError("Run identity differs or is duplicated")
        identities.add(run["id"])
        if (
            RunConfig.model_validate(
                {key: run["config"][key] for key in config}
            ).model_dump()
            != config
        ):
            raise ValueError("Executed configuration differs")
        if run["status"] not in {"completed", "stopped", "exhausted"}:
            raise ValueError("Episode ended without a valid evaluation outcome")
        source_identities.add(
            json.dumps(run["config"]["source_hashes"], sort_keys=True)
        )
        model_identities.add(run["config"]["model_manifest"]["digest"])
        row = measurements(payload)
        key = (config["scenario_id"], config["fault"], config["seed"])
        groups[key][config["strategy"]] = row
        totals[(config["scenario_id"], config["fault"], config["strategy"])].append(row)
    if (
        len(source_identities) > 1
        or len(model_identities) > 1
        or None in model_identities
    ):
        raise ValueError(
            "The evaluation changed source or has inconsistent model identity"
        )
    rows = [
        "# Release team evaluation",
        "",
        f"Verified episodes: {len(identities)}/{len(expected)}.",
        "",
        "Fixed before inference: three new seeds (17, 43, 71), two fixtures, clean and tool-timeout conditions, two strategies, Python adapter, scripted passengers, Qwen3.5:4b at temperature 0.2, 16 steps and 160,000 observed tokens per episode. Paired strategy order alternates. The timeout is scheduled at tick 8, leaving up to eight subsequent decisions. These are short budget tests.",
        "",
        "The transfer fixture changes arrival requirements, transport modes, party order, early and rail capacity, and compensation. It was reserved from agent tuning before these runs. This measures transfer within the same synthetic airport domain. It is now public evaluation data.",
        "",
        "| Scenario | Fault | Strategy | Episodes | Mean people / 7 | Mean model calls | Calls / tool action | Mean tokens | Mean seconds | Violations |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (scenario, fault, strategy), values in sorted(totals.items()):
        rows.append(
            f"| {scenario} | {fault} | {strategy} | {len(values)} | {mean(v['satisfied_people'] for v in values):.2f} | {mean(v['model_calls'] for v in values):.1f} | {sum(v['model_calls'] for v in values) / sum(v['tool_calls'] for v in values):.2f} | {mean(v['tokens'] for v in values):.0f} | {mean(v['elapsed_ms'] for v in values) / 1000:.1f} | {sum(v['violations'] for v in values)} |"
        )
    rows += [
        "",
        "## Matched outcomes",
        "",
        "| Scenario | Fault | Seed | Solo people | Team people | Solo calls | Team calls |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (scenario, fault, seed), pair in sorted(groups.items()):
        if len(pair) == 2:
            a, b = pair["coordinated"], pair["team"]
            rows.append(
                f"| {scenario} | {fault} | {seed} | {a['satisfied_people']} | {b['satisfied_people']} | {a['model_calls']} | {b['model_calls']} |"
            )
    rows += [
        "",
        "## Fault follow-through",
        "",
        "| Scenario | Strategy | Exposed episodes | Episodes with later actions | Episodes with a later successful tool | Episodes with a later booking | Episodes retrying timed-out action successfully |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for (scenario, fault, strategy), values in sorted(totals.items()):
        if fault == "tool_timeout":
            rows.append(
                f"| {scenario} | {strategy} | {sum(v['fault_delivered'] for v in values)} | {sum(v['post_fault_actions'] > 0 for v in values)} | {sum(v['successful_post_fault_actions'] > 0 for v in values)} | {sum(v['post_fault_bookings'] > 0 for v in values)} | {sum(v['timed_out_action_succeeded_later'] for v in values)} |"
            )
    rows += [
        "",
        "A later successful tool, a booking, and retrying the failed action are distinct observations. They do not establish that the clean outcome was restored. Runs stopping before tick 8 are unexposed. Three seeds, one model, the same simulator and short budgets limit generalization. Local API charge is zero; hardware and electricity were unmeasured. Timing includes local contention and inference warm-up.",
        "",
        "Full exports and SHA-256 checksums are listed in [the manifest](manifest.json). Verify with `uv run python scripts/evaluate_team.py --verify`.",
    ]
    path.with_name("report.md").write_text("\n".join(rows) + "\n")
    return len(identities)


async def evaluate(path, base_url):
    if path.exists():
        verify(path, complete=False)
        manifest = json.loads(path.read_text())
    else:
        provenance = build_provenance()
        if provenance["tracked_changes_at_start"]:
            raise ValueError("Commit the evaluation implementation before running")
        path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "planned_configs": planned_configs(),
            "runs": [{"config": config} for config in planned_configs()],
            **provenance,
        }
        save(path, manifest)
    async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:
        for index, entry in enumerate(manifest["runs"]):
            if "trace" in entry:
                continue
            if "id" not in entry:
                response = await client.post("/api/runs", json=entry["config"])
                response.raise_for_status()
                entry["id"] = response.json()["id"]
                save(path, manifest)
            while True:
                response = await client.get("/api/runs/" + entry["id"])
                response.raise_for_status()
                if response.json()["status"] not in {"queued", "running"}:
                    break
                await asyncio.sleep(2)
            response = await client.get(f"/api/runs/{entry['id']}/export")
            response.raise_for_status()
            payload = response.json()
            verify_export(payload, strict_attempt_links=True)
            trace = path.parent / "traces" / f"{entry['id']}.json"
            trace.parent.mkdir(exist_ok=True)
            trace.write_text(json.dumps(payload, indent=2) + "\n")
            entry.update(
                trace=str(trace.relative_to(path.parent)),
                sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
            )
            save(path, manifest)
            verify(path, complete=False)
            result = payload["run"]["result"]
            print(
                f"{index + 1}/24 {entry['config']['scenario_id']} {entry['config']['fault']} seed {entry['config']['seed']} {entry['config']['strategy']}: {result['satisfied_people']}/7, {result['model_calls']} calls, {payload['run']['status']}",
                flush=True,
            )
    count = verify(path)
    print(
        f"Verified {count} episodes. Report: {path.with_name('report.md')}", flush=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("evidence/team-evaluation/manifest.json")
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        print(f"Verified {verify(args.output)} episodes")
    else:
        asyncio.run(evaluate(args.output, args.url))
