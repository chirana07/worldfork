# WorldFork competition audit

**Self-score: 82/100.** The six scores below carry equal weight and sum to 49/60. This is a release review estimate. The score remains unchanged after the weakness work because evaluation breadth and agent consistency still limit the claims. No organizer score or weights are implied.

| Area | Score | Evidence and remaining weakness |
| --- | ---: | --- |
| Innovation | 9/10 | Shared seats, compensation and consent make decisions consequential for other travelers. Side-by-side scores and traces expose allocation failures and the cost of adding agents. |
| Technical execution | 9/10 | Python and LangGraph integrations, a generic adapter smoke, controlled faults, a deterministic scorer, 66 tests and verified Docker replays. New tests exercise advice reuse through both adapters and demonstrate a feasible ten-step allocation on the transfer fixture. |
| Problem and impact | 8/10 | The benchmark exposes failures that isolated tickets miss. The release adds a fixture reserved from tuning, but its evidence remains within a synthetic airport domain. |
| Use of AI | 8/10 | Real model calls through Bifrost, two advisory specialists and an inspectable orchestrator. Selective consultation skipped 150 specialist requests on the observed paths. The team still used more model calls than the solo planner and lost three comparisons. |
| User experience | 8/10 | Reviewers can inspect bookings, receipts, dated advice and consultation reasons. The archive now compares repeated-run success and resource means under matching conditions, with ranges, missing-value coverage and links to receipts. The 24-run release replay works without inference services. The three-minute silent demo covers the original pilot, revised team, repeated-run summaries and measured tradeoffs. |
| Scalability and potential | 7/10 | Repeatable paired runs, exportable traces and reference integrations provide a base. The live queue is local and serial. Other domains, models and production workloads remain untested. |

## What changed

The team consults both specialists initially, after a booking changes the allocation, or after an unsuccessful action. Between consultations the orchestrator reassesses earlier advice against fresh public observations. Advice retains its original logical tick and named action, so changing menu indices cannot reinterpret an old recommendation. The inspector explains each consultation decision.

A fixed release protocol was committed before inference. It uses three new seeds, two fixtures, clean and tool-timeout conditions, and the solo and revised-team strategies. All 24 episodes use the Python adapter, scripted passengers and Qwen3.5:4b with identical settings and budgets within each pair. Each run allows 16 steps. A timeout at tick 8 leaves up to eight later decisions. The transfer fixture changes transport requirements, deadlines, capacity, compensation and queue order. It was reserved from agent tuning before these runs and is now public evaluation data. [Protocol](evaluation.md)

## Measured results

| Measure | Solo planner | Orchestrated team |
| --- | ---: | ---: |
| Episodes | 12 | 12 |
| Mean travelers whose needs were met, including the initial booking | 2.33 / 7 | 3.25 / 7 |
| Total tool actions | 166 | 166 |
| Total model calls | 166 | 288 |
| Total observed tokens | 337,860 | 600,469 |
| Early stops | 2 | 2 |
| Committed policy violations | 0 | 0 |
| Configured timeout episodes | 6 | 6 |
| Delivered timeout episodes | 4 | 5 |
| Exposed episodes with a subsequent successful tool result | 4 | 5 |
| Exposed episodes with a subsequent booking | 2 | 5 |
| Exposed episodes successfully retrying the same timed-out action | 3 | 1 |

The team won **7 of 12 configuration-matched pairs**, lost 3 and tied 2. It reused earlier advice on **75 of 166 decisions**, skipping 150 specialist requests that the earlier consultation rule would have dispatched on those recorded paths. That request count does not establish what outcomes the earlier policy would have produced. The revised team used **1.73 times** the solo planner's model calls across this matrix.

Nine of twelve configured timeouts were delivered. Three episodes ended before the trigger and remain in the results. A subsequent successful tool, booking and exact retry are reported separately. Tool success means `ok: true`; booking requires a committed receipt. These observations do not establish restoration of a clean outcome. The per-seed table makes the exposure differences explicit. [Full release report and trace manifest](../evidence/team-evaluation/report.md)

These are short budget tests. Twenty episodes reached the step cap and four stopped early. No release episode met all seven travelers' requirements. Three seeds, one model and the same synthetic domain limit performance conclusions. Local API charge was zero. Hardware and electricity were unmeasured, and timings include normal desktop contention.

The original frozen pilot remains a separate 30-episode comparison across Python, LangGraph, two solo strategies and three controlled faults. All 47 published evidence checksums remain intact. The four earlier eight-step team demonstrations are also retained. [Original pilot](../evidence/pilot-summary.md) · [Earlier team exports](../evidence/team-demo)

## Remaining weaknesses to prioritize

1. **Plan quality and premature stopping.** The team lost two of the three clean transfer comparisons and stopped early in two release episodes. Improve the reference policy using development cases, then evaluate a new untouched fixture. Preserve these results as the baseline.
2. **Coordination cost.** Selective consultation reduces repeated specialist requests, but the team still spends more calls and tokens. Its extra resolved travelers must be weighed against that cost under each workload.
3. **Generalization and scale.** Add independent models, another support domain and broader third-party adapters before claiming general reliability. The current local serial queue bounds the deployment claim.
4. **Submission presentation.** Use the release replay to demonstrate the revised team and its mixed outcomes. The silent demo now covers the pilot and release evidence, with an eight-slide deck and narration handoff for Chirana. Participant audio and the final organizer form remain pending.

## Submission checks

The rendered official prototype instructions were rechecked on November 7. They permit Bifrost-only entries and make hosting optional. The public repository, detailed README and editable pitch deck are prepared. [Eligibility notes](eligibility.md) · [Organizer page](https://hackculture.io/hackathons/ai-global-hackathon)
