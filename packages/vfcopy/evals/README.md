# Eval suite — עברית · vfcopy

מריצים:

```bash
python3 scripts/check-vfcopy.py eval
```

כל מקרה בודק **סגנון** ו/או **אילוצים עובדתיים**.  
`expect`: `pass` | `fail_style` | `needs_input` | `fail_fact`  
מקרי anti-slop יכולים להוסיף `expect_patterns` עם מזהי דפוסים; ה-eval דורש שהמזהים עצמם יזוהו, לא רק כישלון כללי.

אין רשת. אין שליחה. אין המצאת תשובות «נכונות» לכיתוב — רק לינט/שערים.
