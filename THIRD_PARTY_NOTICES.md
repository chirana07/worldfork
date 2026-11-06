# Third-party components

WorldFork's original application code is distinct from these existing components. Dependency versions are pinned by `uv.lock` and `frontend/package-lock.json`; dependencies, model weights and the Bifrost binary are obtained separately during setup.

| Component | Tested version | Declared license |
|---|---|---|
| Bifrost transport | 2.4.0 | Apache-2.0 |
| Bifrost npm launcher | 1.6.3 | See upstream package |
| LangGraph | 1.2.20 | MIT |
| LangChain Core | 1.7.6 | MIT |
| FastAPI | 0.162.0 | MIT |
| Pydantic | 2.14.3 | MIT |
| HTTPX | 0.28.1 | BSD-3-Clause |
| Uvicorn | 0.54.0 | BSD-3-Clause |
| React / React DOM | 19.3.1 | MIT |
| Vite | 6.4.5 | MIT |
| TypeScript | 5.9.3 | Apache-2.0 |
| Lucide React | 0.468.0 | ISC |
| Manrope, via Fontsource Variable | 5.3.0 package | OFL-1.1 |
| IBM Plex Sans, via Fontsource Variable | 5.3.0 package | OFL-1.1 |
| Qwen3.5:4b model | Digest recorded per run | Apache-2.0 in local model metadata |

Package license identifiers above were inspected in the installed distribution metadata. Bifrost's [upstream license](https://github.com/maximhq/bifrost/blob/main/LICENSE) was also inspected. Font license files remain in their installed packages. Transitive dependencies retain their own licenses.

Ollama is the separately installed inference service. Optional Llama3.1 and Gemma2 models have their own licenses and terms; their weights are not distributed with this source. Organizer PDFs and copied resource announcements are local reference materials and are excluded from the clean source package.

The walkthrough uses actual WorldFork UI captures, original deck content and locally generated macOS speech-synthesis narration. It contains no microphone or system-audio recording. The narrated development comparison is labeled separately from the frozen pilot. The narration and implementation were prepared with AI assistance.
