#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fail(m): print("FAIL "+m,file=sys.stderr); raise SystemExit(1)
st=json.loads((ROOT/"packages/velvetos/TOOL-STATUS.json").read_text(encoding="utf-8"))
by={x["id"]:x for x in st["tools"]}
for k,v in {"cloudflare-instagram-publisher":"ACTIVE_CANONICAL","openpost":"FROZEN","canva":"FORBIDDEN_REMOVED","vfcanva":"FORBIDDEN_REMOVED"}.items():
 if by.get(k,{}).get("status")!=v: fail(f"{k} status")
for rel in [".cursor-plugin",".cursor/vf-canva.json",".cursor/rules/vf-canva-instagram.mdc",".cursor/skills/vf-canva-instagram",".cursor/skills/canva",".cursor/skills/canva-brand-check",".cursor/skills/canva-bulk-create",".cursor/skills/canva-edit-design",".cursor/skills/canva-implement-feedback",".cursor/skills/canva-get-design-feedback",".cursor/skills/canva-resize-for-social-media","packages/vfcanva","docs/CANVA.md","scripts/check-vf-canva.py"]:
 if (ROOT/rel).exists(): fail("forbidden surface exists: "+rel)
m=json.loads((ROOT/".cursor/mcp.json").read_text(encoding="utf-8"))
if "canva" in (m.get("mcpServers") or {}): fail("Canva MCP configured")
p=json.loads((ROOT/"packages/vfigos/PUBLISHER.json").read_text(encoding="utf-8"))
if p.get("schedulerAuthority")!="cloudflare-instagram-publisher": fail("publisher authority")
op=json.loads((ROOT/"packages/vfigos/OPENPOST.json").read_text(encoding="utf-8"))
if op.get("integrationMode")!="frozen" or op.get("activeSchedules")!=0: fail("OpenPost not frozen")
if (ROOT/"packages/vfigos/openpost").exists() or (ROOT/"packages/vfigos/failover").exists(): fail("OpenPost implementation still active-path")
if not (ROOT/"packages/vfigos/archive/openpost").is_dir(): fail("OpenPost archive missing")
print("OK tool authority")
