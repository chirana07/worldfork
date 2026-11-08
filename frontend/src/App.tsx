import { useEffect, useState, useRef } from "react";
import {
  GitFork,
  ArrowUpRight,
  ArrowRight,
  Plane,
  TrainFront,
  Users,
  Play,
  Pause,
  RotateCcw,
  Download,
  ListOrdered,
  Square,
  Check,
  Clock3,
  ChevronRight,
  Radio,
  FlaskConical,
  History,
  BookOpen,
  X,
  AlertCircle,
} from "lucide-react";

type Booking = { option_id: string; voucher: number; version: number };
type Party = {
  id: string;
  name: string;
  people: number;
  request: string;
  known: Record<string, unknown>;
  booking: Booking | null;
};
type Option = {
  id: string;
  label: string;
  arrival: string;
  mode: string;
  capacity: number;
  available: number;
};
type Snapshot = {
  tick: number;
  cases: Party[];
  options: Option[];
  budget: { total: number; spent: number; reserved: number; available: number };
  offers: Record<
    string,
    { party_id: string; status: string; option_id: string }
  >;
};
type Config = {
  framework: string;
  strategy: string;
  scenario_id: string;
  passenger_mode: string;
  model: string;
  fault: string;
  seed: number;
  max_steps?: number;
  temperature?: number;
  max_tokens?: number;
  wall_seconds?: number;
  scenario_hash?: string;
  source_hashes?: Record<string, string>;
  model_manifest?: { digest: string | null };
};
type Run = {
  id: string;
  created_at: string;
  status: string;
  config: Config;
  snapshot: Snapshot;
  result: Record<string, any> | null;
};
type RunSummary = Omit<Run, "snapshot">;
type BenchmarkRow = {
  framework: string;
  strategy: string;
  configured: number;
  scored: number;
  completed: number;
  resolved_mean: number | null;
  resolved_range: number[] | null;
  fault_exposed: number;
  statuses: Record<string, number>;
  metrics: Record<
    string,
    { mean: number | null; known: number; range: number[] | null }
  >;
  run_ids: string[];
  seeds: number[];
};
type BenchmarkCohort = {
  id: string;
  config: Omit<Config, "framework" | "strategy" | "seed"> & {
    model_digest: string;
  };
  rows: BenchmarkRow[];
};
type TeamProposal = {
  role: string;
  action_id?: number;
  plan?: string;
};
type Event = {
  seq: number;
  tick: number;
  type: string;
  action?: { tool: string; arguments: Record<string, any> };
  result?: Record<string, any>;
  error?: string;
  fault?: string;
  visibility?: string;
  message?: string;
  truth?: unknown;
  shown?: unknown;
  snapshot: Snapshot;
  observation?: unknown;
  candidate_actions?: { id: number; tool: string }[] | null;
  attempts?: unknown[];
  coordination?: {
    proposals: TeamProposal[];
    action_id: number;
    plan: string;
    consultation_reason?: string;
    prior_advice?: { role: string; tick: number; plan: string }[];
  };
};
type Scenario = {
  id: string;
  label: string;
  policy: string;
  initial: Snapshot;
};
const strategies: Record<string, string> = {
  case_by_case: "Case-by-case service",
  coordinated: "Shared-constraint planning",
  team: "Orchestrated team",
};
const strategyLabel = (strategy: string) => strategies[strategy] ?? strategy;
const active = (r?: Run | null) =>
  !!r && ["running", "queued"].includes(r.status);
function saveRunLink(a?: Run | null, b?: Run | null) {
  const url = new URL(window.location.href);
  url.hash = "";
  for (const [key, run] of [
    ["a", a],
    ["b", b],
  ] as const) {
    if (run) url.searchParams.set(key, run.id);
    else url.searchParams.delete(key);
  }
  window.history.replaceState(null, "", url);
}
const fmt = (n?: number | null) => (n == null ? "Unknown" : n.toLocaleString());
async function api<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(
    "/api" + path,
    body === undefined
      ? undefined
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!r.ok) {
    const text = await r.text();
    let message = text;
    try {
      const d = JSON.parse(text);
      message =
        typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail);
    } catch {}
    throw new Error(message || `Request failed (${r.status})`);
  }
  return r.json();
}
const config = (
  strategy: string,
  framework: string,
  scenario_id: string,
  fault: string,
  passenger_mode: string,
  model: string,
): Config => ({
  strategy,
  framework,
  scenario_id,
  fault,
  passenger_mode,
  model,
  seed: 11,
  temperature: 0.2,
  max_steps: 48,
});

function WorldPanel({
  side,
  run,
  strategy,
  snapshot,
  onSelect,
  onCancel,
}: {
  side: string;
  run: Run | null;
  strategy: string;
  snapshot: Snapshot;
  onSelect: (p: Party, trigger: HTMLButtonElement) => void;
  onCancel: () => void;
}) {
  const booked = snapshot.cases
    .filter((p) => p.booking)
    .reduce((n, p) => n + p.people, 0);
  return (
    <section className="world" aria-label={`World ${side}`}>
      <div className="world-top">
        <span className={`world-letter side-${side.toLowerCase()}`}>
          {side}
        </span>
        <div>
          <h2>{strategyLabel(run?.config.strategy ?? strategy)}</h2>
          <p>
            {run
              ? `${run.config.framework === "python" ? "Plain Python" : "LangGraph"} · ${run.config.passenger_mode === "llm" ? "LLM passengers" : "Scripted passengers"}`
              : "Same people. Same starting resources."}
          </p>
        </div>
        <span className={`status ${active(run) ? "is-live" : ""}`}>
          {run ? run.status.replaceAll("_", " ") : "Initial state"}
        </span>
      </div>
      <div className="departure-board">
        <div className="board-head">
          <span>Available connections</span>
          <span>Arrival / seats left</span>
        </div>
        {snapshot.options.map((o) => (
          <div className="departure" key={o.id}>
            <div className="route-id">
              {o.mode === "flight" ? (
                <Plane size={17} />
              ) : (
                <TrainFront size={17} />
              )}
              <span>{o.id}</span>
            </div>
            <div className="route-name">
              {o.label}
              <small>
                {o.mode === "flight"
                  ? "Harbor → destination"
                  : "Ground alternative"}
              </small>
            </div>
            <span className="time">{o.arrival}</span>
            <div className="seat-count">
              <b>{o.available}</b>
              <span>/{o.capacity}</span>
            </div>
          </div>
        ))}
        <div className="board-foot">
          <span>Compensation available</span>
          <span>
            {snapshot.budget.available}
            <small> / {snapshot.budget.total} credits</small>
          </span>
        </div>
      </div>
      <div className="passenger-heading">
        <h3>People in this world</h3>
        <span>
          <Users size={14} />
          {booked} of 7 booked
        </span>
      </div>
      <div className="passenger-list">
        {snapshot.cases.map((p) => {
          const offer = Object.values(snapshot.offers).find(
            (o) => o.party_id === p.id && o.status === "accepted",
          );
          return (
            <button
              className="passenger"
              onClick={(e) => onSelect(p, e.currentTarget)}
              key={p.id}
            >
              <span className={`avatar ${p.booking ? "has-booking" : ""}`}>
                {p.name[0]}
                {p.people > 1 && <small>2</small>}
              </span>
              <span className="passenger-copy">
                <strong>{p.name}</strong>
                <span>
                  {p.known.deadline
                    ? `Arrive by ${String(p.known.deadline)}`
                    : p.people === 2
                      ? "Two people · same departure"
                      : "Requirements not yet disclosed"}
                </span>
              </span>
              <span
                className={`passenger-state ${p.booking ? "booked" : offer ? "offered" : ""}`}
              >
                {p.booking ? (
                  <>
                    <Check size={13} />
                    Booked {p.booking.option_id}
                  </>
                ) : offer ? (
                  "Offer accepted"
                ) : (
                  <>
                    <Clock3 size={12} />
                    Waiting
                  </>
                )}
              </span>
              <ChevronRight size={15} className="chevron" />
            </button>
          );
        })}
      </div>
      <div className="world-footer">
        <span>
          Logical tick <b>{snapshot.tick}</b>
        </span>
        <span>
          Spent <b>{snapshot.budget.spent}</b> credits
        </span>
        {active(run) && (
          <button className="text-button danger" onClick={onCancel}>
            <Square size={12} />
            Cancel run
          </button>
        )}
      </div>
      {run?.result && (
        <div className="world-result">
          <span className="summary-label">
            End-of-run summary · {run.status.replaceAll("_", " ")}
          </span>
          <strong>
            {run.result.satisfied_people} / {run.result.total_people} people’s
            requirements met
          </strong>
          <span>
            Allocation upper bound: {run.result.oracle_max} ·{" "}
            {fmt(run.result.model_calls)} model calls ·{" "}
            {fmt(
              run.result.usage_coverage === 0 ||
                run.result.input_tokens == null ||
                run.result.output_tokens == null
                ? null
                : run.result.input_tokens + run.result.output_tokens,
            )}{" "}
            tokens · {(run.result.elapsed_ms / 1000).toFixed(1)}s
          </span>
          <span>
            {fmt(run.result.steps)} steps · {fmt(run.result.tool_calls)} tool
            calls ·{" "}
            {run.result.api_cost === 0
              ? "Local API charge $0"
              : "See trace for API cost"}
          </span>
          <a href={`/api/runs/${run.id}/export`} download>
            <Download size={13} />
            Export trace
          </a>
        </div>
      )}
    </section>
  );
}

function BenchmarkResults({
  scenarios,
  preferredRun,
  onInspect,
  disabled,
}: {
  scenarios: Scenario[];
  preferredRun?: string;
  onInspect: (id: string) => void;
  disabled: boolean;
}) {
  const [report, setReport] = useState<{
    cohorts: BenchmarkCohort[];
    unidentified_runs: number;
  } | null>(null);
  const [phase, setPhase] = useState("loading");
  const [revision, setRevision] = useState(0);
  const [choice, setChoice] = useState("");
  useEffect(() => {
    let mounted = true;
    setPhase("loading");
    api<{ cohorts: BenchmarkCohort[]; unidentified_runs: number }>(
      "/benchmarks",
    )
      .then((data) => {
        if (!mounted) return;
        setReport(data);
        setChoice((current) =>
          data.cohorts.some((cohort) => cohort.id === current)
            ? current
            : (data.cohorts.find((cohort) =>
                cohort.rows.some((row) =>
                  row.run_ids.includes(preferredRun ?? ""),
                ),
              )?.id ??
              data.cohorts[0]?.id ??
              ""),
        );
        setPhase("ready");
      })
      .catch(() => {
        if (mounted) setPhase("error");
      });
    return () => {
      mounted = false;
    };
  }, [revision, preferredRun]);
  const cohort = report?.cohorts.find((group) => group.id === choice);
  function metric(row: BenchmarkRow, field: string, divisor = 1) {
    const value = row.metrics[field];
    if (value.mean === null) return "Unknown";
    const precision =
      field === "api_cost"
        ? { maximumSignificantDigits: 4 }
        : { maximumFractionDigits: 1 };
    const number = (value.mean / divisor).toLocaleString(undefined, precision);
    return value.known === row.scored
      ? number
      : `${number} (${value.known}/${row.scored} measured)`;
  }
  return (
    <section className="benchmark-results" aria-labelledby="benchmark-title">
      <div className="benchmark-heading">
        <h2 id="benchmark-title">Compare repeated runs</h2>
        <button
          className="text-button"
          disabled={phase === "loading"}
          onClick={() => setRevision((value) => value + 1)}
        >
          {phase === "error" ? "Retry results" : "Refresh results"}
        </button>
      </div>
      <p>Compare outcomes and resources under the same test conditions.</p>
      {phase === "loading" ? (
        <p role="status">Loading measured results…</p>
      ) : phase === "error" ? (
        <p role="alert">
          Results could not be loaded. Use Retry results to try again.
        </p>
      ) : cohort ? (
        <>
          <label className="benchmark-condition">
            Test conditions
            <select
              value={choice}
              onChange={(event) => setChoice(event.target.value)}
            >
              {report?.cohorts.map((group) => (
                <option key={group.id} value={group.id}>
                  {scenarios.find(
                    (scenario) => scenario.id === group.config.scenario_id,
                  )?.label ?? group.config.scenario_id}{" "}
                  ·{" "}
                  {group.config.fault === "none"
                    ? "clean"
                    : group.config.fault.replaceAll("_", " ")}{" "}
                  · {group.config.model.replace("ollama/", "")} ·{" "}
                  {group.config.max_steps} steps · {group.id.slice(0, 6)}
                </option>
              ))}
            </select>
          </label>
          <div className="benchmark-comparison">
            {cohort.rows.map((row) => (
              <article
                className="benchmark-agent"
                key={`${row.framework}-${row.strategy}`}
              >
                <h3>{strategyLabel(row.strategy)}</h3>
                <p>
                  {row.framework} · {row.scored} scored of {row.configured}{" "}
                  retained runs · {row.seeds.length} requested seeds
                </p>
                <dl className="benchmark-metrics">
                  <div>
                    <dt>Travelers met, mean</dt>
                    <dd>
                      {row.resolved_mean === null
                        ? "Unknown"
                        : `${row.resolved_mean.toFixed(2)} / ${row.metrics.total_people.mean ?? "?"}`}
                      {row.resolved_range && (
                        <small>Range {row.resolved_range.join("–")}</small>
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Full success</dt>
                    <dd>
                      {row.scored
                        ? `${row.completed} / ${row.scored} runs`
                        : "Awaiting scores"}
                    </dd>
                  </div>
                  <div>
                    <dt>Steps, mean</dt>
                    <dd>{metric(row, "steps")}</dd>
                  </div>
                  <div>
                    <dt>Tool calls, mean</dt>
                    <dd>{metric(row, "tool_calls")}</dd>
                  </div>
                  <div>
                    <dt>Model calls, mean</dt>
                    <dd>{metric(row, "model_calls")}</dd>
                  </div>
                  <div>
                    <dt>Tokens, mean</dt>
                    <dd>{metric(row, "tokens")}</dd>
                  </div>
                  <div>
                    <dt>API charge, mean</dt>
                    <dd>
                      {row.metrics.api_cost.mean === null
                        ? "Unknown"
                        : `$${metric(row, "api_cost")}`}
                    </dd>
                  </div>
                  <div>
                    <dt>Time, mean (s)</dt>
                    <dd>{metric(row, "elapsed_ms", 1000)}</dd>
                  </div>
                  <div>
                    <dt>Fault delivered</dt>
                    <dd>
                      {row.fault_exposed} / {row.configured} runs
                    </dd>
                  </div>
                </dl>
                <p className="benchmark-status">
                  {Object.entries(row.statuses)
                    .map(
                      ([status, count]) =>
                        `${count} ${{ exhausted: "budget reached", stopped: "stopped early", completed: "fully resolved" }[status] ?? status.replaceAll("_", " ")}`,
                    )
                    .join(" · ")}
                </p>
                <button
                  className="text-button"
                  disabled={disabled}
                  onClick={() => onInspect(row.run_ids[0])}
                >
                  Open latest run <ArrowRight size={15} />
                </button>
              </article>
            ))}
          </div>
          <details className="benchmark-method">
            <summary>How these results are grouped</summary>
            <p>
              Each group fixes the scenario, model digest, source version,
              passenger mode, fault setting, decoding and budgets. Only the
              framework, strategy and requested seed vary.
            </p>
            <p>
              Passenger mode {cohort.config.passenger_mode} · temperature{" "}
              {cohort.config.temperature} · token budget{" "}
              {cohort.config.max_tokens?.toLocaleString()} · wall budget{" "}
              {cohort.config.wall_seconds} s.
            </p>
            <p>
              Means exclude cancelled, interrupted and simulator-error runs.
              Missing measurements stay unknown. Traveler totals include the
              initial booking. Local API charge excludes hardware and
              electricity. Timing includes desktop contention. Model seeds are
              recorded requests.
            </p>
          </details>
        </>
      ) : (
        <p>
          Finish a run with recorded model and source information to start
          comparing results.
        </p>
      )}
      {!!report?.unidentified_runs && (
        <p>
          {report.unidentified_runs} retained runs lack the model or source
          information needed for grouping.
        </p>
      )}
    </section>
  );
}

export default function App() {
  const [singleRun, setSingleRun] = useState(false);
  const inspectorRef = useRef<HTMLElement>(null);
  const inspectorTrigger = useRef<HTMLElement | null>(null);
  const [view, setView] = useState("lab"),
    [scenarios, setScenarios] = useState<Scenario[]>([]),
    [scenarioId, setScenarioId] = useState("harbor-v1");
  const [frameworkA, setFrameworkA] = useState("python"),
    [frameworkB, setFrameworkB] = useState("python"),
    [strategyA, setStrategyA] = useState("case_by_case"),
    [strategyB, setStrategyB] = useState("coordinated"),
    [fault, setFault] = useState("none"),
    [passengers, setPassengers] = useState("scripted");
  const [model, setModel] = useState("ollama/qwen3.5:4b"),
    [models, setModels] = useState<string[]>([]);
  const [runA, setRunA] = useState<Run | null>(null),
    [runB, setRunB] = useState<Run | null>(null),
    [eventsA, setEventsA] = useState<Event[]>([]),
    [eventsB, setEventsB] = useState<Event[]>([]);
  const [health, setHealth] = useState<Record<string, string>>({}),
    [archive, setArchive] = useState<RunSummary[]>([]),
    [archiveState, setArchiveState] = useState("loading"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<{
      side: string;
      event?: Event;
      party?: Party;
    } | null>(null),
    [cursor, setCursor] = useState<number | null>(null),
    [playing, setPlaying] = useState(false);
  const scenario = scenarios.find((s) => s.id === scenarioId) || scenarios[0];
  const maxTick = Math.max(runA?.snapshot.tick || 0, runB?.snapshot.tick || 0);
  const replay = health.mode === "replay";
  const experimentActive = active(runA) || active(runB);
  const archiveRequest = useRef(0);
  async function loadArchive() {
    const request = ++archiveRequest.current;
    setArchiveState("loading");
    try {
      const rows = await api<RunSummary[]>("/runs?summary=true");
      if (request === archiveRequest.current) {
        setArchive(rows);
        setArchiveState("ready");
      }
    } catch {
      if (request === archiveRequest.current) setArchiveState("error");
    }
  }
  useEffect(() => {
    let mounted = true;
    void loadArchive();
    Promise.all([
      api<Scenario[]>("/scenarios"),
      api<Record<string, string>>("/health"),
      api<string[]>("/models").catch(() => [] as string[]),
    ])
      .then(async ([s, h, installed]) => {
        if (mounted) {
          setScenarios(s);
          setHealth(h);
          setModels(installed);
          if (installed.length && !installed.includes(model))
            setModel(installed[0]);
          const query = new URLSearchParams(window.location.search);
          const aId = query.get("a"),
            bId = query.get("b");
          if (aId) {
            try {
              const [a, b] = await Promise.all([
                api<Run>("/runs/" + encodeURIComponent(aId)),
                bId
                  ? api<Run>("/runs/" + encodeURIComponent(bId))
                  : Promise.resolve(null),
              ]);
              const shared = (run: Run) => {
                const c = run.config;
                return JSON.stringify([
                  c.scenario_id,
                  c.model,
                  c.passenger_mode,
                  c.fault,
                  c.seed,
                  c.temperature,
                  c.max_steps,
                  c.max_tokens,
                  c.wall_seconds,
                  c.scenario_hash,
                  c.source_hashes,
                ]);
              };
              if (b && shared(a) !== shared(b))
                throw new Error(
                  "The linked runs do not share the same experiment conditions.",
                );
              if (
                b &&
                a.config.model_manifest?.digest &&
                b.config.model_manifest?.digest &&
                a.config.model_manifest.digest !==
                  b.config.model_manifest.digest
              )
                throw new Error(
                  "The linked runs used different model weights.",
                );
              if (!mounted) return;
              setRunA(a);
              setRunB(b);
              setSingleRun(!b);
              setScenarioId(a.config.scenario_id);
              if (installed.includes(a.config.model)) setModel(a.config.model);
              setPassengers(a.config.passenger_mode);
              setFault(a.config.fault);
              setFrameworkA(a.config.framework);
              setStrategyA(a.config.strategy);
              if (b) {
                setFrameworkB(b.config.framework);
                setStrategyB(b.config.strategy);
              }
            } catch (e) {
              if (mounted)
                setError(
                  `Cannot restore the saved run link. ${(e as Error).message}`,
                );
            }
          }
        }
      })
      .catch(
        (e) =>
          mounted &&
          setError(
            `Cannot reach the local API. Start the backend and refresh. ${e.message}`,
          ),
      );
    return () => {
      mounted = false;
      archiveRequest.current++;
    };
  }, []);
  useEffect(() => {
    if (!runA && !runB) return;
    let cancelled = false,
      inflight = false;
    const cached: { a: Event[]; b: Event[] } = { a: [], b: [] };
    let timer: ReturnType<typeof setInterval>;
    const refresh = async () => {
      if (inflight) return;
      inflight = true;
      try {
        const load = async (r: Run | null, side: "a" | "b") => {
          if (!r) return null;
          const after = cached[side].at(-1)?.seq || 0;
          const latest = await api<Run>("/runs/" + r.id);
          const delta = await api<Event[]>(
            "/runs/" + r.id + "/events?after_seq=" + after,
          );
          cached[side] = [...cached[side], ...delta];
          return { run: latest, events: cached[side] };
        };
        const [a, b] = await Promise.all([load(runA, "a"), load(runB, "b")]);
        if (cancelled) return;
        if (a) {
          setRunA(a.run);
          setEventsA(a.events);
        }
        if (b) {
          setRunB(b.run);
          setEventsB(b.events);
        }
        setError((current) =>
          current.startsWith("Could not refresh experiment:") ? "" : current,
        );
        if (!active(a?.run) && !active(b?.run)) clearInterval(timer);
      } catch (e) {
        if (!cancelled)
          setError("Could not refresh experiment: " + (e as Error).message);
      } finally {
        inflight = false;
      }
    };
    timer = setInterval(refresh, 1500);
    refresh();
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [runA?.id, runB?.id]);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () =>
        setCursor((t) => {
          const next = (t ?? 0) + 1;
          if (next >= maxTick) {
            setPlaying(false);
            return maxTick;
          }
          return next;
        }),
      650,
    );
    return () => clearInterval(timer);
  }, [playing, maxTick]);
  const snapshot = (r: Run | null, events: Event[]) => {
    if (!r) return scenario?.initial;
    if (cursor === null) return r.snapshot;
    return (
      [...events].reverse().find((e) => e.tick <= cursor)?.snapshot ||
      scenario?.initial
    );
  };
  const currentA = snapshot(runA, eventsA),
    currentB = snapshot(runB, eventsB);
  const selectedParty = selected?.party
    ? (selected.side === "A" ? currentA : currentB)?.cases.find(
        (p) => p.id === selected.party?.id,
      ) || selected.party
    : null;
  const inspectorOpen = !!selected;
  useEffect(() => {
    if (!inspectorOpen) return;
    const previous = inspectorTrigger.current;
    inspectorRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setSelected(null);
        return;
      }
      if (e.key === "Tab") {
        const items = inspectorRef.current?.querySelectorAll<HTMLElement>(
          'button,a[href],summary,input,select,textarea,[tabindex="0"]',
        );
        if (!items?.length) return;
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previous?.focus();
    };
  }, [inspectorOpen]);
  async function launch() {
    setBusy(true);
    setError("");
    try {
      const c = await api<{ run_ids: { a: string; b: string }[] }>(
        "/comparisons",
        {
          a: config(
            strategyA,
            frameworkA,
            scenarioId,
            fault,
            passengers,
            model,
          ),
          b: config(
            strategyB,
            frameworkB,
            scenarioId,
            fault,
            passengers,
            model,
          ),
          repeats: 1,
        },
      );
      const pair = c.run_ids[0];
      const [a, b] = await Promise.all([
        api<Run>("/runs/" + pair.a),
        api<Run>("/runs/" + pair.b),
      ]);
      setSingleRun(false);
      setCursor(null);
      setPlaying(false);
      setSelected(null);
      setRunA(a);
      setRunB(b);
      saveRunLink(a, b);
      setEventsA([]);
      setEventsB([]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function cancel(r: Run | null) {
    if (r) {
      try {
        await api("/runs/" + r.id + "/cancel", {});
      } catch (e) {
        setError((e as Error).message);
      }
    }
  }
  function openArchive() {
    setView("archive");
    void loadArchive();
  }
  async function inspectRun(id: string) {
    if (busy) return;
    if (active(runA) || active(runB)) {
      setError(
        "Finish or cancel the active experiment before inspecting another run.",
      );
      return;
    }
    setBusy(true);
    setError("");
    let r: Run;
    try {
      r = await api<Run>("/runs/" + encodeURIComponent(id));
    } catch (e) {
      setError(`Could not open the archived run. ${(e as Error).message}`);
      return;
    } finally {
      setBusy(false);
    }
    setSingleRun(true);
    saveRunLink(r);
    setSelected(null);
    setScenarioId(r.config.scenario_id);
    if (models.includes(r.config.model)) setModel(r.config.model);
    setFrameworkA(r.config.framework);
    setStrategyA(r.config.strategy);
    setFault(r.config.fault);
    setPassengers(r.config.passenger_mode);
    setRunA(r);
    setRunB(null);
    if (r.id !== runA?.id) setEventsA([]);
    setEventsB([]);
    setCursor(null);
    setPlaying(false);
    setView("lab");
    requestAnimationFrame(() => {
      window.scrollTo(0, 0);
      document.getElementById("workspace")?.focus({ preventScroll: true });
    });
  }
  const timeline = [
    ...eventsA.map((event) => ({ side: "A", event })),
    ...eventsB.map((event) => ({ side: "B", event })),
  ]
    .filter((x) =>
      ["action", "fault", "error", "agent_error"].includes(x.event.type),
    )
    .sort(
      (a, b) => a.event.tick - b.event.tick || a.side.localeCompare(b.side),
    );
  const visibleTimeline =
    cursor === null ? timeline : timeline.filter((x) => x.event.tick <= cursor);
  const firstBooking = timeline.find(
    ({ event }) =>
      event.action?.tool === "commit_offer" &&
      event.result?.receipt?.status === "committed",
  );
  const receipt = firstBooking?.event.result?.receipt;
  const bookedParty = firstBooking?.event.snapshot.cases.find(
    (party) => party.id === receipt?.party_id,
  );
  const bookedRoute = firstBooking?.event.snapshot.options.find(
    (option) => option.id === receipt?.option_id,
  );
  const visibleArchive = archive.map((r) =>
    r.id === runA?.id ? runA : r.id === runB?.id ? runB : r,
  );
  return (
    <div className="app">
      <a className="skip-link" href="#workspace">
        Skip to experiment
      </a>
      <aside className="sidebar" inert={inspectorOpen ? true : undefined}>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("lab");
          }}
        >
          <GitFork size={27} />
          <span>
            worldfork<span className="brand-period">.</span>
          </span>
        </a>
        <div className="nav-label">Workspace</div>
        <nav aria-label="Main">
          <button
            className={view === "lab" ? "active" : ""}
            aria-current={view === "lab" ? "page" : undefined}
            onClick={() => setView("lab")}
          >
            <FlaskConical size={18} />
            Experiment lab
          </button>
          <button
            className={view === "archive" ? "active" : ""}
            aria-current={view === "archive" ? "page" : undefined}
            onClick={openArchive}
          >
            <History size={18} />
            Run archive<span>{archive.length}</span>
          </button>
          <button
            className={view === "method" ? "active" : ""}
            aria-current={view === "method" ? "page" : undefined}
            onClick={() => setView("method")}
          >
            <BookOpen size={18} />
            Method & rules
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="connection">
            <span
              className={`dot ${health.gateway === "ok" || health.mode === "replay" ? "connected" : ""}`}
            />
            <span>
              {health.mode === "replay" ? "Recorded replay" : "Local gateway"}
              <small>
                {health.mode === "replay"
                  ? "Verified traces loaded"
                  : health.gateway === "ok"
                    ? "Bifrost is responding"
                    : "Connection not established"}
              </small>
            </span>
          </div>
          <p>
            A small world.
            <br />
            Consequences you can inspect.
          </p>
          <span className="local-label">LOCAL RESEARCH PROTOTYPE</span>
        </div>
      </aside>
      <main
        id="workspace"
        tabIndex={-1}
        inert={inspectorOpen ? true : undefined}
      >
        <header className="topbar">
          <span>
            WorldFork <ChevronRight size={13} />
            {view === "lab"
              ? "Experiment lab"
              : view === "archive"
                ? "Run archive"
                : "Method & rules"}
          </span>
          <span className="fictional">
            <FlaskConical size={14} />
            Fictional scenario · real execution
          </span>
        </header>
        {(active(runA) || active(runB)) && (
          <div className="run-banner">
            <Radio size={16} />
            <span>
              {singleRun
                ? `Run active · ${runA?.status}`
                : `Experiment active · A: ${runA?.status} · B: ${runB?.status}`}
            </span>
            <button onClick={() => setView("lab")}>Return to lab</button>
            <button
              onClick={() => {
                cancel(runA);
                cancel(runB);
              }}
            >
              Cancel experiment
            </button>
          </div>
        )}
        {error && (
          <div className="error" role="alert">
            <AlertCircle size={18} />
            <span>{error}</span>
            <button aria-label="Dismiss error" onClick={() => setError("")}>
              <X size={16} />
            </button>
          </div>
        )}
        {view === "lab" && (
          <>
            <div className={`page-heading${replay ? " replay-heading" : ""}`}>
              <div>
                <h1>
                  {singleRun
                    ? "How did this AI rebook travelers?"
                    : "Which AI approach rebooks more travelers?"}
                </h1>
                <p>
                  {singleRun
                    ? "Follow an AI support strategy as it helps travelers find a new route after a flight cancellation."
                    : "Two support strategies face the same flight cancellation in separate simulations. Compare how they help travelers when each booking changes what’s available to the next party."}
                </p>
              </div>
              <div className="scenario-note">
                <Plane size={21} />
                <strong>Harbor Airport</strong>
                <span>6 parties · 7 people · 3 alternatives</span>
                <small>One early seat is already booked.</small>
              </div>
            </div>
            {replay ? (
              <section
                className="replay-overview"
                id="recorded-experiment"
                tabIndex={-1}
                aria-labelledby="replay-overview-title"
              >
                <div className="replay-overview-header">
                  <div>
                    <h2 id="replay-overview-title">Recorded experiment</h2>
                    <p>
                      {runA
                        ? `${scenario?.label ?? "Harbor Airport"} · ${runA.config.model.replace("ollama/", "")} · ${runA.config.passenger_mode === "llm" ? "LLM passengers" : "Scripted passengers"}`
                        : "Open a run from the archive to inspect its results."}
                    </p>
                  </div>
                  <div className="replay-actions">
                    {maxTick > 0 &&
                      !eventsA.length &&
                      !eventsB.length &&
                      !error && (
                        <button className="replay-start" disabled>
                          Loading booking example…
                        </button>
                      )}
                    {firstBooking && bookedParty && bookedRoute && (
                      <a
                        className="replay-start"
                        href="#playback-controls"
                        onClick={() => {
                          setPlaying(false);
                          setCursor(firstBooking.event.tick);
                        }}
                      >
                        <Play size={16} /> See the first booking
                      </a>
                    )}
                    {runA && (
                      <a href="#decision-ledger">
                        <ListOrdered size={16} /> Decision ledger
                      </a>
                    )}
                    {singleRun && (
                      <a href={window.location.pathname}>Opening comparison</a>
                    )}
                    <button onClick={openArchive}>
                      <History size={16} /> Browse {archive.length || ""} runs
                    </button>
                  </div>
                </div>
                {runA && (
                  <div className="replay-outcomes" aria-label="Final scores">
                    {[
                      { side: "A", run: runA },
                      { side: "B", run: runB },
                    ].map(
                      ({ side, run }) =>
                        run && (
                          <div className="replay-outcome" key={side}>
                            <span
                              className={`world-letter side-${side.toLowerCase()}`}
                            >
                              {side}
                            </span>
                            <div>
                              <strong>
                                {strategyLabel(run.config.strategy)}
                              </strong>
                              <small>
                                {run.config.framework === "langgraph"
                                  ? "LangGraph"
                                  : "Plain Python"}{" "}
                                · {run.status.replaceAll("_", " ")}
                              </small>
                            </div>
                            <div className="outcome-score">
                              <strong>
                                {run.result
                                  ? `${run.result.satisfied_people} / ${run.result.total_people}`
                                  : "—"}
                              </strong>
                              <small>
                                {run.result
                                  ? "travelers helped"
                                  : "No scored result"}
                              </small>
                            </div>
                          </div>
                        ),
                    )}
                  </div>
                )}
              </section>
            ) : (
              <section
                className="configuration"
                aria-label="Experiment configuration"
              >
                <div className="config-launch">
                  <span className="budget-note">
                    <Clock3 size={14} />
                    {models.length
                      ? "Each agent gets up to 48 decisions. The runs take turns."
                      : "Recorded runs are available · start Ollama for new runs"}
                  </span>
                  <button
                    className="primary"
                    disabled={
                      busy ||
                      active(runA) ||
                      active(runB) ||
                      !scenario ||
                      !models.length
                    }
                    onClick={launch}
                  >
                    {busy
                      ? "Creating worlds…"
                      : active(runA) || active(runB)
                        ? "Experiment in progress"
                        : "Run comparison"}
                    <GitFork size={17} />
                  </button>
                </div>
                <details className="experiment-settings">
                  <summary>Experiment settings</summary>
                  <div className="config-fields">
                    <label>
                      Scenario
                      <select
                        disabled={busy || experimentActive}
                        value={scenarioId}
                        onChange={(e) => {
                          setScenarioId(e.target.value);
                          saveRunLink();
                          setRunA(null);
                          setRunB(null);
                          setSingleRun(false);
                          setEventsA([]);
                          setEventsB([]);
                          setSelected(null);
                          setCursor(null);
                          setPlaying(false);
                        }}
                      >
                        {scenarios.map((s) => (
                          <option value={s.id} key={s.id}>
                            {s.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      World A integration
                      <select
                        value={frameworkA}
                        disabled={busy || experimentActive}
                        onChange={(e) => setFrameworkA(e.target.value)}
                      >
                        <option value="python">Plain Python</option>
                        <option value="langgraph">LangGraph</option>
                      </select>
                    </label>
                    <label>
                      World B integration
                      <select
                        value={frameworkB}
                        disabled={busy || experimentActive}
                        onChange={(e) => setFrameworkB(e.target.value)}
                      >
                        <option value="python">Plain Python</option>
                        <option value="langgraph">LangGraph</option>
                      </select>
                    </label>
                    <label>
                      Controlled fault
                      <select
                        value={fault}
                        disabled={busy || experimentActive}
                        onChange={(e) => setFault(e.target.value)}
                      >
                        <option value="none">None</option>
                        <option value="model_unavailable">
                          Model unavailable
                        </option>
                        <option value="tool_timeout">Tool timeout</option>
                        <option value="misleading_observation">
                          Misleading inventory
                        </option>
                      </select>
                    </label>
                  </div>
                  <div className="config-bottom">
                    {[
                      {
                        side: "A",
                        strategy: strategyA,
                        setStrategy: setStrategyA,
                      },
                      {
                        side: "B",
                        strategy: strategyB,
                        setStrategy: setStrategyB,
                      },
                    ].map(({ side, strategy, setStrategy }) => (
                      <label className="passenger-mode" key={side}>
                        World {side} strategy
                        <select
                          value={strategy}
                          disabled={busy || experimentActive}
                          onChange={(e) => setStrategy(e.target.value)}
                        >
                          {Object.entries(strategies).map(([value, label]) => (
                            <option value={value} key={value}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </label>
                    ))}
                    <label className="passenger-mode">
                      Shared model
                      <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        disabled={busy || experimentActive || !models.length}
                      >
                        {!models.length && (
                          <option value={model}>
                            No local model available
                          </option>
                        )}
                        {models.map((name) => (
                          <option key={name} value={name}>
                            {name.replace("ollama/", "")}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="passenger-mode">
                      Population
                      <select
                        value={passengers}
                        disabled={busy || experimentActive}
                        onChange={(e) => setPassengers(e.target.value)}
                      >
                        <option value="scripted">
                          Scripted · reproducible
                        </option>
                        <option value="llm">LLM · constrained consent</option>
                      </select>
                    </label>
                  </div>
                  {frameworkA !== frameworkB && (
                    <p className="comparison-note">
                      Different integrations compare two complete setups. Choose
                      the same integration to isolate strategy.
                    </p>
                  )}
                </details>
              </section>
            )}
            <div className="comparison-heading">
              <h2>{singleRun ? "Single-run inspection" : "The two worlds"}</h2>
              <span>
                {cursor !== null
                  ? "Recorded playback"
                  : active(runA) || active(runB)
                    ? "Live execution"
                    : runA
                      ? "Recorded results"
                      : "Initial conditions"}
                <span
                  className={`dot ${active(runA) || active(runB) ? "connected" : ""}`}
                />
              </span>
            </div>
            {maxTick > 0 && (
              <div
                className="playback-bar"
                id="playback-controls"
                tabIndex={-1}
              >
                <span>
                  {singleRun ? "Replay this world" : "Replay both worlds"}
                </span>
                <div className="playback">
                  <button
                    disabled={!maxTick}
                    aria-label={
                      playing
                        ? "Pause recorded playback"
                        : "Play recorded playback"
                    }
                    onClick={() => {
                      setCursor(cursor === maxTick ? 0 : (cursor ?? 0));
                      setPlaying(!playing);
                    }}
                  >
                    {playing ? <Pause size={17} /> : <Play size={17} />}
                  </button>
                  <button
                    disabled={!maxTick}
                    aria-label="Return to latest state"
                    onClick={() => {
                      setPlaying(false);
                      setCursor(null);
                    }}
                  >
                    <RotateCcw size={16} />
                  </button>
                  <label className="sr-only" htmlFor="tick">
                    Replay logical tick
                  </label>
                  <input
                    id="tick"
                    type="range"
                    min={0}
                    max={maxTick || 1}
                    value={cursor ?? maxTick}
                    disabled={!maxTick}
                    onChange={(e) => {
                      setPlaying(false);
                      setCursor(Number(e.target.value));
                    }}
                  />
                  <span>
                    Step {cursor ?? maxTick} / {maxTick}
                  </span>
                </div>
                {firstBooking &&
                  bookedParty &&
                  bookedRoute &&
                  cursor === firstBooking.event.tick && (
                    <p className="booking-example" aria-live="polite">
                      <strong>
                        World {firstBooking.side} booked {bookedParty.name} on
                        the {bookedRoute.label.toLowerCase()}.
                      </strong>{" "}
                      {bookedRoute.available === 0
                        ? "That connection is now full."
                        : `${bookedRoute.available} ${bookedRoute.available === 1 ? "seat remains" : "seats remain"} on that connection.`}{" "}
                      Move the slider to see what happens next.
                    </p>
                  )}
              </div>
            )}
            <div className={`world-grid ${singleRun ? "single-world" : ""}`}>
              {currentA && (
                <WorldPanel
                  side="A"
                  run={runA}
                  strategy={strategyA}
                  snapshot={currentA}
                  onSelect={(party, trigger) => {
                    inspectorTrigger.current = trigger;
                    setSelected({ side: "A", party });
                  }}
                  onCancel={() => cancel(runA)}
                />
              )}{" "}
              {!singleRun && currentB && (
                <WorldPanel
                  side="B"
                  run={runB}
                  strategy={strategyB}
                  snapshot={currentB}
                  onSelect={(party, trigger) => {
                    inspectorTrigger.current = trigger;
                    setSelected({ side: "B", party });
                  }}
                  onCancel={() => cancel(runB)}
                />
              )}
            </div>
            <section
              className="timeline-section"
              id="decision-ledger"
              tabIndex={-1}
              aria-labelledby="ledger-title"
            >
              <div className="timeline-header">
                <div>
                  <h2 id="ledger-title">Decision ledger</h2>
                  <p>
                    Select a decision to see what the agent knew, what it tried,
                    and what changed.
                  </p>
                </div>
                {maxTick > 0 && (
                  <a className="ledger-jump" href="#playback-controls">
                    Back to playback
                  </a>
                )}
                {replay && (
                  <a className="ledger-jump" href="#recorded-experiment">
                    See the comparison
                  </a>
                )}
              </div>
              {visibleTimeline.length ? (
                <div className="ledger">
                  {visibleTimeline.map(({ side, event }) => (
                    <button
                      key={`${side}-${event.seq}`}
                      className={`ledger-row ${event.type === "fault" ? "fault-row" : ""}`}
                      onClick={(e) => {
                        inspectorTrigger.current = e.currentTarget;
                        setSelected({ side, event });
                      }}
                    >
                      <span className="ledger-tick">
                        {String(event.tick).padStart(2, "0")}
                      </span>
                      <span
                        className={`small-world side-${side.toLowerCase()}`}
                      >
                        {side}
                      </span>
                      <span className="ledger-action">
                        {event.action
                          ? event.action.tool.replaceAll("_", " ")
                          : event.type.replaceAll("_", " ")}
                        <small>
                          {event.action
                            ? Object.values(event.action.arguments).join(" · ")
                            : event.fault || event.error}
                        </small>
                      </span>
                      <span className="ledger-result">
                        {event.result?.ok === false
                          ? event.result.code
                          : event.result?.offer?.status ||
                            event.result?.receipt?.status ||
                            (event.type === "fault"
                              ? "Injected fault"
                              : "Recorded")}
                      </span>
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              ) : (
                <div className="empty-ledger">
                  <Radio size={24} />
                  <strong>
                    {runA
                      ? "No decisions at this point in the recording."
                      : "The world is ready. Nothing has happened yet."}
                  </strong>
                  <p>
                    {runA
                      ? "Advance the replay to inspect the recorded actions."
                      : "Run an experiment to see offers, consent, bookings and their consequences."}
                  </p>
                </div>
              )}
            </section>
            <p className="footnote">
              Synthetic outcomes, not predictions of real passenger behavior.
              Initial booking is included in totals. Model:{" "}
              {(runA?.config.model || model).replace("ollama/", "")} through
              Bifrost · local API charge: 0; hardware and electricity
              unmeasured.
            </p>
          </>
        )}
        {view === "archive" && (
          <section className="archive">
            <h1>Run archive</h1>
            <p>
              Retained evidence, including incomplete and unsuccessful runs.
            </p>
            <BenchmarkResults
              preferredRun={runA?.id}
              scenarios={scenarios}
              onInspect={inspectRun}
              disabled={busy || experimentActive}
            />
            <h2>Individual runs</h2>
            {archive.length >= 100 && (
              <p>
                The list shows the latest 100 runs. Repeated-run results include
                all runs with recorded comparison conditions.
              </p>
            )}
            {visibleArchive.length ? (
              visibleArchive.map((r) => (
                <button
                  disabled={busy || experimentActive}
                  key={r.id}
                  className="archive-row"
                  onClick={() => inspectRun(r.id)}
                >
                  <History size={19} />
                  <span>
                    <strong>{strategyLabel(r.config.strategy)}</strong>
                    <small>
                      {r.config.framework} · {r.config.fault} ·{" "}
                      {r.id.slice(0, 8)}
                    </small>
                  </span>
                  <span>
                    <strong>{r.status.replaceAll("_", " ")}</strong>
                    <small>
                      {r.result
                        ? `${r.result.satisfied_people}/${r.result.total_people} requirements met`
                        : "No scored result"}
                    </small>
                  </span>
                  <ArrowRight size={17} />
                </button>
              ))
            ) : (
              <div className="empty-ledger">
                {archiveState === "error" ? (
                  <button className="text-button" onClick={loadArchive}>
                    Could not load runs. Try again
                  </button>
                ) : archiveState === "loading" ? (
                  <span role="status">Loading runs…</span>
                ) : (
                  "No runs yet. Start in the experiment lab."
                )}
              </div>
            )}
          </section>
        )}
        {view === "method" && (
          <section className="method">
            <h1>A world with rules.</h1>
            <p className="method-lead">
              Models make decisions. The environment owns the facts.
            </p>
            <h2>What is being compared?</h2>
            <p>
              Two customer-support strategies receive the same population,
              information, tools and budgets. The plain Python and LangGraph
              integrations can each run either strategy. Changing both strategy
              and framework compares packaged systems; it does not isolate a
              framework effect.
            </p>
            <p>
              An orchestrated team adds an inventory specialist and a traveler
              specialist. Their advice helps an orchestrator choose the next
              action. Compare model calls, tokens and elapsed time alongside the
              traveler score to see what coordination costs.
            </p>
            <h2>The fictional policy</h2>
            <p>{scenario?.policy}</p>
            <h2>What counts as success?</h2>
            <p>
              Confirmed bookings must satisfy each party’s explicit arrival and
              travel constraints. Whole-party capacity, passenger consent and
              compensation are enforced by code. An allocation oracle provides
              an upper bound using all private constraints; the agent cannot see
              it.
            </p>
            <h2>What is autonomous?</h2>
            <p>
              The reference agents select from a public-state action menu. The
              shared harness removes repeated disclosures and requires resolving
              consented offers. Scripted passengers follow explicit acceptance
              contracts. LLM passenger mode permits independent consent
              decisions within those contracts; neither mode is a validated
              model of real people.
            </p>
            <h2>Evidence and limits</h2>
            <p>
              Events retain observations, candidate actions, tool results, model
              usage and world snapshots. Faults are injected experiments and are
              labeled. A single run is illustrative; use repeated trials and
              report all outcomes before drawing conclusions.
            </p>
          </section>
        )}
        <footer className="page-footer">
          <span>
            <GitFork size={14} />
            WorldFork
          </span>
          <span>Built to make agent decisions visible.</span>
        </footer>
      </main>
      {selected && (
        <aside
          ref={inspectorRef}
          role="dialog"
          aria-modal="true"
          className="inspector"
          aria-label="Evidence inspector"
        >
          <header>
            <span>
              World {selected.side} ·{" "}
              {selected.party ? "Passenger" : "Decision"} inspector
            </span>
            <button
              aria-label="Close inspector"
              onClick={() => setSelected(null)}
            >
              <X size={18} />
            </button>
          </header>
          {selectedParty ? (
            <>
              <h2>{selectedParty.name}</h2>
              <p>
                {selectedParty.people}{" "}
                {selectedParty.people === 1 ? "person" : "people"} · fictional
                passenger
              </p>
              <blockquote>{selectedParty.request}</blockquote>
              <h3>Disclosed requirements</h3>
              {Object.keys(selectedParty.known).length ? (
                <pre>{JSON.stringify(selectedParty.known, null, 2)}</pre>
              ) : (
                <p>No private requirements disclosed yet.</p>
              )}
              <h3>Booking receipt</h3>
              <pre>{JSON.stringify(selectedParty.booking, null, 2)}</pre>
              <p className="inspector-note">
                Private ground truth is excluded from this view and from
                support-agent observations.
              </p>
            </>
          ) : selected.event?.type === "fault" ? (
            <>
              <h2>{selected.event.fault?.replaceAll("_", " ")}</h2>
              <p>Injected fault · tick {selected.event.tick}</p>
              {selected.event.message && <p>{selected.event.message}</p>}
              {selected.event.visibility && (
                <p>
                  Recorded visibility:{" "}
                  {selected.event.visibility.replaceAll("_", " ")}
                </p>
              )}
              {selected.event.truth !== undefined && (
                <>
                  <h3>Actual inventory</h3>
                  <pre>{JSON.stringify(selected.event.truth, null, 2)}</pre>
                </>
              )}
              {selected.event.shown !== undefined && (
                <>
                  <h3>Inventory shown to the agent</h3>
                  <pre>{JSON.stringify(selected.event.shown, null, 2)}</pre>
                </>
              )}
            </>
          ) : (
            <>
              <h2>
                {selected.event?.action?.tool.replaceAll("_", " ") ||
                  selected.event?.type}
              </h2>
              <p>
                Logical tick {selected.event?.tick} · event{" "}
                {selected.event?.seq}
              </p>
              {selected.event?.coordination && (
                <>
                  <h3>Orchestrator plan</h3>
                  <p>{selected.event.coordination.plan}</p>
                  {selected.event.coordination.consultation_reason && (
                    <p>
                      {
                        {
                          initial:
                            "Both specialists were consulted to begin the plan.",
                          booking_changed:
                            "Both specialists were consulted after a booking changed availability.",
                          action_failed:
                            "Both specialists were consulted after an unsuccessful action.",
                          resolve_offer:
                            "The orchestrator is resolving an accepted offer using its latest receipt.",
                          reuse_advice:
                            "The orchestrator is reassessing earlier advice against the current world.",
                        }[selected.event.coordination.consultation_reason]
                      }
                    </p>
                  )}
                  {selected.event.coordination.prior_advice?.length ? (
                    <>
                      <h3>Earlier specialist advice</h3>
                      <ul>
                        {selected.event.coordination.prior_advice.map(
                          (advice) => (
                            <li key={advice.role}>
                              {advice.role === "inventory_specialist"
                                ? "Inventory specialist"
                                : "Traveler specialist"}
                              {" · tick "}
                              {advice.tick}
                              <p>{advice.plan}</p>
                            </li>
                          ),
                        )}
                      </ul>
                    </>
                  ) : null}
                  {selected.event.coordination.proposals.length > 0 && (
                    <>
                      <h3>Specialist proposals</h3>
                      <ul>
                        {selected.event.coordination.proposals.map(
                          (proposal) => {
                            const action =
                              selected.event?.candidate_actions?.find(
                                (candidate) =>
                                  candidate.id === proposal.action_id,
                              );
                            return (
                              <li key={proposal.role}>
                                <strong>
                                  {proposal.role === "inventory_specialist"
                                    ? "Inventory specialist"
                                    : "Traveler specialist"}
                                </strong>
                                {action && (
                                  <> · {action.tool.replaceAll("_", " ")}</>
                                )}
                                <p>
                                  {proposal.plan ??
                                    "No valid proposal returned."}
                                </p>
                              </li>
                            );
                          },
                        )}
                      </ul>
                    </>
                  )}
                </>
              )}
              <h3>Action</h3>
              <pre>
                {JSON.stringify(
                  selected.event?.action || { fault: selected.event?.fault },
                  null,
                  2,
                )}
              </pre>
              <h3>Tool result</h3>
              <pre>
                {JSON.stringify(
                  selected.event?.result || selected.event?.error || null,
                  null,
                  2,
                )}
              </pre>
              <details>
                <summary>Stored agent observation</summary>
                {selected.event?.action?.tool === "ask_question" &&
                  selected.event.result?.ok &&
                  (selected.side === "B" ? runB : runA)?.config.source_hashes
                    ?.engine ===
                    "7b9aed1bc23dc5a8d8f1fa31d60b80ce12c979cb1334996b40f733c2e8ec91ca" && (
                    <p className="inspector-note">
                      Archived disclosure: the saved view may include the answer
                      from this tool result. The model request was sent before
                      the answer.
                    </p>
                  )}
                <pre>
                  {JSON.stringify(selected.event?.observation, null, 2)}
                </pre>
              </details>
              <details>
                <summary>Candidate actions</summary>
                <pre>
                  {JSON.stringify(selected.event?.candidate_actions, null, 2)}
                </pre>
              </details>
              <details>
                <summary>Model attempt metrics</summary>
                <pre>{JSON.stringify(selected.event?.attempts, null, 2)}</pre>
              </details>
            </>
          )}
        </aside>
      )}
    </div>
  );
}
