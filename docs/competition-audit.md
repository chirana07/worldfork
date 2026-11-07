# WorldFork competition audit

**Self-score: 82/100.** The six scores below carry equal weight and sum to 49/60. This is a release review estimate. No organizer score or weights are implied.

| Area | Score | Evidence and remaining weakness |
| --- | ---: | --- |
| Innovation | 9/10 | Shared seats, compensation and consent make each decision consequential for other travelers. Side-by-side scores and traces show where outcomes diverge. The demo needs to show that consequence early. |
| Technical execution | 9/10 | Working Python and LangGraph integrations, a generic adapter smoke, controlled faults, a deterministic scorer, 55 tests, and a Docker replay. Additional third-party integrations would strengthen the framework-independence claim. |
| Problem and impact | 8/10 | The benchmark exposes allocation failures that isolated support tickets miss. Evidence comes from synthetic airport cases. Impact in other support settings is unmeasured. |
| Use of AI | 8/10 | Real model calls through Bifrost, constrained actions, and an inspectable two-specialist team. The extra calls and latency are substantial for a one-traveler gain in the short demo. |
| User experience | 8/10 | Reviewers can jump to a booking, scrub the timeline, inspect the receipt and start a verified replay offline. The recorded video covers the original pilot. Team mode is shown in the separate interactive replay. |
| Scalability and potential | 7/10 | Repeated paired runs, exportable traces and two reference integrations provide a base. The live queue is local and serial. Generalization is still limited to development variants of one scenario. |

## What the evidence supports

The frozen pilot contains **30 verified solo episodes** and **18 delivered fault exposures**. It supports a benchmark demonstration across two frameworks, two strategies and controlled faults on the configured fixture. The original exports and 47 published checksums are intact. [Pilot report](../evidence/pilot-summary.md)

The later team demonstration holds the scenario, seed 11, Qwen3.5:4b, Python adapter, scripted passengers, decoding settings and budgets fixed within each pair. Each run took eight tool steps. All four finished at the step cap with zero committed policy violations. The timeout was delivered once per world in the second pair, at the final step.

| Condition | Strategy | Travelers whose needs were met | Model calls | Tokens | Elapsed | Trace |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Clean | Solo planner | 2/7 | 8 | 17,126 | 14.9 s | [Solo](../evidence/team-demo/solo.json) |
| Clean | Orchestrated team | 3/7 | 22 | 45,132 | 131.0 s | [Team](../evidence/team-demo/team.json) |
| Tool timeout | Solo planner | 2/7 | 8 | 17,123 | 10.1 s | [Solo with timeout](../evidence/team-demo/timeout-solo.json) |
| Tool timeout | Orchestrated team | 3/7 | 22 | 45,023 | 127.5 s | [Team with timeout](../evidence/team-demo/timeout-team.json) |

Local API charge was $0 for these Ollama runs. Hardware and electricity were unmeasured. These short comparisons demonstrate the planning, booking, fault and replay paths. One seed limits performance conclusions, and injecting the timeout at the final step leaves no subsequent action to evaluate recovery. Use additional seeds, longer post-fault budgets and a held-out fixture to measure those effects.

## Weaknesses to prioritize

1. **Evaluation breadth.** The biggest credibility gain would come from testing a held-out scenario and more seeds with the same budgets. Keep the existing pilot and team demonstrations separate so the entry can support each claim with the right evidence.
2. **Coordination cost.** The team used 2.75 times as many model calls in both short pairs. To evaluate efficiency, test a version that asks specialists only when availability or disclosed requirements change, and compare scores, violations, tokens and elapsed time under matched conditions.
3. **Judge access.** The repository now includes verified clean and timeout replays for the team, with advice, plan and receipt visible. Use the team replay to demonstrate orchestration and the original video to introduce the benchmark. [Replay instructions](../README.md#quick-start-with-recorded-evidence)

## Submission checks

The challenge asks for framework independence, consistent measurement, repeatability, failure testing and detailed inspection. The original pilot covers the repeated framework and strategy matrix. The new team traces cover measured orchestration and fault inspection. The official FAQ captured on November 5 permits Bifrost-only entries, while the challenge PDF footer lists both sponsors. The public page returned only its footer during this release check. The saved FAQ supports the Bifrost-only entry. Confirm final form requirements in the organizer portal before submitting. [Eligibility notes](eligibility.md) · [Organizer page](https://hackculture.io/hackathons/ai-global-hackathon)
