"""Summarize retained pilot counts without hiding unsuccessful terminal states."""

from collections import Counter, defaultdict
from statistics import mean

from .engine import digest


def benchmark_summary(runs):
    """Keep repeated-run means within a single measured task and harness."""
    groups = {}
    unidentified = 0
    fields = [
        "scenario_id",
        "scenario_hash",
        "model",
        "passenger_mode",
        "fault",
        "temperature",
        "max_steps",
        "max_tokens",
        "wall_seconds",
        "source_hashes",
    ]
    for run in runs:
        config = {field: run["config"].get(field) for field in fields}
        config["model_digest"] = (run["config"].get("model_manifest") or {}).get(
            "digest"
        )
        if (
            any(value is None for value in config.values())
            or not config["source_hashes"]
        ):
            unidentified += 1
            continue
        key = digest(config)
        cohort = groups.setdefault(key, {"id": key, "config": config, "runs": []})
        entry = dict(run)
        if run.get("result"):
            result = run["result"]
            tokens = [result.get("input_tokens"), result.get("output_tokens")]
            entry["result"] = {
                **result,
                "tokens": sum(tokens) if all(t is not None for t in tokens) else None,
            }
        cohort["runs"].append(entry)
    cohorts = []
    for cohort in groups.values():
        entries = cohort.pop("runs")
        rows = summarize({"runs": entries})["rows"]
        for row in rows:
            members = [
                entry
                for entry in entries
                if entry["config"]["framework"] == row["framework"]
                and entry["config"]["strategy"] == row["strategy"]
            ]
            row["run_ids"] = [entry["id"] for entry in members]
            row["seeds"] = sorted({entry["config"]["seed"] for entry in members})
        cohorts.append({**cohort, "rows": rows})
    return {"cohorts": cohorts, "unidentified_runs": unidentified}


def summarize(manifest):
    groups = defaultdict(list)
    for entry in manifest["runs"]:
        config = entry["config"]
        key = (
            config.get("model", "unspecified"),
            config.get("scenario_id", "harbor-v1"),
            config.get("passenger_mode", "scripted"),
            config.get("framework", "python"),
            config.get("strategy", "coordinated"),
            config.get("fault", "none"),
        )
        groups[key].append(entry)
    rows = []
    for (model, scenario, population, framework, strategy, fault), entries in sorted(
        groups.items()
    ):
        statuses = Counter(e.get("status", "pending") for e in entries)
        scored = [
            e["result"]
            for e in entries
            if e.get("result")
            and e.get("status") not in ["cancelled", "simulator_error", "interrupted"]
        ]
        resolved = [r["satisfied_people"] for r in scored]
        metrics = {}
        for field in [
            "model_calls",
            "tokens",
            "total_people",
            "steps",
            "tool_calls",
            "input_tokens",
            "output_tokens",
            "elapsed_ms",
            "compensation_spent",
            "invalid_attempts",
            "committed_policy_violations",
            "api_cost",
        ]:
            values = [r[field] for r in scored if r.get(field) is not None]
            metrics[field] = {
                "known": len(values),
                "mean": mean(values) if values else None,
                "range": [min(values), max(values)] if values else None,
            }
        rows.append(
            {
                "model": model,
                "scenario": scenario,
                "population": population,
                "framework": framework,
                "strategy": strategy,
                "fault": fault,
                "configured": len(entries),
                "statuses": dict(statuses),
                "scored": len(scored),
                "completed": sum(e.get("status") == "completed" for e in entries),
                "metrics": metrics,
                "resolved_mean": mean(resolved) if resolved else None,
                "resolved_range": [min(resolved), max(resolved)] if resolved else None,
                "fault_exposed": sum(
                    bool(e.get("result", {}).get("fault_delivered"))
                    for e in entries
                    if e.get("result")
                ),
                "elapsed_mean_ms": mean(r["elapsed_ms"] for r in scored)
                if scored
                else None,
            }
        )
    return {
        "kind": "synthetic pilot",
        "rows": rows,
        "runs": [
            {
                "id": e.get("id", "unassigned"),
                "config": e["config"],
                "status": e.get("status", "pending"),
                "result": e.get("result"),
            }
            for e in manifest["runs"]
        ],
        "notes": [
            "Raw terminal counts include every retained run.",
            "Cancelled, interrupted and simulator-error runs are excluded from means, not erased.",
            "Fault exposure denominator may be smaller than configured count.",
            "Small pilot; no significance or real-world prediction claim.",
            "Model-unavailable recovery includes an automatic harness retry; do not attribute that retry to model reasoning.",
            "Means use known values only; each resource cell reports its known/scored denominator.",
        ],
    }


def markdown(report):
    lines = [
        "# WorldFork pilot summary",
        "",
        "Synthetic development scenarios; not a real-world forecast.",
        "",
        "| Framework | Strategy | Fault | Configured / scored | Requirements met (mean; range) | Fault exposures | Terminal states |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for r in report["rows"]:
        value = (
            "unavailable"
            if r["resolved_mean"] is None
            else f"{r['resolved_mean']:.2f}; {r['resolved_range'][0]}–{r['resolved_range'][1]}"
        )
        statuses = ", ".join(f"{k}: {v}" for k, v in r["statuses"].items())
        lines.append(
            f"| {r['framework']} | {r['strategy']} | {r['fault']} | {r['configured']} / {r['scored']} | {value} | {r['fault_exposed']} | {statuses} |"
        )
    lines.extend(
        [
            "",
            "## Resource measurements",
            "",
            "Each mean is followed by its known/scored denominator. Unknown usage is not zero.",
            "",
            "| Framework | Strategy | Fault | Steps | Tool calls | Input tokens | Output tokens | Elapsed seconds | Credits spent | Invalid attempts | Committed violations |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for r in report["rows"]:

        def cell(field, divisor=1, row=r):
            metric = row["metrics"][field]
            if metric["mean"] is None:
                return "unknown"
            return (
                f"{metric['mean'] / divisor:,.1f} ({metric['known']}/{row['scored']})"
            )

        lines.append(
            f"| {r['framework']} | {r['strategy']} | {r['fault']} | "
            + " | ".join(
                [
                    cell("steps"),
                    cell("tool_calls"),
                    cell("input_tokens"),
                    cell("output_tokens"),
                    cell("elapsed_ms", 1000),
                    cell("compensation_spent"),
                    cell("invalid_attempts"),
                    cell("committed_policy_violations"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Configuration groups", ""])
    for model, scenario, population in sorted(
        {(r["model"], r["scenario"], r["population"]) for r in report["rows"]}
    ):
        lines.append(
            f"- Model: {model}; scenario: {scenario}; passengers: {population}."
        )
    lines.extend(
        [
            "",
            "Local API charge is recorded per run. Hardware and electricity are unmeasured.",
            "",
            "## Raw episode outcomes",
            "",
            "| Run | Framework / strategy | Fault | Status | Requirements met | Steps | Fault delivered |",
            "|---|---|---|---|---:|---:|---|",
        ]
    )
    for e in report.get("runs", []):
        c, result = e["config"], e.get("result") or {}
        lines.append(
            f"| {e['id']} | {c.get('framework', 'python')} / {c.get('strategy', 'coordinated')} | {c.get('fault', 'none')} | {e['status']} | {result.get('satisfied_people', 'unknown')} | {result.get('steps', 'unknown')} | {result.get('fault_delivered', 'unknown')} |"
        )
    lines.extend(["", *["- " + note for note in report["notes"]], ""])
    return "\n".join(lines)
