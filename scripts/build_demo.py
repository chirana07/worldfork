"""Assemble a silent demo from recorded UI clips and write its narration handoff."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "artifacts/submission-build"


def run(command):
    result = subprocess.run(
        [str(arg) for arg in command],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return result.stdout


def probe(filename):
    return json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                filename,
            ]
        )
    )


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build(manifest_path, output):
    manifest = json.loads(manifest_path.read_text())
    storyboard = json.loads((ROOT / "scripts/demo_storyboard.json").read_text())
    scenes = manifest["scenes"]
    if [{key: scene[key] for key in storyboard[0]} for scene in scenes] != storyboard:
        raise ValueError("Recorded scenes differ from the approved storyboard")
    run(
        [
            sys.executable,
            ROOT / "scripts/verify_evidence.py",
            ROOT / "evidence/pilot-manifest.json",
        ]
    )
    run([sys.executable, ROOT / "scripts/evaluate_team.py", "--verify"])
    output.parent.mkdir(parents=True, exist_ok=True)
    clips = []
    elapsed = 0
    captions = []
    timing = [
        "# WorldFork narration for Chirana",
        "",
        "The silent demo runs for three minutes. Read the paragraphs in order, with a brief pause between scenes. The average pace is about 136 words per minute. Record naturally and provide one WAV, M4A or MP3, or numbered clips for each scene. The edit can be retimed to fit your recording.",
        "",
        "The SRT uses the planned scene timing. Final narration and caption timing will follow the supplied audio. The video contains no audio stream.",
        "",
    ]
    for index, scene in enumerate(scenes, 1):
        video = ROOT / scene["video"]
        if hashlib.sha256(video.read_bytes()).hexdigest() != scene["video_sha256"]:
            raise ValueError(f"Recorded clip differs for scene {index}")
        metadata = probe(video)
        seconds = scene["seconds"]
        start = max(0, float(metadata["format"]["duration"]) - seconds)
        band = BUILD / "bands" / f"band-{index:02d}.png"
        if (
            hashlib.sha256(band.read_bytes()).hexdigest()
            != manifest["caption_sha256"][index - 1]
        ):
            raise ValueError(f"Caption band differs for scene {index}")
        filters = (
            "[0:v]scale=1760:990:flags=lanczos,"
            "pad=1920:1080:80:0:color=0xf5f4ef,setsar=1,"
            "tpad=stop_mode=clone:stop_duration=1[base];"
            "[base][1:v]overlay=0:990:format=auto,format=yuv420p[video]"
        )
        clip = BUILD / f"edited-{index:02d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-ss",
                start,
                "-i",
                video,
                "-loop",
                1,
                "-i",
                band,
                "-t",
                seconds,
                "-filter_complex",
                filters,
                "-map",
                "[video]",
                "-an",
                "-r",
                24,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                20,
                "-threads",
                2,
                clip,
            ]
        )
        clips.append(clip)
        captions.append(
            f"{index}\n{timestamp(elapsed)} --> {timestamp(elapsed + seconds)}\n{textwrap.fill(scene['speech'], 72)}\n"
        )
        timing.extend(
            [
                f"## {timestamp(elapsed)[:8]} to {timestamp(elapsed + seconds)[:8]}",
                "",
                scene["title"],
                "",
                scene["speech"],
                "",
            ]
        )
        elapsed += seconds
        print(f"Rendered silent scene {index}/{len(scenes)}", flush=True)
    listing = BUILD / "silent-concat.txt"
    listing.write_text(
        "\n".join("file '" + str(clip).replace("'", "'\\''") + "'" for clip in clips)
    )
    temporary = BUILD / "silent-review.mp4"
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
            "-an",
            "-c:v",
            "copy",
            "-movflags",
            "+faststart",
            temporary,
        ]
    )
    metadata = probe(temporary)
    videos = [
        stream for stream in metadata["streams"] if stream["codec_type"] == "video"
    ]
    assert (
        len(videos) == 1 and videos[0]["width"] == 1920 and videos[0]["height"] == 1080
    )
    assert all(stream["codec_type"] != "audio" for stream in metadata["streams"])
    assert abs(float(metadata["format"]["duration"]) - elapsed) < 0.15
    run(["ffmpeg", "-v", "error", "-i", temporary, "-f", "null", "-"])
    output.write_bytes(temporary.read_bytes())
    (output.parent / "WorldFork-demo.txt").write_text(
        "\n\n".join(scene["speech"] for scene in scenes) + "\n"
    )
    (output.parent / "WorldFork-demo-script.md").write_text("\n".join(timing))
    (output.parent / "WorldFork-demo.srt").write_text("\n".join(captions))
    receipt = {
        "seconds": elapsed,
        "scenes": len(scenes),
        "video_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "audio_streams": 0,
        "source_runs": manifest["source_runs"],
        "source_revision": manifest["source_revision"],
        "video": os.path.relpath(output, ROOT),
    }
    (BUILD / "media-verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--captures", type=Path, default=BUILD / "capture-manifest.json"
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "deliverables/WorldFork-demo-silent.mp4"
    )
    args = parser.parse_args()
    build(args.captures, args.output)
