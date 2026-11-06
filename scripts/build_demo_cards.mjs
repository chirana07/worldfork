import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const ink = "#203236",
  teal = "#176D5E",
  muted = "#526562",
  paper = "#F6F5EF";
function text(slide, value, x, y, width, height, size = 28, color = ink) {
  const t = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  t.text = value;
  t.text.style = { fontFamily: "Arial", fontSize: size, color };
}
async function image(
  slide,
  filename,
  position,
  { crop, fit = "contain" } = {},
) {
  const bytes = await fs.readFile(filename);
  const mime = filename.endsWith(".jpg") ? "image/jpeg" : "image/png";
  return slide.images.add({
    dataUrl: `data:${mime};base64,${bytes.toString("base64")}`,
    position,
    fit,
    ...(crop ? { crop } : {}),
    alt: "Actual WorldFork recorded UI or measured pitch slide",
  });
}
export async function renderCards(
  presentation,
  {
    indices,
    final = false,
    manifestPath = "artifacts/benchmark-20261105T170022Z.json",
  } = {},
) {
  const spec = JSON.parse(
    await fs.readFile(path.join(root, "artifacts/demo-scenes.json"), "utf8"),
  );
  const manifestBytes = await fs.readFile(path.join(root, manifestPath));
  const manifest = JSON.parse(manifestBytes.toString());
  if (
    final &&
    (manifest.runs.length !== 30 ||
      manifest.runs.some(
        (e) => !e.result || !["completed", "exhausted", "stopped"].includes(e.status),
      ))
  )
    throw new Error("Finish the frozen pilot before final media");
  const original = presentation.slides.items.length;
  const out = path.join(root, "artifacts/demo-cards");
  await fs.mkdir(out, { recursive: true });
  try {
    for (const [i, scene] of spec.scenes.entries()) {
      if (indices && !indices.includes(i)) continue;
      const slide = presentation.slides.add({ width: 1920, height: 1080 });
      slide.background.fill = paper;
      if (scene.kind === "replay") {
        await image(
          slide,
          scene.image,
          { left: 40, top: 100, width: 1328, height: 940 },
          {
            fit: "cover",
            crop: { left: 0, top: 0, right: 0, bottom: 112 / 912 },
          },
        );
        text(
          slide,
          `Recorded development trace | Logical tick ${scene.tick}`,
          40,
          28,
          1700,
          60,
          28,
        );
        text(slide, scene.caption, 1415, 250, 470, 330, 38, teal);
        text(
          slide,
          "World A | case-by-case\n\nWorld B | coordinated",
          1415,
          710,
          470,
          140,
          26,
          muted,
        );
        text(
          slide,
          "Condensed logical time; scripted passengers; real Qwen/Bifrost decisions",
          40,
          1040,
          1840,
          40,
          23,
          muted,
        );
      } else {
        await image(slide, scene.image, {
          left: 0,
          top: 0,
          width: 1920,
          height: 1080,
        });
        if (scene.kind === "inspector") {
          const label = slide.shapes.add({
            geometry: "textbox",
            position: { left: 24, top: 1028, width: 1872, height: 50 },
            fill: paper,
            line: { fill: "none", width: 0 },
          });
          label.text = "Recorded UI inspection | actual stored event";
          label.text.style = { fontFamily: "Arial", fontSize: 26, color: ink };
        }
      }
      if (i === spec.scenes.length - 1)
        text(
          slide,
          "Generated narration | macOS speech synthesis",
          115,
          1034,
          1700,
          40,
          22,
          muted,
        );
      const png = await presentation.export({ slide, format: "png", scale: 1 });
      await fs.writeFile(
        path.join(
          out,
          `scene-${String(scene.scene_number).padStart(2, "0")}.png`,
        ),
        new Uint8Array(await png.arrayBuffer()),
      );
    }
  } finally {
    presentation.slides.keep(Array.from({ length: original }, (_, i) => i));
  }
  const receipt = {
    final,
    source: manifestPath,
    pilot_manifest_sha256: createHash("sha256")
      .update(manifestBytes)
      .digest("hex"),
    scene_count: spec.scenes.length,
  };
  await fs.writeFile(
    path.join(out, "receipt.json"),
    JSON.stringify(receipt, null, 2),
  );
  return receipt;
}
