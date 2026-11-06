# Frozen pilot evidence

`pilot-manifest.json` has portable trace paths. `original-manifest.json` preserves the measured manifest byte for byte. The `interrupted/` folder preserves the paused parent manifest and all three original interrupted traces. The continuation links each original run to its replacement.

All 30 scored episodes were replayed from recorded actions without model calls. `replay-verification.json` records receipt, state, score, source identity and token-accounting checks. [Trace provenance](../docs/trace-provenance.md) describes the historical observation logging discrepancy.

From the repository root:

```sh
uv run python scripts/verify_evidence.py evidence/pilot-manifest.json
shasum -a 256 -c evidence/SHA256SUMS
```

Trace exports include the complete fictional scenario, including evaluator-only private constraints. Live agents receive only public observations; do not feed the full export into a live agent.

The four-decision generic ReAct smoke and Qwen gateway smoke are separate integration evidence. The `development/` traces are illustrative development diagnostics and are excluded from pilot aggregates.

Three repeats per cell support a small synthetic pilot. The ordinary desktop host was not isolated for latency measurements. Automatic unavailable-model retries are harness behavior. There is no significance, human-prediction or universal agent-compatibility claim.
