# Release team evaluation

Verified episodes: 24/24.

Fixed before inference: three new seeds (17, 43, 71), two fixtures, clean and tool-timeout conditions, two strategies, Python adapter, scripted passengers, Qwen3.5:4b at temperature 0.2, 16 steps and 160,000 observed tokens per episode. Paired strategy order alternates. The timeout is scheduled at tick 8, leaving up to eight subsequent decisions. These are short budget tests.

The transfer fixture changes arrival requirements, transport modes, party order, early and rail capacity, and compensation. It was reserved from agent tuning before these runs. This measures transfer within the same synthetic airport domain. It is now public evaluation data.

| Scenario | Configured fault | Strategy | Episodes | Mean people / 7 | Mean model calls | Calls / tool action | Mean tokens | Mean seconds | Violations | Early stops |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| harbor-transfer-v1 | none | coordinated | 3 | 2.00 | 16.0 | 1.00 | 31566 | 84.3 | 0 | 0 |
| harbor-transfer-v1 | none | team | 3 | 2.33 | 18.3 | 1.57 | 37684 | 133.7 | 0 | 1 |
| harbor-transfer-v1 | tool_timeout | coordinated | 3 | 2.00 | 12.0 | 1.00 | 24401 | 49.5 | 0 | 1 |
| harbor-transfer-v1 | tool_timeout | team | 3 | 3.33 | 19.7 | 1.69 | 39822 | 127.2 | 0 | 1 |
| harbor-v1 | none | coordinated | 3 | 3.00 | 16.0 | 1.00 | 33074 | 79.5 | 0 | 0 |
| harbor-v1 | none | team | 3 | 3.33 | 26.0 | 1.62 | 54898 | 184.2 | 0 | 0 |
| harbor-v1 | tool_timeout | coordinated | 3 | 2.33 | 11.3 | 1.00 | 23578 | 60.7 | 0 | 1 |
| harbor-v1 | tool_timeout | team | 3 | 4.00 | 32.0 | 2.00 | 67752 | 223.4 | 0 | 0 |

Across the recorded team paths, 75 of 166 tool decisions reassessed earlier advice, skipping 150 specialist requests that the previous consultation rule would have dispatched on those paths. The orchestrator received fresh observations on every decision. The matched outcomes below show the resulting allocation and resource tradeoffs.

## Matched outcomes

| Scenario | Configured fault | Seed | Solo people | Team people | Solo calls | Team calls | Solo fault exposed | Team fault exposed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| harbor-transfer-v1 | none | 17 | 2 | 5 | 16 | 28 | no | no |
| harbor-transfer-v1 | none | 43 | 2 | 1 | 16 | 22 | no | no |
| harbor-transfer-v1 | none | 71 | 2 | 1 | 16 | 5 | no | no |
| harbor-transfer-v1 | tool_timeout | 17 | 1 | 5 | 4 | 26 | no | yes |
| harbor-transfer-v1 | tool_timeout | 43 | 3 | 1 | 16 | 5 | yes | no |
| harbor-transfer-v1 | tool_timeout | 71 | 2 | 4 | 16 | 28 | yes | yes |
| harbor-v1 | none | 17 | 3 | 3 | 16 | 32 | no | no |
| harbor-v1 | none | 43 | 3 | 3 | 16 | 22 | no | no |
| harbor-v1 | none | 71 | 3 | 4 | 16 | 24 | no | no |
| harbor-v1 | tool_timeout | 17 | 3 | 5 | 16 | 34 | yes | yes |
| harbor-v1 | tool_timeout | 43 | 1 | 3 | 2 | 28 | no | yes |
| harbor-v1 | tool_timeout | 71 | 3 | 4 | 16 | 34 | yes | yes |

## Fault follow-through

| Scenario | Strategy | Exposed episodes | Episodes with later actions | Episodes with a later successful tool | Episodes with a later booking | Episodes retrying timed-out action successfully |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| harbor-transfer-v1 | coordinated | 2 | 2 | 2 | 2 | 2 |
| harbor-transfer-v1 | team | 2 | 2 | 2 | 2 | 0 |
| harbor-v1 | coordinated | 2 | 2 | 2 | 0 | 1 |
| harbor-v1 | team | 3 | 3 | 3 | 3 | 1 |

Tool success means a receipt with `ok: true`. A booking requires a committed receipt. A later successful tool, a booking, and retrying the failed action are distinct observations. They do not establish that the clean outcome was restored. Runs stopping before tick 8 are unexposed. Three seeds, one model, the same simulator and short budgets limit generalization. Requested model seeds are recorded, but model completions can vary across repeated requests. Local API charge is zero. Hardware and electricity were unmeasured. Timing includes local contention and inference warm-up.

Full exports and SHA-256 checksums are listed in [the manifest](manifest.json). Verify with `uv run python scripts/evaluate_team.py --verify`.
