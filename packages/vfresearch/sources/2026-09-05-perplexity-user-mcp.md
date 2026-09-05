# מחקר · vscode-perplexity-mcp · 5.9.2026

מושב: תפעול. פק `vfmcp`. לא פק חדש. לא סוד בגיט.

מקור: [Automations-Project/VSCode-Perplexity-MCP](https://github.com/automations-project/vscode-perplexity-mcp)  
npm: `perplexity-user-mcp` · Marketplace: `Nskha.perplexity-vscode`  
GitHub `pushed_at` 2026-07-17. README: experimental, not affiliated with Perplexity.

## קונספט

לא מפתח Sonar API. Chromium אמיתי (patchright) מול חשבון Free/Pro/Max שכבר מחובר.  
שומר `cf_clearance` + סשן ב־`~/.perplexity-mcp/` (vault מוצפן).  
פוסט ל־`https://www.perplexity.ai/rest/sse/perplexity_ask` כמו האפליקציה.

זה **כן** עונה על «יש לי מנוי, אין לי חיוב API».  
MCP הרשמי `@perplexity-ai/mcp-server` / `https://api.perplexity.ai/mcp` דורש מפתח API נפרד מהמנוי.

## למה לא ב־Cloud Agent

- IP חווה + לוגין = אותן אזעקות שכבר היו ב־Google/OpenAI.
- README עצמו: ToS / scraping / חשבון עלול להיחסם.
- auto-config כותב `.cursor/mcp.json` ו־`.cursor/rules`.
- נקודת REST פרטית נשברת כשPerplexity משנים את האפליקציה.
- העתקת vault לענן = גניבת סשן. אסור.

## דין HQ

לא מותקן. לא עוגיות. לא npx.  
שולחן Perplexity = `WebSearch` / «דולג — חומה».  
מק בשדרות: רק אחרי ראש צוות, עם סיכון ToS גלוי.  
בעלים דחה מפתחות API (Gemini / ChatGPT / Perplexity).

`packages/vfmcp/SUBSCRIPTIONS.md`.
