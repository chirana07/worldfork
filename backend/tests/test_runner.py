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


async def test_cancel_keeps_active_run_pollable_until_final_result(
    monkeypatch, tmp_path
):
    import asyncio

    generating = asyncio.Event()
    closing = asyncio.Event()
    finish_close = asyncio.Event()

    class PausedGateway(FakeGateway):
        async def generate(self, *args, **kwargs):
            generating.set()
            await asyncio.Future()

        async def close(self):
            closing.set()
            await finish_close.wait()

    monkeypatch.setattr("worldfork.runner.Gateway", PausedGateway)
    store = Store(tmp_path / "runs.sqlite")
    runner = Runner(store)
    active = runner.create(RunConfig())
    active_task = runner.tasks[active]
    try:
        await asyncio.wait_for(generating.wait(), 2)
        queued = runner.create(RunConfig())
        queued_task = runner.tasks[queued]
        runner.cancel(queued)
        with pytest.raises(asyncio.CancelledError):
            await queued_task
        assert queued not in runner.tasks
        assert store.get(queued)["status"] == "cancelled"
        assert store.get(queued)["result"] is None

        runner.cancel(active)
        await asyncio.wait_for(closing.wait(), 2)
        runner.cancel(active)
        assert store.get(active)["status"] == "running"
        assert not active_task.done()
    finally:
        finish_close.set()
        await asyncio.wait_for(active_task, 2)
    run = store.get(active)
    assert run["status"] == "cancelled"
    assert run["result"] == store.events(active)[-1]["result"]


@pytest.mark.parametrize("framework", ["python", "langgraph"])
async def test_team_advises_then_books_through_simulator(
    monkeypatch, tmp_path, framework
):
    class TeamGateway(FakeGateway):
        async def generate(self, messages, **kwargs):
            role = kwargs["role"]
            context = json.loads(messages[-1]["content"])
            assert "terms" not in context["world"]
            if role == "orchestrator":
                if context["world"]["active_offers"]:
                    assert context["specialist_proposals"] == []
                else:
                    assert [p["role"] for p in context["specialist_proposals"]] == [
                        "inventory_specialist",
                        "traveler_specialist",
                    ]
                    assert context["specialist_proposals"][1]["status"] == "invalid"
                raw = await super().generate(messages, **kwargs)
                return json.dumps(
                    {**json.loads(raw), "plan": "Confirm a feasible move."}
                )
            self.attempts.append({"role": role, "input_tokens": 10, "output_tokens": 5})
            return json.dumps(
                {
                    "action_id": 0 if role == "inventory_specialist" else -1,
                    "plan": "Check a route.",
                }
            )

    monkeypatch.setattr("worldfork.runner.Gateway", TeamGateway)
    store = Store(tmp_path / "team.sqlite")
    runner = Runner(store)
    rid = runner.create(RunConfig(strategy="team", framework=framework, max_steps=2))
    await runner.tasks[rid]
    actions = [event for event in store.events(rid) if event["type"] == "action"]
    assert [event["action"]["tool"] for event in actions] == [
        "propose_offer",
        "commit_offer",
    ]
    assert actions[1]["result"]["receipt"]["status"] == "committed"
    assert actions[0]["coordination"]["plan"] == "Confirm a feasible move."
    assert [a["role"] for event in actions for a in event["attempts"]] == [
        "inventory_specialist",
        "traveler_specialist",
        "orchestrator",
        "orchestrator",
    ]
    assert store.get(rid)["result"]["model_calls"] == 4
