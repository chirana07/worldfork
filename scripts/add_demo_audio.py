"""Fit the recorded demo scenes to participant-supplied numbered audio clips."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from build_demo import BUILD, ROOT, probe, run, timestamp


def build(audio_directory, output):
    scenes = json.loads((ROOT / "scripts/demo_storyboard.json").read_text())
    transcripts = json.loads((BUILD / "audio-transcripts.json").read_text())
    clips = {}
    for filename in audio_directory.iterdir():
        match = re.fullmatch(
            r"clip\s*(\d+)\.(mp3|wav|m4a)", filename.name, re.IGNORECASE
        )
        if match:
            number = int(match[1])
            if number in clips:
                raise ValueError(f"Duplicate clip number {number}")
            clips[number] = filename
    if set(clips) != set(range(1, len(scenes) + 1)):
        raise ValueError("Exactly one numbered audio clip is required per scene")
    destination = BUILD / "narrated"
    destination.mkdir(exist_ok=True)
    elapsed = 0
    provenance = []
    subtitles = []
    parts = []
    for number, scene in enumerate(scenes, 1):
        audio = clips[number]
        video = BUILD / f"edited-{number:02}.mp4"
        duration = float(probe(audio)["format"]["duration"])
        seconds = math.ceil((duration + 0.5) * 24) / 24
        original_seconds = float(probe(video)["format"]["duration"])
        part = destination / f"scene-{number:02}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                video,
                "-i",
                audio,
                "-filter_complex",
                (
                    f"[0:v]setpts={seconds / original_seconds:.12f}*(PTS-STARTPTS),"
                    "fps=24,tpad=stop_mode=clone:stop_duration=1[v];"
                    "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
                    f"adelay=200:all=1,apad,atrim=duration={seconds}[a]"
                ),
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-t",
                seconds,
                "-c:v",
                "libx264",
                "-crf",
                20,
                "-preset",
                "fast",
                "-threads",
                2,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ac",
                1,
                part,
            ]
        )
        transcript = transcripts[number - 1]
        if Path(transcript["file"]).name != audio.name:
            raise ValueError("Transcript clip order differs")
        # Keep recognition text and actual speech timestamps; hand corrections
        # to names and punctuation live in the reviewed transcript, not inference.
        for segment in transcript["segments"]:
            words = segment["words"]
            for offset in range(0, len(words), 10):
                group = words[offset : offset + 10]
                if not group:
                    continue
                start = elapsed + 0.2 + group[0]["start"]
                end = min(elapsed + 0.2 + group[-1]["end"], elapsed + seconds)
                text = "".join(w["word"] for w in group).strip()
                subtitles.append((start, max(start + 0.08, end), text))
        provenance.append(
            {
                "scene": number,
                "title": scene["title"],
                "start": elapsed,
                "seconds": seconds,
                "audio": str(audio.relative_to(ROOT)),
                "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
                "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
            }
        )
        parts.append(part)
        elapsed += seconds
        print(f"Fitted scene {number}: {seconds:.3f}s", flush=True)
    listing = destination / "concat.txt"
    listing.write_text(
        "\n".join("file '" + str(p).replace("'", "'\\''") + "'" for p in parts)
    )
    temporary = destination / "final.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            0,
            "-i",
            listing,
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            temporary,
        ]
    )
    metadata = probe(temporary)
    assert len(metadata["streams"]) == 2
    video_stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    audio_stream = next(s for s in metadata["streams"] if s["codec_type"] == "audio")
    assert (video_stream["width"], video_stream["height"]) == (1920, 1080)
    assert audio_stream["codec_name"] == "aac"
    assert abs(float(metadata["format"]["duration"]) - elapsed) < 0.2
    run(["ffmpeg", "-v", "error", "-i", temporary, "-f", "null", "-"])
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(temporary.read_bytes())
    output.with_suffix(".srt").write_text(
        "\n".join(
            f"{i}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n"
            for i, (start, end, text) in enumerate(subtitles, 1)
        )
    )
    guide = [
        "# WorldFork narrated demo — Chirana",
        "",
        "Timings follow the supplied audio clips. Voice speed is unchanged.",
        "",
    ]
    for entry, scene in zip(provenance, scenes, strict=True):
        guide.extend(
            [
                (
                    f"## {timestamp(entry['start'])[:8]} to "
                    f"{timestamp(entry['start'] + entry['seconds'])[:8]}"
                ),
                "",
                scene["title"],
                "",
                scene["speech"],
                "",
            ]
        )
    (output.parent / "WorldFork-demo-script.md").write_text("\n".join(guide))
    receipt = {
        "duration": elapsed,
        "scenes": provenance,
        "video_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "decode": "passed",
        "resolution": "1920x1080",
        "audio": "participant clips; AAC",
        "processing": "loudness normalization; 200ms lead; video retimed; voice speed unchanged",
    }
    (BUILD / "narrated-verification.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )
    print(f"Created {output}: {elapsed:.3f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, default=ROOT / "Audio clips")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "deliverables/WorldFork-demo.mp4"
    )
    args = parser.parse_args()
    build(args.audio_dir.resolve(), args.output.resolve())
