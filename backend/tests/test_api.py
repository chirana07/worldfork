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
    with TestClient(app) as c:
        yield c


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
