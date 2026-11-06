# WorldFork build status

WorldFork is ready for local review. The review bundle contains the source archive, an editable seven-slide deck, a narrated 1080p demo, a silent copy, captions and narration text.

The frozen pilot scored 30 episodes with Qwen3.5:4b through Bifrost. Fifteen reached full completion, ten exhausted their budget, and five stopped early. All 18 configured synthetic fault exposures were delivered. The audit replayed 1,302 recorded actions and checked 1,308 model attempts. [Pilot report](evidence/pilot-summary.md)

Three runs interrupted by the laptop closure were repeated under the frozen harness and model digest. The source archive preserves the original attempts and links them to their replacements. A one-line fix captures passenger observations before later disclosures mutate the shared state. The audit explicitly accounts for 439 affected historical observation records. [Trace provenance](docs/trace-provenance.md)

The read-only replay server serves the production frontend and all 30 pilot episodes, including their event and export endpoints. The current suite passes 35 tests. The frontend production build and Python lint checks pass.

The public repository and final submission remain for user review. The project targets the Bifrost benchmarking challenge. [Eligibility notes](docs/eligibility.md)
