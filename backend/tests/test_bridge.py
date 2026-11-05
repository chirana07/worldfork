import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from worldfork.bridge import RunnableAgentAdapter
from worldfork.engine import World


async def test_existing_runnable_gets_only_public_state_and_matching_receipt():
    observed = []

    async def existing_agent(state):
        observed.append(state["messages"])
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "ask_question",
                            "args": {"party_id": "P1", "topic": "deadline"},
                            "id": "call1",
                        }
                    ],
                )
            ]
        }

    world = World()
    bridge = RunnableAgentAdapter(RunnableLambda(existing_agent), "Public tool context")
    world.advance()
    action = await bridge.next_action(world.observation())
    assert action.tool == "ask_question"
    assert "terms" not in observed[0][-1].content
    with pytest.raises(RuntimeError):
        await bridge.next_action(world.observation())
    bridge.observe_tool_result(action, world.execute(action))
    assert isinstance(bridge.messages[-1], ToolMessage)
    assert bridge.messages[-1].tool_call_id == "call1"
    assert "13:00" in bridge.messages[-1].content


async def test_bridge_rejects_multiple_actions_before_world_mutates():
    async def invalid(state):
        return {"messages": [AIMessage(content="No pending tools")]}

    world = World()
    before = world.snapshot()
    bridge = RunnableAgentAdapter(RunnableLambda(invalid), "context")
    with pytest.raises(ValueError):
        await bridge.next_action(world.observation())
    assert world.snapshot() == before
