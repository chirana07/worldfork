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
