# Planning review

A fresh reader reviewed the implementation specification before implementation. Six findings concerned baseline deferral, offer transactions, undelivered faults, adapter claims, scope/runtime, and token budgets. Resolutions are recorded in section22 of the specification.

Implementation adjustments:
- Explicitly scoped offer expiry, same-route requests, active proposals, and irreversible compensation.
- Fixed population remains six parties; control scenario is labeled development, not held-out.
- Baseline queue guidance will use public state only and bounded deferral.
- Faults fire on the first eligible decision at/after tick8 rather than requiring a particular tool call; model fault fires at first decision. This reduces silent non-exposure and must be stated in exports.
- A 12-decision smoke episode used12,586 input tokens. Initial aggregate30k cap was too low for a full48-step episode; experimental default is120k, identical for all designs, pending full-episode measurement. Maximum context is bounded by structured state and six recent action/result pairs.
- Schema-constrained outputs through Bifrost/Ollama passed a real smoke call; simple JSON alone had admitted invalid tool arguments.
- Framework coverage is exactly plain Python and an actual LangGraph invocation of the same decision component. An existing generic-agent adapter demonstration remains outstanding; no universal compatibility claim.

Action-harness refinement after actual local inference:
- Raw action JSON produced invalid argument shapes; schema-constrained JSON fixed those shapes but did not stop repeated questions or neglected offers.
- Reference adapters now select a numbered, schema-constrained action from a shared public-state menu. Already-disclosed questions and previously rejected identical proposals are omitted. Proposals use the same declared 0/40-credit choices for both strategies; other compatible external agents can still call the full typed tool contract.
- A shared transaction policy requires committing or withdrawing a consented live offer before another task. This is a harness control, not evidence that the model independently learned transaction handling. Record candidate actions with each decision.
- No private acceptance table or oracle assignment is used to build the menu. All comparisons must use the same harness revision; old smoke episodes are development diagnostics, not evaluation results.
