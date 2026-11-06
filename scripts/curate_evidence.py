"""Copy the completed pilot into a portable, verifiable source evidence folder."""

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

from verify_evidence import verify_manifest
from worldfork.report import markdown, summarize

ROOT = Path(__file__).resolve().parents[1]


def curate(source, target):
    verification = verify_manifest(source)
    raw = source.read_bytes()
    original = json.loads(raw)
    manifest = copy.deepcopy(original)
    target.mkdir(parents=True, exist_ok=True)
    (target / "traces").mkdir(exist_ok=True)
    (target / "original-manifest.json").write_bytes(raw)
    manifest["original_manifest_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["curation"] = (
        "Only trace paths were rebased for portability; configurations and results are unchanged."
    )
    for entry in manifest["runs"]:
        origin = Path(entry["trace"])
        if not origin.is_absolute():
            origin = ROOT / origin
        copied = target / "traces" / (entry["id"] + ".json")
        shutil.copy2(origin, copied)
        entry["trace"] = str(copied.relative_to(ROOT))
    if continuation := manifest.get("continuation"):
        interrupted = target / "interrupted"
        interrupted.mkdir(exist_ok=True)
        parent = interrupted / "parent-manifest.json"
        shutil.copy2(ROOT / continuation["parent_manifest"], parent)
        continuation["parent_manifest"] = str(parent.relative_to(ROOT))
        for replacement in continuation["replacements"]:
            entry = replacement["original"]
            archived = interrupted / (entry["id"] + ".json")
            shutil.copy2(ROOT / entry["trace"], archived)
            entry["trace"] = str(archived.relative_to(ROOT))
    portable = target / "pilot-manifest.json"
    portable.write_text(json.dumps(manifest, indent=2))
    (target / "pilot-summary.md").write_text(markdown(summarize(manifest)))
    verify_manifest(portable)
    (target / "replay-verification.json").write_text(json.dumps(verification, indent=2))
    for filename in ["generic-react-integration.json", "qwen-smoke.json"]:
        shutil.copy2(ROOT / "artifacts" / filename, target / filename)
    regression = ROOT / "artifacts/post-fix-smoke.json"
    if regression.exists():
        shutil.copy2(regression, target / regression.name)
    (target / "development").mkdir(exist_ok=True)
    # The illustrative walkthrough is separate from the frozen pilot.
    for filename in [
        "calibration-case_by_case.json",
        "calibration-coordinated.json",
        "calibration-qwen-case_by_case.json",
        "calibration-qwen-coordinated.json",
    ]:
        origin = ROOT / "artifacts" / filename
        if origin.exists():
            shutil.copy2(origin, target / "development" / filename)
    (target / "README.md").write_text(
        "# Frozen pilot evidence\n\n"
        "`pilot-manifest.json` has portable trace paths. `original-manifest.json` preserves the measured manifest byte for byte. The `interrupted/` folder preserves the paused parent manifest and all three original interrupted traces. The continuation links each original run to its replacement.\n\n"
        "All 30 scored episodes were replayed from recorded actions without model calls. `replay-verification.json` records receipt, state, score, source identity and token-accounting checks. [Trace provenance](../docs/trace-provenance.md) describes the historical observation logging discrepancy.\n\n"
        "From the repository root:\n\n```sh\nuv run python scripts/verify_evidence.py evidence/pilot-manifest.json\nshasum -a 256 -c evidence/SHA256SUMS\n```\n\n"
        "Trace exports include the complete fictional scenario, including evaluator-only private constraints. Live agents receive only public observations; do not feed the full export into a live agent.\n\n"
        "The four-decision generic ReAct smoke and Qwen gateway smoke are separate integration evidence. The `development/` traces are illustrative development diagnostics and are excluded from pilot aggregates.\n\n"
        "Three repeats per cell support a small synthetic pilot. The ordinary desktop host was not isolated for latency measurements. Automatic unavailable-model retries are harness behavior. There is no significance, human-prediction or universal agent-compatibility claim.\n"
    )
    hashes = []
    for filename in sorted(target.rglob("*")):
        if filename.is_file() and filename.name != "SHA256SUMS":
            hashes.append(
                hashlib.sha256(filename.read_bytes()).hexdigest()
                + "  "
                + str(filename.relative_to(ROOT))
            )
    (target / "SHA256SUMS").write_text("\n".join(hashes) + "\n")
    return verification


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--destination", type=Path, default=ROOT / "evidence")
    args = parser.parse_args()
    print(json.dumps(curate(args.manifest, args.destination.resolve()), indent=2))
