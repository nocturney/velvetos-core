import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {evaluateInstagramPublish} from "./instagram-publish-evaluator.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const policy = JSON.parse(fs.readFileSync(path.join(here, "instagram.publish.json"), "utf8"));
const vectors = JSON.parse(fs.readFileSync(path.join(here, "instagram-publish-test-vectors.json"), "utf8"));

function merge(base, patch) {
  if (patch === null || typeof patch !== "object" || Array.isArray(patch)) return patch;
  const out = {...base};
  for (const [key, value] of Object.entries(patch)) {
    if (value && typeof value === "object" && !Array.isArray(value) && base?.[key] && typeof base[key] === "object" && !Array.isArray(base[key])) {
      out[key] = merge(base[key], value);
    } else {
      out[key] = value;
    }
  }
  return out;
}

let failures = 0;
for (const row of vectors.cases) {
  const context = merge(vectors.base_context, row.patch || {});
  const result = evaluateInstagramPublish(policy, context);
  const ok = result.decision === row.expected_decision && result.reason_codes.includes(row.expected_reason);
  if (!ok) {
    failures += 1;
    console.error("FAIL", row.id, JSON.stringify({expected: row, actual: result}));
  } else {
    console.log("PASS", row.id, result.decision, row.expected_reason);
  }
}
if (failures) process.exit(1);
console.log("OK instagram.publish vectors=" + vectors.cases.length);
