# Living Studio — capability unification layer

VelvetOS is an **Operating System for a Living Studio**:  
רואה → מבין → מזהה → מציע → פועל לפי policy → לומד → שומר זיכרון.

This directory is **connective tissue**, not a second Control Plane.

## Laws

- Reuse existing Sources of Truth from `office/control-plane.json`.
- Never create a parallel jobs/media/approvals/calendar/decisions/handoff store.
- World Model = **read/query projection** only.
- Signal Room = normalize existing events (JSONL / envelopes) — not an event bus runtime.
- Skills = thin routers over packs. No daemon-per-skill.
- Paused routines stay paused (`PAUSED` ≠ `BROKEN`).
- No invented ₪ / Insights / liveVerified.

## CLI

```bash
python3 scripts/vf_living_studio.py world-model
python3 scripts/vf_living_studio.py pulse
python3 scripts/vf_living_studio.py signal-room
python3 scripts/vf_living_studio.py intake --kind note --text "..."
python3 scripts/vf_living_studio.py invisible-work
python3 scripts/vf_living_studio.py failure-museum
python3 scripts/vf_living_studio.py lab list
python3 scripts/vf_living_studio.py opportunity
python3 scripts/vf_living_studio.py commercial-qa --mode devil --path <draft>
python3 scripts/vf_living_studio.py content-universe
python3 scripts/vf_living_studio.py work-to-story
python3 scripts/vf_living_studio.py skill list|route <name>
python3 scripts/vf_living_studio.py commission --dry-run
python3 scripts/vf_living_studio.py selftest
```

## Registry

`REGISTRY.json` maps the approved Skill library + Living Studio capabilities onto packs and SoTs.

## Sensor

`python3 scripts/check-living-studio.py`
