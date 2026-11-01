import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { format } from "prettier";
import { compile } from "json-schema-to-typescript";
const base = new URL("../", import.meta.url);
const schema = JSON.parse(
  await readFile(new URL("../../contracts/v1/api.schema.json", base), "utf8"),
);
// A wrapper forces all public definitions to be named and emitted. Never load private content.
const properties = Object.fromEntries(
  Object.keys(schema.$defs).map((name) => [name, { $ref: "#/$defs/" + name }]),
);
const output = await compile(
  {
    ...schema,
    type: "object",
    properties,
    required: Object.keys(properties),
    additionalProperties: false,
  },
  "Contract",
  {
    bannerComment:
      "/* Generated from frozen public API 1.0.0. Run node scripts/generate-types.mjs. */",
    unreachableDefinitions: true,
  },
);
await mkdir(new URL("src/generated/", base), { recursive: true });
await writeFile(
  fileURLToPath(new URL("src/generated/contract.ts", base)),
  await format(output, { parser: "typescript" }),
);
