# WorldFork build status

WorldFork is ready for local review. The review bundle contains the source archive, an editable eight-slide deck and PDF, a three-minute silent 1080p demo, provisional captions and a narration script for Chirana. Participant audio and final organizer upload remain pending.

The frozen pilot scored 30 episodes with Qwen3.5:4b through Bifrost. Fifteen reached full completion, ten exhausted their budget, and five stopped early. All 18 configured synthetic fault exposures were delivered. The audit replayed 1,302 recorded actions and checked 1,308 model attempts. [Pilot report](evidence/pilot-summary.md)

Three runs interrupted by the laptop closure were repeated under the frozen harness and model digest. The source archive preserves the original attempts and links them to their replacements. A one-line fix captures passenger observations before later disclosures mutate the shared state. The audit explicitly accounts for 439 affected historical observation records. [Trace provenance](docs/trace-provenance.md)

## Product verification

1. The browser launched a live Python and LangGraph comparison through Bifrost and Ollama with Qwen3.5:4b. Both runs made 48 model decisions with zero committed policy violations. They stopped at six and five of seven satisfied passengers. Both traces replayed successfully after restarting the API.
2. The browser restored a live comparison on refresh, opened the decision inspector, scrubbed the timeline, downloaded a JSON trace, and reopened a run from the archive. Cancelling an active and a queued run preserved the active run's partial trace and kept the queued run unscored.
3. A live initial-state fork recorded four model-generated passenger consent decisions. The API rejected a fork with a different scenario. Llama3.1 and Gemma2 each passed a two-step live compatibility check. Gemma2 exposed a JSON fence parsing bug that was fixed and retested with the original model reply preserved.
4. The read-only replay server serves the production frontend and all 30 pilot episodes. The mobile browser check passed after fixing a bug that cleared the decision ledger when reopening the same archived run.
5. The test suite passes 66 tests. The frontend production build, Python lint checks and deterministic pilot replay audit pass. The team advice regression is exercised through both adapters.

## Release team evaluation

The revised team consults specialists at plan boundaries and reassesses dated advice between consultations. The release matrix contains 24 verified episodes across three new seeds, two fixtures and clean/timeout conditions. The team won 7 matched pairs, lost 3 and tied 2, with 288 model calls versus 166 for solo planning. Nine of twelve configured timeouts were delivered. The replay exposes all outcomes and consultation decisions without inference services. [Release measurements](evidence/team-evaluation/report.md) · [Updated competition audit](docs/competition-audit.md)

The archive includes repeated-run summaries with strict comparison groups and links to individual runs. Its summary covers all stored records and preserves unknown usage and unsuccessful outcomes. [Challenge alignment](docs/challenge-alignment.md)

## Lifecycle tracker

| Phase | Status |
| --- | --- |
| Repository, environment and architecture | Complete for the local benchmark. [Architecture](docs/architecture.md) |
| Data, agent orchestration and application | Complete for three synthetic fixtures, reference integrations, selective specialist consultation and replay. [Evaluation protocol](docs/evaluation.md) |
| Testing, pilot and operational performance | Complete for the recorded pilot and local container workload. [Performance report](docs/performance.md) |
| Reproducible deployment and CI | Production replay image built and verified locally, including restart and browser tests. [GitHub Actions](https://github.com/chirana07/worldfork/actions/workflows/verify.yml) · [Deployment guide](docs/deployment.md) |
| Public hosting | Deferred at the user's request. |
| Public repository | [WorldFork on GitHub](https://github.com/chirana07/worldfork) |
| Final submission | Pending. [Eligibility notes](docs/eligibility.md) |
