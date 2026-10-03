import policy from "../../../velvetos/policy/instagram.publish.json" with { type: "json" };
import {evaluateInstagramPublish} from "../../../velvetos/policy/instagram-publish-evaluator.mjs";

const te = new TextEncoder();

function hex(buffer) {
  return [...new Uint8Array(buffer)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function sha256Text(value) {
  return hex(await crypto.subtle.digest("SHA-256", te.encode(value)));
}

function mutationTool(kind) {
  if (kind === "image") return "publish_image";
  if (kind === "carousel") return "publish_carousel";
  if (kind === "reel") return "publish_reel";
  if (kind === "story") return "publish_story";
  return "unsupported";
}

function isoSeconds(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return null;
  return new Date(n * 1000).toISOString();
}

export async function buildInstagramPublishContext(job, env) {
  const auth = job?.authorization && typeof job.authorization === "object" ? job.authorization : {};
  const supplied = auth.policy_context && typeof auth.policy_context === "object" ? auth.policy_context : null;
  const context = {
    channel: "instagram",
    publication_type: "organic",
    mutation_tool: mutationTool(job?.kind),
    content_id: job?.content_id ?? null,
    package_sha256: job?.package_sha256 ?? null,
    copy_sha256: await sha256Text(String(job?.caption ?? "")),
    media_sha256s: Array.isArray(job?.media) ? job.media.map((item) => item.sha256) : [],
    risk_class: supplied?.risk_class ?? null,
    standing_authorization: String(env?.STANDING_AUTHORIZATION ?? "").toLowerCase() === "true",
    forbidden_effects: Array.isArray(supplied?.forbidden_effects) ? supplied.forbidden_effects : [],
    content_ready: supplied?.content_ready && typeof supplied.content_ready === "object" ? supplied.content_ready : null,
    gates: supplied?.gates && typeof supplied.gates === "object" ? supplied.gates : {}, // bounded Stage 4D compatibility only
    human_approval: supplied?.human_approval ?? null,
    legacy_authorization: supplied ? null : auth,
    job_created_at: isoSeconds(job?.created_at),
  };
  if (!supplied) context.copy_sha256 = null;
  return context;
}

export async function evaluateInstagramPublishJob(job, env) {
  const context = await buildInstagramPublishContext(job, env);
  return {
    context,
    result: evaluateInstagramPublish(policy, context),
  };
}

export {policy as instagramPublishPolicy};
