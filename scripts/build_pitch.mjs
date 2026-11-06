import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const ink = "#203236",
  teal = "#176D5E",
  muted = "#526562",
  paper = "#F6F5EF";

function text(
  slide,
  value,
  x,
  y,
  width,
  height,
  size = 28,
  color = ink,
  bold = false,
) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  box.text = value;
  box.text.style = { fontFamily: "Arial", fontSize: size, color, bold };
  return box;
}
function title(slide, value) {
  text(slide, value, 72, 56, 1136, 100, 48, ink, true);
}
function table(slide, values, top, widths, frame = {}) {
  const t = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: frame.left ?? 72,
    top,
    width: frame.width ?? 1136,
    height: values.length * 54,
    columnWidths: widths,
    values,
  });
  t.borders.assign({ fill: "#D7DFD8", width: 0.6, style: "solid" });
  for (let r = 0; r < values.length; r++)
    for (let c = 0; c < values[0].length; c++) {
      const cell = t.getCell(r, c);
      cell.fill = r === 0 ? ink : paper;
      cell.text.style = {
        fontFamily: "Arial",
        fontSize: 25,
        color: r === 0 ? "#FFFFFF" : ink,
        bold: r === 0,
      };
    }
  return t;
}
function notes(slide, value) {
  slide.speakerNotes.text = value;
}
function group(m, framework, strategy, fault = "none") {
  return m.runs.filter(
    (e) =>
      e.config.framework === framework &&
      e.config.strategy === strategy &&
      (e.config.fault || "none") === fault,
  );
}
function values(entries) {
  return entries.map((e) => e.result?.satisfied_people ?? "—").join(", ");
}
function complete(entries) {
  return `${entries.filter((e) => e.status === "completed").length}/${entries.length}`;
}

export async function author(
  presentation,
  {
    manifestPath = "artifacts/benchmark-20261105T170022Z.json",
    final = false,
  } = {},
) {
  const m = JSON.parse(
    await fs.readFile(path.join(root, manifestPath), "utf8"),
  );
  const finished = m.runs.filter(
    (e) => e.result && ["completed", "exhausted", "stopped"].includes(e.status),
  ).length;
  if (final && (m.runs.length !== 30 || finished !== 30))
    throw new Error(`Pilot incomplete: ${finished}/30`);
  presentation.slides.keep([]);
  const add = () => {
    const s = presentation.slides.add({ width: 1280, height: 720 });
    s.background.fill = paper;
    return s;
  };
  let s = add();
  text(s, "worldfork.", 72, 150, 1136, 125, 104, ink, true);
  text(
    s,
    "Test agents where consequences\nare shared",
    76,
    315,
    1050,
    150,
    48,
    teal,
  );
  text(
    s,
    "A local experiment lab for AI support agents",
    78,
    590,
    1100,
    50,
    26,
    muted,
  );
  notes(
    s,
    "WorldFork. Original local hackathon prototype. Bifrost benchmarking challenge. All passengers, resources and policies are fictional. AI-assisted implementation using Codex.",
  );

  s = add();
  title(s, "Seven people, three early seats");
  text(s, "5/7", 72, 194, 400, 150, 110, teal, true);
  text(s, "people’s requirements met", 78, 355, 450, 70, 30);
  text(
    s,
    "11 commits · 7 replacements\n80 credits spent · 0 committed violations",
    78,
    470,
    470,
    110,
    26,
    muted,
  );
  table(
    s,
    [
      ["Early-flight seats", "People"],
      ["Leo", "1"],
      ["Mira", "1"],
      ["Jules", "1"],
    ],
    185,
    [430, 150],
    { left: 625, width: 580 },
  );
  text(s, "Arun & Nila: two people waiting", 625, 440, 580, 80, 32, ink, true);
  text(
    s,
    "Valid transactions can still produce\na poor shared allocation.",
    625,
    550,
    580,
    100,
    28,
    muted,
  );
  notes(
    s,
    "Development diagnostic, not frozen pilot. Llama3.1 case_by_case run 6fe13b2d-145d-4db8-a394-21f98a586017: 48 decisions, 5/7 people, 80 compensation spent, 11 commits including 7 replacements, zero committed policy violations. Retained full trace: artifacts/calibration-case_by_case.json. The displayed allocation is actual terminal state. The all-seven allocation is feasible under full synthetic information.",
  );

  s = add();
  title(s, "Replay the consequences");
  text(s, "7/7", 72, 160, 230, 90, 66, teal, true);
  text(s, "case-by-case", 292, 184, 290, 50, 27);
  text(s, "5/7", 680, 160, 230, 90, 66, ink, true);
  text(s, "coordinated design", 900, 184, 320, 50, 27);
  const image = await fs.readFile(path.join(root, "artifacts/pitch-ui.jpg"));
  s.images.add({
    dataUrl: "data:image/jpeg;base64," + image.toString("base64"),
    alt: "Actual WorldFork recorded comparison showing limited connections in two independent worlds",
    fit: "contain",
    position: { left: 72, top: 275, width: 1136, height: 382 },
  });
  text(
    s,
    "Development pair · same Qwen3.5:4b, seed, tools and budgets",
    74,
    662,
    1130,
    32,
    19,
    muted,
  );
  notes(
    s,
    "Actual Qwen development comparison, separate from frozen pilot. A a39a0063-698d-48e7-85a2-b3362aba36fd completed 7/7 in 41 decisions; B d4a6ab5c-3168-488e-9282-4e73ed69dcc5 exhausted 48 decisions at 5/7. Both Python, scripted passengers, seed11, temperature0.2. The screenshot is actual rendered app data. These two runs do not establish a strategy advantage.",
  );

  s = add();
  title(s, "The experiment boundary");
  text(s, "Model calls", 72, 184, 300, 40, 25, muted, true);
  text(
    s,
    "Agent  →  Bifrost  →  local Ollama",
    72,
    246,
    1136,
    70,
    42,
    ink,
    true,
  );
  text(s, "Tool execution", 72, 372, 300, 40, 25, muted, true);
  text(
    s,
    "Agent  →  shared world  →  independent scorer",
    72,
    430,
    1136,
    80,
    38,
    teal,
    true,
  );
  text(
    s,
    "Private passenger constraints stay outside the support-agent context.\nConsent, capacity, holds and compensation are enforced in code.\nReact + FastAPI + SQLite expose the recorded decisions and receipts.",
    72,
    558,
    1136,
    120,
    26,
    muted,
  );
  notes(
    s,
    "Implemented architecture: React/Vite/TypeScript -> FastAPI -> single local inference queue -> Python or LangGraph reference adapter -> measured Bifrost -> Ollama; typed tool execution returns to deterministic world and SQLite traces. Scripted acceptance baseline; optional LLM passenger consent mode exists but is outside this pilot. Full-private-information oracle stays evaluator-only. Native text/arrows are editable.",
  );

  s = add();
  title(
    s,
    final
      ? "Clean pilot: three seeds per design"
      : "Clean pilot in progress",
  );
  const designs = [
    ["Python", "python", "case_by_case"],
    ["Python", "python", "coordinated"],
    ["LangGraph", "langgraph", "case_by_case"],
    ["LangGraph", "langgraph", "coordinated"],
  ];
  table(
    s,
    [
      ["Integration", "Strategy", "Resolved people / 7", "Completed"],
      ...designs.map(([label, f, st]) => {
        const e = group(m, f, st);
        return [
          label,
          st === "case_by_case" ? "Case-by-case" : "Coordinated",
          values(e),
          complete(e),
        ];
      }),
    ],
    190,
    [240, 300, 366, 230],
  );
  text(
    s,
    "Seeds 11, 29, 47 · identical public-menu harness and budgets\nQwen3.5:4b · scripted passengers · Harbor development fixture",
    72,
    520,
    1136,
    95,
    27,
    muted,
  );
  text(
    s,
    "Three repeats per cell are a pilot; no statistical significance claim.",
    72,
    638,
    1136,
    40,
    22,
    muted,
  );
  notes(
    s,
    `Source: ${manifestPath}; frozen harness ${m.git_revision}; lock ${m.dependency_lock_sha256}. Clean matrix 2 frameworks x2 strategies x3 seeds. Outcome order follows queue seed order. Framework and strategy are independent axes. Reversed/rotated order is incompletely counterbalanced with three repeats. Every failure is retained. Pilot completion at authoring: ${finished}/30.`,
  );

  s = add();
  title(
    s,
    final
      ? "Controlled faults: exposure and completion"
      : "Fault pilot in progress",
  );
  const faultNames = {
    model_unavailable: "Model unavailable",
    tool_timeout: "Tool timeout",
    misleading_observation: "Misleading inventory",
  };
  const rows = [];
  for (const fault of Object.keys(faultNames))
    for (const st of ["case_by_case", "coordinated"]) {
      const e = group(m, "python", st, fault);
      rows.push([
        faultNames[fault],
        st === "case_by_case" ? "Case-by-case" : "Coordinated",
        `${e.filter((x) => x.result?.fault_delivered).length}/${e.length}`,
        complete(e),
        values(e),
      ]);
    }
  table(
    s,
    [
      ["Synthetic fault", "Strategy", "Exposed", "Completed", "People / 7"],
      ...rows,
    ],
    180,
    [320, 240, 166, 190, 220],
  );
  text(
    s,
    "Python reference integration · three seeds per fault and strategy\nUnavailable-model retry is automatic harness behavior.",
    72,
    588,
    1136,
    85,
    25,
    muted,
  );
  notes(
    s,
    `Source: ${manifestPath}. Faults are controlled interventions, not natural incidents. Model unavailable injects one no-provider-request failure, then the harness retries. Timeout fails before mutation at/after tick8. Misleading observation adds one displayed early-flight seat at/after tick8; ground-truth capacity remains enforced. Exposures and terminal counts are separate. Reported completion describes the whole system under that intervention, not model-generated retry reasoning.`,
  );

  s = add();
  title(s, "A small, inspectable testbed");
  text(s, "Implemented", 72, 180, 400, 45, 28, teal, true);
  text(
    s,
    "Two reference integrations\nGeneric ReAct bridge example\nConsent and transaction receipts\nPortable traces and model usage",
    72,
    252,
    535,
    200,
    30,
  );
  text(s, "Scope", 680, 180, 470, 45, 28, ink, true);
  text(
    s,
    "Synthetic passenger contracts\nTwo development fixtures\nOne small local model in this pilot\nNo real-world reliability claim",
    680,
    252,
    535,
    200,
    30,
    muted,
  );
  text(
    s,
    "Next: untouched scenarios and independently tested agent integrations",
    72,
    520,
    1136,
    85,
    30,
    ink,
    true,
  );
  text(
    s,
    "Run locally:  uv run python scripts/backend.py",
    72,
    641,
    1136,
    40,
    25,
    teal,
  );
  notes(
    s,
    "AI use: local Ollama decisions, Bifrost inference gateway, LangGraph integration, Codex-assisted implementation. Main pilot uses scripted passenger acceptance contracts, not a swarm of independently validated human models. LLM passenger mode is implemented separately and is not represented as evaluated here. Third-party prebuilt ReAct smoke: four actual disclosure actions through measured Bifrost, with no changes to the library agent loop. Its factory is deprecated in the installed release; no universal integration claim. Future features are explicitly labeled Next.",
  );
  return { slides: presentation.slides.items.length, finished, manifestPath };
}

export async function render(
  presentation,
  directory = "artifacts/pitch-previews",
) {
  const target = path.join(root, directory);
  await fs.mkdir(target, { recursive: true });
  for (const [i, s] of presentation.slides.items.entries()) {
    const image = await presentation.export({
      slide: s,
      format: "png",
      scale: 1,
    });
    await fs.writeFile(
      path.join(target, `slide-${i + 1}.png`),
      new Uint8Array(await image.arrayBuffer()),
    );
  }
  return target;
}
