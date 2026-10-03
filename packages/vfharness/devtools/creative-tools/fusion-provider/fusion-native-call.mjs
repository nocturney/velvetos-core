import fs from "node:fs";
import {
  Client,
  connectToRemoteServer
} from "file:///D:/Velvet/Tools/CreativeTools/FusionNativeProxy/0.14.3/node_modules/mcp-remote/dist/chunk-CGVEK4Z7.js";

const [toolName, argsPath] = process.argv.slice(2);
if (!toolName || !argsPath) {
  process.stderr.write("Usage: node fusion-native-call.mjs <toolName> <argsJsonPath>\n");
  process.exit(64);
}

const args = JSON.parse(fs.readFileSync(argsPath, "utf8"));
const client = new Client(
  { name: "VelvetOS-FusionBackend", version: "0.1.0" },
  { capabilities: {} }
);

try {
  await connectToRemoteServer(
    client,
    "http://127.0.0.1:27182/mcp",
    null,
    {},
    null,
    "http-only",
    "legacy"
  );
  const result = await client.request({
    method: "tools/call",
    params: { name: toolName, arguments: args }
  });
  process.stdout.write(JSON.stringify({ ok: true, result }) + "\n");
} catch (error) {
  process.stdout.write(JSON.stringify({
    ok: false,
    error: String(error?.message || error)
  }) + "\n");
  process.exitCode = 2;
} finally {
  await client.close().catch(() => {});
}
