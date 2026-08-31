# reflection לפני שליחה — טיוטה → ביקורת → שליחה

מקור: [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — דפוס reflection / self-critique (ללא LangGraph חי).  
חבילות: `vfsales`, `vfconvert`, `vfcopy`, `vfigos`.  
שליחה: **רק** דרך כלי HQ (`constitution/SEND.md`).

## מתי

לפני `send_message` / `reply` / failover IG — כשהטיוטה מוכנה אבל רגישה (הצעה, מענה פנייה, בריף, כיתוב IG).

## שלב 1 — טיוטה (worker)

כתוב את הטיוטה המלאה (מייל / caption / בריף slot).

## שלב 2 — reflection (verifier — אותו agent, הקשר נפרד)

ענה על ה checklist **בלי** לשכתב עדיין:

```
□ יש ₪ שלא נאמר במקור? → אם כן, מחק / decision_gate
□ יש Insights / ספירות שלא נמדדו? → «אין ספירה» או הסר
□ CTA אחד בלבד? (WhatsApp 050-2517000 / איסוף שדרות — לא DM)
□ עברית מדוברת, בלי «נשמח לעמוד לשירותך»
□ משלוח ארצי / בוסט / auto-DM? → הסר
□ שמות לקוח / סיסמאות בגיט? → הסר
□ htmlBody תצוגה 3 לבריף? (לא plaintext)
```

## שלב 3 — תיקון

יישם רק תיקונים מה-checklist. אם ₪ חסר → `decision_gate`, לא שליחה.

## שלב 4 — שליחה

- Gmail: `send_message` / `reply` עם גוף מאומת
- IG: publish MCP או failover Canva+Drive+Gmail
- תג: `#נשלח-מ-HQ`

## מה לא

- שרשרת LangGraph / CrewAI נפרדת
- reflection אינסופי — **סיבוב אחד** אחרי הטיוטה
- LLM-as-judge על ₪ — רק השוואה למקור או `decision_gate`
