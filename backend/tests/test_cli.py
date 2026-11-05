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
