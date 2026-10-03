import assert from "node:assert/strict";
import {publishJob, validateJob, verifyMedia} from "./src/index.js";

const enc = new TextEncoder();
const hex = (buffer) => [...new Uint8Array(buffer)].map((v) => v.toString(16).padStart(2, "0")).join("");
const digest = async (bytes) => hex(await crypto.subtle.digest("SHA-256", bytes));

function response(data, status = 200) {
  return new Response(JSON.stringify(data), {status, headers: {"content-type": "application/json"}});
}

function makeEnv(mediaRows) {
  return {
    GRAPH_VERSION: "v21.0",
    META_ACCESS_TOKEN: "test-token",
    IG_USER_ID: "17841407772120429",
    MEDIA: {
      async getWithMetadata(key) {
        const row = mediaRows[key];
        if (!row) return {value: null, metadata: null};
        return {
          value: row.bytes.buffer.slice(row.bytes.byteOffset, row.bytes.byteOffset + row.bytes.byteLength),
          metadata: {sha256: row.sha256, content_type: row.content_type},
        };
      },
    },
  };
}

function baseJob(kind, media, caption = "Velvet Factory") {
  return {
    id: "job-" + kind,
    content_id: "G100",
    package_sha256: "a".repeat(64),
    kind,
    scheduled_at: Math.floor(Date.now() / 1000) + 600,
    caption,
    media,
    authorization: {kind: "policy_authorization_v1", evidence: "CONTENT_READY", policy_context: {}},
    created_at: Math.floor(Date.now() / 1000),
  };
}

const imageBytes = enc.encode("image-bytes");
const imageSha = await digest(imageBytes);
const image2Bytes = enc.encode("image-two");
const image2Sha = await digest(image2Bytes);
const videoBytes = enc.encode("video-bytes");
const videoSha = await digest(videoBytes);

const rows = {
  "one.jpg": {bytes: imageBytes, sha256: imageSha, content_type: "image/jpeg"},
  "two.png": {bytes: image2Bytes, sha256: image2Sha, content_type: "image/png"},
  "clip.mp4": {bytes: videoBytes, sha256: videoSha, content_type: "video/mp4"},
};
const env = makeEnv(rows);

validateJob({
  ...baseJob("image", [{key: "one.jpg", sha256: imageSha}]),
  scheduled_at: new Date(Date.now() + 60000).toISOString(),
});
validateJob({
  ...baseJob("carousel", [{key: "one.jpg", sha256: imageSha}, {key: "two.png", sha256: image2Sha}]),
  scheduled_at: new Date(Date.now() + 60000).toISOString(),
});
validateJob({
  ...baseJob("reel", [{key: "clip.mp4", sha256: videoSha}]),
  scheduled_at: new Date(Date.now() + 60000).toISOString(),
});
validateJob({
  ...baseJob("story", [{key: "one.jpg", sha256: imageSha}]),
  scheduled_at: new Date(Date.now() + 60000).toISOString(),
});

await assert.rejects(
  () => verifyMedia(env, [{key: "one.jpg", sha256: imageSha}], "reel"),
  /reel_requires_mp4/,
);

const calls = [];
const originalFetch = globalThis.fetch;
globalThis.fetch = async (url, options = {}) => {
  const u = new URL(String(url));
  const method = options.method || "GET";
  const params = method === "GET"
    ? u.searchParams
    : new URLSearchParams(options.body || "");
  const path = u.pathname;
  calls.push({method, path, params: Object.fromEntries(params.entries())});
  if (method === "GET" && params.get("fields") === "status_code,status") {
    return response({id: path.split("/").pop(), status_code: "FINISHED"});
  }
  if ((options.method || "GET") === "GET" && params.get("fields") === "id,media_type,permalink,timestamp") {
    const id = path.split("/").pop();
    return response({id, media_type: "IMAGE", permalink: "https://instagram.test/p/" + id, timestamp: "2030-01-01T00:00:00Z"});
  }
  if (path.endsWith("/media_publish")) return response({id: "live-" + calls.length});
  if (path.endsWith("/media")) return response({id: "container-" + calls.length});
  throw new Error("unexpected Graph call " + path);
};

try {
  calls.length = 0;
  const imageJob = baseJob("image", [{key: "one.jpg", url: "https://media.test/one.jpg", sha256: imageSha}]);
  const imageLive = await publishJob(env, imageJob);
  assert.ok(imageLive.permalink);
  assert.equal(calls.find((c) => c.path.endsWith("/media"))?.params.image_url, "https://media.test/one.jpg");

  calls.length = 0;
  const carouselJob = baseJob("carousel", [
    {key: "one.jpg", url: "https://media.test/one.jpg", sha256: imageSha},
    {key: "two.png", url: "https://media.test/two.png", sha256: image2Sha},
  ]);
  await publishJob(env, carouselJob);
  const carouselParent = calls.filter((c) => c.path.endsWith("/media") && c.params.media_type === "CAROUSEL")[0];
  assert.ok(carouselParent);
  assert.equal(carouselParent.params.caption, "Velvet Factory");
  assert.ok(carouselParent.params.children.includes(","));

  calls.length = 0;
  const reelJob = baseJob("reel", [{key: "clip.mp4", url: "https://media.test/clip.mp4", sha256: videoSha}]);
  await publishJob(env, reelJob);
  const reelCreate = calls.find((c) => c.path.endsWith("/media") && c.params.media_type === "REELS");
  assert.ok(reelCreate);
  assert.equal(reelCreate.params.video_url, "https://media.test/clip.mp4");
  assert.equal(reelCreate.params.share_to_feed, "true");

  calls.length = 0;
  const storyImage = baseJob("story", [{key: "one.jpg", url: "https://media.test/one.jpg", sha256: imageSha}], "");
  await publishJob(env, storyImage);
  const storyImageCreate = calls.find((c) => c.path.endsWith("/media") && c.params.media_type === "STORIES");
  assert.ok(storyImageCreate);
  assert.equal(storyImageCreate.params.image_url, "https://media.test/one.jpg");
  assert.equal(storyImageCreate.params.video_url, undefined);

  calls.length = 0;
  const storyVideo = baseJob("story", [{key: "clip.mp4", url: "https://media.test/clip.mp4", sha256: videoSha}], "");
  await publishJob(env, storyVideo);
  const storyVideoCreate = calls.find((c) => c.path.endsWith("/media") && c.params.media_type === "STORIES");
  assert.ok(storyVideoCreate);
  assert.equal(storyVideoCreate.params.video_url, "https://media.test/clip.mp4");
  assert.equal(storyVideoCreate.params.image_url, undefined);
} finally {
  globalThis.fetch = originalFetch;
}

console.log("OK cloudflare publisher format contracts image carousel reel story");
