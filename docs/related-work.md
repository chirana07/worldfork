# Related work and contribution scope

Customer-support agent evaluation is an established area. Sierra's [τ-bench / τ²-bench repository](https://github.com/sierra-research/tau2-bench) provides tool-agent-user interaction benchmarks. [MURMUR and Cross-User Poisoning](https://arxiv.org/abs/2511.17671) examine shared-context agents, interleaved users and user/task boundary failures, including an airline domain.

WorldFork does not claim the first airline support benchmark, multi-user environment or shared-resource simulator. Its hackathon contribution is the implemented local workflow: a compact original six-party allocation scenario, explicit consent/reserve/commit transactions, initial-world comparisons, framework adapters, measured Bifrost calls, controlled faults and inspectable replay. Its research question is exploratory: how do packaged support strategies affect a shared allocation under equal budgets?

The implementation and synthetic fixture are original project work. These sources informed positioning; their benchmark datasets and agent implementations were not imported into WorldFork. We have not evaluated WorldFork against those published benchmarks. Novel scientific value and generalization remain unproven.
