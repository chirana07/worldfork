# WorldFork build status

Authoritative specification: WORLD_FORK_IMPLEMENTATION_PLAN.md. User selected implementation November5,2026 and delegated direct React design.

| Stage | Status | Evidence / remaining gate |
|---|---|---|
| Detailed plan | Complete and reader-reviewed | Scenario, tools, transactions, fairness, metrics, UI, tests, demo and contingency details |
| Gateway and scaffold | Working | Bifrost transport2.4.0 -> local Llama real completion, structured JSON and actual token usage |
| Simulator and scorer | Working | Capacity, consent, expiry, idempotence, budget, isolation and feasible7-person witness tests |
| Reference agent integrations | Working; calibration in progress | Plain Python and actual LangGraph performed real calls/bookings; short episodes are development evidence only |
| Runs, faults and persistence | Implemented | API queue, initial forks/comparisons, cancellation, SQLite events/export; unit/integration tests cover faults; real repeated fault pilot not yet run |
| Comparison UI | Working first iteration | Desktop/mobile inspected, actual create/cancel/replay/inspector tested; five review findings resolved; current UI review ship verdict limited to those fixes |
| Evaluation and submission | Not complete | Frozen30-episode pilot and final deck/video outstanding; generic wrapper smoke passed; official FAQ permits Bifrost-only; user confirmed registration/Discord |

Checks at this checkpoint:34 pytest tests passed; frontend production build passed; Ruff checks passed. Mechanical design detector returned no findings. After fixing concurrent store access,40 actual concurrent API read requests returned200. A short real LangGraph episode executed8 decisions with zero rejected malformed actions, one new booking and an explicitly exhausted status; it is not evidence that the overall strategy succeeds.

Development finding: the original Llama model often chose poor actions. Schema-constrained public action menus and a shared transaction-resolution policy are explicit harness controls, not model capability claims. Qwen3.5:4b downloaded and passed real gateway/schema smoke. Development calibration produced7/7 on case-by-case and5/7 on coordinated, both at seed11. It is now the default; this pair is not the repeated frozen pilot. A separate four-decision prebuilt generic ReAct integration performed real public-information tool calls. No winning strategy is claimed.

Environment: Node24; uv; local Python3.12.12; Ollama0.40.14. Docker is installed; user authorizes starting it if needed, but native Bifrost is used. Services currently run locally on5173/8000/8080/11434. Runtime artifacts/logs/databases are ignored by Git.

Important: no repository has been published and no organizer message/submission sent. All scenario people/policies/credits are fictional. Local documents and source remain in this workspace.
