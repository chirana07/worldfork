"""Framework adapters. Strategies and model budgets are shared across integrations."""

import json
from typing import Protocol, TypedDict

from langgraph.graph import END, START, StateGraph

from .engine import Action

STRATEGIES = {
    "case_by_case": "Handle cases in queue order. Discover the current party requirements, offer a feasible option and commit consented offers. After two failed actions defer the blocked case; revisit when availability changes. Already-booked people remain contactable for voluntary moves. Do not repeat failed requests indefinitely.",
    "coordinated": "Consider shared capacity across all parties. Discover inflexible deadlines and transport requirements before consuming scarce early seats. Ask flexible parties about compensation; negotiate voluntary moves when useful. Use the same limited tools and budget. Do not assume private requirements. Commit accepted offers promptly.",
}


class Agent(Protocol):
    async def next_action(self, observation: dict) -> Action: ...
    def observe_tool_result(self, action: Action, result: dict) -> None: ...


class PythonAgent:
    def __init__(self, gateway, run_id, policy, strategy):
        self.gateway, self.run_id, self.policy, self.strategy = (
            gateway,
            run_id,
            policy,
            strategy,
        )
        self.history = []
        self.proposed = set()
        self.failures = {}

    def action_menu(self, observation):
        # Every filter uses public observations or this agent's own actions, never fixture truth.
        menu = []
        for offer in observation["active_offers"]:
            menu.append(
                Action(tool="commit_offer", arguments={"offer_id": offer["id"]})
            )
            menu.append(
                Action(tool="withdraw_offer", arguments={"offer_id": offer["id"]})
            )
        if menu:
            return menu  # Resolve consented transactions before opening another; shared harness policy.
        active = {o["party_id"] for o in observation["active_offers"]}
        for case in observation["cases"]:
            pid = case["id"]
            for topic in ["deadline", "modes", "compensation"]:
                if topic not in case["known"]:
                    menu.append(
                        Action(
                            tool="ask_question",
                            arguments={"party_id": pid, "topic": topic},
                        )
                    )
            if pid in active:
                continue
            for option in observation["options"]:
                if option["available"] < case["people"]:
                    continue
                if case["booking"] and case["booking"]["option_id"] == option["id"]:
                    continue
                for voucher in [0, 40]:
                    if voucher > observation["credits"]["available"]:
                        continue
                    if (pid, option["id"], voucher) in self.proposed:
                        continue
                    menu.append(
                        Action(
                            tool="propose_offer",
                            arguments={
                                "party_id": pid,
                                "option_id": option["id"],
                                "voucher": voucher,
                            },
                        )
                    )
        menu.append(
            Action(
                tool="finish",
                arguments={"reason": "No further useful actions selected"},
            )
        )
        return menu

    async def decide(self, observation):
        menu = self.action_menu(observation)
        if self.strategy == "case_by_case":
            pending = [
                c["id"]
                for c in observation["cases"]
                if not c["booking"] and self.failures.get(c["id"], 0) < 2
            ]
            observation["queue_guidance"] = {
                "focus": pending[0] if pending else None,
                "deferred": [p for p, n in self.failures.items() if n >= 2],
                "rule": "Public bookings and bounded failures only; already-booked parties remain contactable.",
            }
        system = (
            self.policy
            + "\nSTRATEGY: "
            + STRATEGIES[self.strategy]
            + '\nSelect one next action from the numbered menu. Return only JSON {"action_id":integer}. Discover unknown constraints, then book feasible alternatives. Avoid unnecessary questions after you have enough information. Commit accepted offers before they expire. The menu removes already answered questions and exact previously proposed offers, but does not tell you which choices succeed. Finish only if useful work is exhausted.'
        )
        numbered = [{"id": i, **a.model_dump()} for i, a in enumerate(menu)]
        self.last_menu = numbered
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "world": observation,
                        "recent_actions": self.history[-4:],
                        "available_actions": numbered,
                    },
                    separators=(",", ":"),
                ),
            },
        ]
        schema = {
            "type": "object",
            "properties": {
                "action_id": {"type": "integer", "enum": list(range(len(menu)))}
            },
            "required": ["action_id"],
            "additionalProperties": False,
        }
        for repair in range(2):
            raw = await self.gateway.generate(
                messages, run_id=self.run_id, schema=schema
            )
            try:
                selected = json.loads(raw)["action_id"]
                if type(selected) is not int or not 0 <= selected < len(menu):
                    raise ValueError("Unknown action ID")
                return menu[selected]
            except Exception as exc:
                if repair:
                    raise ValueError(
                        "Model returned invalid action selection after one repair"
                    ) from exc
                messages.extend(
                    [
                        {"role": "assistant", "content": raw},
                        {
                            "role": "user",
                            "content": 'Return only {"action_id": a valid integer from the current menu}.',
                        },
                    ]
                )

    async def next_action(self, observation):
        return await self.decide(observation)

    def observe_tool_result(self, action, result):
        pid = action.arguments.get("party_id")
        if pid and (
            result.get("ok") is False
            or result.get("offer", {}).get("status") == "rejected"
        ):
            self.failures[pid] = self.failures.get(pid, 0) + 1
        if result.get("receipt", {}).get("status") == "committed":
            self.failures.clear()
        if (
            action.tool == "propose_offer"
            and result.get("offer", {}).get("status") == "rejected"
        ):
            self.proposed.add(
                (
                    action.arguments["party_id"],
                    action.arguments["option_id"],
                    action.arguments["voucher"],
                )
            )
        self.history.append({"action": action.model_dump(), "result": result})
        self.history = self.history[-6:]


class GraphState(TypedDict):
    observation: dict
    action: Action


class LangGraphAgent(PythonAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        async def decision_node(state):
            return {"action": await self.decide(state["observation"])}

        graph = StateGraph(GraphState)
        graph.add_node("model_decision", decision_node)
        graph.add_edge(START, "model_decision")
        graph.add_edge("model_decision", END)
        self.graph = graph.compile()

    async def next_action(self, observation):
        result = await self.graph.ainvoke({"observation": observation})
        return result["action"]


ADAPTERS = {"python": PythonAgent, "langgraph": LangGraphAgent}
