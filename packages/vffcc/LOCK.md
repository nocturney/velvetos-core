# vffcc locks

נעילות מול [free-claude-code](https://github.com/Alishahryar1/free-claude-code). לא מתקינים ראנטיים שני ב־HQ. לא שולחים. לא ממציאים ₪.

## Cursor Cloud — לא הפרוקסי הזה

`fcc-server` מאזין ל־`localhost:8082` על **מחשב הבעלים**. Cloud Agent של Cursor מחייג למודל של Cursor (הריצה הזו: `cursor-grok-4.6-high-fast`). אין `ANTHROPIC_BASE_URL` שמשנה את החשבון של Cursor.

אסור:

- להתקין `fcc-server` / `fcc-claude` / `curl …/install.sh` בסביבת Cloud Agent
- לשכפל את עץ FCC לתוך `packages/`
- לטעון שמריצים «קלוד חינם» מתוך HQ
- לשים מפתחות (`NVIDIA_NIM_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, …) בגיט או ב־`.env` של הריפו

## קידוד כמשרד שני — דלג ב־HQ

אותה נעילה כמו `vfe2b/LOCK.md`: Claude Code, Codex, Pi, OpenCode, Cline, Hermes, DeepSeek Harness, Grok Build, Muse Code, Aider — **לא** מותקנים כאן. Cursor כבר המשרד.

חריג **מקומי בלבד** (מחשב כריסטיאן, אחרי ראש צוות): ראה `playbooks/local-offload.md`. לא מהריצה הזו.

## שליחה — נעילה קבועה

Discord bot, Telegram bot, וואטסאפ, אינסטגרם, Gmail `send_message` / `reply` / `forward` — אסורים מ־FCC ומ־HQ. Grok שולח.

## קול / טלפון — דלג

Voice notes, Whisper מקומי, NVIDIA NIM transcription, «כמו OpenClaw» — לא מוצר הסטודיו. אדם ב־`050-2517000`.

## מספרים

אין ₪ מכירה בלי ראש צוות. אין Insights מומצא. מגבלות ספק («1.3B+ free tokens») הן טענת הפרויקט; אנחנו לא ממציאים מכסה שנותרה.

## ספקים שנשארים בחוץ מ־HQ

Azure OpenAI, Amazon Bedrock, Google Vertex, Cloudflare Workers AI — ענן ארגוני. לא הסטודיו.

חיבור ChatGPT / xAI / Anthropic רשמי כמפתח ב־HQ — דולג. התזמורת כבר פותחת ChatGPT וג׳מיני בדפדפן. Grok Bot נשאר השולח החי.
