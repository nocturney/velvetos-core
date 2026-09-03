# Instance Onboard — פרונט חדש על הליבה

מודול: `expert-instance-onboard`.

## מתי

עסק חדש → ריפו `VelvetOS — <Business Name>` נפרד (לא tenant בתוך Core).

## צעדים

### 1. בחר preset

| preset | אנכי |
|---|---|
| `maker-print` | הדפסה / maker (VF) |
| `beauty-multi-ig` | יופי multi-IG |
| `clinical-legal-opinions` | חוות דעת (ללא IG חי) |

קובץ: `packages/velvetos/presets/<id>.json`

### 2. modulesEnabled

העתק מ-preset + הוסף מומחים לפי צורך:

- `expert-revenue-loop` — IG כפרנסה
- `expert-social-booster` · `expert-media-director` · `expert-trend-explorer`
- `expert-insights-ingest` — מדידה
- `office-learning` — רטרו יומי
- `expert-instance-onboard` — meta (אופציונלי)

### 3. Scaffold

```bash
# מ-Core:
PUSH=1 ./scripts/publish-instance.sh <instance-id> nocturney/velvetos-<name>
```

מקור: `instances/<instance-id>/` · `REPOS.md`

### 4. זיכרון per-instance

צור: `packages/vfops/data/owner-memory-<instance-id>.md`  
(בפרונט: `vendor/velvetos-core/packages/vfops/data/owner-memory-<instance-id>.md`)

בריף ורטרו קוראים **קובץ ה-instance**, לא זיכרון VF אחר.

### 5. ערוצים

- IG: `instance/*.json` → `channels.instagram[]` (primary אחד)
- CTA / WhatsApp / pickup: `cta`, `fulfillment`
- compliance: `compliance-beauty` וכו׳

### 6. חיבור Core

```bash
cd velvetos-<name>
./scripts/attach-core.sh
python3 vendor/velvetos-core/scripts/check-all.py  # מ-Core
```

Cloud: `.cursor/environment.json` → `install: ./scripts/attach-core.sh`

### 7. ראש צוות

- `INITIAL-RETRO.md` פעם אחת
- `DAILY-RETRO.md` מכאן ואילך
- `WEEKLY-REVENUE-PULSE.md` אם `expert-revenue-loop` מופעל

## אסור

- עסק שני חי **בתוך** Core (רק `instances/` scaffold)
- המצאת Origin slug
- ₪ / Insights בפרופיל instance
