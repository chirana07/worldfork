import pytest
from worldfork.engine import Action, World, oracle, scenario, score


def act(w, tool, **arguments):
    w.advance()
    return w.execute(Action(tool=tool, arguments=arguments))


def book(w, pid, oid, voucher=0):
    result = act(w, "propose_offer", party_id=pid, option_id=oid, voucher=voucher)
    assert result["ok"] and result["offer"]["status"] == "accepted", result
    return act(w, "commit_offer", offer_id=result["offer"]["id"])


def test_feasible_witness_and_oracle():
    w = World()
    assert oracle(w.fixture)["max_satisfied_people"] == 7
    for pid, oid, voucher in [
        ("P5", "L", 40),
        ("P1", "E", 0),
        ("P2", "E", 0),
        ("P3", "L", 40),
        ("P4", "R", 0),
        ("P6", "R", 0),
    ]:
        assert book(w, pid, oid, voucher)["ok"]
    s = score(w)
    assert (
        s["satisfied_people"],
        s["newly_satisfied_people"],
        s["oracle_gap"],
        s["compensation_spent"],
    ) == (7, 6, 0, 80)


def test_capacity_and_no_partial_family_booking():
    w = World()
    book(w, "P1", "E")
    result = act(w, "propose_offer", party_id="P2", option_id="E", voucher=0)
    assert result["code"] == "capacity"
    assert "P2" not in w.bookings and w.available("E") == 1


def test_move_retains_booking_and_reserves_budget_until_commit():
    w = World()
    r = act(w, "propose_offer", party_id="P5", option_id="L", voucher=40)
    assert w.bookings["P5"]["option_id"] == "E" and w.available("L") == 2
    assert w.spent == 0 and w.budget_available() == 40
    act(w, "commit_offer", offer_id=r["offer"]["id"])
    assert w.available("E") == 3 and w.spent == 40


def test_rejection_and_no_consent_cannot_commit():
    w = World()
    r = act(w, "propose_offer", party_id="P1", option_id="L", voucher=40)
    assert r["offer"]["status"] == "rejected"
    assert w.available("L") == 3 and w.budget_available() == 80
    assert not act(w, "commit_offer", offer_id=r["offer"]["id"])["ok"]


def test_expiry_boundary_and_idempotence():
    w = World()
    r = act(w, "propose_offer", party_id="P5", option_id="L", voucher=40)
    w.advance()
    w.advance()
    w.advance()
    assert w.tick == r["offer"]["expires_tick"]
    assert not w.execute(
        Action(tool="commit_offer", arguments={"offer_id": r["offer"]["id"]})
    )["ok"]
    assert w.bookings["P5"]["option_id"] == "E" and w.budget_available() == 80
    receipt = book(w, "P5", "L", 40)
    assert act(w, "commit_offer", offer_id=receipt["receipt"]["id"])["idempotent"]
    assert w.spent == 40


def test_active_offer_and_same_route_do_not_spend_extra():
    w = World()
    assert (
        act(w, "propose_offer", party_id="P5", option_id="E", voucher=40)["code"]
        == "already_booked"
    )
    r = act(w, "propose_offer", party_id="P5", option_id="L", voucher=40)
    assert (
        act(w, "propose_offer", party_id="P5", option_id="L", voucher=40)["code"]
        == "active_offer"
    )
    act(w, "withdraw_offer", offer_id=r["offer"]["id"])
    assert w.spent == 0 and w.budget_available() == 80


def test_private_profiles_not_in_observation():
    w = World()
    assert all(not c["known"] for c in w.observation()["cases"])
    act(w, "ask_question", party_id="P3", topic="compensation")
    assert w.observation()["cases"][0]["known"] == {"compensation": {"E": 0, "L": 40}}
    assert w.revealed["P1"] == {}


def test_worlds_do_not_share_state_and_scarcity_bound():
    a, b = World(), World()
    book(a, "P5", "L", 40)
    assert b.bookings["P5"]["option_id"] == "E"
    assert (
        oracle(scenario(True))["max_satisfied_people"] == 7
    )  # spare late seat can take Dani


@pytest.mark.parametrize(
    "args",
    [
        {"party_id": {}, "option_id": "E", "voucher": 0},
        {"party_id": "P1", "option_id": [], "voucher": 0},
        {"party_id": "P1", "option_id": "E", "voucher": True},
        {"party_id": "P1", "option_id": "E", "voucher": 1.5},
    ],
)
def test_malformed_arguments_are_errors_not_crashes(args):
    assert not act(World(), "propose_offer", **args)["ok"]
