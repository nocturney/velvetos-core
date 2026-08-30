# Agency desk + tools

The Agency dump installed **273** Cursor specialists (`docs/AGENCY-AGENTS.md`). Velvet Factory uses a **desk** of 28, wired to the office packs and the live tools on this HQ.

Machine map: [`.cursor/vf-desk.json`](../.cursor/vf-desk.json).  
Always-on router: [`.cursor/rules/velvet-factory-desk.mdc`](../.cursor/rules/velvet-factory-desk.mdc).  
Refresh Agency rules: `./scripts/install-agency-agents.sh` (preserves the desk rule).  
Check: `python3 scripts/check-vf-desk.py`.

HQ still does not send Instagram or Gmail. Live send stays on Grok Bot.

## Why a desk

The install put every official Agency role on disk, including Godot, GIS, healthcare, and China-social. Those stay in the **warehouse** (`alwaysApply: false`). The desk is what a Velvet Factory job should mention.

Checked 2026-08-30 on this HQ:

| Tool | Status on this agent | Mode |
|---|---|---|
| Gmail | Ready (`nocturney@gmail.com`) | **Read** inbox / bills. No send, reply, or forward. |
| Google Calendar | Ready (`nocturney@gmail.com`, `Asia/Jerusalem`) | **Read** today / pickup windows. Create only if asked. |
| Google Drive | Ready | **Search by job/SKU**. No dedicated VF studio folder was found. |
| Mobbin | Plugin installed; MCP namespace not on this cloud agent | Brief UX only, when the server is actually available. |
| Superdesign | Skill installed | Covers / brief graphics (skip repo init). Needs CLI login for generate. |
| Treg | Skill installed; needs `treg login` | Live SEO/social/ads. Say the catalog price before spending. |

Do not invent Insights to replace Treg. Do not invent ₪ to replace a slicer or Christian.

## Five seats

| Seat | Packs | Desk specialists | Tools |
|---|---|---|---|
| ראש צוות | `vfops` `vfbriefux` | `@studio-operations` `@chief-of-staff` `@meeting-notes-specialist` `@workflow-architect` `@ux-architect` | Calendar, Gmail read, Mobbin |
| סטודיו | `vfconvert` `vfsales` `vfcopy` | `@email-intelligence-engineer` `@discovery-coach` `@sales-engineer` `@proposal-strategist` `@content-creator` `@brand-guardian` | Gmail read, Drive by job |
| צמיחה | `vfgrowth` `vfcovers` `vfigos` `vfinsights` | `@instagram-curator` `@visual-storyteller` `@image-prompt-engineer` `@growth-hacker` `@analytics-reporter` `@social-media-strategist` | Superdesign, Treg, Drive |
| תפעול | `vfcost` `vfbooks` `vfbiz` | `@pricing-analyst` `@bookkeeper-controller` `@finance-tracker` `@business-strategist` | Gmail חשבונות, Drive |
| ייצור | `vfprod` `vfsku` `vlicense` `vfresearch` | `@studio-producer` `@operations-manager` `@legal-compliance-checker` `@research-synthesist` `@trend-researcher` | Drive, Calendar, Treg |

## Daily skills

| Ask for | Skill |
|---|---|
| בריף בוקר / what is open | `.cursor/skills/vf-morning-brief/SKILL.md` |
| פנייה / quote this | `.cursor/skills/vf-inquiry-chain/SKILL.md` |
| חבילת תוכן / covers | `.cursor/skills/vf-content-sprint/SKILL.md` |
| החלטה / קיר / דופק כסף / רוטציה | `.cursor/skills/vf-makers/SKILL.md` |

## Example mentions

```
@studio-operations בריף בוקר
@email-intelligence-engineer קרא את הפנייה הזו ובנה בריף ל-vfconvert
@pricing-analyst גורמי עלות בלי מחיר מכירה
@sales-engineer טיוטת הצעה אחרי הסכום שאמר כריסטיאן
@instagram-curator סקירת לוח בלבד — בלי שליחה
@vfmakers decide האם לפתוח את סט הלוגו
```

## Warehouse

Mention a non-desk `@slug` only when the user asks for that specialty. Do not drag `@godot-gameplay-scripter`, `@gis-analyst`, or `@xiaohongshu-specialist` onto a Sderot print job.
