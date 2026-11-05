"""A bounded, real prebuilt ReAct-agent integration smoke, not a benchmark cell.

Run only while the API inference queue is idle:
    uv run python examples/generic_react.py
"""

import asyncio
import json
import uuid
import warnings
from pathlib import Path

import httpx
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from worldfork.bridge import RunnableAgentAdapter
from worldfork.engine import Action, World, action_schema, score
from worldfork.gateway import Gateway


def execution_guard(**kwargs):
    raise RuntimeError("Tools execute in WorldFork, never inside the wrapped graph")


def existing_generic_agent(gateway):
    """Configure the installed library's generic agent; do not edit its loop."""
    dispatch = StructuredTool.from_function(
        execution_guard,
        name="world_tool",
        description="Select an environment tool and its arguments.",
        args_schema=Action,
    )

    async def measured_model(messages):
        # Model transport shim: the existing agent still owns its own graph.
        # Use textual transcripts because this local gateway uses JSON actions.
        transcript = [
            {
                "type": m.type,
                "content": m.content,
                "tool_calls": getattr(m, "tool_calls", None),
            }
            for m in messages
        ]
        raw = await gateway.generate(
            [
                {
                    "role": "system",
                    "content": "Select one useful next environment action. Return only JSON with tool and arguments. Tool schema: "
                    + json.dumps(action_schema()),
                },
                {"role": "user", "content": json.dumps(transcript)},
            ],
            run_id="generic-react-integration",
            schema=action_schema(),
        )
        action = Action.model_validate_json(raw)
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "world_tool",
                    "args": action.model_dump(),
                    "id": str(uuid.uuid4()),
                }
            ],
        )

    def model(state, runtime):
        return RunnableLambda(measured_model)

    # The installed LangGraph version retains this factory but deprecates it
    # in favor of langchain.create_agent. This is a compatibility example.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return create_react_agent(model, tools=[dispatch], interrupt_before=["tools"])


async def main():
    async with httpx.AsyncClient(timeout=5) as client:
        health = await client.get("http://127.0.0.1:8000/api/health")
        health.raise_for_status()
        if health.json()["active_runs"]:
            raise SystemExit(
                "Wait for the API queue to become idle before this integration smoke"
            )
    gateway = Gateway("ollama/qwen3.5:4b")
    world = World()
    adapter = RunnableAgentAdapter(
        existing_generic_agent(gateway),
        world.fixture["policy"]
        + " Maximize people with consented confirmed bookings. Discover private constraints through questions. The WorldFork harness executes your pending tool call and returns its receipt.",
    )
    events = []
    try:
        async with asyncio.timeout(180):
            for _ in range(4):
                world.advance()
                observation = world.observation()
                action = await adapter.next_action(observation)
                result = world.execute(action)
                adapter.observe_tool_result(action, result)
                events.append(
                    {
                        "observation": observation,
                        "action": action.model_dump(),
                        "result": result,
                        "snapshot": world.snapshot(),
                    }
                )
                print(action.model_dump(), result, flush=True)
                if world.finished:
                    break
    finally:
        await gateway.close()
        path = Path("artifacts/generic-react-integration.json")
        path.parent.mkdir(exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "kind": "integration smoke; not a benchmark cell",
                    "model_manifest": await _manifest(),
                    "events": events,
                    "attempts": gateway.attempts,
                    "score": score(world),
                    "limitations": "Separate bounded driver; run while queue is idle. Graph factory is deprecated in installed LangGraph. No universal compatibility claim.",
                },
                indent=2,
            )
        )
        print(path, flush=True)


async def _manifest():
    gateway = Gateway("ollama/qwen3.5:4b")
    try:
        return await gateway.describe_model()
    finally:
        await gateway.close()


if __name__ == "__main__":
    asyncio.run(main())
