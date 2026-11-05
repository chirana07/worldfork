#!/usr/bin/env python3
"""Start project-local services; never stop unrelated processes."""

import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
(ROOT / "artifacts").mkdir(exist_ok=True)
children = []
logs = []


def healthy(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except OSError:
        return False


def start(command, name, url):
    if healthy(url):
        print(f"{name} is already responding at {url}", flush=True)
        return
    log = (ROOT / "artifacts" / f"{name}.log").open("a")
    logs.append(log)
    process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    children.append(process)
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError(f"{name} exited; inspect artifacts/{name}.log")
        if healthy(url):
            print(f"{name} ready: {url}", flush=True)
            return
        time.sleep(0.5)
    raise RuntimeError(f"{name} startup timed out; inspect its log")


try:
    if not healthy("http://127.0.0.1:11434/api/version"):
        raise RuntimeError(
            "Ollama is not responding. Start Ollama or run ollama serve, then retry."
        )
    config = ROOT / ".bifrost/config.json"
    if not config.exists():
        config.parent.mkdir(exist_ok=True)
        config.write_text((ROOT / "config/bifrost.example.json").read_text())
    start(
        [
            "npx",
            "--yes",
            "@maximhq/bifrost@1.6.3",
            "--transport-version",
            "v2.4.0",
            "-app-dir",
            str(config.parent),
            "-host",
            "127.0.0.1",
            "-port",
            "8080",
        ],
        "bifrost",
        "http://127.0.0.1:8080/health",
    )
    start(
        [
            "uv",
            "run",
            "uvicorn",
            "worldfork.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        "api",
        "http://127.0.0.1:8000/docs",
    )
    print(
        "Backend ready. API explorer: http://127.0.0.1:8000/docs\nCtrl+C stops only processes launched by this script.",
        flush=True,
    )
    while children:
        if any(p.poll() is not None for p in children):
            raise RuntimeError("A service exited; inspect artifacts logs")
        time.sleep(1)
except KeyboardInterrupt:
    pass
except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
    print(str(exc), flush=True)
    raise SystemExit(1)
finally:
    for process in reversed(children):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
    for log in logs:
        log.close()
