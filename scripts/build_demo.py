"""Build a narrated walkthrough from actual UI captures and the measured deck.

No screen, microphone or system-audio capture occurs in this script. UI frames
are collected separately through browser controls. macOS `say` writes narration
to files without playing it. The final script refuses an unfinished pilot.
"""

import argparse
import hashlib
import json
import math
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "artifacts/demo-build"


def run(args):
    try:
        subprocess.run([str(a) for a in args], check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.decode(errors="replace")[-3000:]) from exc


def duration(path):
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        )
    )


def scenes():
    def slide(number, speech):
        return {
            "image": ROOT / f"artifacts/pitch-previews/slide-{number}.png",
            "kind": "slide",
            "speech": speech,
        }

    def replay(tick, caption, speech):
        return {
            "image": ROOT / f"artifacts/demo-frames/tick-{tick:02d}.jpg",
            "kind": "replay",
            "tick": tick,
            "caption": caption,
            "speech": speech,
        }

    def inspector(name, speech):
        return {
            "image": ROOT / f"artifacts/demo-frames/{name}.jpg",
            "kind": "inspector",
            "speech": speech,
        }

    result = [
        slide(
            1,
            "Could an agent make valid bookings and still strand a family? World Fork evaluates the shared world left behind by its decisions.",
        ),
        slide(
            2,
            "Every committed transaction here obeyed the rules. Yet repeated changes spent all eighty credits and left a two-person party waiting. Five of seven people had suitable bookings.",
        ),
        replay(
            0,
            "Six parties.\nSeven people.\nShared capacity.",
            "Now replay a separate, real development comparison. Both designs use the same local model, initial world, tools and budgets. This is condensed recorded playback, not a forecast of passenger behavior.",
        ),
        replay(
            2,
            "A books the\nparty of two\non the early flight.",
            "At tick two, world A commits the party of two. One existing booking occupies the remaining early seat.",
        ),
        replay(
            12,
            "Leo consents\nto the late flight.\n40 credits spent.",
            "By tick twelve, Leo has accepted the late flight with forty compensation credits. The receipt confirms consent.",
        ),
        replay(
            28,
            "Sam takes rail.\nThe allocation\nkeeps changing.",
            "At tick twenty-eight, Sam books rail. Every confirmed choice changes the alternatives available to everyone else.",
        ),
        replay(
            35,
            "Dani moves\nto rail.\nA late seat opens.",
            "Dani then voluntarily moves from the late flight to rail. The original seat releases only when the move commits.",
        ),
        replay(
            39,
            "Jules moves\nfrom E to L.\nMira gets a chance.",
            "Jules accepts forty credits and moves to the late flight. This frees the early seat that Mira needs. An offer alone would not release it.",
        ),
        replay(
            41,
            "Mira commits.\nWorld A reaches\n7 of 7.",
            "Mira's booking commits at tick forty-one. World A now meets all seven people's requirements.",
        ),
        replay(
            48,
            "World B ends\nat 5 of 7.\nThe family waits.",
            "The coordinated-design run reaches its decision limit at five of seven. This illustrative pair is separate from the aggregate pilot.",
        ),
        inspector(
            "commit-inspector",
            "Inspect Jules's consent, replacement booking and previous reservation in the ledger. The trace retains the exact public observation, tool result and measured model attempt.",
        ),
        slide(
            4,
            "Every model decision passes through Bifrost to local Ollama. World Fork owns tool execution and independently scores confirmed outcomes. Private constraints stay outside the support-agent context. Capacity, consent, expiring holds and compensation are enforced in code.",
        ),
        slide(
            5,
            "The frozen pilot runs twelve clean episodes: two integrations, two strategies, three seeds. These are the raw outcomes, including failures. We record source hashes, model identity, steps, tools, tokens, local API charge and elapsed time. Three repetitions support a pilot, not statistical significance.",
        ),
        slide(
            6,
            "Eighteen more episodes apply synthetic failures to both strategies. The table separates configured runs, actual exposure and full completion. Model-unavailable recovery includes an automatic harness retry. We do not credit that retry to model reasoning, and we retain every terminal state.",
        ),
        inspector(
            "fault-inspector",
            "This recorded tool timeout occurs before execution. No booking mutation is applied. The agent receives a retryable error, and the fault and subsequent action remain inspectable.",
        ),
        slide(
            7,
            "World Fork has two reference integrations and a separate generic-agent bridge example. Passenger contracts are synthetic, and these scenarios were used during development. The build and full traces run locally.",
        ),
    ]
    for index, item in enumerate(result, 1):
        item["scene_number"] = index
    return result


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def prepare(items, voice, rate):
    BUILD.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(items):
        stem = BUILD / f"scene-{item['scene_number']:02d}"
        script = stem.with_suffix(".txt")
        audio = stem.with_suffix(".aiff")
        digest = hashlib.sha256(f"{voice}:{rate}:{item['speech']}".encode()).hexdigest()
        marker = stem.with_suffix(".sha256")
        script.write_text(item["speech"])
        if not audio.exists() or not marker.exists() or marker.read_text() != digest:
            run(["say", "-v", voice, "-r", str(rate), "-f", script, "-o", audio])
            marker.write_text(digest)
        item["audio"] = audio
        item["duration"] = math.ceil((duration(audio) + 0.65) * 24) / 24
    return sum(item["duration"] for item in items)


def build(items, output):
    elapsed = 0.0
    subtitles = []
    concat = []
    for i, item in enumerate(items):
        card = ROOT / f"artifacts/demo-cards/scene-{item['scene_number']:02d}.png"
        if not card.exists():
            raise FileNotFoundError(
                f"Render the captioned storyboard card first: {card}"
            )
        filters = ["scale=1920:1080:flags=lanczos", "setsar=1", "format=yuv420p"]
        clip = BUILD / f"scene-{item['scene_number']:02d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-loop",
                "1",
                "-i",
                card,
                "-i",
                item["audio"],
                "-vf",
                ",".join(filters),
                "-af",
                "apad=pad_dur=0.8",
                "-t",
                str(item["duration"]),
                "-r",
                "24",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-threads",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-ar",
                "48000",
                "-ac",
                "2",
                clip,
            ]
        )
        concat.append("file '" + str(clip).replace("'", "'\\''") + "'")
        subtitles.append(
            f"{i + 1}\n{timestamp(elapsed)} --> {timestamp(elapsed + item['duration'] - 0.1)}\n"
            + textwrap.fill(item["speech"], 80)
            + "\n"
        )
        elapsed += item["duration"]
        print(f"Rendered {i + 1}/{len(items)}", flush=True)
    subtitle = output.with_suffix(".srt")
    subtitle.write_text("\n".join(subtitles))
    listing = BUILD / "concat.txt"
    listing.write_text("\n".join(concat))
    stitched = BUILD / "stitched.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            listing,
            "-c",
            "copy",
            stitched,
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            stitched,
            "-i",
            subtitle,
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=eng",
            "-disposition:s:0",
            "0",
            "-movflags",
            "+faststart",
            output,
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            output,
            "-an",
            "-sn",
            "-c:v",
            "copy",
            output.with_name(output.stem + "-silent.mp4"),
        ]
    )
    output.with_suffix(".txt").write_text("\n\n".join(item["speech"] for item in items))
    return elapsed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "artifacts/benchmark-20261105T170022Z.json",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "deliverables/WorldFork-demo.mp4"
    )
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--voice", default="Samantha")
    parser.add_argument("--rate", type=int, default=175)
    args = parser.parse_args()
    items = scenes()
    total = prepare(items, args.voice, args.rate)
    (ROOT / "artifacts/demo-scenes.json").write_text(
        json.dumps({"scenes": items, "duration": total}, default=str, indent=2)
    )
    print(f"Prepared {len(items)} narration segments: {total:.2f}s", flush=True)
    if not args.prepare_only:
        manifest = json.loads(args.manifest.read_text())
        assert len(manifest["runs"]) == 30
        assert all(
            e.get("result") and e.get("status") in {"completed", "exhausted", "stopped"}
            for e in manifest["runs"]
        ), "Wait for all frozen episodes"
        card_receipt = json.loads(
            (ROOT / "artifacts/demo-cards/receipt.json").read_text()
        )
        assert card_receipt["final"] is True, "Render final captioned cards first"
        assert (
            card_receipt["pilot_manifest_sha256"]
            == hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        ), "Storyboard and pilot manifest differ"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        seconds = build(items, args.output)
        print(f"Created {args.output}: {seconds:.2f}s", flush=True)
