"""Adapt an existing message-based tool agent without changing its internals.

The supplied runnable must stop before executing tools. WorldFork owns tool
execution, ticks, constraints, and scoring. This bridge owns only message I/O.
"""

import copy
import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from .engine import Action


class RunnableAgentAdapter:
    def __init__(self, runnable, context):
        self.runnable = runnable
        self.messages = [SystemMessage(content=context)]
        self.pending = None

    async def next_action(self, observation):
        if self.pending is not None:
            raise RuntimeError("Supply the previous tool result before invoking again")
        self.messages.append(
            HumanMessage(content=json.dumps(copy.deepcopy(observation)))
        )
        output = await self.runnable.ainvoke({"messages": list(self.messages)})
        message = output["messages"][-1]
        if not isinstance(message, AIMessage) or len(message.tool_calls) != 1:
            raise ValueError(
                "The wrapped agent must return exactly one pending tool call"
            )
        call = message.tool_calls[0]
        # Both a single dispatch tool and ordinary named tools are supported.
        action = Action.model_validate(
            call["args"]
            if call["name"] == "world_tool"
            else {"tool": call["name"], "arguments": call["args"]}
        )
        self.pending = (action, call["id"])
        self.messages.append(message)
        return action

    def observe_tool_result(self, action, result):
        if self.pending is None or action != self.pending[0]:
            raise ValueError("Tool result does not match the pending action")
        self.messages.append(
            ToolMessage(
                content=json.dumps(copy.deepcopy(result)), tool_call_id=self.pending[1]
            )
        )
        self.pending = None
