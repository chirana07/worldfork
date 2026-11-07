import json

import pytest
from worldfork.engine import Action, World, digest, oracle, scenario
from worldfork.scenarios import load_scenario
from worldfork.team import TEAM_ADAPTERS


def test_transfer_fixture_changes_constraints_without_changing_earlier_scenarios():
    assert load_scenario("harbor-v1") == scenario()
    assert load_scenario("harbor-scarce-v1") == scenario(True)
    fixture = load_scenario("harbor-transfer-v1")
    assert digest(fixture) != digest(scenario())
    assert oracle(fixture)["max_satisfied_people"] == 7
    world = World(fixture)
    assert world.budget_available() == 40
    assert all(not case["known"] for case in world.observation()["cases"])
    assert world.available("E") == 1
    assert fixture["parties"]["P1"]["modes"] == ["rail"]


@pytest.mark.parametrize("framework", ["python", "langgraph"])
async def test_team_reuses_named_advice_and_refreshes_after_booking_and_failure(
    framework,
):
    planned = [
        Action(tool="ask_question", arguments={"party_id": "P1", "topic": "deadline"}),
        Action(tool="ask_question", arguments={"party_id": "P1", "topic": "modes"}),
        Action(
            tool="propose_offer",
            arguments={"party_id": "P1", "option_id": "E", "voucher": 0},
        ),
        Action(tool="commit_offer", arguments={"offer_id": "O001"}),
        Action(tool="ask_question", arguments={"party_id": "P2", "topic": "deadline"}),
        Action(tool="ask_question", arguments={"party_id": "P2", "topic": "deadline"}),
    ]

    class Gateway:
        def __init__(self):
            self.roles = []
            self.decisions = 0

        async def generate(self, messages, **kwargs):
            role = kwargs["role"]
            self.roles.append(role)
            context = json.loads(messages[-1]["content"])
            menu = context["available_actions"]
            if role != "orchestrator":
                selected = (
                    next(
                        a["id"]
                        for a in menu
                        if a["tool"] == "ask_question"
                        and a["arguments"] == {"party_id": "P1", "topic": "deadline"}
                    )
                    if self.decisions == 0
                    else 0
                )
                return json.dumps(
                    {"action_id": selected, "plan": "Discover requirements."}
                )
            if self.decisions == 1:
                advice = context["prior_advice"]
                assert advice[0]["tick"] == 1
                assert "action_id" not in advice[0]
                assert advice[0]["action"] == planned[0].model_dump()
                assert all(
                    a["arguments"] != advice[0]["action"]["arguments"] for a in menu
                )
                assert context["specialist_proposals"] == []
            action = planned[self.decisions].model_dump()
            selected = next(
                a["id"]
                for a in menu
                if {k: v for k, v in a.items() if k != "id"} == action
            )
            self.decisions += 1
            return json.dumps(
                {"action_id": selected, "plan": "Check consent and booking receipts."}
            )

    gateway = Gateway()
    world = World()
    agent = TEAM_ADAPTERS[framework](gateway, "test", world.fixture["policy"], "team")
    reasons = []
    for tick in range(1, 7):
        world.advance()
        action = await agent.next_action(world.observation())
        reasons.append(agent.last_coordination["consultation_reason"])
        result = (
            {"ok": False, "code": "timeout"} if tick == 5 else world.execute(action)
        )
        agent.observe_tool_result(action, result)
    assert reasons == [
        "initial",
        "reuse_advice",
        "reuse_advice",
        "resolve_offer",
        "booking_changed",
        "action_failed",
    ]
    assert gateway.roles.count("orchestrator") == 6
    assert gateway.roles.count("inventory_specialist") == 3
    assert gateway.roles.count("traveler_specialist") == 3
    assert world.bookings["P1"]["option_id"] == "E"
