# WorldFork system audit

## A. System overview

WorldFork runs paired customer-support experiments against the same fictional airport scenario. React and TypeScript render comparisons, archived runs and evidence. FastAPI validates configurations and queues work. A single asynchronous worker calls Bifrost and Ollama through the Python or LangGraph adapter. The deterministic engine owns booking, capacity, compensation and consent. SQLite records snapshots, decisions and scores. The replay container verifies bundled traces at startup, imports them into temporary SQLite storage and serves a read-only interface.

The audit started at commit `78eb76e`. It covered the app, engine, adapter boundary, worker, storage, evidence tools, CLI, Docker build and CI definition. Tests that changed run state used local synthetic data or temporary databases.

## B. Findings and C. Implemented fixes

| Severity | Area | Root cause and impact | Implemented change |
| --- | --- | --- | --- |
| High | Live API | CORS alone left the bodyless cancellation endpoint reachable from a foreign origin. The API also accepted arbitrary Host headers. | Reject foreign hosts and foreign origins on live mutations. Retain documented localhost browser and CLI access. Serve replay with its own read-only configuration and hide the live API explorer. |
| High | Run lifecycle | Cancellation published a terminal status before the score was saved, letting the UI stop polling too early. Queued cancellations retained IDs in memory. A failed worker could disappear from the queue while its row still looked active. | Save the finished event, snapshot and score in one transaction. Keep active runs pollable during cancellation. Clear task state on exit and flag unexpected unfinished workers as interrupted. |
| High | Evidence verifier | Trace identity, terminal event results, model-attempt links, source hash keys, public action menus and queue guidance were incompletely checked. Large forged ticks could trigger unbounded advancement. | Require the source keys and bounded ticks before replay. Bind events to their run and terminal result. Reconstruct the public menu, guidance and injected inventory, and check ordered attempt links. Require complete links for the frozen matrix. |
| Medium | Gateway | Malformed upstream token counts could crash result accounting. HTTP error text could embed the configured gateway URL in the trace. | Treat invalid counts as unknown and report sanitized status or transport errors. The health response omits the gateway URL and probes the configured gateway. |
| Medium | API input and queue | Forks bypassed the 30-run queue cap. Repeat seeds could exceed the validated range, and event offsets could overflow SQLite integers. | Apply the same queue cap to every creation path. Validate seed expansion and the event offset range before enqueue or SQL. |
| Medium | Archive and startup | App startup waited for a large archive payload containing full snapshots and attempts. An archive failure prevented valid saved links from opening. | Provide an opt-in archive summary and load it independently. Fetch run details on selection. Preserve the full list and export contracts and provide an archive retry. |
| Medium | Live UI | A restored run could submit a model missing from the installed list. A rejected launch could replace the single-run layout before a pair existed. | Restore only installed model choices and switch the comparison view after a successful launch. |
| Medium | CLI | An HTTP failure partway through a matrix left acknowledged runs queued. One failed cleanup request could prevent later cancellations. | Request cancellation for all acknowledged, outstanding runs on HTTP failure or interrupt, and report any unconfirmed cancellations with the manifest path. |
| Low | Replay UX | Opening a deep archive row could leave the new run offscreen. Fault details existed in exports but were missing from the inspector. | Return focus and scroll to the opened run. Show fault visibility and actual versus displayed inventory when recorded. |

The source compatibility exceptions in the verifier pin exact historical and audited runner and gateway digests. Archived exports and manifests were preserved. All 47 published checksums matched.

## D. Testing results

- Baseline **36 tests passed**. Final suite **51 passed** with **77% combined statement and branch coverage** for the Python package. Ruff, the TypeScript/Vite build and the Docker checks stage passed.
- The verifier checked **30 episodes**, **1,302 actions** and **1,308 attempts**. Tests rejected altered identities, scores, source hashes, ticks, attempts, action menus and queue guidance.
- Chromium replay checks passed at **1440, 390 and 320 px**. They covered playback, focus, archive navigation, export and fault inspection. Controlled HTTP failures verified archive recovery, model fallback and preservation of the current view on a rejected launch.
- A real Bifrost/Ollama smoke returned a valid tool action with measured usage. A live pair recorded one injected timeout per world and zero committed policy violations. The live cancellation check preserved the active run's partial trace and left the queued run unscored.
- The nonroot replay container built, served the full evidence set with a read-only root filesystem, and passed the same deployment check after restart.

## E. Performance

Both archive paths were tested against the same replay process with gzip. Each path was sampled in three interleaved 100-request trials at eight concurrent clients. The mixed workload used 25 requests each for the archive, run detail, events and export. The table shows the median of the three per-trial values.

| Metric | Full archive path | Summary path used by the browser |
| --- | ---: | ---: |
| Archive wire body | 101,090 bytes | 2,298 bytes |
| Archive p95 | 225.90 ms | 111.93 ms |
| Mixed workload throughput | 51.6 requests/s | 81.7 requests/s |

The archive response transferred 97.7% fewer bytes. Latency and throughput reflect a short local test with concurrent local activity. Live inference remains serialized and continues to dominate live episode time. The archive query is limited to 100 rows and the event cursor uses the SQLite primary-key index.

## F. Security assessment

The live host and origin regression checks block the reproduced cancellation path. Replay returns HTTP 405 for mutation requests and omits live API documentation. SQL inputs are parameterized, and the archive column selection is fixed. The frontend renders trace fields as text. The application has no upload surface or end-user sessions. The dependency scans reported zero known advisories across the npm audit and 44 pinned Python packages. That scan covered package advisories and did not include a separate operating system image assessment.

## G. Production readiness

The verified replay image is suitable for serving this synthetic evidence behind a host's HTTPS ingress. Its filesystem can stay read-only and its temporary database is rebuilt from verified files on restart. The live service is intended for a single local operator with one worker. Horizontal workers would need a durable queue and coordinated database ownership.

## H. Remaining action items

- Public live operation requires authentication and authorization, queue and request limits per user, a durable worker, monitoring and a data retention policy.
- A public replay deployment still needs an ingress capacity test. The local benchmark does not measure public traffic or tail latency over the network.
- Add browser regression checks to CI if maintaining the interface beyond the hackathon. The current workflow validates the simulator, frozen evidence and replay container. Live tests require a running Bifrost/Ollama stack and a supported local model.
- Independent agent integrations must stop before executing tools outside the simulator. New models and scenarios need their own validation and are separate from the frozen pilot.
