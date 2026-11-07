import pytest
from fastapi.testclient import TestClient
from worldfork.api import app


@pytest.fixture
def client(monkeypatch, tmp_path):
    from worldfork.runner import Runner
    from worldfork.store import Store

    s = Store(tmp_path / "api.sqlite")
    monkeypatch.setattr("worldfork.api.store", s)
    monkeypatch.setattr("worldfork.api.runner", Runner(s))
    try:
        with TestClient(app, base_url="http://localhost") as c:
            yield c
    finally:
        s.db.close()


def test_scenario_public_state_and_missing_run(client):
    data = client.get("/api/scenarios").json()
    assert len(data[0]["initial"]["cases"]) == 6
    assert all(not c["known"] for c in data[0]["initial"]["cases"])
    assert client.get("/api/runs/missing").status_code == 404


def test_invalid_comparison_rejected_before_work(client):
    response = client.post(
        "/api/comparisons",
        json={
            "a": {"scenario_id": "harbor-v1"},
            "b": {"scenario_id": "harbor-scarce-v1"},
        },
    )
    assert response.status_code == 400
    assert client.get("/api/runs").json() == []


def test_budget_and_unknown_options_validated(client):
    assert client.post("/api/runs", json={"max_steps": 100000}).status_code == 422
    assert (
        client.post("/api/runs", json={"framework": "fake-framework"}).status_code
        == 422
    )


def test_model_choices_exclude_cloud_and_missing_models(client, monkeypatch):
    import httpx

    class LocalModels:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return httpx.Response(
                200,
                request=httpx.Request("GET", url),
                json={
                    "models": [
                        {"name": "llama3.1:latest"},
                        {"name": "gpt-oss:120b-cloud"},
                    ]
                },
            )

    monkeypatch.setattr("worldfork.api.httpx.AsyncClient", LocalModels)
    assert client.get("/api/models").json() == ["ollama/llama3.1:latest"]


def test_live_browser_boundary_blocks_foreign_host_and_cancel(client, monkeypatch):
    from worldfork.api import runner, store

    store.create("queued", {}, {})
    cancelled = []
    monkeypatch.setattr(runner, "cancel", cancelled.append)
    path = "/api/runs/queued/cancel"
    assert (
        client.get("/api/runs", headers={"Host": "untrusted.example"}).status_code
        == 400
    )
    for origin in ["https://untrusted.example", "null"]:
        assert client.post(path, headers={"Origin": origin}).status_code == 403
    assert cancelled == []
    assert (
        client.post(path, headers={"Origin": "http://localhost:5173"}).status_code
        == 200
    )
    assert client.post(path).status_code == 200
    assert cancelled == ["queued", "queued"]


def test_queue_limit_applies_to_forks_and_seed_validation_precedes_enqueue(client):
    from worldfork.api import runner, store

    store.create("parent", {"scenario_id": "harbor-v1"}, {})
    assert (
        client.post(
            "/api/comparisons",
            json={"a": {"seed": 1000000}, "b": {"seed": 1000000}, "repeats": 2},
        ).status_code
        == 422
    )
    runner.tasks.update(dict.fromkeys(range(30)))
    try:
        assert client.post("/api/runs/parent/fork", json={}).status_code == 429
        assert client.post("/api/runs", json={}).status_code == 429
        assert (
            client.post("/api/comparisons", json={"a": {}, "b": {}}).status_code == 429
        )
    finally:
        runner.tasks.clear()
    assert len(client.get("/api/runs").json()) == 1


def test_archive_summary_preserves_full_run_contract_and_validates_event_offset(client):
    from worldfork.api import store

    store.create("run", {"strategy": "coordinated"}, {"tick": 1})
    store.update(
        "run",
        status="stopped",
        result={
            "satisfied_people": 3,
            "total_people": 7,
            "attempts": [{"raw_response": "{}"}],
        },
    )
    full = client.get("/api/runs").json()[0]
    summary = client.get("/api/runs?summary=true").json()[0]
    assert full == client.get("/api/runs/run").json()
    assert full["snapshot"] == {"tick": 1}
    assert full["result"]["attempts"] == [{"raw_response": "{}"}]
    assert "snapshot" not in summary
    assert summary["result"] == {"satisfied_people": 3, "total_people": 7}
    for offset in [-1, 9223372036854775808]:
        assert client.get(f"/api/runs/run/events?after_seq={offset}").status_code == 422


def test_repeat_team_comparisons_share_seeds_and_faults(client, monkeypatch):
    from worldfork.api import runner

    configs = []

    def record(config):
        configs.append(config)
        return str(len(configs))

    monkeypatch.setattr(runner, "create", record)
    common = {"seed": 11, "framework": "langgraph", "fault": "tool_timeout"}
    response = client.post(
        "/api/comparisons",
        json={
            "a": {**common, "strategy": "coordinated"},
            "b": {**common, "strategy": "team"},
            "repeats": 3,
        },
    )
    assert response.status_code == 202
    for seed, pair in enumerate(response.json()["run_ids"], start=11):
        solo, team = (configs[int(pair[side]) - 1] for side in ("a", "b"))
        assert solo.strategy == "coordinated" and team.strategy == "team"
        assert solo.seed == team.seed == seed
        assert solo.fault == team.fault == "tool_timeout"
        assert solo.model_dump(exclude={"strategy"}) == team.model_dump(
            exclude={"strategy"}
        )
