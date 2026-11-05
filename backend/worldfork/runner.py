import asyncio
import copy
import json
import time
import uuid
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .agents import ADAPTERS
from .engine import World, digest, scenario, score
from .gateway import BudgetExhausted, Gateway

SOURCE_HASHES = {
    name: digest(Path(__file__).with_name(name + ".py").read_text())
    for name in ["engine", "agents", "gateway", "runner"]
}


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: Literal["harbor-v1", "harbor-scarce-v1"] = "harbor-v1"
    framework: Literal["python", "langgraph"] = "python"
    strategy: Literal["case_by_case", "coordinated"] = "coordinated"
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
        self.cancelled = set()

    def create(self, config: RunConfig):
        rid = str(uuid.uuid4())
        fixture = scenario(config.scenario_id == "harbor-scarce-v1")
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
        self.tasks[rid].add_done_callback(lambda _: self.tasks.pop(rid, None))
        return rid

    async def run(self, rid, config):
        async with self.lock:
            if rid in self.cancelled:
                self.store.update(rid, status="cancelled")
                return
            world = World(scenario(config.scenario_id == "harbor-scarce-v1"))
            gateway = Gateway(config.model, config.temperature, config.seed)
            gateway.token_limit = config.max_tokens
            agent = ADAPTERS[config.framework](
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
                        if rid in self.cancelled:
                            terminal = "cancelled"
                            break
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
                await gateway.close()
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
                )
                self.store.update(rid, status=terminal, result=result)
                self.cancelled.discard(rid)

    def cancel(self, rid):
        self.cancelled.add(rid)
        task = self.tasks.get(rid)
        if task:
            task.cancel()
        self.store.update(rid, status="cancelled")
