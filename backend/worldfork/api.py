import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .engine import World, scenario
from .runner import RunConfig, Runner
from .store import Store

store = Store(os.getenv("WORLDFORK_DB", "artifacts/worldfork.sqlite"))
runner = Runner(store)


@asynccontextmanager
async def lifespan(app):
    store.recover_interrupted()
    yield
    tasks = list(runner.tasks.values())
    for t in tasks:
        if not t.cancelling():
            t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


router = APIRouter()
FRONTEND_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]


async def require_local_origin(request: Request):
    origin = request.headers.get("origin")
    same_origin = f"{request.url.scheme}://{request.url.netloc}"
    if origin is not None and origin not in [*FRONTEND_ORIGINS, same_origin]:
        raise HTTPException(403, "Origin cannot modify the local lab")


def require_queue_space(count=1):
    if len(runner.tasks) + count > 30:
        raise HTTPException(429, "Local queue full")


@router.get("/api/health")
async def health():
    gateway = os.getenv("WORLDFORK_GATEWAY", "http://127.0.0.1:8080/v1")
    gateway_health = gateway.rstrip("/").removesuffix("/v1") + "/health"
    result = {
        "api": "ok",
        "gateway": "unavailable",
        "ollama": "unavailable",
        "active_runs": len(runner.tasks),
    }
    async with httpx.AsyncClient(timeout=2) as client:
        for key, url in [
            ("gateway", gateway_health),
            ("ollama", "http://127.0.0.1:11434/api/version"),
        ]:
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    result[key] = "ok"
            except (httpx.HTTPError, httpx.InvalidURL):
                pass
    return result


@router.get("/api/scenarios")
async def scenarios():
    return [
        {
            "id": s["id"],
            "label": s["label"],
            "policy": s["policy"],
            "initial": World(s).snapshot(),
            "people": 7,
            "parties": 6,
            "kind": "development" if not scarce else "control variant; not held-out",
        }
        for scarce in [False, True]
        for s in [scenario(scarce)]
    ]


@router.get("/api/models")
async def models():
    """Only advertise installed local models supported by the run contract."""
    allowed = RunConfig.model_fields["model"].annotation.__args__
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get("http://127.0.0.1:11434/api/tags")
            response.raise_for_status()
            installed = {item["name"] for item in response.json()["models"]}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(503, "Cannot inspect local Ollama models") from None
    return [name for name in allowed if name.removeprefix("ollama/") in installed]


@router.post("/api/runs", status_code=202, dependencies=[Depends(require_local_origin)])
async def create_run(config: RunConfig):
    require_queue_space()
    rid = runner.create(config)
    return store.get(rid)


@router.get("/api/runs")
async def runs(summary: bool = False):
    return store.list(summary=summary)


def require(rid):
    run = store.get(rid)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/api/runs/{rid}")
async def run(rid: str):
    return require(rid)


@router.get("/api/runs/{rid}/events")
async def events(
    rid: str, after_seq: int = Query(default=0, ge=0, le=9223372036854775807)
):
    require(rid)
    return store.events(rid, after_seq)


@router.post("/api/runs/{rid}/cancel", dependencies=[Depends(require_local_origin)])
async def cancel(rid: str):
    run = require(rid)
    if run["status"] in ["running", "queued"]:
        runner.cancel(rid)
    return require(rid)


@router.post(
    "/api/runs/{rid}/fork",
    status_code=202,
    dependencies=[Depends(require_local_origin)],
)
async def fork(rid: str, config: RunConfig):
    parent = require(rid)
    if config.scenario_id != parent["config"]["scenario_id"]:
        raise HTTPException(400, "A paired fork must retain the same initial scenario")
    require_queue_space()
    new_id = runner.create(config)
    return {"parent_id": rid, "run": store.get(new_id), "fork_kind": "initial_state"}


class ComparisonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: RunConfig
    b: RunConfig
    repeats: int = Field(default=1, ge=1, le=3)


@router.post(
    "/api/comparisons", status_code=202, dependencies=[Depends(require_local_origin)]
)
async def compare(config: ComparisonConfig):
    equal = [
        "scenario_id",
        "passenger_mode",
        "model",
        "fault",
        "max_steps",
        "max_tokens",
        "wall_seconds",
        "temperature",
        "seed",
    ]
    if any(getattr(config.a, k) != getattr(config.b, k) for k in equal):
        raise HTTPException(
            400,
            "Paired runs must share scenario, population mode, model, faults, seed, decoding and budgets",
        )
    require_queue_space(2 * config.repeats)
    if config.a.seed + config.repeats - 1 > 1000000:
        raise HTTPException(422, "Repeated comparison seeds exceed the supported range")
    ids = []
    for i in range(config.repeats):
        # Alternate execution order to reduce systematic warm-cache order advantage.
        pair = {}
        for side in ["a", "b"] if i % 2 == 0 else ["b", "a"]:
            c = getattr(config, side).model_copy(update={"seed": config.a.seed + i})
            pair[side] = runner.create(c)
        ids.append(pair)
    cid = str(uuid.uuid4())
    return store.comparison(cid, config.model_dump(), ids)


@router.get("/api/comparisons/{cid}")
async def comparison(cid: str):
    c = store.comparison(cid)
    if not c:
        raise HTTPException(404, "Comparison not found")
    return {
        **c,
        "runs": [
            {side: require(rid) for side, rid in pair.items()} for pair in c["run_ids"]
        ],
    }


@router.get("/api/runs/{rid}/export")
async def export(rid: str):
    import json

    run = require(rid)
    payload = {
        "schema_version": 1,
        "run": run,
        "scenario": scenario(run["config"]["scenario_id"] == "harbor-scarce-v1"),
        "events": store.events(rid),
        "notice": "Fictional data; includes evaluator-only private goals. Do not feed into a live agent.",
    }
    return Response(
        json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="worldfork-{rid}.json"'},
    )


def create_app(*, replay=False):
    app = FastAPI(
        title="WorldFork",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url=None if replay else "/openapi.json",
    )
    app.include_router(router)
    if not replay:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=FRONTEND_ORIGINS,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"]
        )
    return app


app = create_app()
