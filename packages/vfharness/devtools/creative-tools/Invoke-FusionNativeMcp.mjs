import fs from "node:fs";
import {
  Client,
  connectToRemoteServer
} from "file:///D:/Velvet/Tools/CreativeTools/FusionNativeProxy/0.14.3/node_modules/mcp-remote/dist/chunk-CGVEK4Z7.js";

const [toolName, argsPath] = process.argv.slice(2);
if (!toolName) throw new Error("Usage: node Invoke-FusionNativeMcp.mjs <toolName> [argsJsonPath]");
const args = argsPath ? JSON.parse(fs.readFileSync(argsPath, "utf8")) : {};

const timeout = (promise, ms, label) => Promise.race([
  promise,
  new Promise((_, reject) => setTimeout(() => reject(new Error(label + " timed out after " + ms + "ms")), ms))
]);

const client = new Client({ name: "VelvetOS", version: "0.1.0" }, { capabilities: {} });

try {
  process.stderr.write("[stage] connect\n");
  await timeout(connectToRemoteServer(
    client,
    "http://127.0.0.1:27182/mcp",
    undefined,
    {},
    async () => ({ waitForAuthCode: async () => "", skipBrowserAuth: true }),
    "http-only",
    "legacy"
  ), 8000, "connect");
  process.stderr.write("[stage] connected\n");

  process.stderr.write("[stage] tools/list\n");
  const tools = await timeout(client.request({ method: "tools/list" }), 8000, "tools/list");
  process.stderr.write("[stage] tools/list ok " + JSON.stringify((tools.tools || []).map(t => t.name)) + "\n");

  process.stderr.write("[stage] tools/call " + toolName + "\n");
  const result = await timeout(client.request({
    method: "tools/call",
    params: { name: toolName, arguments: args }
  }), 12000, "tools/call");
  process.stderr.write("[stage] tools/call ok\n");

  process.stdout.write(JSON.stringify({ ok: true, result }, null, 2) + "\n");
} finally {
  try { await client.close(); } catch {}
}
