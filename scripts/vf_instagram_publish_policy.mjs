#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {evaluateInstagramPublish} from "../packages/velvetos/policy/instagram-publish-evaluator.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const policyPath = path.join(root, "packages", "velvetos", "policy", "instagram.publish.json");
const policy = JSON.parse(fs.readFileSync(policyPath, "utf8"));

function arg(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
}

let raw = "";
const contextPath = arg("--context");
if (contextPath) {
  raw = fs.readFileSync(path.resolve(contextPath), "utf8");
} else if (!process.stdin.isTTY) {
  raw = fs.readFileSync(0, "utf8");
} else {
  console.error("usage: vf_instagram_publish_policy.mjs --context <json> OR pipe JSON on stdin");
  process.exit(64);
}

let context;
try {
  context = JSON.parse(raw);
} catch (error) {
  console.error(JSON.stringify({decision: "DENY", reason_codes: ["CONTEXT_JSON_INVALID"], error: String(error)}));
  process.exit(3);
}

const result = evaluateInstagramPublish(policy, context);
console.log(JSON.stringify(result, null, 2));
if (result.decision === "ALLOW") process.exit(0);
if (result.decision === "REQUIRE_OWNER_APPROVAL") process.exit(2);
process.exit(3);
