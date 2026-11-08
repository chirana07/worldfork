/** Author the current submission deck from retained evidence and real UI captures. */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../", import.meta.url));
const colors = {
  ink: "#172C30",
  teal: "#096958",
  muted: "#526469",
  paper: "#F5F4EF",
  line: "#D9DFDC",
};
function text(
  slide,
  value,
  x,
  y,
  width,
  height,
  size = 28,
  color = colors.ink,
  bold = false,
) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = { fontFamily: "Arial", fontSize: size, color, bold };
  shape.text.insets = 0;
  return shape;
}
function title(slide, value) {
  text(slide, value, 72, 48, 1136, 100, 46, colors.ink, true);
}
function note(slide, value) {
  slide.speakerNotes.text = value;
}
function table(
  slide,
  values,
  y,
  widths,
  fontSize = 26,
  frame = { left: 72, width: 1136 },
) {
  const result = slide.tables.add({
    rows: values.length,
    columns: values[0].length,
    left: frame.left,
    top: y,
    width: frame.width,
    height: values.length * 66,
    columnWidths: widths,
    values,
  });
  result.borders.assign({ fill: colors.line, width: 0.6, style: "solid" });
  for (let r = 0; r < values.length; r++)
    for (let c = 0; c < values[0].length; c++) {
      const cell = result.getCell(r, c);
      cell.fill = r === 0 ? colors.ink : colors.paper;
      cell.text.style = {
        fontFamily: "Arial",
        fontSize,
        color: r === 0 ? "#FFFFFF" : colors.ink,
        bold: r === 0,
      };
    }
  return result;
}
async function image(slide, filename, frame, alt) {
  const bytes = await fs.readFile(
    path.join(root, "artifacts/submission-build", filename),
  );
  slide.images.add({
    dataUrl: "data:image/png;base64," + bytes.toString("base64"),
    position: frame,
    fit: "contain",
    alt,
  });
}
function node(slide, label, x, y, width) {
  const shape = slide.shapes.add({
    geometry: "rect",
    position: { left: x, top: y, width, height: 100 },
    fill: "#FFFFFF",
    line: { fill: colors.line, width: 1 },
  });
  text(slide, label, x + 14, y + 18, width - 28, 72, 25, colors.ink, true);
  return shape;
}
function arrow(slide, x, y, width) {
  slide.shapes.add({
    geometry: "rightArrow",
    position: { left: x, top: y, width, height: 17 },
    fill: colors.teal,
    line: { fill: "none", width: 0 },
  });
}
export async function author(
  presentation,
  {
    manifestPath = "evidence/pilot-manifest.json",
    releaseManifestPath = "evidence/team-evaluation/manifest.json",
    presenter = "Chirana",
  } = {},
) {
  const read = async (filename) =>
    JSON.parse(await fs.readFile(path.join(root, filename), "utf8"));
  const pilotManifest = await read(manifestPath);
  const releaseManifest = await read(releaseManifestPath);
  const pilot = await Promise.all(
    pilotManifest.runs.map(async (e) => (await read(e.trace)).run),
  );
  const release = await Promise.all(
    releaseManifest.runs.map(
      async (e) => (await read("evidence/team-evaluation/" + e.trace)).run,
    ),
  );
  if (
    pilot.length !== 30 ||
    release.length !== 24 ||
    [...pilot, ...release].some(
      (r) => !["completed", "stopped", "exhausted"].includes(r.status),
    )
  )
    throw Error("Evidence is incomplete");
  const totals = (strategy) => {
    const runs = release.filter((r) => r.config.strategy === strategy);
    return {
      n: runs.length,
      mean:
        runs.reduce((sum, r) => sum + r.result.satisfied_people, 0) /
        runs.length,
      calls: runs.reduce((sum, r) => sum + r.result.model_calls, 0),
      tokens: runs.reduce(
        (sum, r) => sum + r.result.input_tokens + r.result.output_tokens,
        0,
      ),
    };
  };
  const solo = totals("coordinated"),
    team = totals("team");
  if (solo.calls !== 166 || team.calls !== 288)
    throw Error("Release figures differ from the reviewed evidence");
  presentation.slides.keep([]);
  const add = () => {
    const slide = presentation.slides.add({ width: 1280, height: 720 });
    slide.background.fill = colors.paper;
    return slide;
  };
  let s = add();
  text(s, "worldfork.", 72, 138, 1136, 126, 100, colors.ink, true);
  text(
    s,
    "Benchmark support agents\nwhere resources are shared",
    76,
    310,
    1120,
    150,
    46,
    colors.teal,
  );
  text(
    s,
    `${presenter}\nGlobal AI Hackathon. Bifrost agent benchmarking challenge.`,
    78,
    586,
    1120,
    84,
    25,
    colors.muted,
  );
  note(
    s,
    "WorldFork is an original local hackathon prototype. Its fictional passengers and resources create shared allocation consequences. Repository: https://github.com/chirana07/worldfork. Codex assisted implementation.",
  );

  s = add();
  title(s, "Valid bookings can leave a family waiting");
  text(s, "7 / 7", 72, 153, 240, 80, 60, colors.teal, true);
  text(s, "Case-by-case service", 315, 173, 310, 60, 28);
  text(s, "5 / 7", 710, 153, 240, 80, 60, colors.ink, true);
  text(s, "Shared planning", 940, 173, 285, 60, 28);
  const waitingRun = pilot.find(
    (run) => run.id === "68bbf46f-fe10-4342-96d3-acdbdbac47eb",
  );
  const early = waitingRun.snapshot.cases.filter(
    (party) => party.booking?.option_id === "E",
  );
  text(s, "World B's early flight", 72, 247, 530, 45, 25, colors.muted);
  table(
    s,
    [
      ["Committed booking", "People"],
      ...early.map((party) => [party.name, String(party.people)]),
    ],
    300,
    [370, 160],
    25,
    { left: 72, width: 530 },
  );
  text(s, "Arun & Nila", 680, 280, 525, 60, 36, colors.ink, true);
  text(
    s,
    "Two people need the same flight.\nNo early seats remain.",
    680,
    360,
    525,
    95,
    28,
  );
  await image(
    s,
    "family.png",
    { left: 680, top: 490, width: 525, height: 83 },
    "Actual waiting-party row from World B",
  );
  text(
    s,
    "Both runs recorded zero committed policy violations. The party of two waits in World B.",
    72,
    621,
    1136,
    62,
    22,
    colors.muted,
  );
  note(
    s,
    "Illustrative frozen-pilot pair, not an aggregate. LangGraph, seed 29, Qwen3.5:4b, scripted passengers, same initial fixture and budgets. Case-by-case fe3b30ed-4b91-49c2-918c-383b8e2e936a reached 7/7. Coordinated 68bbf46f-fe10-4342-96d3-acdbdbac47eb ended at 5/7 with Arun and Nila unbooked. Source exports are linked in evidence/pilot-manifest.json.",
  );

  s = add();
  title(s, "Architecture and the experiment boundary");
  text(s, "Model decisions", 72, 160, 600, 45, 27, colors.muted);
  node(s, "Python or\nLangGraph agent", 72, 225, 245);
  arrow(s, 332, 266, 40);
  node(s, "Measured\nmodel client", 387, 225, 225);
  arrow(s, 627, 266, 40);
  node(s, "Bifrost\ngateway", 682, 225, 225);
  arrow(s, 922, 266, 40);
  node(s, "Local\nOllama model", 977, 225, 230);
  text(s, "Tool execution and scoring", 72, 378, 900, 45, 27, colors.muted);
  node(s, "Selected action", 72, 440, 285);
  arrow(s, 375, 481, 55);
  node(s, "World rules\nand transactions", 448, 440, 325);
  arrow(s, 792, 481, 55);
  node(s, "Receipts and\nindependent score", 865, 440, 342);
  text(
    s,
    "React, FastAPI and SQLite expose the recorded state and decisions.\nPrivate requirements and the scoring oracle stay outside the support-agent context.",
    72,
    594,
    1136,
    95,
    24,
    colors.muted,
  );
  note(
    s,
    "Implemented architecture in docs/architecture.md. All scored reference-agent inference uses Gateway through Bifrost. Native Ollama inspection endpoints provide model metadata. The world enforces capacity, whole parties, consent, expiring holds, compensation and atomic replacement. Optional LLM passenger consent is outside the scored studies. The diagram is editable.",
  );

  s = add();
  title(s, "Specialists advise an orchestrator");
  text(
    s,
    "Inventory specialist\nRecommends uses of scarce capacity.\n\nTraveler specialist\nChecks disclosed requirements.\n\nOrchestrator\nReassesses advice and chooses an action.",
    72,
    180,
    570,
    350,
    29,
  );
  await image(
    s,
    "team-detail.png",
    { left: 700, top: 155, width: 505, height: 450 },
    "Actual decision inspector with specialist proposals and the orchestrator plan",
  );
  text(
    s,
    "Specialists refresh after bookings or failed actions. Earlier advice keeps its original tick and action.",
    72,
    603,
    1136,
    75,
    25,
    colors.muted,
  );
  note(
    s,
    "Actual release trace e.g. first clean transfer seed 17. source in evidence/team-evaluation/manifest.json. TeamAgent consults specialists initially, after committed bookings or failed actions. It resolves accepted offers before reconsulting. Advice is advisory data, and receipts determine actual changes. A model plan may be mistaken.",
  );

  s = add();
  title(s, "Repeated runs reveal outcome variation");
  await image(
    s,
    "summary-detail.png",
    { left: 72, top: 150, width: 1136, height: 430 },
    "Actual repeated-run comparison panel showing means, outcome ranges and measured resources",
  );
  text(
    s,
    "The first pair scored 2 versus 5.\nThree clean seed means: solo 2.00, team 2.33.",
    72,
    592,
    1136,
    65,
    25,
    colors.teal,
    true,
  );
  text(
    s,
    "Groups match the task, model digest, source, decoding and budgets. Missing usage stays unknown.",
    72,
    666,
    1136,
    38,
    20,
    colors.muted,
  );
  note(
    s,
    "Source: evidence/team-evaluation/report.md, clean harbor-transfer-v1 rows and matched outcomes. The team scores were 5,1,1, the solo scores 2,2,2. Screenshot comes from the actual /api/benchmarks panel. It also reports full success, steps, tool/model calls, tokens, local API charge, elapsed time and fault exposure. Runtime API aggregates every retained record, independent of the individual archive window.",
  );

  s = add();
  title(s, "Thirty verified pilot episodes");
  const cleanRows = [];
  for (const framework of ["python", "langgraph"])
    for (const strategy of ["case_by_case", "coordinated"]) {
      const runs = pilot
        .filter(
          (r) =>
            r.config.framework === framework &&
            r.config.strategy === strategy &&
            r.config.fault === "none",
        )
        .sort((a, b) => a.config.seed - b.config.seed);
      cleanRows.push([
        framework === "python" ? "Python" : "LangGraph",
        strategy === "case_by_case" ? "Case-by-case" : "Shared planning",
        runs.map((r) => r.result.satisfied_people).join(", "),
        `${runs.filter((r) => r.status === "completed").length} / ${runs.length}`,
      ]);
    }
  table(
    s,
    [
      ["Integration", "Strategy", "People met / 7", "Full success"],
      ...cleanRows,
    ],
    178,
    [230, 300, 330, 276],
    25,
  );
  text(
    s,
    "12 clean runs. Three requested seeds per design.\n18 additional controlled fault trials, with all 18 exposures delivered.",
    72,
    542,
    1136,
    90,
    28,
    colors.teal,
  );
  text(
    s,
    "Qwen3.5:4b. Harbor development fixture. Source and continuation provenance accompany the exports.",
    72,
    650,
    1136,
    42,
    20,
    colors.muted,
  );
  note(
    s,
    "Source: evidence/pilot-summary.md and pilot-manifest.json. Seeds 11,29,47. Clean matrix two frameworks by two strategies by three seeds. Fault matrix Python, two strategies, three fault types, three seeds. Three original interrupted misleading-input trials have retained originals and declared replacements. Historical observation alias affects 439 logged disclosure observations, documented in docs/trace-provenance.md. Recorded actions, receipts, scores and token sums all passed deterministic replay.",
  );

  s = add();
  title(s, "Coordination improves some outcomes at a cost");
  table(
    s,
    [
      ["Design", "Mean people / 7", "Model calls", "Observed tokens"],
      [
        "Solo planner",
        solo.mean.toFixed(2),
        solo.calls.toLocaleString("en-US"),
        solo.tokens.toLocaleString("en-US"),
      ],
      [
        "Specialist team",
        team.mean.toFixed(2),
        team.calls.toLocaleString("en-US"),
        team.tokens.toLocaleString("en-US"),
      ],
    ],
    180,
    [300, 280, 260, 296],
    27,
  );
  text(
    s,
    "7 team wins, 3 losses and 2 ties across 12 matched pairs",
    72,
    424,
    1136,
    64,
    34,
    colors.teal,
    true,
  );
  text(
    s,
    "9 of 12 configured timeouts were delivered. Later bookings followed in\n5 of 5 exposed team runs and 2 of 4 exposed solo runs.",
    72,
    512,
    1136,
    90,
    27,
  );
  text(
    s,
    "Separate 24-run study. Python. Three seeds. Two fixtures. Sixteen steps per run. No release run met all seven.",
    72,
    638,
    1136,
    58,
    20,
    colors.muted,
  );
  note(
    s,
    "Source: evidence/team-evaluation/report.md and manifest.json. Seeds 17,43,71, two fixtures, clean/timeout conditions, solo/team strategies. Each strategy has 12 episodes and 166 actual tool actions. Team used 288 calls vs166 solo, 1.73 times. Team reused advice on75 decisions, skipping150 specialist requests on those observed paths. This does not predict what the earlier policy would have achieved. Twenty runs reached the step cap, four stopped early. Every exposed timeout episode had subsequent successful tools. Success means ok true; a booking requires a committed receipt. These observations do not establish restoration of the clean outcome.",
  );

  s = add();
  title(s, "A reproducible benchmark for review");
  const repo = text(
    s,
    "github.com/chirana07/worldfork",
    72,
    175,
    1136,
    65,
    40,
    colors.teal,
    true,
  );
  repo.hyperlink = {
    uri: "https://github.com/chirana07/worldfork",
    isExternal: true,
  };
  text(
    s,
    "Public source and verified traces\n66 tests and Docker verification\nRecorded replay without model credentials",
    72,
    285,
    590,
    190,
    31,
  );
  text(
    s,
    "AI decisions use Ollama through Bifrost.\nLangGraph provides one integration.\nCodex assisted implementation.",
    720,
    285,
    490,
    170,
    28,
    colors.muted,
  );
  text(
    s,
    "Current evidence covers one small model and a synthetic airport domain.\nAdditional models, support domains and agent integrations need validation.",
    72,
    505,
    1136,
    100,
    28,
  );
  text(
    s,
    `${presenter}. Local replay and installation instructions are in the README.`,
    72,
    640,
    1136,
    45,
    23,
    colors.muted,
  );
  note(
    s,
    "Public repository https://github.com/chirana07/worldfork. README includes source-faithful setup and no-inference replay commands. docs/challenge-alignment.md maps the Bifrost briefing to features. docs/adapter-guide.md describes reference adapter and generic message-tool bridge limits. No real airline, travelers, transactions or money. Local API charge is zero, with hardware and electricity unmeasured. 66 tests and full Docker CI passed before this media refresh. Source tests will run again with the final package.",
  );
  return {
    slides: presentation.slides.items.length,
    pilot_runs: pilot.length,
    release_runs: release.length,
    presenter,
  };
}
