# Submission media

The current demo uses guided playback from retained real traces. On-screen context identifies the recorded pilot, release study and synthetic scope. The silent cut has no audio stream. The narrated cut uses the ten numbered audio files supplied by Chirana, with each scene retimed to its recording. `deliverables/WorldFork-demo.txt` contains the clean narration, and `WorldFork-demo-script.md` contains scene timings. The narrated cut includes captions timed from a locally transcribed and reviewed recording.

## Source scenes

The opening pair uses LangGraph, seed 29 and the clean Harbor pilot fixture. Case-by-case run `fe3b30ed-4b91-49c2-918c-383b8e2e936a` reaches 7/7. Coordinated run `68bbf46f-fe10-4342-96d3-acdbdbac47eb` ends at 5/7 with the party of two waiting. Both have zero committed policy violations. The video identifies this as one illustrative pair.

The team and fault scenes use the prespecified release seed 17. The team-advice scene shows a consultation after a booking and then an action that reuses earlier advice. The fault scene shows an actual timeout receipt and a later committed booking. Aggregate figures come from the independently verified manifests, not from the illustrative pair.

## Build tools

`scripts/record_demo.mjs` reads the tracked storyboard and source manifests, checks that both services are in replay mode, and records Chromium video without microphone or system audio. It also captures the actual UI images used in the pitch deck. Playwright is an optional media dependency. A custom Playwright module path and Chromium executable can be supplied through `WORLDFORK_PLAYWRIGHT_MODULE` and `WORLDFORK_CHROME`.

`scripts/build_pitch.mjs` exports an authoring function for the supplied presentation runtime. Its tables and architecture diagram are editable. Speaker notes cite the retained evidence. UI images show the actual app.

`scripts/build_demo.py` uses FFmpeg to assemble the recorded clips with context captions, exports the narration and timing files, and checks resolution, duration, full decode and the absence of an audio stream. It validates source evidence before assembly. It performs no speech synthesis.

```sh
# Start these in separate terminals after building the frontend.
uv run python scripts/replay_server.py --port 8002
uv run python scripts/replay_server.py --evaluation --port 8006

# Export slides 7 and 8 to artifacts/submission-build/slides/slide-07.png
# and slide-08.png using the pitch authoring runtime.
# With Playwright and Chromium available, capture actual replay footage.
node scripts/record_demo.mjs

# FFmpeg assembles the video and browser-rendered caption bands.
uv run python scripts/build_demo.py
```

The public project itself does not require the media-authoring dependencies. Build intermediates, scene clips and verification receipts remain in the ignored `artifacts/submission-build/` directory so the video can be retimed when the participant supplies audio.

Caption bands can be regenerated with `node scripts/record_demo.mjs --captions-only`. The recorder enlarges Chrome’s native window to preserve the full viewport in screencast frames. Final media must be visually inspected as well as decoded; the automated stream checks alone do not establish visual quality.

## Participant narration

`scripts/add_demo_audio.py` assembles `WorldFork-demo.mp4` from the prepared scene videos and `clip 1` through `clip 10` MP3, WAV or M4A recordings. It keeps voice speed unchanged, normalizes loudness, adds a short lead and tail, and retimes each scene to fit. It verifies a complete decode, a 1080p video stream and an AAC audio stream before replacing the output. Supplied audio files are local submission assets and are not included in Git.

The assembly expects reviewed `artifacts/submission-build/audio-transcripts.json`: an ordered list of objects with `file` and `segments`; each segment has `words` entries containing `start`, `end` in seconds and `word` text including its leading space. Transcription was performed locally with Faster Whisper; recognition text was checked against the supplied script and corrected for names and numbers. The transcript is used for caption timing. Media dependencies remain separate from the application environment.

```sh
uv run python scripts/add_demo_audio.py --audio-dir "Audio clips"
```

Narrated and silent cuts have different durations. Their caption files and timing guides must not be interchanged. Original recordings remain unchanged.
