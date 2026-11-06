# Archived observation provenance

After the fix, an eight-decision Bifrost/Qwen smoke run passed the replay audit with zero observation discrepancies. [Smoke trace](../evidence/post-fix-smoke.json)

The frozen pilot ran from `cc23f05`. Its original exports are preserved byte for byte. A post-run replay audit found a logging alias in that revision: `World.observation()` returned case dictionaries whose `known` fields referenced mutable world state. A successful `ask_question` updated that dictionary before the event was saved, so the saved `observation` may include the newly disclosed answer in that same event.

The model request was serialized before the action executed. The alias did not feed the answer to that model decision, change the candidate menu, execute a different action, or change the tool receipt, world snapshot, terminal score or measured usage. The full trace still records the question and answer, ordering, action selection, and before/after world history. The issue is limited to the saved pre-action observation field on affected disclosure events.

The released engine copies the public case data when creating an observation. A regression test checks that an earlier observation cannot acquire a newly disclosed answer. The exact frozen engine source remains at `evidence/frozen-source/engine.py`; the replay verifier permits only the known one-line observation-copy correction when checking that historical source hash.

The verifier reconstructs the public projection from the initial fixture and actual recorded actions. It accepts a legacy mismatch only when it is exactly the newly disclosed field from a successful question under the known frozen engine digest. It counts those events, checks that the measured model reply selects the recorded action, and verifies every receipt, snapshot, terminal score and token sum. It does not alter archived observations or rerun inference. The recorded replay interface labels the affected fields as stored observations.
