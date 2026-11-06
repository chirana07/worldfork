# WorldFork

A shared-world laboratory for customer-support agents. Six fictional passenger parties need alternatives after a cancellation; their decisions compete for actual capacity in a local simulator. Compare support strategies through plain Python and LangGraph adapters using the same model, tools, goals and budgets.

WorldFork runs live comparisons through Bifrost and includes a read-only replay of the recorded pilot. See [build status](BUILD_STATUS.md) and the [implementation specification](WORLD_FORK_IMPLEMENTATION_PLAN.md).

## Review recorded evidence

The replay server opens the real frozen comparison from bundled traces. It verifies and imports the evidence into a temporary database. This mode needs neither Ollama nor Bifrost and accepts no run-creation requests.

```sh
uv sync --frozen --python 3.12
npm ci --prefix frontend
npm run build --prefix frontend
uv run python scripts/replay_server.py
```

Open http://127.0.0.1:8001. Use the replay slider, decision inspector and archive to review the recorded runs. The source archive includes the JSON exports, measured report and deterministic replay verifier. See [evidence guide](evidence/README.md) and [archived observation provenance](docs/trace-provenance.md).

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

The smoke command must return an actual Bifrost→Ollama completion with usage metadata. It is not a simulated inference call.

## World rules

The scenario is fictional. Six parties represent seven people. Early flight capacity3 includes an existing booking; late flight capacity3; rail capacity2. There are80 fictional compensation credits. Private deadlines, transport constraints and compensation terms are revealed through questions. Accepted offers reserve seats and credits; a separate idempotent commit confirms consent. Existing bookings remain until a replacement commits. Models cannot directly mutate inventory or score their own success.

The environment enforces hard constraints, and scores outcomes from bookings and receipts. Passenger acceptance contracts are simulation assumptions, not validated human models. Scripted passengers are the reproducible baseline; an optional LLM passenger consent mode adds constrained autonomous choices and is evaluated separately.

## Reference-agent design

Framework (`python` or `langgraph`) and strategy (`case_by_case` or `coordinated`) are independent settings. Both adapters use the same gateway client and decision component. A LangGraph run invokes a compiled StateGraph; it is not a label on the Python loop.

The local reference agents select from a schema-constrained action menu derived only from public observations. It omits repeated answered questions and identical rejected offers. Proposal vouchers are discretized to0/40 credits for both designs. A common transaction policy requires resolving a live consented offer before other work. These are harness controls, not claimed model intelligence. The environment's typed tool API supports the full0–40 range. A generic message-based bridge and a real prebuilt ReAct integration smoke are included; see [adapter guide](docs/adapter-guide.md). Universal compatibility is not claimed.

## API

`POST /api/runs` accepts scenario, framework, strategy, passenger mode, model, fault, seed, temperature and budgets. Defaults are defined in `RunConfig`. `GET /api/runs/{id}/events?after_seq=N` retrieves an ordered persisted trace. Cancel, initial-state fork, paired comparison and JSON export endpoints are documented in the API explorer. Mid-run branching is not implemented.

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

The project targets the hackathon's agent-benchmarking statement. Tavily is not integrated. The live official FAQ checked November 5 permits Bifrost-only projects; see [submission requirements](docs/eligibility.md). The original core was created during the hackathon. See [related work](docs/related-work.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Organizer PDFs and copied announcements are local reference materials and are excluded from the source archive.
