# Bifrost challenge alignment

WorldFork targets **Build a Benchmarking Platform for AI Agents, Not Just Models**. The supplied Bifrost track briefing describes this challenge on slide 6. Its focus is one class of agents, identical tasks, repeated measurements, controlled failures and inspectable runs. WorldFork's chosen class is customer-support agents allocating shared travel capacity.

| Briefing requirement | Implemented evidence | How to check |
| --- | --- | --- |
| Different frameworks use the same tasks | Plain Python and compiled LangGraph adapters share the world, tools, budgets and scorer. A message-based bridge also wraps an existing prebuilt ReAct agent. | Read the [adapter guide](adapter-guide.md), run the generic integration example, or open the original pilot's clean benchmark group to compare the four framework/strategy combinations. |
| Success, steps, tools, tokens, cost and time across repeated runs | Run archive now includes a repeated-run comparison panel with full-success counts, mean travelers met and their range, steps, tool calls, model calls, tokens, local API charge and elapsed time. | Open Run archive and choose Test conditions. Each design shows retained/scored counts, requested seeds and terminal outcomes. |
| Tools, models and input can fail | The original 30-episode pilot includes all three controlled fault types. The release adds 24 solo/team trials with time left after a scheduled timeout. | Select a fault condition, check delivered exposures, then inspect its decisions and receipts. Read the [release fault follow-through table](../evidence/team-evaluation/report.md#fault-follow-through). |
| Any recorded run can be inspected step by step | The comparison panel opens the latest retained run for each design. The archive, playback, decision ledger and exports expose the rest. | Select Open latest run, move the playback slider, open a decision and export its trace. |

## Comparing the same conditions

The comparison API groups only records with the same scenario identity and hash, model identity and weight digest, passenger mode, fault setting, decoding, budgets and source hashes. Framework, strategy and requested seed may vary inside a group. The UI defaults to the condition containing the run currently being reviewed.

Cancelled, interrupted and simulator-error records remain visible in terminal counts and inspection links while being excluded from means, consistent with the existing report policy. Missing resource usage remains unknown and has a measured/scored denominator. Records lacking model or source identity are counted separately. Early stops and exhausted budgets remain scored outcomes.

The summary reads every stored record using a metadata projection. It is independent of the individual archive's 100-run display window. No raw model responses, observations or snapshots are needed to compute the displayed means.

## Bifrost's role

Support, specialist, orchestrator and optional passenger model requests use the supplied measured client against the same Bifrost endpoint. Provider response usage and actual attempts are attached to tool decisions. The local gateway configuration enables gateway logging. The scorer and environment operate independently of model statements.

An external agent must use the supplied transport to participate in these resource measurements. Calls that bypass it are outside the measurement boundary. The working examples establish compatibility with the two reference integrations and the bounded generic-agent smoke. Further integrations need their own tests. [Architecture](architecture.md) · [Adapter contract](adapter-guide.md)

## What to demonstrate

Start with a confirmed booking and its remaining capacity, then inspect the receipt. Open Run archive to compare repeated-run outcomes and resources. Choose a timeout condition to show actual exposure and later actions. The revised team won seven configuration-matched pairs, lost three and tied two, using 288 model calls versus 166 for the solo planner. Those mixed results demonstrate why coordination needs measurement. [Full results](../evidence/team-evaluation/report.md)

The presentation's gateway features are options to use when the problem needs them. WorldFork's submission demonstrates the benchmarking challenge through actual inference, controlled tools, measured outcomes and verifiable traces.
