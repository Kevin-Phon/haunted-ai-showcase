import { readFile, readdir } from "node:fs/promises";
const files = await readdir(new URL("../dist/assets/", import.meta.url));
const js = (
  await Promise.all(
    files
      .filter((f) => f.endsWith(".js"))
      .map((f) =>
        readFile(new URL("../dist/assets/" + f, import.meta.url), "utf8"),
      ),
  )
).join("");
const forbidden = [
  "Readable fixture fragment",
  "Synthetic terminal interface fixture",
  "fixture_run_1_event_1",
  "eleanor_disconnected_stabilizer",
  "thomas_restored_power",
  "game-data.schema.json",
  "/contracts/v1/examples/",
];
for (const marker of forbidden)
  if (js.includes(marker))
    throw Error("Production bundle contains fixture/private marker: " + marker);
if (files.some((f) => f.startsWith("dev-")))
  throw Error("Development transport chunk found");
console.log(
  "PASS: production bundle excludes development fixture/private-answer markers and development transport chunks.",
);
