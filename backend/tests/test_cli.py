from collections import Counter

from worldfork.cli import pilot_configs


def test_pilot_matrix_keeps_all_cells_and_varies_clean_order():
    configs = pilot_configs(model="ollama/qwen3.5:4b")
    assert len(configs) == 21
    clean = configs[:12]
    assert Counter((c["framework"], c["strategy"]) for c in clean) == {
        (framework, strategy): 3
        for framework in ["python", "langgraph"]
        for strategy in ["case_by_case", "coordinated"]
    }
    orders = [
        tuple((c["framework"], c["strategy"]) for c in clean[i : i + 4])
        for i in [0, 4, 8]
    ]
    assert len(set(orders)) == 3
    assert Counter(c["fault"] for c in configs[12:]) == {
        "model_unavailable": 3,
        "tool_timeout": 3,
        "misleading_observation": 3,
    }
    assert all(c["model"] == "ollama/qwen3.5:4b" for c in configs)
    assert len(pilot_configs(full=True)) == 30


async def test_partial_enqueue_failure_cancels_all_acknowledged_runs(
    monkeypatch, tmp_path
):
    import httpx
    import pytest
    from worldfork import cli

    cancelled = []
    accepted = iter(["one", "two", None])

    async def handle(request):
        if request.url.path == "/api/runs":
            rid = next(accepted)
            return httpx.Response(202, json={"id": rid}) if rid else httpx.Response(429)
        cancelled.append(request.url.path)
        return httpx.Response(503 if "one" in request.url.path else 200)

    client = httpx.AsyncClient(
        base_url="http://127.0.0.1:8000", transport=httpx.MockTransport(handle)
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.httpx, "AsyncClient", lambda **kwargs: client)
    monkeypatch.setattr(
        cli, "build_provenance", lambda: {"tracked_changes_at_start": False}
    )
    with pytest.raises(httpx.HTTPStatusError) as raised:
        await cli.benchmark()
    assert raised.value.response.status_code == 429
    assert sorted(cancelled) == ["/api/runs/one/cancel", "/api/runs/two/cancel"]
    assert len(list((tmp_path / "artifacts").glob("benchmark-*.json"))) == 1
