# WorldFork implementation specification

Status: selected for implementation by the user on November 5, 2026. This is the authoritative plan; earlier idea files are background. Build days: November 6–7, Sri Lanka time; work can begin now. Prototype deadline recorded by organizer: November 15; exact cutoff still requires checking. Target submission November 14. No assumption that post-deadline code changes are permitted.

## 1. Product and acceptance

WorldFork is a local, shared-world benchmark for customer-support agents. Six fictional passenger parties pursue different goals after a cancellation. Support agents act through real simulator tools. Their choices change others' options. Users compare worlds with the same initial conditions, inspect each decision and rerun controlled interventions.

One-line pitch: "One agent can solve a ticket. Can a population of agents resolve a crisis?"
Research question: Does a support strategy that considers shared constraints change collective outcomes relative to case-by-case service, under equal budgets?
Claim boundary: measured synthetic outcomes, not predictions of real passengers or airline operations. No guaranteed strategy winner or award. All characters, rules, compensation and schedules are fictional.

Release acceptance:
- [ ] Working local app, original core implementation, public-ready repository and setup.
- [ ] Six passenger parties, three alternatives, explicit private constraints and real shared capacity.
- [ ] At least two independent execution integrations: plain Python and LangGraph.
- [ ] Strategy and framework are separate settings. Same strategy available through either integration.
- [ ] Both strategies receive the same tools, policies, visible information and budgets.
- [ ] World forks start from the same scenario, arrival order and exogenous events.
- [ ] Compare normal runs and controlled faults with multiple repeats.
- [ ] Record success, steps, tool calls, tokens, cost and elapsed time with full traces.
- [ ] Independent deterministic scoring; no model judge deciding whether bookings succeeded.
- [ ] Recorded demo, README, architecture, results/limitations and AI-use disclosure.

## 2. Challenge compliance

Primary: statement 02, customer-support agent benchmarking. Source: local "Build a Benchmarking Platform for AI Agents Not Just Models.pdf".
Framework independence: versioned adapter protocol wraps normal agent invocations and environment tools; no requirement to rewrite their internal decision logic. Demonstrate plain-code and graph implementations; document configuration steps and limitations rather than claiming all frameworks work automatically.
Consistent evaluation: same scenario snapshot, tools and declared budget; every action logged.
Repeatability: three independent repetitions per published cell; disclose small sample size and nondeterminism.
Failure testing: model unavailable, tool timeout and misleading tool observation.
Inspection: compare outcomes and drill into chronological observations/actions/results.
Bifrost: real gateway for every live model call. Collect our own tool/agent traces because gateway logs alone cannot describe world actions.
Technology ambiguity: local PDF footer says integrate Bifrost + Tavily; user reports single-track submissions are allowed. Implement Bifrost first. Reserve a bounded Tavily scenario-evidence importer if both are required or credits are available; do not claim statement 05/06 compliance from a decorative search call. Confirm current form requirements before submission.

## 3. Scope tiers

P0: deterministic simulator; typed tools and consent; generic adapter; both frameworks and strategies; actual Bifrost/Ollama inference; bounded scheduler; snapshots/forks; persistent event traces; deterministic scorer; required fault cases; repeated comparison; readable 2D UI; setup/tests/demo.
P1: mid-run fork; evidence importer; additional scenario; improved animation; richer statistical intervals.
Out: real bookings, financial trading, real personal data, web browsing by passengers, stock forecasts, 3D airport, model training, large autonomous swarms, user accounts, billing, cloud deployment, open-ended tool execution.
Never cut capacity/consent enforcement, repeatability, framework demonstration, metrics, failure testing or truthful traces to add visual effects.

## 4. Concrete world: Harbor Airport

Time is logical ticks, not real wall time. All arrivals below are same-day synthetic local times. Party is the unit of negotiation; people is the unit of seats. Six parties contain seven people.

| Alternative | Arrival | Capacity | Initial allocation |
|---|---:|---:|---|
| E: early flight | 12:00 | 3 | One seat already booked by P5 |
| L: late flight | 18:00 | 3 | Empty |
| R: rail transfer | 16:00 | 2 | Empty |

| Party | People | Hard requirements | Private acceptance terms |
|---|---:|---|---|
| P1 Mira | 1 | Arrive by 13:00; flight | E only |
| P2 Arun & Nila | 2 | Same departure; arrive by 17:00; flight | E only; all-or-none booking |
| P3 Leo | 1 | Arrive by 20:00; flight | E accepted; L accepted with 40 credits |
| P4 Sam | 1 | Arrive by 17:00; no additional payment | E or R; R accepted without voucher |
| P5 Jules | 1 | Arrive by 20:00; flight; initially E | Keep E, or voluntarily move to L for 40 credits |
| P6 Dani | 1 | Arrive by 19:00 | E/L/R accepted without voucher |

Compensation pool: 80 integer credits; each offer capped at 40. No money is collected. Credits are fictional units, not currency or legal entitlements.
Initial queue: P3, P4, P1, P2, P5, P6. Every initial message says the general request and party size; detailed deadlines/modes/compensation thresholds require questions. P5 says they have an existing E booking and are open to discussing alternatives; nobody silently releases it.
A feasible full allocation exists: E=P1+P2 (3 people), L=P3+P5 (2), R=P4+P6 (2), total vouchers=80. This is a scenario fixture, not the scripted agent outcome.
A local exact enumeration oracle validates feasibility and computes the maximum achievable satisfied people under the declared rules; it cannot supply an answer to the support agent.
Case-by-case choices can consume scarce E seats early. Coordinated choices might reserve E for constrained parties and negotiate changes. Neither outcome is forced.

## 5. Agent roles and information boundaries

Passenger state: own hard constraints, acceptable offers, current booking, last few messages and any offers made to them. No access to others' private profiles, oracle results or desired ending.
Support state: public case summaries, revealed answers, live tool results, fictional policy, own action history. Neither strategy receives the private ground-truth table directly.
Benchmark observer/scorer: full state for validation and scores, never included in agent prompts.
Operator UI: may reveal private goals in an explicitly labeled evaluator view; cannot feed the displayed truth into a live run.
Passenger speech: model-generated when enabled; structured facts always come from the fixture. Offer acceptance is constrained by the passenger's declared contract, so a passenger hallucination cannot redefine evaluation ground truth. Support decisions remain autonomous.
Modes: scripted passenger responses for reproducible support-agent comparisons; optional LLM passenger wording/soft decisions for the showcase. Label mode in every run. LLM passenger experiments cannot be silently pooled with scripted runs.
Private acceptance predicates are executable simulation assumptions. They are not calibrated human psychology.

## 6. Tool and transaction semantics

Tools are typed Python functions exposed identically to both adapters. Unknown tools, party IDs, alternatives and extra fields are rejected. No shell/browser/file tools are available to an agent.
- list_cases(): public summaries and known constraints only.
- ask_question(party_id, topic): topic in deadline/mode/compensation; returns canonical answer, records disclosure. Repeated questions are legal but consume a step.
- list_options(): actual available capacity and synthetic schedule. Can be faulted; scoring uses true state.
- get_booking(party_id): actual booking and version.
- propose_offer(party_id, option_id, voucher): attempts an all-or-none provisional hold. Evaluates passenger consent against own contract and records accepted/rejected status. Does not remove old booking.
- commit_offer(offer_id): atomically validates accepted, unexpired consent, hold capacity, expected booking version and budget, then replaces old booking and spends voucher.
- withdraw_offer(offer_id): releases only that provisional hold and any reserved compensation.
- finish(reason): ends the support session, not a claim of successful resolution.

Offer lifecycle: proposed -> accepted/rejected -> committed/expired/withdrawn. IDs minted by the environment, never by the model. At most one active offer per party. Lease lasts three logical ticks. Expire before processing the action at expires_tick. Rejected offers hold nothing. Hold compensation alongside seats, so concurrent accepted offers cannot oversubscribe budget. Committing is idempotent by offer ID and returns the original receipt.
A move counts old occupied seats and target held seats until atomic commit; only then releases the original booking. Staying on the existing option consumes no extra seats. An unaccepted proposal cannot mutate a booking. Tool errors never silently apply a partial update.
Record attempted invalid operations separately from actual policy violations; a safely rejected request is not a completed harmful act.
MVP simulator uses single-writer state transitions, so logical interleaving is explicit and reproducible without requiring parallel LLM inference. This does not claim database concurrency/load testing.

## 7. Scheduler and stopping

A run is one world episode, not one passenger conversation. Default horizon: 48 support decisions, including tool requests. Each decision increments logical tick exactly once. Tool calls do not move time a second time. Passenger response generation does not advance logical time.
At start of each tick: apply scheduled exogenous events, expire holds, then build observation. Policy must describe the same schedule semantics to both agents.
The support agent chooses party and action. Case-by-case strategy prioritizes first unresolved party; coordinated strategy considers known cross-party constraints. Tools and initial information remain equal.
Limits: 48 support decisions; 64 total model attempts; 30,000 observed input+output tokens; 180-second per-model HTTP timeout; 15-minute wall clock per episode initially. These are configurable safety caps, not measured runtime predictions. Tune after a smoke measurement and freeze for published comparisons.
At most one format-repair call per decision; all attempts count. No automatic fallback to a rule-based solver during scored LLM runs.
End states: completed, exhausted, timed_out, cancelled, agent_error, simulator_error. Finish when all hard constraints are satisfied, agent calls finish, or a cap is reached. Passenger errors that corrupt fixture semantics mark simulator_error, not agent failure.
One active local model request globally; compare worlds sequentially. Live screen may show two recorded worlds at once, clearly labeled playback.

## 8. Strategy vs framework

Strategy S1: case-by-case resolution; first unresolved case, discover needs and propose feasible options. A reasonable baseline, not deliberately instructed to make mistakes.
Strategy S2: shared-constraint planning; identify inflexible requests, consider alternatives and voluntarily move flexible bookings. No access to oracle/private facts, no extra model budget.
Framework F1: ordinary Python action loop.
Framework F2: LangGraph state graph with observe -> decide -> validate -> act -> observe.
Prompts/schemas/model/budgets are shared. Strategy is data/configuration, not encoded only inside one framework.
Clean comparison uses the 2x2 matrix. This separates packaged strategy differences from adapter/framework differences. Do not claim framework superiority from one variant.
External adapter contract: initialize(context), next_action(observation), observe_tool_result(result), close(); an HTTP/subprocess bridge is a documented future integration unless implemented. Register a factory; do not hard-code framework imports into the simulator. Demonstrate how an existing generic tool agent can be configured with these tools and instrumented through a wrapper.

## 9. Data contracts

Pydantic is the canonical schema source. Frontend receives generated/OpenAPI-aligned types or an explicitly mirrored small contract with roundtrip fixtures.
Scenario: schema_version, id, version, label, public_policy, alternatives, parties/private profiles, initial_bookings, compensation_budget, arrival_order, exogenous_events.
RunConfig: scenario_id/hash, framework, strategy, passenger_mode, model identity/digest, decoding config, seed, faults, limits, prompt/tool schema hashes.
WorldState: tick, bookings, holds, offers/consent receipts, revealed facts, budget_available/reserved/spent, closed/cancelled routes and status.
Action: tool name and schema-validated arguments. Optional one-sentence rationale stored as a declared explanation, not proof of private chain of thought.
Event: monotonically increasing seq, run_id, tick, timestamp_utc, type, actor, action/request IDs, payload, elapsed_ms, state_hash_after.
ModelAttempt: attempt ID, actor role, configured/actual model if available, start/end, status, prompt/completion tokens, usage_source, error/fault tag. Do not log auth headers.
Result: terminal status, per-party outcomes, aggregate world metrics, operational metrics, faults delivered/not delivered, artifact hashes.
Use integer seats/credits and ISO timestamps. Never trust numeric arithmetic supplied by an LLM.

## 10. Architecture and files

Browser (React/Vite/TypeScript) -> FastAPI control/API -> run orchestrator -> adapter -> Bifrost -> Ollama. Tools return to the simulator. SQLite records events, run snapshots and results. Browser reads events and derived state.
Use Python 3.12 through uv; already installed locally. Node 24 is available. Prefer native Bifrost; Docker is installed but daemon was stopped during inspection. Starting Docker later is authorized if needed. Do not change the global Python installation.
Use local-only bind addresses. Planned ports: UI 5173, API 8000, Bifrost 8080, Ollama existing 11434. Check before binding; do not stop unrelated processes.
Dependencies: FastAPI, uvicorn, pydantic, httpx, langgraph, pytest; React, Vite, TypeScript, lucide-react. Add only justified dependencies. No Redis/vector database/embedding model needed.
Pin tested dependency versions in uv.lock and package-lock.json. Pin Bifrost binary separately from its npm installer package; npm package version and transport version are not interchangeable.

Proposed layout:
- backend/worldfork/{models,scenarios,engine,scoring,store,gateway,agents,runner,api,cli}.py
- backend/tests/{test_engine,test_scoring,test_faults,test_adapters,test_api}.py
- frontend/src/{App,api,types}.tsx/ts; styles.css; components only when useful.
- scenarios/harbor-v1.json; policies/harbor.md
- config/bifrost.example.json; scripts/dev.sh; .env.example
- artifacts/ runs ignored; curated results under examples/results after inspection.
- README.md; docs/{architecture,evaluation,demo,limitations}.md
- WORLD_FORK_IMPLEMENTATION_PLAN.md and BUILD_STATUS.md

## 11. Gateway integration

First verify real chat request, structured action format and usage mapping through Bifrost to llama3.1:latest. Do not treat direct Ollama success as gateway integration success.
Use Bifrost's OpenAI-compatible chat endpoint with the configured provider/model name verified in setup. Native JSON/schema/tool support must be tested against this actual model/gateway pair. Prefer one constrained JSON action per turn; validate locally. A single explicit format repair is permitted and measured.
Start with a 4K context target and output cap around 192 tokens; confirm provider-specific settings forwarding. Keep schemas concise and observations structured. Record actual options that reached the provider where verifiable.
Use llama3.1 8B for support and optionally passenger wording, sequential requests and a loaded model to avoid swapping. Do not automatically download a larger model. If reliability is inadequate, first simplify schemas/context; then discuss a suitable replacement/download.
Bifrost config isolated under project-local runtime directory. No overwriting the user's existing gateway configuration. No API keys required for local Ollama, but gateway access settings must still be explicit. Cache disabled for scored model completions; record any unavoidable provider prompt caching separately.
Log run/attempt correlation IDs. Count usage from actual completion responses; if missing, record unknown, not zero. Gateway logs are secondary reconciliation evidence.

## 12. Persistence, API and replay

SQLite tables: runs, events, model_attempts, comparisons, snapshots. Store scenario/config/result JSON and hashes. Foreign keys enabled. Persist each action, resulting state snapshot and event in a transaction. One orchestrator owns a run's mutable state.
API proposed:
GET /api/health; GET /api/scenarios; GET /api/scenarios/{id}/public
POST /api/runs; GET /api/runs; GET /api/runs/{id}; GET /api/runs/{id}/events?after_seq=N
POST /api/runs/{id}/cancel; POST /api/runs/{id}/fork
POST /api/comparisons; GET /api/comparisons/{id}
GET /api/runs/{id}/export
POST /api/benchmarks for a bounded local matrix, or CLI equivalent for first release.
Use background worker with a global async semaphore/queue. Return queued run IDs immediately. Validate allowed run options. Cancel cooperatively between actions and cancel an in-flight request; retain cancelled trace. Restart marks unfinished runs interrupted; do not falsely mark them completed.
Poll events initially every 1 second with after_seq; SSE is optional if polling is adequate. Apply events once by seq; never trigger model calls from UI renders.
Replay derives UI from stored snapshots/events with no model calls. Initial-state fork is P0. Mid-run fork requires cloned world plus both agent/passenger memory and exogenous schedule cursor; omit rather than implementing a misleading partial clone.
Export JSON includes manifest, scenario and config, events, attempts and score. Redact secrets. Recorded replay and live execution have distinct persistent labels.

## 13. Fault design

Faults are part of RunConfig; injected at named logical ticks or named environment events, not ambiguous wall time. Record whether trigger actually occurred.
F1 model unavailable: at first support decision return one synthetic HTTP 503 from the test transport wrapper before a real request. Agent gets a clear failure/retry outcome. Label as injected fault, not an observed Ollama outage. A bounded retry may recover; count every attempt.
F2 tool timeout: first list_options after tick 8 returns a timeout without mutation. Caller can retry or query alternatives. No real sleep needed. Record attempted and executed actions separately.
F3 misleading observation: first list_options after tick 8 reports E availability one seat higher than ground truth. Booking engine still enforces actual capacity and returns conflict if needed. Log evaluator-only true observation and agent-visible corrupted observation in separate fields.
Each fault fires at most once, and does not grant the agent evaluator-only annotations. No destructive effects outside the local simulator.
For adaptation studies agents may retry at most two transport errors, with all calls counted. Timeouts after mutation are outside MVP to avoid an unimplemented ambiguous-commit protocol masquerading as a correct experiment.

## 14. Scoring and statistical reporting

Per party: people, final route, consent receipt, hard constraints met, compensation, number of changes, disclosures, rejected/invalid action attempts. Existing valid P5 booking counts, but report initially satisfied and newly satisfied separately.
World: satisfied people /7 and parties /6, hard deadline/mode violations, unresolved people, seats used, compensation spent, resource utilization per route, invalid attempts and committed policy violations.
Oracle: enumerate final option/no-resolution assignments for six parties under capacities and budget, including conditional acceptance/move terms. Report maximum satisfied people and achieved gap; document that this is a terminal allocation upper bound, not a proof that an agent could discover the sequence within its budget. Verify a witness sequence with the engine.
No weighted universal fairness score. Show outcomes by explicit constraint category. Always show raw counts.
Operational: support vs passenger vs total model calls/tokens/time; environment tool calls; logical steps; run wall time; retry/repair counts; terminal status. Wall time is not equal to summed model times when concurrency is later introduced.
Local provider API cost: 0, basis=local_ollama. Electricity/hardware costs unmeasured. Missing usage fields remain null and reduce coverage; no fabricated dollar savings.
Pilot matrix: clean 2 frameworks x 2 strategies x 3 repetitions =12 episodes. Fault matrix: plain Python x 2 strategies x 3 faults x 3 repeats =18 episodes. Total target=30; run overnight/background only with visible progress and cancellation. Estimate runtime after first episodes, not from a tiny readiness probe.
Minimum defensible release if runtime is excessive: clean 12 episodes + 3 faults x 1 declared strategy x3 repeats=9 episodes, total21. Disclose reduced fault coverage rather than silently claiming the full matrix.
Choose fixed seeds before running, save all runs including failures. Temperature/config identical. Seeds do not guarantee deterministic generations. Avoid tuning on published evaluation cases; label the main illustrative fixture a development scenario, and include at least one separately defined held-out variant if making generalization claims.
Compare raw 3-run outcomes with ranges; three repeats support a pilot, not strong statistical significance. Do not publish a selected best run as the aggregate.
Counterfactual language: paired synthetic experiment, conditional on scenario assumptions. No real-world causal/behavioral forecasting claim.

## 15. UI specification

Design intent: an airport operations board with clear human consequences, not a chat-wall. Desktop-first at 1440x900, usable down to 390px. Dark navy/ivory base, teal route confirmations, amber pending, rose failures; status always includes text/icon. Respect reduced motion and keyboard focus.
Top: WorldFork, selected fictional scenario, live/replay badge, gateway status, New comparison.
Setup: scenario, model, strategy/framework A+B, fault preset, repeat count, estimated limits. Advanced decoding is collapsed. Explain logical simulation and fictional assumptions in short text.
Main compare: two world panels, each with route capacity bars and passenger party cards. Shared timeline below. On narrow screens stack worlds and retain comparison header.
Passenger card: name/party size, request, known deadline/mode, state (waiting/offered/booked/unresolved), route and voucher. Unknown private facts remain unknown in normal run view; evaluator reveal is labeled.
Inspector: selected event's exact observation, action arguments, validated tool result, model identity, timing and token usage; no hidden-reasoning claim. Follow causal references (offer -> acceptance -> commit), not speculative causal attribution.
Run states: queued, loading model, running, finished, budget reached, interrupted/error, cancelled. Never leave a spinner indefinitely; show last event and timeout/cancel action.
Result panel: raw resolved counts, oracle upper bound, budget, steps, tokens/time/cost basis, fault delivery, replay/export. No invented score or marketing claim.
Playback: play/pause, seek by event, 1x/2x/4x, jump to committed change and keyboard controls. Animations reflect actual events only. No fabricated passenger quotes.

## 16. Verification

Engine tests: conservation across holds and bookings; party all-or-none; no duplicate booking; move retains old booking until commit; consent required; rejected offer no mutation; voucher reservation/spend conservation; stale/expired offers rejected; same commit idempotent; unknown IDs/schema rejected; no state leakage between runs.
Scoring: known optimal witness scores7/7; known partial fixture gives expected counts; no booking and late flight fail correct predicates; initial satisfaction separated; oracle matches exhaustive small controls and cannot leak to prompts.
Scheduler/faults: ticks advance once; events/expiry order fixed; fault fires once; misleading observation cannot corrupt true inventory; timeout no mutation; cancellation persists; caps stop loops; model format repair bounded and counted.
Adapters: same tool contract and scripted action sequence produces same state through both runners; framework and strategy are orthogonal; actual LangGraph path executes (not a renamed plain loop); missing usage remains unknown; failed attempts retained.
Persistence/API: run creation validation; polling seq monotonic/idempotent; exports roundtrip; crash/interrupt status honest; initial fork isolation; model requests not made during replay.
Integration gates: actual Bifrost->Ollama call; actual structured action parse; real multi-party run; one run per framework; controlled faults; complete comparison; pilot matrix results.
UI: verify at desktop and narrow viewport, keyboard navigation, contrast and non-color statuses, no clipped labels, error/empty/loading states, replay matches exported ledger. Use browser tools available at implementation time; screenshot inspection before calling UI complete.
Avoid tests that merely duplicate implementation; focus on invariants and failure boundaries.

## 17. Delivery sequence and time budget

Effort estimates are focused engineering hours, not guaranteed calendar durations. Reserve time for integration failures. Do not build every feature simultaneously.
0. Plan/manifest/status: complete now; reader review before treating the plan as fixed.
1. Scaffold and native gateway smoke (1–2h): uv3.12, backend/frontend skeleton, real gateway call, model action format and token accounting. Gate: /health reports actual components; smoke JSON saved.
2. Simulator and oracle (2–3h): fixture, typed tools, transactions, invariants and witness sequence. Gate: meaningful engine/scorer tests pass.
3. Agent loop and second adapter (2–3h): LLM action contract, passenger disclosure, strategy configs, step limits, usage. Gate: two framework runs mutate actual state with traces.
4. Runs/forks/faults/storage (2–3h): queued API, snapshots, cancellation, replay/export and all fault classes. Gate: isolated comparison and honest fault records.
5. Visual compare (3–4h): route board, parties, inspector, event playback and results. Gate: usable local UI against real API, not mock data.
6. Evaluation and submission pack (2–3h plus unattended inference): pilot, errors, honest results, README, architecture and recording. Gate: clean-start commands, artifacts, deck outline and submission checklist.
Total estimate:12–18 focused hours plus inference and contingency. Two days is tight. If integration overruns, reduce scenario count/polish/population before removing required benchmark functionality.
Day1 stop condition: complete real episode and two adapters. Day2 stop condition: complete comparable/faulted/repeated runs, readable UI, reproducible setup and demo artifacts.

## 18. Demo and judging

Three-minute narrative:
0:00–0:20 show six parties, seven people, limited routes and conflicting goals.
0:20–1:10 play observed case-by-case run; show actual decisions and consequences.
1:10–2:00 fork same world under another design; reveal changes, without promising which wins.
2:00–2:30 show exact tool/action evidence and measured cost/time, then one fault reaction.
2:30–3:00 show repeated results, framework coverage and limitations.
Creative style: airport departure-board typography, split-screen timelines and a visible "same starting world" stamp. No synthetic claim that a real airline was tested.
Keep full unedited traces. Label condensed playback and recorded gateway calls. Have a recording backup for live hardware/network issues.
Judging evidence: innovation=shared-world question and inspectable forks; execution=real tools/gateway/invariants; impact=predeployment support testing; AI=independent role state and decisions; UX=clear visual consequences; potential=adapter API and scenario extension, described as future unless implemented.

## 19. Documentation, provenance and release

README must contain problem, scoped solution, fictional assumptions, installation, exact launch commands, model prerequisites, both framework integrations, tool contract, AI/Bifrost/Tavily roles, test/evaluation commands, measured results, demo instructions, limitations and reused-library licenses.
Public source prepared only after checking no secrets/private machine identifiers/runtime databases. User authorized building; do not publish a repository or send organizer messages without explicit instruction.
Keep dated Git commits during hackathon; separate reused frameworks from original core. Existing resource PDFs are organizer inputs; do not automatically redistribute them in a public repo without checking rights. Runtime traces with fictional data may be curated after review.
Required submission: working demo, repository, project/problem/AI/tool description, pitch deck and video if current form requires. Deployment optional according to supplied announcement. User joins/checks Discord as required; WhatsApp does not supersede that written rule.
Ask user only for actual blockers: Tavily credentials if required, unavailable account setup, branding preference if it changes work, or final publishing/submission action. No need to ask for routine local edits, dependencies or starting Docker (already authorized).

## 20. Known risks and responses

- Local model malformed actions: concise schema, one repair, count failures; do not fake actions.
- Slow inference: one loaded model, bounded context/turns, scripted passenger mode, recorded playback.
- Baseline fails even simple cases: reduce task complexity before interpreting collective results.
- Scenario favors coordinated design: publish fixture and oracle; retain a scarcity/control variant and equal budgets; report null/worse outcomes.
- Shared-state bug mistaken for intelligence result: independent invariant tests and raw ledger inspection first.
- Framework independence superficial: real graph invocation plus documented adapter wrapping and generic tools; do not claim unsupported integrations.
- Tiny sample overclaimed: raw counts, all terminal outcomes and pilot label.
- Technology eligibility ambiguous: reserve bounded Tavily importer; user confirms current submission requirement before final entry.
- Feature creep: P0 gates before P1; keep the film honest and the world small.

## 21. Technical references verified during planning

- https://docs.getbifrost.ai/providers/supported-providers/ollama
- https://docs.getbifrost.ai/quickstart/gateway/setting-up
- https://docs.langchain.com/oss/python/langgraph/overview
- https://docs.ollama.com/api/usage

These support integration choices, not a claim that a local Bifrost installation has already passed. Exact versions/configurations will be recorded after a successful smoke test.

## 22. Reader-review resolutions (before implementation gates)

- Baseline uses only public state; after two unsuccessful actions on a blocked case it defers that case and visits the next case, revisiting after a booking changes. Already-booked parties remain contactable. No scorer predicate chooses its next case.
- Proposal with an active offer rejects. Booking version is captured on proposal. At tick10 a proposal expires at tick13, before tick13's action; committing at tick12 is valid. Compensation already spent is irreversible. Same-route top-ups are rejected. New moves use fresh consent terms; previous vouchers are sunk and count toward total spend. Oracle assumes minimum spending for final assignments and is explicitly an upper bound.
- Fault tables show configured and actually exposed denominators separately. At least one delivered trace per fault class is a release gate; three exposed repeats are required for a per-fault recovery-rate claim. Additional exposure runs are separate, not silently substituted into the fixed matrix.
- Framework-independence claim is limited to the implemented adapter contract and demonstrated integrations until a separately runnable existing generic-agent wrapper is demonstrated. This remains a release requirement, not an automatic consequence of two purpose-built loops.
- Six parties remain P0. Cut polish, optional evidence import and extra scenarios before reducing this fixture. A second scarce fixture is conditional on generalization claims. Evaluation inference time is additional to development time; 21 episodes could take up to5.25h at the configured wall cap.
- Model observations contain current structured state plus the last six action/result pairs; no unbounded transcript. Record actual usage and measure a full episode before freezing the total-token cap. Initial30000-token limit may need raising equally for all cells; do not truncate decisions silently.
