"""Serve verified recorded runs on loopback; no model runtime is required."""

import argparse
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlencode

import uvicorn
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from import_evidence import import_evidence

ROOT = Path(__file__).resolve().parents[1]


def serve(manifest, port):
    dist = ROOT / "frontend/dist"
    if not (dist / "index.html").exists():
        raise SystemExit(
            "Build the frontend first: npm ci --prefix frontend, then npm run build --prefix frontend"
        )
    with tempfile.TemporaryDirectory(prefix="worldfork-replay-") as directory:
        database = Path(directory) / "replay.sqlite"
        import_evidence(manifest, database)
        os.environ["WORLDFORK_DB"] = str(database)
        from worldfork.api import app

        entries = json.loads(manifest.read_text())["runs"]
        # First clean LangGraph pair, fixed by the matrix order, not chosen by outcome.
        pair = [
            e["id"]
            for e in entries
            if e["config"]["framework"] == "langgraph"
            and e["config"]["seed"] == 11
            and e["config"]["fault"] == "none"
        ]
        query = urlencode({"a": pair[0], "b": pair[1]})

        @app.middleware("http")
        async def replay_only(request: Request, call_next):
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                return JSONResponse(
                    {"detail": "This server serves recorded evidence only"},
                    status_code=405,
                )
            if request.url.path == "/api/models":
                return JSONResponse([])
            if request.url.path == "/api/health":
                return JSONResponse(
                    {
                        "api": "ok",
                        "gateway": "offline",
                        "ollama": "offline",
                        "mode": "replay",
                        "active_runs": 0,
                    }
                )
            if request.url.path == "/" and not request.url.query:
                return RedirectResponse("/?" + query)
            return await call_next(request)

        app.mount("/", StaticFiles(directory=dist, html=True), name="replay-interface")
        print(f"Verified recordings ready at http://127.0.0.1:{port}", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=ROOT / "evidence/pilot-manifest.json"
    )
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    serve(args.manifest, args.port)
