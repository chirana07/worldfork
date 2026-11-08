# WorldFork

[![Verify WorldFork](https://github.com/chirana07/worldfork/actions/workflows/verify.yml/badge.svg)](https://github.com/chirana07/worldfork/actions/workflows/verify.yml)

A shared-world laboratory for customer-support agents. Six fictional passenger parties need alternatives after a cancellation; their decisions compete for actual capacity in a local simulator. Compare support strategies through plain Python and LangGraph adapters using the same model, tools, goals and budgets.

WorldFork runs live comparisons through Bifrost and includes a read-only replay of the recorded pilot. The [Bifrost challenge alignment](docs/challenge-alignment.md) maps the organizer briefing to working features. See [build status](BUILD_STATUS.md) and the [implementation specification](WORLD_FORK_IMPLEMENTATION_PLAN.md).

## Quick start with recorded evidence

Start here to review the project. You need Git, `uv`, and Node.js with npm. The replay server verifies the bundled traces, imports them into a temporary database, and opens a recorded comparison. Replay runs without Ollama, Bifrost, or model downloads.

```sh
git clone https://github.com/chirana07/worldfork.git
cd worldfork
uv sync --frozen --python 3.12
npm ci --prefix frontend
npm run build --prefix frontend
uv run python scripts/replay_server.py
```

Open [recorded replay](http://127.0.0.1:8001). The repository includes the JSON exports, measured report and deterministic replay verifier. See [evidence guide](evidence/README.md) and [archived observation provenance](docs/trace-provenance.md).

1. Click **See the first booking** to jump to a confirmed booking and see how many seats remain. The opening comparison uses the same model, scenario, seed and LangGraph integration with different strategies.
2. Move the playback slider to see later changes. Open a decision in the ledger to check what the agent observed, what it tried, and what changed.
3. Open **Run archive** to compare repeated-run results for matching test conditions. Each design shows success, outcome ranges, steps, model/tool calls, tokens, API charge, time and fault exposure. Use **Open latest run** to inspect its decisions. The individual list contains all 30 pilot runs, including cases with injected faults. Use **Export trace** to download a run's configuration, decisions and snapshots.

To see the recorded solo planner versus team comparison, run `uv run python scripts/replay_server.py --team-demo --port 8003` after building the frontend. Open [the clean team replay](http://127.0.0.1:8003) or [the tool-timeout replay](http://127.0.0.1:8003/?a=0b2ee502-2153-413f-be2e-20b2f914fda8&b=d436a8e4-6ce5-4784-9b68-71370bb23cbe). Select a World B decision in the ledger to see the specialists' advice and the orchestrator's plan. This replay imports four verified development traces. [Release audit and judging self-score](docs/competition-audit.md)

The revised team and the 24-run release evaluation have a separate replay. Start `uv run python scripts/replay_server.py --evaluation --port 8006`, then open [the transfer comparison](http://127.0.0.1:8006). The archive contains all three seeds on both fixtures under clean and timeout conditions. The decision inspector explains when specialists were consulted and when earlier advice was reassessed. [Release measurements](evidence/team-evaluation/report.md)

Run these in a second terminal to check the service and audit the evidence independently.

```sh
uv run python scripts/check_replay_deployment.py http://127.0.0.1:8001
uv run python scripts/verify_evidence.py evidence/pilot-manifest.json
uv run pytest -q
```

For a reproducible read-only service, see the [container deployment and verification guide](docs/deployment.md) and [performance report](docs/performance.md).

## Run live experiments

Prerequisites: macOS/Linux, uv, Python3.12, Node, Ollama with `qwen3.5:4b` installed (`ollama pull qwen3.5:4b`). Llama3.1 and Gemma2 are optional local choices. The tested gateway is Bifrost transport v2.4.0, installed via npm launcher1.6.3. Docker is optional.

```sh
uv sync --frozen --python 3.12
uv run python scripts/backend.py
```

The launcher creates isolated gateway configuration under `.bifrost/`, leaves existing configuration untouched, and binds the gateway and API to loopback. It reuses already responding services and stops only processes it launched. Local gateway inference authentication is explicitly disabled in the example configuration; this is not a public deployment configuration.

API explorer: http://127.0.0.1:8000/docs
Bifrost dashboard: http://127.0.0.1:8080

```sh
uv run python -m worldfork.cli smoke
uv run pytest -q
```

Start the interface in a second terminal:

```sh
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open http://127.0.0.1:5173. The interface includes initial-world comparisons, a complete decision ledger, passenger/receipt inspection, cancellation, an archive and recorded playback. The shared-model selector lists installed supported local models; refresh after installing another model. An end-of-run summary is labeled separately from a historical replay snapshot. Saved run links restore an inspection or comparison after refreshing.

Click **Run comparison** and watch the ledger as the worlds execute in sequence. Open **Experiment settings** to change the setup or choose a fault preset. Keep the model, integration and scenario fixed to compare the two strategies. The smoke command checks an actual Bifrost-to-Ollama completion with usage metadata.

To compare a solo planner with a team, set World A to **Shared-constraint planning** and World B to **Orchestrated team**. An inventory specialist and a traveler specialist suggest actions from the same public menu. The orchestrator considers their advice and recent receipts, gives a short plan, and chooses the next action. Booking still requires an accepted offer and a successful simulator commit. Open a World B decision to see the advice, plan and receipt together. The score panel also shows model calls, tool calls, tokens, elapsed time and local API charge.

The specialists are consulted at the start, after a committed booking or after a failed action. Between consultations, the orchestrator reassesses dated advice against the current observation and action menu. Choose **Harbor · changed connections** to try the release evaluation fixture with different transport constraints, capacity and compensation. Run `uv run python scripts/evaluate_team.py` to reproduce the fixed release matrix, or add `--verify` to audit its recorded exports without inference.

For a repeat comparison, send the same scenario, model, population, framework and budgets on both sides. Use the same initial seed and request three repeats. The API advances the seed together on both sides for each repeat. Try a clean comparison first, then repeat under a controlled fault. Team calls share the run budget, so compare their resource use alongside the traveler score. The 30-run pilot is the earlier solo baseline.

## World rules

The scenario is fictional. Six parties represent seven people. Early flight capacity3 includes an existing booking; late flight capacity3; rail capacity2. There are80 fictional compensation credits. Private deadlines, transport constraints and compensation terms are revealed through questions. Accepted offers reserve seats and credits; a separate idempotent commit confirms consent. Existing bookings remain until a replacement commits. Models cannot directly mutate inventory or score their own success.

The environment enforces hard constraints, and scores outcomes from bookings and receipts. Passenger acceptance contracts are simulation assumptions, not validated human models. Scripted passengers are the reproducible baseline; an optional LLM passenger consent mode adds constrained autonomous choices and is evaluated separately.

## Reference-agent design

Framework (`python` or `langgraph`) and strategy (`case_by_case`, `coordinated` or `team`) are independent settings. Both adapters use the same gateway client. A LangGraph run invokes a compiled StateGraph.

The local reference agents select from a schema-constrained action menu derived only from public observations. It omits repeated answered questions and identical rejected offers. Proposal vouchers are discretized to0/40 credits for both designs. A common transaction policy requires resolving a live consented offer before other work. These are harness controls, not claimed model intelligence. The environment's typed tool API supports the full0–40 range. A generic message-based bridge and a real prebuilt ReAct integration smoke are included; see [adapter guide](docs/adapter-guide.md). Universal compatibility is not claimed.

## API

`POST /api/runs` accepts scenario, framework, strategy, passenger mode, model, fault, seed, temperature and budgets. Defaults are defined in `RunConfig`. `GET /api/runs/{id}/events?after_seq=N` retrieves an ordered persisted trace. Cancel, initial-state fork, paired comparison and JSON export endpoints are documented in the API explorer. Mid-run branching is not implemented.

`GET /api/benchmarks` summarizes all stored runs under matching task, model, decoding, budget and source conditions. It retains status counts, measured-value denominators and inspection links. `GET /api/runs?summary=true` lists archive metadata and scores. The full list, run detail and export endpoints retain their existing payloads. An active cancellation stays pollable until its partial score and terminal receipt are saved.

```sh
curl -X POST http://127.0.0.1:8000/api/comparisons \
  -H 'Content-Type: application/json' \
  -d '{"a":{"framework":"python","strategy":"case_by_case"},"b":{"framework":"langgraph","strategy":"coordinated"},"repeats":1}'
```

This example compares two packaged designs and is not evidence that a framework caused the result. Use the complete2×2 clean matrix to separate framework and strategy.

## Evaluation

The frozen pilot scored 30 episodes through Qwen3.5:4b and Bifrost. In clean runs, case-by-case met all seven requirements in 6 of 6 episodes and coordinated did so in 1 of 6. All 18 configured fault exposures were delivered. The full report includes per-seed outcomes, resource usage and terminal states. [Pilot report](evidence/pilot-summary.md)

```sh
uv run python -m worldfork.cli benchmark --model ollama/qwen3.5:4b
# Full target:30 episodes rather than21 minimum
uv run python -m worldfork.cli benchmark --full
```

Commit tracked changes before a frozen pilot. These commands queue sequential inference through the API worker and retain a manifest, full per-run exports, model and source identities, and resource summaries under `artifacts/`.

Three fault classes are explicit synthetic interventions: one unavailable model attempt, one pre-execution tool timeout, or one misleading inventory observation. Capacity enforcement always uses ground truth. Faults and exposure are logged; they are not represented as natural provider incidents.

Report raw resolved people/parties, terminal statuses, oracle allocation upper bound, invalid attempts, compensation, steps/tools, measured token coverage and elapsed time. Local API charge is0; electricity/hardware cost is unmeasured. Three repetitions are a pilot, not proof of real-world reliability. The base fixture and scarcity variant are development scenarios, not held-out evaluations.

## AI disclosure and provenance

Ollama provides local inference; Bifrost is the actual gateway; LangGraph supplies one orchestration integration. Passenger speech/consent may use local inference when configured. World rules, transactions, scoring, limits and persistence are deterministic application code. Codex assists implementation. No real airline, passengers, transactions or personal records are used.

The project targets the hackathon's agent-benchmarking statement. Tavily is not integrated. The official prototype instructions checked November 7 permit Bifrost-only projects; see [submission requirements](docs/eligibility.md). The original core was created during the hackathon. See [related work](docs/related-work.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Organizer PDFs and copied announcements are local reference materials and are excluded from the source archive.

## Submission media

The review package includes a three-minute silent demonstration, an editable eight-slide pitch deck and PDF, and a timed narration script for Chirana. The demo shows actual retained traces, repeated-run comparisons and measured tradeoffs. A separate narrated cut fits each scene to Chirana’s supplied audio, with updated captions. [Media sources and reproduction](docs/demo-production.md).
