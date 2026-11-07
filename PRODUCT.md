# WorldFork

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Agent developers and hackathon judges who need to compare agent behavior and inspect the evidence behind an outcome.

## Product Purpose

WorldFork is a shared-world benchmark for customer support agents. The fictional Harbor Airport scenario tests how support decisions change what remains possible for other passengers during a disruption.

## Positioning

Both runs start from the same scenario. They use the same tools and constraints, so a reviewer can inspect how differences in decisions change the resulting world. Seats, compensation and commitments are shared within each run.

## Operating Context

Reviewers can start with the bundled replay, compare final outcomes, scrub through snapshots, inspect receipts and export traces. Developers can run live comparisons through local Ollama and Bifrost using the Python or LangGraph integration. React and TypeScript power the interface, with FastAPI and SQLite serving run state and evidence. The source is public at [WorldFork on GitHub](https://github.com/chirana07/worldfork).

## Capabilities and Constraints

The Harbor scenario has six passenger parties, seven people, three travel alternatives and 80 fictional compensation credits. The environment enforces capacity, whole-party bookings, consent and compensation. The pilot uses scripted passengers. Optional LLM passenger consent is a separate experiment. The recorded replay is read-only and works without the local model stack. The final submission details remain open.

## Brand Commitments

WorldFork uses plain operational language and explicitly labels synthetic scenarios and experimental limits. The user delegated design decisions and chose direct implementation in React.

## Evidence on Hand

The repository includes [30 scored pilot episodes](evidence/pilot-summary.md), the original trace exports, and a deterministic verifier. The project also has a recorded demo and an editable pitch deck. The pilot measures one configured local model on a development scenario.

## Product Principles

- Show what a decision changed in the shared world and let reviewers open its receipt.
- Identify the scenario, integration, model and fault so comparisons remain interpretable.
- Distinguish recorded final outcomes from the world state at the current playback tick.
- Keep incomplete runs inspectable and explain where a score is unavailable.

## Accessibility & Inclusion

Keep the desktop comparison and stacked mobile layout usable with native keyboard controls, visible focus and reduced motion. Pair status colors with readable labels.
