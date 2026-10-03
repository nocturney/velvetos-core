import readline from "node:readline";
import {
  Client,
  connectToRemoteServer
} from "file:///D:/Velvet/Tools/CreativeTools/FusionNativeProxy/0.14.3/node_modules/mcp-remote/dist/chunk-CGVEK4Z7.js";

const PROVIDER_NAME = "velvetos-fusion-provider";
const PROVIDER_VERSION = "0.1.0";
const NATIVE_URL = "http://127.0.0.1:27182/mcp";

function log(message, data = undefined) {
  const suffix = data === undefined ? "" : " " + JSON.stringify(data);
  process.stderr.write(new Date().toISOString() + " " + message + suffix + "\n");
}

function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

function parseTextContent(result) {
  const block = Array.isArray(result?.content)
    ? result.content.find((item) => item?.type === "text")
    : null;
  if (!block || typeof block.text !== "string") {
    return result;
  }
  try {
    return JSON.parse(block.text);
  } catch {
    return block.text;
  }
}

async function withNativeClient(operation) {
  const client = new Client(
    { name: PROVIDER_NAME, version: PROVIDER_VERSION },
    { capabilities: {} }
  );
  try {
    await connectToRemoteServer(
      client,
      NATIVE_URL,
      null,
      {},
      null,
      "http-only",
      "legacy"
    );
    return await operation(client);
  } finally {
    await client.close().catch(() => {});
  }
}

async function nativeRead(args) {
  return await withNativeClient((client) =>
    client.request({
      method: "tools/call",
      params: {
        name: "fusion_mcp_read",
        arguments: args
      }
    })
  );
}

const tools = [
  {
    name: "velvet_fusion_status",
    description:
      "Read-only Fusion connectivity/status probe through Autodesk Fusion native MCP. Does not modify the document.",
    inputSchema: {
      type: "object",
      properties: {},
      additionalProperties: false
    }
  }
];

async function callTool(name, args) {
  if (name !== "velvet_fusion_status") {
    return {
      content: [{ type: "text", text: JSON.stringify({ error: "tool_not_found", tool: name }) }],
      isError: true
    };
  }

  const started = Date.now();
  const active = await nativeRead({ queryType: "activeCommand" });
  const payload = {
    provider: PROVIDER_NAME,
    providerVersion: PROVIDER_VERSION,
    nativeEndpoint: NATIVE_URL,
    nativeMcp: true,
    activeCommand: parseTextContent(active),
    elapsedMs: Date.now() - started
  };
  return {
    content: [{ type: "text", text: JSON.stringify(payload) }],
    isError: false
  };
}

async function handleMessage(message) {
  const method = message?.method;
  const id = message?.id;

  if (method === "initialize") {
    send({
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: message?.params?.protocolVersion || "2025-11-25",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: PROVIDER_NAME, version: PROVIDER_VERSION }
      }
    });
    return;
  }

  if (method === "notifications/initialized" || method === "notifications/cancelled") {
    return;
  }

  if (method === "ping") {
    send({ jsonrpc: "2.0", id, result: {} });
    return;
  }

  if (method === "tools/list") {
    send({ jsonrpc: "2.0", id, result: { tools } });
    return;
  }

  if (method === "tools/call") {
    try {
      const result = await callTool(
        String(message?.params?.name || ""),
        message?.params?.arguments || {}
      );
      send({ jsonrpc: "2.0", id, result });
    } catch (error) {
      log("TOOL_ERROR", { tool: message?.params?.name, error: String(error?.message || error) });
      send({
        jsonrpc: "2.0",
        id,
        result: {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                error: "fusion_native_unavailable",
                message: String(error?.message || error)
              })
            }
          ],
          isError: true
        }
      });
    }
    return;
  }

  if (id !== undefined) {
    send({
      jsonrpc: "2.0",
      id,
      error: { code: -32601, message: "Method not found: " + String(method) }
    });
  }
}

const rl = readline.createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
  terminal: false
});

let queue = Promise.resolve();
rl.on("line", (line) => {
  if (!line.trim()) return;
  queue = queue
    .then(async () => {
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        log("INVALID_JSON");
        return;
      }
      await handleMessage(message);
    })
    .catch((error) => {
      log("UNHANDLED", { error: String(error?.stack || error) });
    });
});

rl.on("close", () => {
  log("STDIN_CLOSED");
});
