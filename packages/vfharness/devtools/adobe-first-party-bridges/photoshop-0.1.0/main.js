"use strict";
const uxp = require("uxp");
const { entrypoints } = uxp;
const photoshop = require("photoshop");

entrypoints.setup({
  panels: {
    velvetPhotoshopBridge: {
      show() {},
      hide() {}
    }
  }
});

const JSONRPC_VERSION = "2.0";
const ERROR_METHOD_NOT_FOUND = -32601;
const ERROR_HOST_SCRIPT = -32004;
const url = globalThis.__ADOBEPY_BROKER_URL;
const token = globalThis.__ADOBEPY_TOKEN;
const target = globalThis.__ADOBEPY_TARGET || "default";
let socket = null;
let reconnectTimer = null;
let reconnectDelayMs = 1000;
const temporaryDocumentIds = new Set();

function scalar(value) {
  if (value === null || value === undefined) return null;
  if (typeof value !== "object") return value;
  try {
    const converted = value.valueOf();
    if (typeof converted !== "object") return converted;
  } catch (_) {}
  if (typeof value.value === "number" || typeof value.value === "string") return value.value;
  return String(value);
}

function documentInfo(doc) {
  if (!doc) return null;
  return {
    id: scalar(doc.id),
    name: scalar(doc.title || doc.name),
    width: scalar(doc.width),
    height: scalar(doc.height),
    resolution: scalar(doc.resolution),
    saved: scalar(doc.saved),
    mode: scalar(doc.mode)
  };
}

function activeDocumentInfo() {
  return documentInfo(photoshop.app.activeDocument);
}

async function createTemporaryDocument(options) {
  const input = options && typeof options === "object" ? options : {};
  const width = Math.max(8, Math.min(Number(input.width) || 64, 512));
  const height = Math.max(8, Math.min(Number(input.height) || 64, 512));
  const name = "VelvetOS Acceptance " + Date.now();
  return await photoshop.core.executeAsModal(async () => {
    const doc = await photoshop.app.createDocument({ width, height, resolution: 72, mode: "RGBColorMode", fill: "transparent", name });
    temporaryDocumentIds.add(String(doc.id));
    return documentInfo(doc);
  }, { commandName: "VelvetOS temporary document" });
}

async function closeTemporaryDocument(id) {
  const key = String(id);
  if (!temporaryDocumentIds.has(key)) throw new Error("refusing to close a document not created by this bridge session");
  const doc = Array.from(photoshop.app.documents || []).find((item) => String(item.id) === key);
  if (!doc) {
    temporaryDocumentIds.delete(key);
    return { closed: false, id: scalar(id), reason: "not_found" };
  }
  await photoshop.core.executeAsModal(async () => {
    await Promise.resolve(doc.closeWithoutSaving());
  }, { commandName: "Close VelvetOS temporary document" });
  temporaryDocumentIds.delete(key);
  return { closed: true, id: scalar(id) };
}

function hostVersion() {
  return String((photoshop.app && photoshop.app.version) || (uxp.host && uxp.host.version) || photoshop.version || "unknown");
}

function capabilities() {
  return {
    host: "photoshop",
    bridgeKind: "uxp",
    bridgeVersion: "0.1.0",
    hostVersion: hostVersion(),
    namespaces: ["app", "document", "action"],
    features: ["reconnect", "batchPlayReadOnly", "controlledTemporaryWrite"],
    methods: {
      app: ["getVersion"],
      document: ["getActive", "createTemporary", "closeTemporary"],
      action: ["batchPlayReadOnly"]
    }
  };
}

function assertReadOnlyDescriptors(descriptors) {
  if (!Array.isArray(descriptors)) throw new Error("descriptors must be an array");
  const allowed = new Set(["get", "multiGet"]);
  for (const descriptor of descriptors) {
    if (!descriptor || typeof descriptor !== "object" || !allowed.has(descriptor._obj)) {
      throw new Error("only read-only Photoshop get/multiGet descriptors are allowed");
    }
  }
}

async function dispatch(request) {
  if (request.namespace === "app" && request.method === "getVersion") {
    return hostVersion();
  }
  if (request.namespace === "document" && request.method === "getActive") {
    return activeDocumentInfo();
  }
  if (request.namespace === "document" && request.method === "createTemporary") {
    return await createTemporaryDocument(request.args && request.args[0]);
  }
  if (request.namespace === "document" && request.method === "closeTemporary") {
    return await closeTemporaryDocument(request.args && request.args[0]);
  }
  if (request.namespace === "action" && request.method === "batchPlayReadOnly") {
    const descriptors = (request.args && request.args[0]) || [];
    const options = (request.args && request.args[1]) || {};
    assertReadOnlyDescriptors(descriptors);
    const result = await photoshop.action.batchPlay(descriptors, options);
    const failures = Array.isArray(result) ? result.filter((item) => item && item._obj === "error") : [];
    if (failures.length) throw new Error(failures.map((item) => item.message || "Photoshop batchPlay failed").join("; "));
    return result;
  }
  const error = new Error("unsupported method " + request.namespace + "." + request.method);
  error.code = ERROR_METHOD_NOT_FOUND;
  throw error;
}

function hostError(id, error) {
  return {
    jsonrpc: JSONRPC_VERSION,
    id,
    error: {
      code: Number.isInteger(error && error.code) ? error.code : ERROR_HOST_SCRIPT,
      message: error instanceof Error ? error.message : String(error)
    }
  };
}

function send(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelayMs);
  reconnectDelayMs = Math.min(reconnectDelayMs * 2, 15000);
}

function connect() {
  if (typeof url !== "string" || !url || typeof token !== "string" || !token) {
    console.error("[velvetos-photoshop] broker configuration missing");
    return;
  }
  try {
    socket = new WebSocket(url);
  } catch (error) {
    console.error("[velvetos-photoshop] websocket create failed", String(error));
    scheduleReconnect();
    return;
  }
  socket.addEventListener("open", () => {
    reconnectDelayMs = 1000;
    send({ type: "hello", token, target, capabilities: capabilities() });
  });
  socket.addEventListener("message", async (event) => {
    let message;
    try {
      message = JSON.parse(event.data);
    } catch (_) {
      return;
    }
    if (!message || message.type !== "request" || !message.request) return;
    const request = message.request;
    try {
      const result = await dispatch(request);
      send({ type: "response", response: { jsonrpc: JSONRPC_VERSION, id: request.id, result: result === undefined ? null : result } });
    } catch (error) {
      send({ type: "error", error: hostError(request.id, error) });
    }
  });
  socket.addEventListener("close", scheduleReconnect);
  socket.addEventListener("error", () => {
    try { socket.close(); } catch (_) {}
  });
}

connect();
