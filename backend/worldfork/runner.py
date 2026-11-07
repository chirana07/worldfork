import asyncio
import copy
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .agents import ADAPTERS
from .engine import World, digest, score
from .gateway import BudgetExhausted, Gateway
from .scenarios import ScenarioId, load_scenario
from .team import TEAM_ADAPTERS, TeamAgent

logger = logging.getLogger(__name__)

SOURCE_HASHES = {
    name: digest(Path(__file__).with_name(name + ".py").read_text())
    for name in ["engine", "agents", "gateway", "runner", "team", "scenarios"]
}


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: ScenarioId = "harbor-v1"
    framework: Literal["python", "langgraph"] = "python"
    strategy: Literal["case_by_case", "coordinated", "team"] = "coordinated"
    passenger_mode: Literal["scripted", "llm"] = "scripted"
    model: Literal[
        "ollama/llama3.1:latest", "ollama/gemma2:2b", "ollama/qwen3.5:4b"
    ] = "ollama/qwen3.5:4b"
    fault: Literal[
        "none", "model_unavailable", "tool_timeout", "misleading_observation"
    ] = "none"
    seed: int = Field(default=1, ge=0, le=1000000)
    temperature: float = Field(default=0.2, ge=0, le=1)
    max_steps: int = Field(default=48, ge=1, le=64)
    max_tokens: int = Field(default=120000, ge=1000, le=200000)
    wall_seconds: int = Field(default=900, ge=30, le=1800)


class Runner:
    def __init__(self, store):
        self.store = store
        self.lock = asyncio.Lock()
        self.tasks = {}

    def create(self, config: RunConfig):
        rid = str(uuid.uuid4())
        fixture = load_scenario(config.scenario_id)
        self.store.create(
            rid,
            {
                **config.model_dump(),
                "scenario_hash": digest(fixture),
                "schema_version": 1,
                "source_hashes": SOURCE_HASHES,
            },
            World(fixture).snapshot(),
        )
        self.tasks[rid] = asyncio.create_task(self.run(rid, config))
        self.tasks[rid].add_done_callback(lambda task: self.finish_task(rid, task))
        return rid

    def finish_task(self, rid, task):
        self.tasks.pop(rid, None)
        error = None if task.cancelled() else task.exception()
        if error is not None:
            logger.error("Run %s terminated unexpectedly", rid, exc_info=error)
        if task.cancelled() or error is not None:
            run = self.store.get(rid)
            if run and run["status"] in {"queued", "running"}:
                self.store.update(rid, status="interrupted")

    async def run(self, rid, config):
        async with self.lock:
            world = World(load_scenario(config.scenario_id))
            gateway = Gateway(config.model, config.temperature, config.seed)
            gateway.token_limit = config.max_tokens
            adapters = TEAM_ADAPTERS if config.strategy == "team" else ADAPTERS
            agent = adapters[config.framework](
                gateway, rid, world.fixture["policy"], config.strategy
            )
            started = time.monotonic()
            fault_delivered = False
            terminal = "exhausted"
            passenger_memory = {pid: [] for pid in world.parties}
            self.store.update(rid, status="running")
            self.store.append(
                rid,
                {
                    "type": "started",
                    "tick": 0,
                    "framework": config.framework,
                    "strategy": config.strategy,
                },
                world.snapshot(),
            )
            try:
                async with asyncio.timeout(config.wall_seconds):
                    if hasattr(gateway, "describe_model"):
                        self.store.enrich_manifest(
                            rid, {"model_manifest": await gateway.describe_model()}
                        )
                    for _ in range(config.max_steps):
                        usage = sum(
                            (a.get("input_tokens") or 0) + (a.get("output_tokens") or 0)
                            for a in gateway.attempts
                        )
                        if usage >= config.max_tokens or len(gateway.attempts) >= 64:
                            break
                        world.advance()
                        observation = world.observation()
                        # Observation channel is the only source of the injected incorrect inventory.
                        if (
                            config.fault == "misleading_observation"
                            and not fault_delivered
                            and world.tick >= 8
                        ):
                            observation = copy.deepcopy(observation)
                            observation["options"][0]["available"] += 1
                            fault_delivered = True
                            self.store.append(
                                rid,
                                {
                                    "type": "fault",
                                    "tick": world.tick,
                                    "fault": config.fault,
                                    "visibility": "evaluator_only",
                                    "truth": world.option_view(),
                                    "shown": observation["options"],
                                },
                                world.snapshot(),
                            )
                        if config.fault == "model_unavailable" and not fault_delivered:
                            try:
                                await gateway.generate(
                                    [], run_id=rid, injected_failure=True
                                )
                            except (httpx.ConnectError, ConnectionError):
                                # The injected attempt is recorded by the gateway; one retry follows.
                                fault_delivered = True
                            fault_delivered = True
                            self.store.append(
                                rid,
                                {
                                    "type": "fault",
                                    "tick": world.tick,
                                    "fault": config.fault,
                                    "visibility": "transport",
                                    "message": "Injected unavailable attempt; bounded retry next.",
                                },
                                world.snapshot(),
                            )
                        before = len(gateway.attempts)
                        try:
                            action = await agent.next_action(observation)
                        except BudgetExhausted:
                            terminal = "exhausted"
                            break
                        except Exception as exc:  # noqa: BLE001 -- worker boundary records unexpected errors
                            self.store.append(
                                rid,
                                {
                                    "type": "agent_error",
                                    "tick": world.tick,
                                    "error": str(exc)[:500],
                                    "attempts": gateway.attempts[before:],
                                },
                                world.snapshot(),
                            )
                            terminal = "agent_error"
                            break
                        consent = None
                        passenger = None
                        if (
                            config.passenger_mode == "llm"
                            and action.tool == "propose_offer"
                        ):
                            pid = action.arguments.get("party_id")
                            oid = action.arguments.get("option_id")
                            voucher = action.arguments.get("voucher")
                            if (
                                isinstance(pid, str)
                                and pid in world.parties
                                and isinstance(oid, str)
                                and oid in world.options
                                and type(voucher) is int
                            ):
                                profile = world.parties[pid]
                                raw = await gateway.generate(
                                    [
                                        {
                                            "role": "system",
                                            "content": 'You are one fictional passenger. Decide for yourself using only your own profile, memory and this offer. Never invent facts. Return JSON {"accept":true or false,"message":"one short sentence"}.',
                                        },
                                        {
                                            "role": "user",
                                            "content": json.dumps(
                                                {
                                                    "profile": profile,
                                                    "booking": world.bookings.get(pid),
                                                    "memory": passenger_memory[pid][
                                                        -4:
                                                    ],
                                                    "option": world.options[oid],
                                                    "voucher": voucher,
                                                }
                                            ),
                                        },
                                    ],
                                    run_id=rid,
                                    role="passenger",
                                )
                                passenger = json.loads(raw)
                                if type(passenger.get("accept")) is not bool:
                                    raise ValueError(
                                        "Passenger returned invalid consent"
                                    )
                                consent = passenger["accept"]
                                passenger_memory[pid].append(
                                    {"offer": action.arguments, "decision": passenger}
                                )
                        if (
                            config.fault == "tool_timeout"
                            and not fault_delivered
                            and world.tick >= 8
                        ):
                            result = {
                                "ok": False,
                                "code": "timeout",
                                "message": "Tool timed out before execution; no state changed. You may retry.",
                            }
                            fault_delivered = True
                            self.store.append(
                                rid,
                                {
                                    "type": "fault",
                                    "tick": world.tick,
                                    "fault": config.fault,
                                    "visibility": "tool_result",
                                },
                                world.snapshot(),
                            )
                            world.last_result = result
                        else:
                            result = world.execute(action, consent)
                        agent.observe_tool_result(action, result)
                        self.store.append(
                            rid,
                            {
                                "type": "action",
                                "tick": world.tick,
                                "observation": observation,
                                "candidate_actions": getattr(agent, "last_menu", None),
                                "action": action.model_dump(),
                                "result": result,
                                "passenger": passenger,
                                **(
                                    {"coordination": agent.last_coordination}
                                    if isinstance(agent, TeamAgent)
                                    else {}
                                ),
                                "attempts": gateway.attempts[before:],
                            },
                            world.snapshot(),
                        )
                        if score(world)["satisfied_people"] == 7:
                            terminal = "completed"
                            break
                        if world.finished:
                            terminal = (
                                "completed"
                                if score(world)["satisfied_people"] == 7
                                else "stopped"
                            )
                            break
            except TimeoutError:
                terminal = "timed_out"
            except BudgetExhausted:
                terminal = "exhausted"
            except asyncio.CancelledError:
                terminal = "cancelled"
            except Exception as exc:  # noqa: BLE001 -- worker boundary records unexpected errors
                terminal = "simulator_error"
                self.store.append(
                    rid,
                    {"type": "error", "tick": world.tick, "error": str(exc)[:500]},
                    world.snapshot(),
                )
            finally:
                try:
                    await gateway.close()
                except asyncio.CancelledError:
                    terminal = "cancelled"
                except Exception:
                    logger.warning("Could not close gateway for %s", rid, exc_info=True)
                attempts = gateway.attempts
                result = {
                    **score(world),
                    "terminal": terminal,
                    "steps": world.tick,
                    "tool_calls": sum(
                        e["type"] == "action" for e in self.store.events(rid)
                    ),
                    "model_calls": len(attempts),
                    "input_tokens": sum(a["input_tokens"] for a in attempts)
                    if all(a["input_tokens"] is not None for a in attempts)
                    else None,
                    "output_tokens": sum(a["output_tokens"] for a in attempts)
                    if all(a["output_tokens"] is not None for a in attempts)
                    else None,
                    "usage_coverage": sum(
                        a["input_tokens"] is not None for a in attempts
                    )
                    / len(attempts)
                    if attempts
                    else None,
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                    "api_cost": 0,
                    "cost_basis": "local_ollama; hardware/electricity unmeasured",
                    "fault_configured": config.fault,
                    "fault_delivered": fault_delivered,
                    "attempts": attempts,
                }
                self.store.append(
                    rid,
                    {"type": "finished", "tick": world.tick, "result": result},
                    world.snapshot(),
                    terminal=terminal,
                )

    def cancel(self, rid):
        task = self.tasks.get(rid)
        if task and not task.done() and not task.cancelling():
            if self.store.get(rid)["status"] == "queued":
                self.store.update(rid, status="cancelled")
            task.cancel()
