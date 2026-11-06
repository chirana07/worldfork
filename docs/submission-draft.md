# WorldFork — test agents where consequences are shared

Submission copy for review. Add the public repository and video links when preparing the entry.

## Short description

WorldFork is a local experiment lab for AI support agents. It places an agent inside a fictional airport disruption where six parties compete for limited travel capacity and compensation. Every offer, consent, reservation and booking changes what remains possible for everyone else. Run two designs from identical starting conditions, inspect their decisions, and score the resulting world independently of what the agent says it accomplished.

## The problem

A support agent can produce convincing replies and valid individual transactions while leaving a worse overall allocation. Isolated question-and-answer tests miss interactions between scarce resources, private requirements, existing commitments and voluntary changes. Teams need a way to inspect those consequences before connecting an agent to real systems.

## What the prototype does

- Runs real local inference through Bifrost and Ollama using plain Python and compiled LangGraph integrations.
- Separates strategy from framework so comparisons can hold one constant.
- Gives agents public observations and tools while keeping synthetic private requirements and the scoring oracle outside the support-agent context.
- Enforces party sizes, transport capacity, consent, expiring holds, compensation and atomic booking changes in deterministic code.
- Persists actual decisions, model usage, tool results and snapshots for replay and export.
- Injects explicitly labeled model unavailability, pre-execution tool timeouts and misleading inventory observations, recording whether each intervention was actually delivered.
- Shows two worlds, their resource allocations, passenger details and complete decision ledgers in a React interface.

## What makes it different

The unit of evaluation is the resulting shared world. A successful tool call is only one event inside that world. The lab can reveal a valid booking that consumes a resource another party uniquely needs, a voluntary move that unlocks a better allocation, or repeated changes that spend compensation without increasing resolved people.

The airport is a small executable scenario, with a known feasible allocation for all seven people. That makes failures inspectable. The oracle is an evaluator with full synthetic information; it is not available to the support agent and does not prove the agent can find the allocation within its action budget.

## AI use and technologies

Ollama supplies local language-model decisions. Bifrost is the inference gateway. Python, FastAPI, Pydantic and SQLite implement the environment and trace service; LangGraph provides a real orchestration integration; React, TypeScript and Vite implement the interface. Codex assists development. Scripted passenger contracts provide the reproducible baseline. An optional LLM passenger mode allows additional constrained consent decisions and must be reported separately.

The reference agents use a public action menu and a common transaction-resolution rule. These controls are disclosed as part of the harness. They are not model capability claims. World state, consent guards and outcome scoring are application code.

## Measured pilot

The frozen pilot scored 30 scripted episodes with Qwen3.5:4b through Bifrost. Across the clean Python and LangGraph cells, case-by-case met all seven passenger requirements in 6 of 6 episodes and coordinated did so in 1 of 6. All 18 configured synthetic faults were delivered. Across those fault episodes, case-by-case completed 6 of 9 and coordinated completed 2 of 9. Every scored episode passed the deterministic replay audit. The report contains the per-seed outcomes, resource measurements and terminal states. [Pilot report](../evidence/pilot-summary.md)

The review bundle includes the full traces, source revision and model digest, an editable pitch deck, a narrated demonstration, and a read-only replay launcher. The walkthrough identifies its development comparison separately from the scored pilot.

## Limits and next steps

The current scenarios were used during development. Synthetic passengers are not validated human behavior, and results do not establish real-airline reliability. The two reference integrations work. A separately runnable generic ReAct agent has also completed a real four-decision integration smoke through the message bridge; it is not part of the reference pilot and does not establish universal compatibility. More untouched scenarios, broader agent integrations and stronger models would test how far the mechanism generalizes.

No real passengers, financial trades or travel transactions are involved. Tavily is not integrated. The live official FAQ checked November 5 allows Bifrost-only projects. The user confirmed registration and required Discord membership on November 5. Recheck final form fields before entering this draft.

## Recording hook

“Would you trust an agent that makes valid bookings—and still strands a family?”

Use this hook only alongside the retained real calibration trace that exhibits that outcome. Start with the occupied early-flight seats, reveal the party of two that cannot fit, then rewind through the actual receipts that produced the allocation. Continue with a real paired run and the measured pilot; let the observed outcome determine the narration.
