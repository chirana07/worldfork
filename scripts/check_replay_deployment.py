"""Verify a deployed replay service and optionally measure a mixed HTTP workload."""

import argparse
import gzip
import json
import math
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import median
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, *, encoding="identity", method="GET"):
    req = Request(base + path, headers={"Accept-Encoding": encoding}, method=method)
    started = perf_counter()
    try:
        response = urlopen(req, timeout=15)
    except HTTPError as exc:
        response = exc
    with response:
        body = response.read()
        return (
            response.status,
            response.headers,
            body,
            (perf_counter() - started) * 1000,
            response.geturl(),
        )


def read_json(response):
    status, headers, body, _, _ = response
    if status != 200:
        raise ValueError(f"Expected HTTP 200, received {status}")
    if headers.get("Content-Encoding") == "gzip":
        body = gzip.decompress(body)
    return json.loads(body)


def check(base, *, team_demo=False):
    health = read_json(request(base, "/api/health"))
    assert health == {
        "api": "ok",
        "gateway": "offline",
        "ollama": "offline",
        "mode": "replay",
        "active_runs": 0,
    }
    assert read_json(request(base, "/api/models")) == []
    archive = read_json(request(base, "/api/runs"))
    summaries = read_json(request(base, "/api/runs?summary=true"))
    if team_demo:
        payloads = [
            json.loads((ROOT / "evidence/team-demo" / name).read_text())
            for name in (
                "solo.json",
                "team.json",
                "timeout-solo.json",
                "timeout-team.json",
            )
        ]
        traces = {p["run"]["id"]: p for p in payloads}
    else:
        manifest = json.loads((ROOT / "evidence/pilot-manifest.json").read_text())
        traces = {r["id"]: ROOT / r["trace"] for r in manifest["runs"]}
    assert {r["id"] for r in archive} == set(traces)
    assert [r["id"] for r in summaries] == [r["id"] for r in archive]
    for summary, full in zip(summaries, archive, strict=True):
        assert "snapshot" not in summary
        assert summary["result"] == {
            field: full["result"][field]
            for field in ("satisfied_people", "total_people")
        }
    page = request(base, "/")
    assert page[0] == 200 and b'id="root"' in page[2]
    query = parse_qs(urlsplit(page[4]).query)
    assert set(query) == {"a", "b"}
    pair = (query["a"][0], query["b"][0])
    if team_demo:
        assert pair == tuple(traces)[:2]
    for run_id in traces if team_demo else pair:
        trace = traces[run_id]
        original = json.loads(trace.read_text()) if isinstance(trace, Path) else trace
        assert read_json(request(base, f"/api/runs/{run_id}")) == original["run"]
        assert (
            read_json(request(base, f"/api/runs/{run_id}/events")) == original["events"]
        )
        export = f"/api/runs/{run_id}/export"
        assert read_json(request(base, export)) == original
        assert read_json(request(base, export, encoding="gzip")) == original
    rid = query["a"][0]
    for path in (
        "/api/runs",
        "/api/comparisons",
        f"/api/runs/{rid}/cancel",
        f"/api/runs/{rid}/fork",
    ):
        assert request(base, path, method="POST")[0] == 405
    assert request(base, "/api/runs/unknown")[0] == 404
    return rid


def benchmark(base, rid, count, concurrency, *, archive_summary=False):
    routes = {
        "archive": "/api/runs?summary=true" if archive_summary else "/api/runs",
        "run": f"/api/runs/{rid}",
        "events": f"/api/runs/{rid}/events",
        "export": f"/api/runs/{rid}/export",
    }

    def sample(name):
        status, headers, body, elapsed, _ = request(base, routes[name], encoding="gzip")
        return (
            name,
            status,
            headers.get("Content-Encoding", "identity"),
            len(body),
            elapsed,
        )

    for name in routes:
        sample(name)
    workload = list(routes) * count
    started = perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(sample, workload))
    wall_seconds = perf_counter() - started
    statuses = Counter(r[1] for r in results)
    report = {
        "concurrency": concurrency,
        "requests": len(results),
        "status_counts": dict(statuses),
        "requests_per_second": round(len(results) / wall_seconds, 1),
        "routes": {},
    }
    for name in routes:
        rows = [r for r in results if r[0] == name]
        elapsed = sorted(r[4] for r in rows)
        report["routes"][name] = {
            "p50_ms": round(median(elapsed), 2),
            "p95_ms": round(elapsed[math.ceil(len(elapsed) * 0.95) - 1], 2),
            "median_wire_body_bytes": int(median(r[3] for r in rows)),
            "encodings": dict(Counter(r[2] for r in rows)),
        }
    print(json.dumps(report, indent=2))
    if statuses != {200: len(results)}:
        raise SystemExit("Unexpected workload responses")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--samples-per-route", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--archive-summary", action="store_true")
    parser.add_argument("--team-demo", action="store_true")
    args = parser.parse_args()
    if args.samples_per_route < 0 or args.concurrency < 1:
        parser.error(
            "Sample count must be nonnegative and concurrency must be positive"
        )
    base_url = args.url.rstrip("/")
    initial_run = check(base_url, team_demo=args.team_demo)
    print(
        "Replay health, run identities, default comparison, exports and read-only boundary passed"
    )
    if args.samples_per_route:
        benchmark(
            base_url,
            initial_run,
            args.samples_per_route,
            args.concurrency,
            archive_summary=args.archive_summary,
        )
