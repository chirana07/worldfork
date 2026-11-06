# Evaluation protocol

## Current evidence

The simulator's feasible witness has been exercised by deterministic tests. Real inference through Bifrost and both reference integrations has been exercised. Early model/harness smoke runs are development diagnostics, including cancelled and deliberately short episodes. They are not a final benchmark or evidence of a superior strategy.

Freeze the harness revision, model digest, prompt/schema/configuration and scenario before publishing comparisons. The action-menu harness was changed during development after raw JSON and unconstrained decision failures; do not pool earlier episodes with later ones.

## Matrices

Clean:2 frameworks ×2 strategies ×3 repetitions (seeds11/29/47). Minimum faults: plain Python/coordinated ×3 faults ×3 repeats. Target faults additionally include case-by-case. Total minimum21, target30. All defaults use scripted passenger contracts; LLM passenger runs form a separate experiment.

Same model, temperature, scenario, constraints and budgets in every comparable cell. The API comparison alternates A/B order between repetitions. The CLI reverses and rotates clean-cell order across seeds and records the exact planned order. Three repeats cannot perfectly counterbalance four cells; prompt caching/warmth can still affect latency. Do not infer a framework efficiency advantage from this small pilot. Each terminal episode is exported with its full trace, scenario, source hashes and model manifest beside the pilot summary.

These are packaged strategy comparisons. Case-by-case includes a public queue hint derived from bookings and its own failed actions; coordinated uses its shared-constraint instructions. Both use the same public action menu and transaction-resolution controls. This is not an isolated prompt-only ablation. Seeds and decoding parameters are recorded requests, not a guarantee of bitwise deterministic model responses. The shared world and recorded-action replay are deterministic.

The pilot runs on a normal local desktop while documentation and media preparation also occur. Reported elapsed times use the runner's monotonic timer. Host scheduling, sleep behavior, warm context and concurrent work are uncontrolled; timings are descriptive measurements, not an isolated framework-speed benchmark.

The laptop was closed after 27 of the 30 cells had reached terminal outcomes. The three interrupted coordinated misleading-inventory configurations were rerun after resumption with the same recorded harness hashes and model digest. The evidence manifest links each replacement to its original run and preserves the partial attempts. Interpret elapsed times in light of that session boundary.

## Outcomes

Report confirmed requirements met for people and parties, initial/new satisfaction, resource allocations, compensation, invalid requests, terminal status and committed violations. Report the oracle upper bound and gap, clearly identifying its full-private-information assumption and lack of an action-sequence/budget guarantee. No invented fairness composite.

For resources: disclose all model attempts, support/passenger modes, observed input/output tokens and usage coverage, steps, tools, elapsed time and local API cost basis. Missing provider usage is unknown. Synthetic unavailable calls that never reached the provider are marked separately with zero sent tokens. Hardware/electricity costs are unmeasured.

## Faults

Model unavailable is one explicitly injected transport failure at the first decision. Tool timeout is one pre-execution failed action at/after tick8, without mutation. Misleading observation corrupts one displayed availability at/after tick8, while true capacity enforcement remains unchanged. Every trace records actual exposure; no claim that these were natural provider incidents.

Publish configured and delivered denominators separately. If a run ends before the trigger, it has no exposure. Additional exposure runs must be declared separately, not silently substituted. Keep failures and cancelled development runs; exclude cancelled runs from a completed evaluation only with an explicit declared reason and retain their evidence.

## Interpretation

Three repeats support an initial pilot only. Use raw counts and ranges; do not claim statistical significance or real-airline behavioral accuracy. The fixture and current scarcity variant were used in development and are not held-out evidence. Generalization claims require new untouched scenarios. More model personas do not establish independent human perspectives.
