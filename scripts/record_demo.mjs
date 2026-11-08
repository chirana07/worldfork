/** Record guided playback from verified evidence without microphone or audio capture. */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(root, "artifacts/submission-build");
const { chromium } = await import(
  process.env.WORLDFORK_PLAYWRIGHT_MODULE ?? "playwright"
);
const pilotUrl = process.env.WORLDFORK_PILOT_URL ?? "http://127.0.0.1:8002";
const teamUrl = process.env.WORLDFORK_TEAM_URL ?? "http://127.0.0.1:8006";
const read = async (filename) =>
  JSON.parse(await fs.readFile(path.join(root, filename), "utf8"));
const pilotManifest = await read("evidence/pilot-manifest.json");
const releaseManifest = await read("evidence/team-evaluation/manifest.json");
const storyboard = await read("scripts/demo_storyboard.json");
const sources = {};
for (const strategy of ["case_by_case", "coordinated"]) {
  const entry = pilotManifest.runs.find(
    (e) =>
      e.config.framework === "langgraph" &&
      e.config.seed === 29 &&
      e.config.fault === "none" &&
      e.config.strategy === strategy,
  );
  sources["pilot_" + strategy] = await read(entry.trace);
}
for (const [key, scenario, fault, strategy] of [
  ["solo", "harbor-transfer-v1", "none", "coordinated"],
  ["team", "harbor-transfer-v1", "none", "team"],
  ["fault_solo", "harbor-v1", "tool_timeout", "coordinated"],
  ["fault_team", "harbor-v1", "tool_timeout", "team"],
]) {
  const entry = releaseManifest.runs.find(
    (e) =>
      e.config.seed === 17 &&
      e.config.scenario_id === scenario &&
      e.config.fault === fault &&
      e.config.strategy === strategy,
  );
  sources[key] = await read("evidence/team-evaluation/" + entry.trace);
}
if (
  sources.pilot_case_by_case.run.result.satisfied_people !== 7 ||
  sources.pilot_coordinated.run.result.satisfied_people !== 5
)
  throw Error("Opening outcome differs");
for (const url of [pilotUrl, teamUrl]) {
  const health = await (await fetch(url + "/api/health")).json();
  if (health.mode !== "replay")
    throw Error("Only recorded replay servers may be filmed");
}
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(process.env.WORLDFORK_CHROME
    ? { executablePath: process.env.WORLDFORK_CHROME }
    : {}),
});
const sourceIds = Object.fromEntries(
  Object.entries(sources).map(([key, value]) => [key, value.run.id]),
);

async function pair(page, kind = "pilot") {
  let url = pilotUrl,
    a = sourceIds.pilot_case_by_case,
    b = sourceIds.pilot_coordinated;
  if (kind === "team") {
    url = teamUrl;
    a = sourceIds.solo;
    b = sourceIds.team;
  }
  if (kind === "fault") {
    url = teamUrl;
    a = sourceIds.fault_solo;
    b = sourceIds.fault_team;
  }
  await page.goto(`${url}/?a=${a}&b=${b}`);
  await page.locator(".world-result a[download]").nth(1).waitFor();
  await page.evaluate(() => {
    document.documentElement.style.scrollBehavior = "smooth";
  });
}
async function tick(page, value) {
  await page.getByLabel("Replay logical tick").fill(String(value));
}
async function decision(page, side, logicalTick, tool) {
  await page.locator("#decision-ledger").scrollIntoViewIfNeeded();
  let rows = page
    .locator(".ledger-row:not(.fault-row)")
    .filter({
      has: page.locator(".small-world").getByText(side, { exact: true }),
    })
    .filter({
      has: page
        .locator(".ledger-tick")
        .getByText(String(logicalTick).padStart(2, "0"), { exact: true }),
    });
  if (tool)
    rows = rows.filter({
      has: page
        .locator(".ledger-action")
        .getByText(tool.replaceAll("_", " "), { exact: false }),
    });
  await rows.first().click();
  await page.getByRole("button", { name: "Close inspector" }).waitFor();
}
const teamFresh = sources.team.events.find(
  (e) =>
    e.coordination?.consultation_reason === "booking_changed" &&
    e.action.tool === "ask_question",
);
const teamReused = sources.team.events.find(
  (e) =>
    e.tick > teamFresh.tick &&
    e.coordination?.consultation_reason === "reuse_advice" &&
    e.result?.offer?.status === "accepted",
);
const faultEvent = sources.fault_team.events.find(
  (e) => e.type === "action" && e.result?.code === "timeout",
);
const laterBooking = sources.fault_team.events.find(
  (e) => e.tick > faultEvent.tick && e.result?.receipt?.status === "committed",
);

async function setup(page, kind) {
  if (kind === "tradeoff" || kind === "closing") {
    const image = path.join(
      output,
      "slides",
      kind === "tradeoff" ? "slide-07.png" : "slide-08.png",
    );
    const bytes = await fs.readFile(image);
    await page.setContent(
      `<html><body style="margin:0;background:#f5f4ef;display:grid;place-items:center;width:100vw;height:100vh"><img style="width:100%;height:100%;object-fit:contain" src="data:image/png;base64,${bytes.toString("base64")}" /></body></html>`,
    );
    return;
  }
  await pair(
    page,
    ["team", "summary"].includes(kind)
      ? "team"
      : kind === "fault"
        ? "fault"
        : "pilot",
  );
  if (kind === "initial") await tick(page, 0);
  if (kind === "receipt") {
    await tick(page, 2);
    await decision(page, "A", 2, "commit_offer");
  }
  if (kind === "method")
    await page.getByRole("button", { name: /Method & rules/ }).click();
  if (kind === "team") {
    await tick(page, teamFresh.tick);
    await decision(page, "B", teamFresh.tick);
  }
  if (kind === "summary" || kind === "pilot") {
    await page.getByRole("button", { name: /^Run archive/ }).click();
    await page.getByLabel("Test conditions").waitFor();
  }
  if (kind === "fault") {
    await tick(page, faultEvent.tick);
    await decision(page, "B", faultEvent.tick);
  }
  await page.waitForTimeout(600);
}
async function actions(page, kind) {
  if (kind === "opening") {
    await page.waitForTimeout(3500);
    await page.locator(".world-grid").scrollIntoViewIfNeeded();
  } else if (kind === "initial") {
    await page.locator(".world-grid").scrollIntoViewIfNeeded();
    await page.waitForTimeout(7000);
    await page.getByLabel("Replay logical tick").scrollIntoViewIfNeeded();
  } else if (kind === "receipt") {
    await page.waitForTimeout(7000);
    await page
      .getByRole("heading", { name: "Tool result", exact: true })
      .scrollIntoViewIfNeeded();
  } else if (kind === "method") {
    await page.waitForTimeout(7500);
    await page
      .getByRole("heading", { name: "What is autonomous?", exact: true })
      .scrollIntoViewIfNeeded();
  } else if (kind === "team") {
    await page.waitForTimeout(8500);
    await page.getByRole("button", { name: "Close inspector" }).click();
    await tick(page, teamReused.tick);
    await decision(page, "B", teamReused.tick);
  } else if (kind === "summary") {
    await page.waitForTimeout(7000);
    const report = await (
      await page.request.get(teamUrl + "/api/benchmarks")
    ).json();
    const group = report.cohorts.find(
      (c) =>
        c.config.scenario_id === "harbor-v1" &&
        c.config.fault === "tool_timeout",
    );
    await page.getByLabel("Test conditions").selectOption(group.id);
    await page.waitForTimeout(6500);
    await page.evaluate(() => scrollBy({ top: 260, behavior: "smooth" }));
  } else if (kind === "pilot") {
    await page.waitForTimeout(7500);
    await page.evaluate(() => scrollBy({ top: 450, behavior: "smooth" }));
  } else if (kind === "fault") {
    await page.waitForTimeout(8000);
    await page.getByRole("button", { name: "Close inspector" }).click();
    await tick(page, laterBooking.tick);
    await decision(page, "B", laterBooking.tick, "commit_offer");
  }
}
async function captionBands() {
  const context = await browser.newContext({
    viewport: { width: 1920, height: 90 },
  });
  const page = await context.newPage();
  const hashes = [];
  const escape = (value) =>
    value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  await fs.mkdir(path.join(output, "bands"), { recursive: true });
  for (const [index, scene] of storyboard.entries()) {
    await page.setContent(
      `<html><head><style>body{margin:0;background:#f5f4ef;color:#172c30;font-family:Arial,sans-serif}h1,p{margin:0;position:absolute;left:48px;right:48px;white-space:nowrap}h1{top:8px;font-size:30px;line-height:38px;font-weight:400}p{top:53px;font-size:20px;line-height:26px;color:#526469}</style></head><body><h1>${escape(scene.title)}</h1><p>${escape(scene.source)}</p></body></html>`,
    );
    if (
      !(await page
        .locator("h1,p")
        .evaluateAll((elements) =>
          elements.every(
            (element) => element.scrollWidth <= element.clientWidth,
          ),
        ))
    )
      throw Error("Caption exceeds frame width");
    const filename = path.join(
      output,
      "bands",
      `band-${String(index + 1).padStart(2, "0")}.png`,
    );
    await page.waitForTimeout(250);
    await page.screenshot({ path: filename });
    hashes.push(
      createHash("sha256")
        .update(await fs.readFile(filename))
        .digest("hex"),
    );
  }
  await context.close();
  return hashes;
}
try {
  const assetsOnly = process.argv.includes("--assets-only");
  const captionsOnly = process.argv.includes("--captions-only");
  const scenes = [];
  for (const [index, scene] of (captionsOnly ? [] : storyboard).entries()) {
    if (assetsOnly && ["tradeoff", "closing"].includes(scene.kind)) continue;
    const context = await browser.newContext({
      viewport: { width: 1600, height: 900 },
      deviceScaleFactor: 1,
      ...(!assetsOnly
        ? {
            recordVideo: {
              dir: path.join(output, "raw-clips"),
              size: { width: 1600, height: 900 },
            },
          }
        : {}),
    });
    const page = await context.newPage();
    // Chrome screencasting needs room for its 88px window chrome.
    const captureSession = await context.newCDPSession(page);
    const { windowId } = await captureSession.send("Browser.getWindowForTarget");
    await captureSession.send("Browser.setWindowBounds", {
      windowId, bounds: { width: 1600, height: 988 },
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await setup(page, scene.kind);
    const started = Date.now();
    await page.screenshot({ path: path.join(output, scene.kind + ".png") });
    if (assetsOnly && scene.kind === "opening") {
      await page
        .getByRole("region", { name: "World B" })
        .getByRole("button", { name: /Arun & Nila/ })
        .screenshot({ path: path.join(output, "family.png") });
    }
    if (assetsOnly && scene.kind === "team") {
      const box = await page.locator(".inspector").boundingBox();
      await page.screenshot({
        path: path.join(output, "team-detail.png"),
        clip: {
          x: box.x,
          y: box.y,
          width: box.width,
          height: Math.min(510, box.height),
        },
      });
    }
    if (assetsOnly && scene.kind === "summary") {
      await page.locator(".benchmark-comparison").scrollIntoViewIfNeeded();
      const box = await page.locator(".benchmark-comparison").boundingBox();
      await page.screenshot({
        path: path.join(output, "summary-detail.png"),
        clip: {
          x: box.x,
          y: box.y,
          width: box.width,
          height: Math.min(450, box.height),
        },
      });
    }
    if (!assetsOnly) {
      await actions(page, scene.kind);
      const remaining = scene.seconds * 1000 - (Date.now() - started);
      if (remaining < -250)
        throw Error(
          `Scene ${scene.kind} exceeded its timing by ${-remaining} ms`,
        );
      if (remaining > 0) await page.waitForTimeout(remaining);
    }
    if (errors.length) throw Error(errors.join("\n"));
    const video = page.video();
    await context.close();
    if (!assetsOnly) {
      const videoPath = await video.path();
      scenes.push({
        ...scene,
        scene_number: index + 1,
        video: path.relative(root, videoPath),
        video_sha256: createHash("sha256")
          .update(await fs.readFile(videoPath))
          .digest("hex"),
      });
    }
    console.log(
      `Captured ${scene.kind}`,
      assetsOnly ? "asset" : `${scene.seconds}s`,
    );
  }
  const captionHashes = await captionBands();
  if (captionsOnly) {
    const filename = path.join(output, "capture-manifest.json");
    const existing = JSON.parse(await fs.readFile(filename, "utf8"));
    existing.caption_sha256 = captionHashes;
    await fs.writeFile(filename, JSON.stringify(existing, null, 2) + "\n");
  }
  if (!assetsOnly && !captionsOnly)
    await fs.writeFile(
      path.join(output, "capture-manifest.json"),
      JSON.stringify(
        {
          schema_version: 1,
          source_revision: execFileSync("git", ["rev-parse", "HEAD"], {
            cwd: root,
            encoding: "utf8",
          }).trim(),
          source_runs: sourceIds,
          caption_sha256: captionHashes,
          scene_seconds: storyboard.reduce(
            (sum, scene) => sum + scene.seconds,
            0,
          ),
          scenes,
        },
        null,
        2,
      ) + "\n",
    );
} finally {
  await browser.close();
}
