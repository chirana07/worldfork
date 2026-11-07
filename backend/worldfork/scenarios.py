"""Named fixtures. The transfer fixture is reserved for the release evaluation."""

from typing import Literal

from .engine import scenario

ScenarioId = Literal["harbor-v1", "harbor-scarce-v1", "harbor-transfer-v1"]


def load_scenario(scenario_id: ScenarioId):
    if scenario_id not in ScenarioId.__args__:
        raise ValueError("Unknown scenario")
    fixture = scenario(scenario_id == "harbor-scarce-v1")
    if scenario_id == "harbor-transfer-v1":
        fixture.update(
            id=scenario_id,
            label="Harbor · changed connections",
            order=["P6", "P2", "P4", "P3", "P1", "P5"],
            budget=40,
        )
        fixture["options"]["E"]["capacity"] = 2
        fixture["options"]["R"]["capacity"] = 3
        fixture["parties"]["P1"].update(
            deadline=1020,
            modes=["rail"],
            terms={"R": 0},
            message="I need replacement travel. Please ask about my transport requirements.",
        )
        fixture["parties"]["P2"].update(deadline=1140, terms={"E": 0, "L": 0})
        fixture["parties"]["P3"]["terms"] = {"E": 0, "L": 0}
        fixture["policy"] = fixture["policy"].replace(
            "pool is 80 credits", "pool is 40 credits"
        )
    return fixture
