# VelvetOS Core

Shared kernel for VelvetOS: contracts, policies, modules and verification.

<p align="center"><a href="#hebrew">עברית</a> · <a href="#english">English</a> · <a href="CHANGELOG.md">Changelog</a></p>

<a id="hebrew"></a>

# ‏עברית

‏**VelvetOS Core** היא הליבה המשותפת של VelvetOS. היא מרכזת חוקים, חוזים, מודולים וכלי בדיקה שמופעים עסקיים יכולים להשתמש בהם. זהו ריפו תשתית, לא אפליקציה עצמאית או לוח מצב חי.

## ‏מבנה הפרויקט

- ‏`packages/` — מודולים ויכולות משותפות.
- ‏`constitution/` — עקרונות ומדיניות.
- ‏`office/` — חוזים ותשתיות לתיאום העבודה.
- ‏`instances/` — תבניות ומופעים עסקיים, כולל `velvet-factory`.
- ‏`scripts/` ו־`.github/workflows/` — כלי פיתוח, בדיקות ואוטומציות.

‏חלוקת האחריות: **Core / Kernel** מגדיר את החוזים והיכולות; **Office** משתמש בהם עבור עסק מסוים; **Edge** הוא רכיב מקומי אופציונלי כשנדרש חיבור לסביבה פיזית. [הסבר ארכיטקטורה](packages/velvetos/LAYERS.md).

## ‏מתחילים

```bash
git clone https://github.com/nocturney/velvetos-core.git
cd velvetos-core
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/check-velvetos.py
```

‏לבדיקת הריפו כולו: `python3 scripts/check-all.py`.

‏לעבודה במופע Velvet Factory: [מדריך התחלה בעברית](docs/START-HERE-HE.md).

## ‏כללים ומקורות

- ‏אין להמציא סטטוס, הצלחת פעולה או עובדות עסקיות. הראיות ומקורות האמת הקנוניים קובעים.
- ‏יכולת טכנית אינה הרשאה לפרסם, לשלוח, למחוק, לחייב או להפעיל ציוד.
- ‏הנחיות לפיתוח ולסוכנים: [AGENTS.md](AGENTS.md) · [שער ניתוב בקשות](packages/velvetos/PROJECT-REQUEST-GATE.md).
- ‏מפת הליבה והמופעים: [docs/VELVETOS.md](docs/VELVETOS.md) · [REPOS.md](packages/velvetos/REPOS.md).
- ‏שינויים ותיעוד טכני: [CHANGELOG.md](CHANGELOG.md) והתיעוד שבתיקיות הרכיבים.

<a id="english"></a>

# English

**VelvetOS Core** is the shared kernel for VelvetOS: reusable policies, contracts, modules and verification tooling. Business-specific identities and workflows belong to their instances. Core is not a standalone application or a live operational dashboard.

**Repository layout:** `packages/` (capabilities), `constitution/` (policies), `office/` (coordination contracts), `instances/` (business instances), and `scripts/` (tooling and checks). See the [architecture](packages/velvetos/LAYERS.md) and [repository map](packages/velvetos/REPOS.md).

**Getting started:** clone the repository, run `python3 scripts/velvetos.py core` to inspect the kernel, and `python3 scripts/check-velvetos.py` for a scoped check. Use `python3 scripts/check-all.py` for the full suite. For the Velvet Factory instance, see the [Hebrew setup guide](docs/START-HERE-HE.md).

**Source of truth:** [project instructions](AGENTS.md) · [request gate](packages/velvetos/PROJECT-REQUEST-GATE.md) · [architecture](docs/VELVETOS.md) · [changelog](CHANGELOG.md). Implementation details and historical test evidence live with their components, not in this landing page.

<details>
<summary>Latest repository snapshot / תמונת מצב שמורה (not live)</summary>

<!-- OPERATIONAL-SNAPSHOT:START -->
<table>
<tr>
<td align="center"><strong>HEALTHY</strong><br><sub><span dir="ltr">System Health</span><br><span dir="rtl">בריאות מערכת</span></sub></td>
<td align="center"><strong>4</strong><br><sub><span dir="ltr">Live / Bound Paths</span><br><span dir="rtl">נתיבים חיים / מחוברים</span></sub></td>
<td align="center"><strong>2</strong><br><sub><span dir="ltr">Gated Actions</span><br><span dir="rtl">פעולות מבוקרות</span></sub></td>
<td align="center"><strong>0</strong><br><sub><span dir="ltr">Needs Attention</span><br><span dir="rtl">דורש טיפול</span></sub></td>
</tr>
<tr>
<td align="center"><strong>23</strong><br><sub><span dir="ltr">Living Studio Skills</span><br><span dir="rtl">יכולות</span></sub></td>
<td align="center"><strong>135</strong><br><sub><span dir="ltr">Sensors</span><br><span dir="rtl">חיישנים</span></sub></td>
<td align="center"><strong>19</strong><br><sub><span dir="ltr">Workflows</span><br><span dir="rtl">אוטומציות</span></sub></td>
<td align="center"><strong>31</strong><br><sub><span dir="ltr">Packs</span><br><span dir="rtl">חבילות</span></sub></td>
</tr>
</table>

| Pulse | Current committed evidence |
|---|---|
| **Instagram MCP** | LIVE / VERIFIED |
| **Instagram Insights** | LIVE / VERIFIED |
| **Media Intake / Drive** | LIVE / VERIFIED |
| **Jobs source of truth** | Google Sheet LIVE / VERIFIED write-through |
| **Waiting work** | 1 |
| **Owner blocked** | 0 |
| **Degraded tools** | 0 |
| **Last verified / refreshed evidence** | `2026-10-21T09:58:39+03:00` |

<div dir="rtl"><strong>מה השתנה:</strong> Office Control Plane מוטמע · followups=1 · dead_letters=0</div>
<div dir="ltr"><strong>What changed:</strong> Office Control Plane מוטמע · followups=1 · dead_letters=0</div>

<div dir="rtl"><strong>חוזה הפולס:</strong> הבלוק מציג את הראיות האחרונות שנשמרו בריפו. הוא לא מבצע קריאת ספק חיה בזמן טעינת GitHub ולא הופך “מוגדר” ל“מאומת”.</div>
<div dir="ltr"><strong>Pulse contract:</strong> this block reports the latest evidence committed to the repository. It never performs a live provider call while rendering GitHub, and never turns “configured” into “verified”.</div>
<!-- OPERATIONAL-SNAPSHOT:END -->

</details>
