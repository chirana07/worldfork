# Performance evaluation

## Live agents

The 30-episode pilot used Qwen3.5:4b through Bifrost, scripted passengers, and the Harbor development fixture. Of the 30 episodes, 15 completed, 10 exhausted their budget, and five stopped. All 18 configured faults were delivered. No episode committed a policy violation. The [pilot summary](../evidence/pilot-summary.md) breaks results down by framework, strategy and fault.

| Measurement | Samples | Median | P95 |
| --- | ---: | ---: | ---: |
| Active runner time per episode | 30 | 172.89 s | 200.06 s |
| Bifrost round trip per real model attempt | 1,302 | 3.94 s | 5.26 s |
| Steps per episode | 30 | 45 | 48 |
| Input tokens per episode | 30 | 80,104 | 89,995 |
| Output tokens per episode | 30 | 299 | 321 |

P95 uses nearest rank. The elapsed episode timer excludes time waiting in the single local queue. Real model-attempt elapsed time excludes six injected failures that made no provider request. The median per-episode ratio of summed real model round trips to active runner time was 99.88%. Those round trips include the local gateway and provider path. API charges were zero for these local calls. Hardware and electricity were unmeasured.

Inference dominated the live execution time on this host. The public-menu policy, prompts, inference budget and trace evidence were kept fixed during the replay optimization. Pilot timings are descriptive and the fixture was used during development.

## Replay service before and after gzip

Both versions served the same evidence using Linux arm64 containers on the M4 Pro Mac. Each was limited to one CPU and 512 MiB. The client used loopback and fresh HTTP connections. At each of one and eight simultaneous requests, each version ran three trials of 100 requests, with 25 per route. All 1,200 responses were HTTP 200. The load generator measured full response-body transfer, excluding browser rendering, TLS and internet transit.

| Route | Baseline body | Gzip body | Reduction | Baseline P95 at 8 | Gzip P95 at 8 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archive | 753,979 B | 101,090 B | 86.6% | 210.52 ms | 186.90 ms |
| Run detail | 24,524 B | 4,526 B | 81.5% | 203.09 ms | 129.77 ms |
| Event feed | 362,705 B | 26,438 B | 92.7% | 202.58 ms | 184.97 ms |
| Trace export | 769,292 B | 58,310 B | 92.4% | 209.08 ms | 185.46 ms |

The table reports medians across the three trials. At concurrency one, median throughput was 51.8 requests/s before and 51.0 after. At concurrency eight, it was 54.2 before and 55.2 after. The export P95 at concurrency one increased from 20.18 to 33.56 ms. Peak container memory across startup, validation and load was 109.8 MiB before and 105.9 MiB after. Cumulative container CPU time across the same sequence was 14.04 s before and 14.61 s after. These are local measurements under a short workload. The reproducible improvement is in transferred bytes. Decoded exports matched the frozen originals.

After a container restart, the service rebuilt the temporary database, exposed all 30 recorded run IDs, served the original exports, and rejected live write requests. A mobile browser test also verified the default comparison, decision inspector and repeated archive inspection. See the [deployment guide](deployment.md) for the workload command.
