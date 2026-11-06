# WorldFork pilot summary

Synthetic development scenarios; not a real-world forecast.

| Framework | Strategy | Fault | Configured / scored | Requirements met (mean; range) | Fault exposures | Terminal states |
|---|---|---|---:|---|---:|---|
| langgraph | case_by_case | none | 3 / 3 | 7.00; 7–7 | 0 | completed: 3 |
| langgraph | coordinated | none | 3 / 3 | 5.33; 5–6 | 0 | exhausted: 2, stopped: 1 |
| python | case_by_case | misleading_observation | 3 / 3 | 6.33; 5–7 | 3 | exhausted: 1, completed: 2 |
| python | case_by_case | model_unavailable | 3 / 3 | 6.33; 5–7 | 3 | exhausted: 1, completed: 2 |
| python | case_by_case | none | 3 / 3 | 7.00; 7–7 | 0 | completed: 3 |
| python | case_by_case | tool_timeout | 3 / 3 | 6.33; 5–7 | 3 | exhausted: 1, completed: 2 |
| python | coordinated | misleading_observation | 3 / 3 | 5.00; 5–5 | 3 | exhausted: 2, stopped: 1 |
| python | coordinated | model_unavailable | 3 / 3 | 5.67; 5–7 | 3 | stopped: 1, exhausted: 1, completed: 1 |
| python | coordinated | none | 3 / 3 | 6.00; 5–7 | 0 | completed: 1, stopped: 1, exhausted: 1 |
| python | coordinated | tool_timeout | 3 / 3 | 5.33; 4–7 | 3 | exhausted: 1, completed: 1, stopped: 1 |

## Resource measurements

Each mean is followed by its known/scored denominator. Unknown usage is not zero.

| Framework | Strategy | Fault | Steps | Tool calls | Input tokens | Output tokens | Elapsed seconds | Credits spent | Invalid attempts | Committed violations |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| langgraph | case_by_case | none | 38.3 (3/3) | 38.3 (3/3) | 69,781.7 (3/3) | 259.3 (3/3) | 112.9 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| langgraph | coordinated | none | 47.3 (3/3) | 47.3 (3/3) | 85,557.7 (3/3) | 309.7 (3/3) | 187.9 (3/3) | 53.3 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | case_by_case | misleading_observation | 44.0 (3/3) | 44.0 (3/3) | 80,687.3 (3/3) | 293.3 (3/3) | 162.5 (3/3) | 80.0 (3/3) | 0.7 (3/3) | 0.0 (3/3) |
| python | case_by_case | model_unavailable | 39.7 (3/3) | 39.7 (3/3) | 72,047.0 (3/3) | 266.7 (3/3) | 128.4 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | case_by_case | none | 41.0 (3/3) | 41.0 (3/3) | 73,866.7 (3/3) | 276.7 (3/3) | 162.5 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | case_by_case | tool_timeout | 42.3 (3/3) | 42.3 (3/3) | 77,251.3 (3/3) | 284.3 (3/3) | 160.1 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | coordinated | misleading_observation | 47.3 (3/3) | 47.3 (3/3) | 85,876.7 (3/3) | 309.3 (3/3) | 179.8 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | coordinated | model_unavailable | 45.3 (3/3) | 45.3 (3/3) | 82,566.3 (3/3) | 300.0 (3/3) | 180.8 (3/3) | 80.0 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | coordinated | none | 44.3 (3/3) | 44.3 (3/3) | 81,889.3 (3/3) | 295.3 (3/3) | 182.7 (3/3) | 66.7 (3/3) | 0.0 (3/3) | 0.0 (3/3) |
| python | coordinated | tool_timeout | 44.3 (3/3) | 44.3 (3/3) | 81,618.0 (3/3) | 296.3 (3/3) | 168.8 (3/3) | 66.7 (3/3) | 0.0 (3/3) | 0.0 (3/3) |

## Configuration groups

- Model: ollama/qwen3.5:4b; scenario: harbor-v1; passengers: scripted.

Local API charge is recorded per run. Hardware and electricity are unmeasured.

## Raw episode outcomes

| Run | Framework / strategy | Fault | Status | Requirements met | Steps | Fault delivered |
|---|---|---|---|---:|---:|---|
| dd7d3cb0-7a79-4c8c-9bc1-704d4c2169bd | python / case_by_case | none | completed | 7 | 44 | False |
| 7fd92f63-effb-4201-a05c-4f9b5de7b513 | python / coordinated | none | completed | 7 | 43 | False |
| 67084f40-1118-46f9-8cf6-17fea1a1b7d4 | langgraph / case_by_case | none | completed | 7 | 42 | False |
| 743d7f14-d1fb-4f36-889e-d119115d02c3 | langgraph / coordinated | none | exhausted | 6 | 48 | False |
| 68bbf46f-fe10-4342-96d3-acdbdbac47eb | langgraph / coordinated | none | exhausted | 5 | 48 | False |
| fe3b30ed-4b91-49c2-918c-383b8e2e936a | langgraph / case_by_case | none | completed | 7 | 34 | False |
| 9f14b3e9-2ac2-4e25-b6fa-b568898f0edb | python / coordinated | none | stopped | 6 | 42 | False |
| 649f4eaf-9463-4cfa-b8e5-1dc72fcca9ff | python / case_by_case | none | completed | 7 | 40 | False |
| d6c668db-26d2-4b27-9249-44bcf63f73ef | python / coordinated | none | exhausted | 5 | 48 | False |
| 1c4e9f8d-36cb-4057-aaea-bd3b65723a9f | langgraph / coordinated | none | stopped | 5 | 46 | False |
| 2ef2b913-962a-4827-a5e3-4094971d8516 | python / case_by_case | none | completed | 7 | 39 | False |
| 8da9922c-ac1f-44d7-b222-64a43b07eab6 | langgraph / case_by_case | none | completed | 7 | 39 | False |
| 156d3b75-115d-4b52-8a69-6c9517ec722a | python / case_by_case | model_unavailable | exhausted | 5 | 48 | True |
| ca0d82c6-6f88-465e-b068-caf03fcc8f13 | python / case_by_case | model_unavailable | completed | 7 | 38 | True |
| fd7600d1-cb57-4797-a467-6e97f66c7ae2 | python / case_by_case | model_unavailable | completed | 7 | 33 | True |
| 8cd14d4f-f256-40aa-89f4-86fc5cf021ce | python / coordinated | model_unavailable | stopped | 5 | 48 | True |
| 9fc33c21-ef0a-400e-b49e-b28ae28e386a | python / coordinated | model_unavailable | exhausted | 5 | 48 | True |
| ab0df112-1ce4-43eb-9da1-ee68a2e3c9dd | python / coordinated | model_unavailable | completed | 7 | 40 | True |
| 3cb8921c-b0fb-4b4d-9257-e4570fe491ae | python / case_by_case | tool_timeout | exhausted | 5 | 48 | True |
| 473e08c7-5d7d-402b-a845-ad0463ff530c | python / case_by_case | tool_timeout | completed | 7 | 35 | True |
| 961be8aa-8997-4219-b1a3-c18e195e60e1 | python / case_by_case | tool_timeout | completed | 7 | 44 | True |
| 62a1bb7a-0c8c-4754-9a84-30f2039c13b4 | python / coordinated | tool_timeout | exhausted | 4 | 48 | True |
| 6a1661a9-029f-426c-9fad-8734c56606d9 | python / coordinated | tool_timeout | completed | 7 | 39 | True |
| a12fdb65-27e7-447a-a8fc-38144ff8cb5e | python / coordinated | tool_timeout | stopped | 5 | 46 | True |
| 2a7302f6-170a-4e34-a68c-fc62496161b3 | python / case_by_case | misleading_observation | exhausted | 5 | 48 | True |
| d2d280ad-2c45-4a3b-8450-ea3ea9ccb637 | python / case_by_case | misleading_observation | completed | 7 | 46 | True |
| 9dc1563a-964c-4207-96c7-a09ed39eb5b5 | python / case_by_case | misleading_observation | completed | 7 | 38 | True |
| 12d813d5-a7fa-4004-8922-cadc47923e50 | python / coordinated | misleading_observation | exhausted | 5 | 48 | True |
| d3c6c2d0-ce62-49e4-9a64-d9299972d1a5 | python / coordinated | misleading_observation | exhausted | 5 | 48 | True |
| 9a05d269-2b2c-4993-90d9-f7235b6898c5 | python / coordinated | misleading_observation | stopped | 5 | 46 | True |

- Raw terminal counts include every retained run.
- Cancelled, interrupted and simulator-error runs are excluded from means, not erased.
- Fault exposure denominator may be smaller than configured count.
- Small pilot; no significance or real-world prediction claim.
- Model-unavailable recovery includes an automatic harness retry; do not attribute that retry to model reasoning.
- Means use known values only; each resource cell reports its known/scored denominator.
