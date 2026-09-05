# תחקור VoiceStudio · 2026-09-05

מושב: ייצור · `@research-synthesist`  
מקור: [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) (AGPL-3.0 · ~18k★ · Python/Tauri) · אתר: https://voicestudio.sh  
סטודיו: Velvet Factory · שדרות · איסוף · וואטסאפ `050-2517000` · IG `@velvets_cloud`  
לא פק חדש. לא Docker / DMG / MSI על Cloud Agent. לא ElevenLabs SaaS.

## מה זה

אלטרנטיבה מקומית ל־ElevenLabs: שיבוט קול, עיצוב קול, דיבוב וידאו, דיקטציה, תמלול, ספרי שמע — קטלוג שפות רחב (646 לפי README; כיסוי תלוי מנוע).  
16 מנועי TTS · 11 ASR · Desktop + API מקומי (REST/SSE/WebSocket) + **MCP Server** על `http://localhost:3900/mcp`.  
קודם: OmniVoice-Studio. בטא פעילה — להעדיף release יציב, לא `main` חי.

## דירוג מקור

| שדה | ערך |
|---|---|
| סוג | ריפו OSS + README + `docs/mcp.md` |
| משקל | Primary לתיאור מוצר; לא מדד איכות אודיו שלנו |
| עצמאי | כן (לא ציטוט משני של ElevenLabs) |
| מגבלות | AGPL אפליקציה; משקלי מודל נשארים בתנאי upstream (כולל CC-BY-NC ב־OmniVoice default) |

## מה כבר יש אצלנו (לא לשכפל)

| אצלם | אצלנו | דין |
|---|---|---|
| Voice cloning / design | אין מוצר קול | **skip** — סטודיו מדפיס ומצלם מיטה |
| Video dubbing / localization | `vfom` `localization-dub` = skip | כבר נעול — «Hebrew-first; not a dub shop» |
| Piper / ElevenLabs / cloud TTS | `vfom/LOCK.md` | כבר דולג |
| MCP `generate_speech` / `transcribe` / `clone_voice` | Canva + גלם רצפה לרילים | **skip על Cloud**; Desktop רק אחרי ראש צוות |
| Audiobook / stories / podcast | אין | **skip** |
| Engine catalogue + hot-switch | בחירת כלי לפי משימה | דפוס — לא התקנה |
| Local-first + opt-in network | חוקת failover / בלי סוד בגיט | דפוס מיושר |
| Per-agent voice binding (`X-VoiceStudio-Client-Id`) | מושבים + CTA אנושי | **watch** — לא קול מדובר כמותג בלי אישור |

## מה הוטמע היום (דפוסים)

| מקור | לאן | למה |
|---|---|---|
| נעילת dub/TTS/AGPL שני | `packages/vfom/LOCK.md` | VoiceStudio ליד ElevenLabs — אין מונורפו AGPL שני, אין דיבוב כצינור |
| הערת SaaS/מנוע | `packages/vfom/EMBED.md` | Voiceover מקומי = later אחרי ראש צוות; עוגן = גלם מיטה |
| MCP localhost:3900 | `docs/MCP-FIT.md` + `packages/vfmcp/GAP.md` | Do-not-install על Cloud; Desktop optional אחרי lead + `vlicense` על משקלים |
| רישום | `LINKS.json` | mid-week append |

## מה לדחות / watch

| פריט | למה |
|---|---|
| התקנת DMG/MSI/Docker/`bun run desktop` מ־HQ | Cloud אין GPU/backend מקומי; Cursor = משרד |
| MCP על Cloud Agent | דורש backend על `localhost:3900` |
| שיבוט קול בעלים ל־IG בלי אישור | הסכמה + מותג; ריל VF = הוכחת רצפה |
| משקלי CC-BY-NC / AGPL | שערי `vlicense` — לא מסחרי בלי בדיקה |
| החלפת מוזיקת ריל ב־TTS | מוזיקה = `vfresearch/MUSIC.md`; קול = אדם/רצפה |

## סדר עדיפות (בלי התקנה עיוורת)

1. **רילים** — נשארים Canva + טיימלאפס (`vfom` crews). אין VoiceStudio בצינור.
2. **אם ראש צוות רוצה VO מקומי** — Mac Desktop בלבד; MCP `files` mode (לא base64 בקונטקסט); נתיב בסיס מוגבל; רישיון מודל לפני שימוש מסחרי.
3. **תמלול פניות** — לא עכשיו; Gmail/וואטסאפ אנושיים מספיקים.

## מקורות שנפתחו

- https://github.com/debpalash/VoiceStudio (README, stars, license, topics)
- https://raw.githubusercontent.com/debpalash/VoiceStudio/main/docs/mcp.md
- `packages/vfom/LOCK.md` / `catalog.json` (`localization-dub`)

## אסור שנשמר

אין ₪ · אין Insights · אין טענה ש־IG פורסם · אין התקנת VoiceStudio על Cloud · אין Print מ־HQ · אין אוטו־DM · אין המצאת איכות אודיו.
