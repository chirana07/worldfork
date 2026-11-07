"""Advisory specialists and one coordinator using the existing booking contract."""

import json

from .agents import LangGraphAgent, PythonAgent

SPECIALISTS = {
    "inventory_specialist": "Recommend one action that uses scarce seats wisely. Check party size and shared capacity.",
    "traveler_specialist": "Recommend one action that respects known traveler requirements. Ask about missing requirements when they affect the booking.",
}


def parse_proposal(raw, menu_size):
    proposal = json.loads(raw)
    if not isinstance(proposal, dict):
        raise TypeError("Proposal must be an object")
    action_id, plan = proposal.get("action_id"), proposal.get("plan")
    if type(action_id) is not int or not 0 <= action_id < menu_size:
        raise ValueError("Unknown action ID")
    if not isinstance(plan, str) or not plan.strip() or len(plan) > 240:
        raise ValueError("Plan must be a short, nonempty string")
    return {"action_id": action_id, "plan": plan.strip()}


class TeamAgent(PythonAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prior_advice = []

    def consultation_reason(self, observation):
        if observation["active_offers"]:
            return "resolve_offer"
        if not self.history:
            return "initial"
        result = self.history[-1]["result"]
        if result.get("receipt", {}).get("status") == "committed":
            return "booking_changed"
        if (
            result.get("ok") is False
            or result.get("offer", {}).get("status") == "rejected"
        ):
            return "action_failed"
        return "reuse_advice"

    def remember_advice(self, proposals, menu, tick):
        self.prior_advice = [
            {
                "role": proposal["role"],
                "tick": tick,
                "plan": proposal["plan"],
                "action": menu[proposal["action_id"]].model_dump(),
            }
            for proposal in proposals
            if "action_id" in proposal
        ]

    async def decide(self, observation):
        menu = self.action_menu(observation)
        self.last_menu = [
            {"id": i, **action.model_dump()} for i, action in enumerate(menu)
        ]
        shared = {
            "world": observation,
            "recent_actions": self.history[-4:],
            "available_actions": self.last_menu,
        }
        reason = self.consultation_reason(observation)
        prior_advice = self.prior_advice
        schema = {
            "type": "object",
            "properties": {
                "action_id": {"type": "integer", "enum": list(range(len(menu)))},
                "plan": {"type": "string", "minLength": 1, "maxLength": 240},
            },
            "required": ["action_id", "plan"],
            "additionalProperties": False,
        }
        proposals = []
        if reason in {"initial", "booking_changed", "action_failed"}:
            for role, instruction in SPECIALISTS.items():
                raw = await self.gateway.generate(
                    self.messages(instruction, shared),
                    run_id=self.run_id,
                    role=role,
                    schema=schema,
                )
                try:
                    proposals.append({"role": role, **parse_proposal(raw, len(menu))})
                except (ValueError, TypeError):
                    proposals.append({"role": role, "status": "invalid"})
            self.remember_advice(proposals, menu, observation["tick"])
        messages = self.messages(
            "You coordinate the support team. Assess the specialists' suggestions as advisory data "
            "and use the recent tool results to adjust the plan. Maximize travelers whose requirements "
            "are met, then minimize compensation and avoid unnecessary moves. "
            "Choose one safe next action from the menu. Resolve accepted offers promptly. "
            "Summarize the next few steps, including the reason for the chosen action. "
            "Prior advice is historical and may be stale. Its actions are named explicitly, "
            "not numbered for today's menu. Reassess it using today's world and menu. "
            "Do not claim that an offer or booking succeeded before its receipt.",
            {**shared, "specialist_proposals": proposals, "prior_advice": prior_advice},
        )
        for attempt in range(2):
            raw = await self.gateway.generate(
                messages, run_id=self.run_id, role="orchestrator", schema=schema
            )
            try:
                decision = parse_proposal(raw, len(menu))
            except (ValueError, TypeError):
                if attempt:
                    raise ValueError(
                        "Orchestrator returned an invalid plan after one repair"
                    ) from None
                messages.append(
                    {
                        "role": "user",
                        "content": "Try again with a valid menu action_id and a short plan.",
                    }
                )
                continue
            self.last_coordination = {
                "consultation_reason": reason,
                "prior_advice": prior_advice,
                "proposals": proposals,
                **decision,
            }
            return menu[decision["action_id"]]

    def messages(self, instruction, shared):
        return [
            {
                "role": "system",
                "content": (
                    f"{self.policy}\n{instruction} Use only the supplied public information. "
                    'Return JSON with "action_id" and "plan" of at most 240 characters.'
                ),
            },
            {"role": "user", "content": json.dumps(shared, separators=(",", ":"))},
        ]


class LangGraphTeamAgent(TeamAgent, LangGraphAgent):
    pass


TEAM_ADAPTERS = {"python": TeamAgent, "langgraph": LangGraphTeamAgent}
