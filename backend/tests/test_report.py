from worldfork.report import markdown, summarize


def test_cancelled_and_missing_results_remain_visible_without_biasing_mean():
    rows = [
        {
            "config": {},
            "status": "completed",
            "result": {
                "satisfied_people": 7,
                "elapsed_ms": 100,
                "fault_delivered": False,
            },
        },
        {
            "config": {},
            "status": "cancelled",
            "result": {
                "satisfied_people": 1,
                "elapsed_ms": 50,
                "fault_delivered": False,
            },
        },
        {"config": {}, "status": "queued"},
    ]
    report = summarize({"runs": rows})
    row = report["rows"][0]
    assert row["configured"] == 3 and row["scored"] == 1
    assert row["resolved_mean"] == 7
    assert row["statuses"] == {"completed": 1, "cancelled": 1, "queued": 1}
    assert "cancelled: 1" in markdown(report)


def test_empty_report_is_not_an_invented_success():
    assert summarize({"runs": []})["rows"] == []


def test_models_are_not_pooled_and_missing_usage_stays_unknown():
    entries = [
        {
            "id": model,
            "config": {"model": model},
            "status": "exhausted",
            "result": {"satisfied_people": 5, "elapsed_ms": 100, "input_tokens": None},
        }
        for model in ["local-a", "local-b"]
    ]
    report = summarize({"runs": entries})
    assert len(report["rows"]) == 2
    assert all(
        r["metrics"]["input_tokens"] == {"known": 0, "mean": None, "range": None}
        for r in report["rows"]
    )
    assert "unknown" in markdown(report)


def test_benchmark_results_match_the_complete_release_matrix():
    import json
    from pathlib import Path

    from worldfork.report import benchmark_summary

    root = Path(__file__).resolve().parents[2] / "evidence/team-evaluation"
    manifest = json.loads((root / "manifest.json").read_text())
    runs = [
        json.loads((root / entry["trace"]).read_text())["run"]
        for entry in manifest["runs"]
    ]
    report = benchmark_summary(runs)
    assert len(report["cohorts"]) == 4
    rows = [row for cohort in report["cohorts"] for row in cohort["rows"]]
    assert len(rows) == 8
    assert all(row["scored"] == 3 for row in rows)
    assert sum(row["fault_exposed"] for row in rows) == 9
    assert sum(row["configured"] for row in rows) == 24
    assert (
        sum(
            row["metrics"]["model_calls"]["mean"] * row["scored"]
            for row in rows
            if row["strategy"] == "team"
        )
        == 288
    )
    for row in rows:
        assert len(row["run_ids"]) == 3
        assert row["seeds"] == [17, 43, 71]


def test_benchmark_keeps_unknown_usage_and_incomplete_runs_visible():
    import copy
    import json
    from pathlib import Path

    from worldfork.report import benchmark_summary

    path = Path(__file__).resolve().parents[2] / "evidence/team-demo/solo.json"
    original = json.loads(path.read_text())["run"]
    missing = copy.deepcopy(original)
    missing["id"] = "missing-usage"
    missing["result"]["input_tokens"] = None
    cancelled = copy.deepcopy(original)
    cancelled["id"], cancelled["status"] = "cancelled", "cancelled"
    unidentified = copy.deepcopy(original)
    unidentified["config"].pop("model_manifest")
    report = benchmark_summary([original, missing, cancelled, unidentified])
    row = report["cohorts"][0]["rows"][0]
    assert row["configured"] == 3 and row["scored"] == 2
    assert row["metrics"]["tokens"]["known"] == 1
    assert (
        row["metrics"]["tokens"]["mean"]
        == original["result"]["input_tokens"] + original["result"]["output_tokens"]
    )
    assert row["statuses"]["cancelled"] == 1
    assert report["unidentified_runs"] == 1
    assert benchmark_summary([]) == {"cohorts": [], "unidentified_runs": 0}


def test_benchmark_does_not_pool_different_conditions():
    import copy
    import json
    from pathlib import Path

    from worldfork.report import benchmark_summary

    path = Path(__file__).resolve().parents[2] / "evidence/team-demo/solo.json"
    original = json.loads(path.read_text())["run"]
    variants = {
        "max_steps": 48,
        "max_tokens": 100000,
        "wall_seconds": 1800,
        "temperature": 0.5,
        "scenario_hash": "other-fixture",
        "passenger_mode": "llm",
        "fault": "tool_timeout",
        "source_hashes": {"runner": "other-revision"},
        "model_manifest": {"digest": "other-model-weights"},
    }
    for field, value in variants.items():
        changed = copy.deepcopy(original)
        changed["id"] = field
        changed["config"][field] = value
        report = benchmark_summary([original, changed])
        assert len(report["cohorts"]) == 2, field
    different_seed = copy.deepcopy(original)
    different_seed["id"] = "other-seed"
    different_seed["config"]["seed"] += 1
    report = benchmark_summary([original, different_seed])
    assert len(report["cohorts"]) == 1
    assert report["cohorts"][0]["rows"][0]["configured"] == 2
