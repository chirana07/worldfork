"""Summarize retained pilot counts without hiding unsuccessful terminal states."""

from collections import Counter, defaultdict
from statistics import mean


def summarize(manifest):
    groups = defaultdict(list)
    for entry in manifest["runs"]:
        config = entry["config"]
        key = (
            config.get("framework", "python"),
            config.get("strategy", "coordinated"),
            config.get("fault", "none"),
        )
        groups[key].append(entry)
    rows = []
    for (framework, strategy, fault), entries in sorted(groups.items()):
        statuses = Counter(e.get("status", "pending") for e in entries)
        scored = [
            e["result"]
            for e in entries
            if e.get("result")
            and e.get("status") not in ["cancelled", "simulator_error", "interrupted"]
        ]
        resolved = [r["satisfied_people"] for r in scored]
        rows.append(
            {
                "framework": framework,
                "strategy": strategy,
                "fault": fault,
                "configured": len(entries),
                "statuses": dict(statuses),
                "scored": len(scored),
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
        "notes": [
            "Raw terminal counts include every retained run.",
            "Cancelled, interrupted and simulator-error runs are excluded from means, not erased.",
            "Fault exposure denominator may be smaller than configured count.",
            "Small pilot; no significance or real-world prediction claim.",
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
    lines.extend(["", *["- " + note for note in report["notes"]], ""])
    return "\n".join(lines)
