"""LEGACY OpenPost failover supervisor.

Cloudflare Publisher replaced the OpenPost scheduled publication path on 2026-09-24.
This file intentionally performs no supervision or dispatch. It remains only so an
old task/file reference fails safe if invoked.
"""
from pathlib import Path
import datetime

LOG=Path(r'C:\ProgramData\GrokBotBoot\supervisor.log')
LOG.parent.mkdir(parents=True,exist_ok=True)
with LOG.open('a',encoding='utf-8') as f:
    f.write(datetime.datetime.now().isoformat()+' legacy OpenPost failover supervisor invoked; no-op after Cloudflare Publisher cutover\n')
raise SystemExit(0)
