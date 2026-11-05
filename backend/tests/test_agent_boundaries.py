from worldfork.agents import PythonAgent
from worldfork.engine import Action, World


def agent():
    return PythonAgent(None, "test", "fictional policy", "coordinated")


def test_menu_does_not_depend_on_hidden_profile():
    a, b = World(), World()
    b.parties["P1"]["deadline"] = 1200
    b.parties["P1"]["terms"] = {"E": 40, "L": 0}
    menu_a = [x.model_dump() for x in agent().action_menu(a.observation())]
    menu_b = [x.model_dump() for x in agent().action_menu(b.observation())]
    assert menu_a == menu_b


def test_shared_transaction_guard_and_timeout_retry():
    w = World()
    a = agent()
    w.advance()
    action = Action(
        tool="propose_offer",
        arguments={"party_id": "P5", "option_id": "L", "voucher": 40},
    )
    a.observe_tool_result(action, {"ok": False, "code": "timeout"})
    assert action in a.action_menu(w.observation())
    result = w.execute(action)
    a.observe_tool_result(action, result)
    assert {x.tool for x in a.action_menu(w.observation())} == {
        "commit_offer",
        "withdraw_offer",
    }


def test_rejected_offer_not_repeated_but_capacity_conflict_can_retry():
    w = World()
    a = agent()
    action = Action(
        tool="propose_offer",
        arguments={"party_id": "P1", "option_id": "L", "voucher": 0},
    )
    a.observe_tool_result(action, {"ok": True, "offer": {"status": "rejected"}})
    assert action not in a.action_menu(w.observation())
    retry = Action(
        tool="propose_offer",
        arguments={"party_id": "P1", "option_id": "E", "voucher": 0},
    )
    a.observe_tool_result(retry, {"ok": False, "code": "capacity"})
    assert retry in a.action_menu(w.observation())
