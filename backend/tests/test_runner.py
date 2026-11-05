import json

import pytest
from worldfork.runner import RunConfig, Runner
from worldfork.store import Store


class FakeGateway:
    def __init__(self, *args):
        self.attempts = []
        self.index = 0

    async def generate(self, messages, **kwargs):
        a = {
            "input_tokens": 10,
            "output_tokens": 5,
            "status": "ok",
            "role": kwargs.get("role", "support"),
            "elapsed_ms": 1,
        }
        self.attempts.append(a)
        if kwargs.get("injected_failure"):
            a.update(status="error", input_tokens=None, output_tokens=None)
            raise ConnectionError("injected")
        actions = [
            ("propose_offer", {"party_id": "P5", "option_id": "L", "voucher": 40}),
            ("commit_offer", {"offer_id": "O001"}),
            ("propose_offer", {"party_id": "P1", "option_id": "E", "voucher": 0}),
            ("commit_offer", {"offer_id": "O002"}),
            ("propose_offer", {"party_id": "P2", "option_id": "E", "voucher": 0}),
            ("commit_offer", {"offer_id": "O003"}),
            ("propose_offer", {"party_id": "P3", "option_id": "L", "voucher": 40}),
            ("commit_offer", {"offer_id": "O004"}),
            ("propose_offer", {"party_id": "P4", "option_id": "R", "voucher": 0}),
            ("commit_offer", {"offer_id": "O005"}),
            ("propose_offer", {"party_id": "P6", "option_id": "R", "voucher": 0}),
            ("commit_offer", {"offer_id": "O006"}),
        ]
        if self.index >= len(actions):
            return json.dumps(
                {"tool": "finish", "arguments": {"reason": "test finished"}}
            )
        tool, args = actions[self.index]
        self.index += 1
        menu = json.loads(messages[-1]["content"]).get("available_actions")
        if menu is not None:
            target = next(
                (a["id"] for a in menu if a["tool"] == tool and a["arguments"] == args),
                menu[-1]["id"],
            )
            return json.dumps({"action_id": target})
        return json.dumps({"tool": tool, "arguments": args})

    async def close(self):
        pass


@pytest.mark.parametrize("framework", ["python", "langgraph"])
async def test_frameworks_execute_same_tool_contract(monkeypatch, tmp_path, framework):
    monkeypatch.setattr("worldfork.runner.Gateway", FakeGateway)
    s = Store(tmp_path / "runs.sqlite")
    r = Runner(s)
    rid = r.create(RunConfig(framework=framework))
    await r.tasks[rid]
    run = s.get(rid)
    assert run["status"] == "completed"
    assert run["result"]["satisfied_people"] == 7
    assert run["result"]["input_tokens"] == 120
    events = s.events(rid)
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert not any("terms" in json.dumps(e.get("observation", {})) for e in events)


@pytest.mark.parametrize(
    "fault", ["model_unavailable", "tool_timeout", "misleading_observation"]
)
async def test_faults_are_delivered_logged_and_state_stays_valid(
    monkeypatch, tmp_path, fault
):
    monkeypatch.setattr("worldfork.runner.Gateway", FakeGateway)
    s = Store(tmp_path / "runs.sqlite")
    r = Runner(s)
    rid = r.create(RunConfig(fault=fault))
    await r.tasks[rid]
    result = s.get(rid)["result"]
    assert result["fault_delivered"] is True
    assert len([e for e in s.events(rid) if e["type"] == "fault"]) == 1
    assert result["committed_policy_violations"] == 0
    assert result["terminal"] != "simulator_error"


async def test_step_budget_and_replay_do_not_generate_calls(monkeypatch, tmp_path):
    monkeypatch.setattr("worldfork.runner.Gateway", FakeGateway)
    s = Store(tmp_path / "runs.sqlite")
    r = Runner(s)
    rid = r.create(RunConfig(max_steps=1))
    await r.tasks[rid]
    assert s.get(rid)["status"] == "exhausted"
    before = s.get(rid)["result"]["model_calls"]
    assert s.events(rid)
    assert s.get(rid)["result"]["model_calls"] == before
