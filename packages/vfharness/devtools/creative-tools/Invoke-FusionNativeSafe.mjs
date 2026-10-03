import fs from "node:fs";
import {
  Client,
  connectToRemoteServer
} from "file:///D:/Velvet/Tools/CreativeTools/FusionNativeProxy/0.14.3/node_modules/mcp-remote/dist/chunk-CGVEK4Z7.js";

const allowed = new Set([
  "fusion_mcp_read",
  "fusion_mcp_electronics_read",
  "fusion_mcp_update"
]);

const [toolName, argsPath] = process.argv.slice(2);
if (!toolName) throw new Error("Usage: node Invoke-FusionNativeSafe.mjs <toolName> [argsJsonPath]");
if (!allowed.has(toolName)) {
  throw new Error("Fusion tool blocked by VelvetOS production allowlist: " + toolName);
}
const args = argsPath ? JSON.parse(fs.readFileSync(argsPath, "utf8")) : {};

if (toolName === "fusion_mcp_update") {
  if (!["undo","redo"].includes(args.featureType)) {
    throw new Error("fusion_mcp_update only allows featureType undo or redo");
  }
}

const client = new Client({name:"VelvetOS-Fusion-Safe",version:"0.1.0"},{capabilities:{}});
try {
  await connectToRemoteServer(client,"http://127.0.0.1:27182/mcp",null,{},null,"http-only","legacy");
  const tools = await client.request({method:"tools/list"});
  const available = new Set((tools.tools||[]).map(t=>t.name));
  if (!available.has(toolName)) throw new Error("Allowed Fusion tool is not advertised by current host: " + toolName);
  const result = await client.request({method:"tools/call",params:{name:toolName,arguments:args}});
  process.stdout.write(JSON.stringify({ok:true,tool:toolName,result},null,2)+"\n");
} finally {
  await client.close().catch(()=>{});
}
