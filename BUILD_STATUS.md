# WorldFork build status

WorldFork is ready for local review. The review bundle contains the source archive, an editable seven-slide deck, a narrated 1080p demo, a silent copy, captions and narration text.

The frozen pilot scored 30 episodes with Qwen3.5:4b through Bifrost. Fifteen reached full completion, ten exhausted their budget, and five stopped early. All 18 configured synthetic fault exposures were delivered. The audit replayed 1,302 recorded actions and checked 1,308 model attempts. [Pilot report](evidence/pilot-summary.md)

Three runs interrupted by the laptop closure were repeated under the frozen harness and model digest. The source archive preserves the original attempts and links them to their replacements. A one-line fix captures passenger observations before later disclosures mutate the shared state. The audit explicitly accounts for 439 affected historical observation records. [Trace provenance](docs/trace-provenance.md)

## Product verification

1. The browser launched a live Python and LangGraph comparison through Bifrost and Ollama with Qwen3.5:4b. Both runs made 48 model decisions with zero committed policy violations. They stopped at six and five of seven satisfied passengers. Both traces replayed successfully after restarting the API.
2. The browser restored a live comparison on refresh, opened the decision inspector, scrubbed the timeline, downloaded a JSON trace, and reopened a run from the archive. Cancelling an active and a queued run preserved the active run's partial trace and kept the queued run unscored.
3. A live initial-state fork recorded four model-generated passenger consent decisions. The API rejected a fork with a different scenario. Llama3.1 and Gemma2 each passed a two-step live compatibility check. Gemma2 exposed a JSON fence parsing bug that was fixed and retested with the original model reply preserved.
4. The read-only replay server serves the production frontend and all 30 pilot episodes. The mobile browser check passed after fixing a bug that cleared the decision ledger when reopening the same archived run.
5. The test suite passes 36 tests. The frontend production build, Python lint checks and deterministic pilot replay audit pass.

The public repository and final submission remain for user review. The project targets the Bifrost benchmarking challenge. [Eligibility notes](docs/eligibility.md)
