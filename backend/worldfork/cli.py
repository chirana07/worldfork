"""Run repeatable matrices through the same API worker as the interface."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx


async def benchmark(full=False, model="ollama/llama3.1:latest"):
    configs = []
    for framework in ["python", "langgraph"]:
        for strategy in ["case_by_case", "coordinated"]:
            for seed in [11, 29, 47]:
                configs.append(
                    {"framework": framework, "strategy": strategy, "seed": seed}
                )
    for fault in ["model_unavailable", "tool_timeout", "misleading_observation"]:
        for strategy in ["case_by_case", "coordinated"] if full else ["coordinated"]:
            for seed in [11, 29, 47]:
                configs.append(
                    {
                        "framework": "python",
                        "strategy": strategy,
                        "seed": seed,
                        "fault": fault,
                    }
                )
    for config in configs:
        config["model"] = model
    # Interleave designs across seeds instead of running all of one design first.
    clean = configs[:12]
    clean.sort(
        key=lambda c: ([11, 29, 47].index(c["seed"]), c["framework"], c["strategy"])
    )
    configs = clean + configs[12:]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = Path(f"artifacts/benchmark-{stamp}.json")
    manifest = {
        "schema_version": 1,
        "kind": "pilot",
        "matrix": "full30" if full else "minimum21",
        "created_at": stamp,
        "runs": [],
    }
    path.parent.mkdir(exist_ok=True)
    async with httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", timeout=10
    ) as client:
        try:
            for config in configs:
                response = await client.post("/api/runs", json=config)
                response.raise_for_status()
                run = response.json()
                manifest["runs"].append({"id": run["id"], "config": config})
                path.write_text(json.dumps(manifest, indent=2))
            pending = {r["id"] for r in manifest["runs"]}
            print(f"Queued {len(pending)} episodes. Manifest: {path}", flush=True)
            while pending:
                for rid in list(pending):
                    response = await client.get("/api/runs/" + rid)
                    response.raise_for_status()
                    run = response.json()
                    if run["status"] not in ["running", "queued"]:
                        pending.remove(rid)
                        result = run.get("result")
                        print(
                            rid[:8],
                            run["status"],
                            f"{result['satisfied_people']}/7" if result else "no score",
                            flush=True,
                        )
                        entry = next(r for r in manifest["runs"] if r["id"] == rid)
                        entry.update(status=run["status"], result=result)
                        path.write_text(json.dumps(manifest, indent=2))
                if pending:
                    await asyncio.sleep(3)
        except (KeyboardInterrupt, asyncio.CancelledError):
            for entry in manifest["runs"]:
                await client.post("/api/runs/" + entry["id"] + "/cancel")
            print("Cancelled this matrix; retained completed results.", flush=True)
            raise
    from .report import markdown, summarize

    path.with_suffix(".md").write_text(markdown(summarize(manifest)))
    return path


async def smoke():
    from .engine import Action, action_schema
    from .gateway import Gateway

    g = Gateway()
    try:
        raw = await g.generate(
            [
                {"role": "system", "content": "Return only JSON."},
                {
                    "role": "user",
                    "content": 'Return {"tool":"list_options","arguments":{}}',
                },
            ],
            schema=action_schema(),
        )
        action = Action.model_validate_json(raw)
        output = {"action": action.model_dump(), "attempts": g.attempts}
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/gateway-smoke.json").write_text(json.dumps(output, indent=2))
        print(json.dumps(output, indent=2))
    finally:
        await g.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "benchmark", "report"])
    parser.add_argument(
        "manifest", nargs="?", help="Existing benchmark JSON for report"
    )
    parser.add_argument("--model", default="ollama/llama3.1:latest")
    parser.add_argument(
        "--full",
        action="store_true",
        help="30-cell rather than21-episode minimum pilot",
    )
    args = parser.parse_args()
    try:
        if args.command == "report":
            from .report import markdown, summarize

            if not args.manifest:
                parser.error("report requires a manifest path")
            path = Path(args.manifest)
            result = markdown(summarize(json.loads(path.read_text())))
            path.with_suffix(".md").write_text(result)
            print(result)
        else:
            asyncio.run(
                smoke() if args.command == "smoke" else benchmark(args.full, args.model)
            )
    except httpx.HTTPError as exc:
        raise SystemExit(
            f"API/gateway request failed: {exc}. Start scripts/backend.py and inspect artifacts logs."
        )
