# Wrapping an existing tool agent

The simulator does not import a framework. It accepts validated `Action` objects and returns public receipts. The runner owns the world, ticks, budgets, model transport and persistence. Its two reference factories are registered in `worldfork.agents.ADAPTERS`.

## Implemented interfaces

Reference adapters are constructed with `(gateway, run_id, policy, strategy)`. They implement `async next_action(public_observation) -> Action` and `observe_tool_result(action, result)`. The runner closes its gateway; adapters do not own that connection. Constructor setup is the implemented initialization mechanism. There is no separate asynchronous `initialize`/`close` lifecycle API in this release.

`worldfork.bridge.RunnableAgentAdapter` wraps an already constructed message-based runnable. It forwards a public observation, extracts exactly one pending standard tool call, validates its shape, and supplies the actual receipt as a matching tool message. It accepts ordinary named tools or a single `world_tool` dispatcher. The wrapped agent must stop before tool execution. WorldFork executes tools and enforces all invariants.

## Executable third-party example

```sh
# Finish or cancel active API runs first.
uv run python examples/generic_react.py
```

This configures the installed LangGraph library's prebuilt generic ReAct agent. Its internal loop is unchanged. A model-transport shim maps local JSON actions to standard tool-call messages and records each real Bifrost request using the same measured gateway client. The graph stops before its tool node; a guard fails if internal execution is accidentally attempted. The generic bridge then hands the pending action to the simulator and returns the receipt.

The example executes at most four decisions under a 180-second cap and writes `artifacts/generic-react-integration.json`. It is an integration smoke, with a separate bounded driver, not a benchmark cell. The real local smoke performed four valid information-disclosure actions through Bifrost/Qwen. No task-completion result is claimed from that short run. Unit tests additionally check message/receipt pairing, missing-tool-call rejection and no hidden-profile forwarding.

The prebuilt factory is deprecated in the installed LangGraph release in favor of LangChain's newer agent factory. This example demonstrates compatibility with the installed API, not future API support. The bridge can be configured around other message-based agents, but those integrations require their own tests. HTTP/subprocess agents and universal zero-rewrite compatibility are not implemented.

## Adding an agent to the main runner

Register a factory in `ADAPTERS`, add its name to `RunConfig.framework`, and route every model call through the supplied `Gateway` so attempts, usage and cancellation remain measured. Keep the simulator and scorer unchanged. Add an integration test and a real bounded smoke before adding the integration to a published matrix. Extend the UI label/options if exposing it there. The current frozen comparison uses only the two reference adapters, with an identical public-menu harness on both.
