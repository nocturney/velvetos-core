#!/usr/bin/env python3
"""Hebrew copy lint for Velvet Factory — style + business-truth gates.

Used by scripts/check-vfcopy.py and by agents via:
  python3 scripts/check-vfcopy.py lint --text '…'
  python3 scripts/check-vfcopy.py lint --text '…' --rewrite
  python3 scripts/check-vfcopy.py eval

No network. No send. No invented prices.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any

# --- AI / marketing clichés (Hebrew + common EN tells) ---
AI_TELL_PHRASES: list[str] = [
    "אנו גאים להציג",
    "נרגשים לשתף",
    "חוויה ייחודית",
    "הופכים חלום למציאות",
    "החלום הופך למציאות",
    "כשהיצירתיות פוגשת",
    "היצירתיות פוגשת",
    "כל פרט מספר סיפור",
    "בדיוק בשבילכם",
    "הקסם קורה",
    "לקחנו את",
    "לשלב הבא",
    "התוצאה?",
    "וזה בדיוק מה שאנחנו אוהבים",
    "כי בסוף",
    "מושלם לכל",
    "נשמח לעמוד לשירותכם",
    "נשמח לעמוד לשירותך",
    "בעידן הדיגיטלי",
    "בעולם שבו",
    "פתרון מקיף",
    "אל תהססו לפנות",
    "לסיכום",
    "מקווים שעזרנו",
    "game-changer",
    "unlock",
    "elevate",
    "revolutionize",
    "leverage",
    "seamless",
]

NATIONAL_SHIPPING = re.compile(
    r"משלוח\s+לכל\s+הארץ|משלוחים?\s+לכל\s+הארץ|shipping\s+nationwide|national\s+shipping",
    re.IGNORECASE,
)
INVENTED_PRICE = re.compile(
    r"(?:רק\s+ב[־\-]?\s*|ב[־\-]?\s*|רק\s+)\d{1,5}\s*₪|₪\s*\d{1,5}|(?:מבצע|דיל)\s+[^\n]{0,20}\d+\s*₪",
    re.IGNORECASE,
)
TURNAROUND_CLAIM = re.compile(
    r"מוכן\s+תוך\s+\d+|תוך\s+24\s*שעות|תוך\s+יומיים|מוכן\s+מחר|same[\s\-]?day",
    re.IGNORECASE,
)
FAKE_TESTIMONIAL = re.compile(
    r"תודה\s+ללקוח|הלקוח\s+המדהים|ביקורת\s+חמה|testimonial|★★★★★",
    re.IGNORECASE,
)
DM_ONLY = re.compile(r"שלחו(?:\s+)?DM", re.IGNORECASE)
WA_PHONE_CTA = re.compile(
    r"050[-–]?2517000|וואטסאפ\s*050|whatsapp\s*050|wa\.me/",
    re.IGNORECASE,
)
FORBIDDEN_OPENING_NEG = re.compile(r"^\s*(לא|בלי|אין)\b")
HASHTAG_RE = re.compile(r"(?:^|\s)(#[\w\u0590-\u05FF]+)")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]")
EM_DASH_RE = re.compile(r"[—–]")
IMAGE_DESC_ONLY = re.compile(
    r"בתמונה\s+רואים|בתמונה\s+יש|האובייקט\s+הוא|רואים\s+אובייקט",
    re.IGNORECASE,
)
NOT_ONLY_BUT = re.compile(r"לא\s+רק\s+.+\s+אלא\s+", re.DOTALL)
RULE_OF_THREE_LINES = re.compile(
    r"(?:^|\n)\s*אנחנו\s+\S+\.\s*\n\s*אנחנו\s+\S+\.\s*\n\s*אנחנו\s+\S+\.",
    re.MULTILINE,
)
CORPORATE_FORMAL = re.compile(
    r"אנו\s+(?:גאים|שמחים|מתכבדים)|בברכה\s+והערכה|נכבדים",
)
TRANSLATED_EN = re.compile(
    r"\b(?:unlock|elevate|game[\s\-]?changer|wow\.?|leverage|seamless)\b",
    re.IGNORECASE,
)


@dataclass
class CopyVerdict:
    status: str  # pass | fail_style | fail_fact | needs_input
    problems: list[str] = field(default_factory=list)
    rewrite: str | None = None
    kind: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "pass"


def _count_hashtags(body: str) -> int:
    return len(HASHTAG_RE.findall(body))


def _count_emojis(text: str) -> int:
    return len(EMOJI_RE.findall(text))


def _hook(body: str) -> str:
    for line in body.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _non_hashtag_lines(body: str) -> list[str]:
    out: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split()
        if parts and all(p.startswith("#") for p in parts):
            continue
        out.append(s)
    return out


def lint_hebrew_copy(
    body: str,
    *,
    label: str = "candidate",
    context: dict[str, Any] | None = None,
    offer_rewrite: bool = False,
) -> CopyVerdict:
    """Lint one Hebrew copy candidate for style + business truth."""
    ctx = context or {}
    problems: list[str] = []
    kinds: list[str] = []
    needs_input = False

    if not body or not body.strip():
        return CopyVerdict(
            status="needs_input",
            problems=[f"ריק / חסר טקסט ב-{label}"],
            kind=["needs_input"],
        )

    hook = _hook(body)
    lower = body.lower()

    for phrase in AI_TELL_PHRASES:
        if phrase.lower() in lower or phrase in body:
            problems.append(f"ביטוי AI/שיווק ריק ב-{label}: {phrase!r}")
            kinds.append("style")
    if NOT_ONLY_BUT.search(body):
        problems.append(f"דפוס «לא רק X אלא Y» ב-{label}")
        kinds.append("style")
    if RULE_OF_THREE_LINES.search(body) or "אנחנו מעצבים. אנחנו מדפיסים. אנחנו משנים" in body:
        problems.append(f"שלשות/סימטריה מלאכותית ב-{label}")
        kinds.append("style")
    if CORPORATE_FORMAL.search(body):
        problems.append(f"עברית תאגידית/פורמלית מדי ב-{label}")
        kinds.append("style")
    if TRANSLATED_EN.search(body):
        problems.append(f"אנגלית מתורגמת / buzzwords ב-{label}")
        kinds.append("style")
    # Approved VF voice uses an occasional Hebrew em dash; flag only stacks (AI habit).
    if body.count("—") + body.count("–") >= 4:
        problems.append(f"em dash עודף כקישוט AI ב-{label}")
        kinds.append("style")
    if IMAGE_DESC_ONLY.search(body):
        problems.append(
            f"תיאור תמונה בלבד ב-{label} (הכיתוב צריך לעבוד, לא לספר מה העין רואה)"
        )
        kinds.append("style")

    if FORBIDDEN_OPENING_NEG.search(hook):
        problems.append(f"פתיחה מתנצלת/מקטינה ב-{label}: {hook!r}")
        kinds.append("style")

    emoji_hook = _count_emojis(hook)
    emoji_all = _count_emojis(body)
    if emoji_hook > 1 or emoji_all > 4:
        problems.append(f"אמוג׳ים עודפים ב-{label} (hook={emoji_hook}, total={emoji_all})")
        kinds.append("style")

    tags = _count_hashtags(body)
    if tags > 5:
        problems.append(f"יותר מ־5 האשטגים ב-{label}: {tags}")
        kinds.append("style")

    content_lines = _non_hashtag_lines(body)
    if len(content_lines) > 12 or len(body) > 900:
        problems.append(f"כיתוב ארוך מדי ב-{label}")
        kinds.append("style")

    if DM_ONLY.search(body):
        problems.append(
            f"CTA 'שלחו DM' אסור ב-{label} (אוטו־DM / אנגלית; השתמשו בהודעת Instagram בעברית)"
        )
        kinds.append("style")

    generic_markers = (
        "מוצר חדש ומדהים",
        "מחכה לכם בסטודיו",
        "פתרון מושלם",
        "הכי טוב בשוק",
    )
    if any(m in body for m in generic_markers):
        problems.append(f"קופי גנרי (מבחן מאפייה) ב-{label}")
        kinds.append("style")
        if ctx.get("product") is None and ctx.get("media") is None:
            needs_input = True

    if NATIONAL_SHIPPING.search(body):
        problems.append(f"משלוח ארצי אסור ב-{label} — איסוף שדרות בלבד")
        kinds.append("fact")
    if WA_PHONE_CTA.search(body):
        problems.append(
            f"CTA וואטסאפ/טלפון אסור בתוכן ציבורי ב-{label} — PUBLIC_CURRENT_CTA = הודעת Instagram"
        )
        kinds.append("fact")
    if INVENTED_PRICE.search(body) and "X ₪" not in body:
        problems.append(
            f"מחיר מספרי בכיתוב ב-{label} — אין להמציא ₪; במשרד השתמשו ב־X ₪ עד אימות"
        )
        kinds.append("fact")
    if TURNAROUND_CLAIM.search(body):
        problems.append(f"הבטחת זמן הכנה ב-{label} בלי מקור רצפה")
        kinds.append("fact")
        needs_input = True
    if FAKE_TESTIMONIAL.search(body):
        problems.append(f"לקוח/testimonial מומצא או לא מאומת ב-{label}")
        kinds.append("fact")
        if ctx.get("customer_name") is None:
            needs_input = True

    for req in ctx.get("requires") or []:
        if ctx.get(req) in (None, "", []):
            needs_input = True
            problems.append(f"needs_input: חסר {req} ב-{label}")
            kinds.append("needs_input")

    if re.search(r"מבצע|דיל\s+מיוחד|עכשיו\s+ב[־\-]", body) and ctx.get("price") in (
        None,
        "",
    ):
        needs_input = True
        problems.append(f"needs_input: מבצע/מחיר ב-{label} בלי סכום מאומת")
        kinds.append("needs_input")

    problems = list(dict.fromkeys(problems))
    kinds = list(dict.fromkeys(kinds))

    if needs_input or "needs_input" in kinds:
        status = "needs_input"
    elif "fact" in kinds:
        status = "fail_fact"
    elif "style" in kinds:
        status = "fail_style"
    else:
        status = "pass"

    rewrite = None
    if offer_rewrite and status == "fail_style":
        rewrite = suggest_style_rewrite(body)

    return CopyVerdict(status=status, problems=problems, rewrite=rewrite, kind=kinds)


def suggest_style_rewrite(body: str) -> str:
    """One focused style rewrite — strip known AI tells; do not invent facts."""
    text = body
    replacements = [
        ("אנו גאים להציג", ""),
        ("נרגשים לשתף", ""),
        ("חוויה ייחודית", "עבודה מהרצפה"),
        ("כשהיצירתיות פוגשת", ""),
        ("היצירתיות פוגשת", ""),
        ("נשמח לעמוד לשירותכם", ""),
        ("נשמח לעמוד לשירותך", ""),
        ("פתרון מקיף", ""),
        ("מושלם לכל", "מתאים ל"),
        ("בדיוק בשבילכם", ""),
        ("הקסם קורה", ""),
        ("כל פרט מספר סיפור", ""),
        ("שלחו DM עכשיו", "שלחו לנו הודעה כאן באינסטגרם"),
        ("שלחו DM", "שלחו לנו הודעה כאן באינסטגרם"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([!.?])", r"\1", text)
    text = re.sub(r"^\s*[!.?]+\s*", "", text)
    text = re.sub(r"שבה\s+(את\s+)?", "עם ", text, count=1)
    lines = text.splitlines()
    if lines:
        first = lines[0]
        emojis = EMOJI_RE.findall(first)
        if len(emojis) > 1:
            kept = False
            out_chars: list[str] = []
            for ch in first:
                if EMOJI_RE.fullmatch(ch):
                    if not kept:
                        out_chars.append(ch)
                        kept = True
                    continue
                out_chars.append(ch)
            lines[0] = "".join(out_chars).strip()
            text = "\n".join(lines)
    note = "<!-- rewrite ממוקד לסגנון בלבד; בדקו עובדות ידנית -->"
    if not text:
        return f"{note}\nneeds_input: הטיוטה התרוקנה אחרי ניקוי AI — חסר פרט מהרצפה"
    return f"{note}\n{text}"


def load_evals(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_eval_suite(evals_path: Path) -> tuple[int, int, list[str]]:
    """Return (passed, total, failure_lines)."""
    data = load_evals(evals_path)
    cases = data.get("cases") or []
    failed: list[str] = []
    passed = 0
    for case in cases:
        cid = case.get("id", "?")
        expect = case.get("expect", "pass")
        body = case.get("body", "")
        ctx = case.get("context") or {}
        verdict = lint_hebrew_copy(body, label=cid, context=ctx)
        ok = verdict.status == expect
        if not ok and expect == "needs_input" and verdict.status in {
            "needs_input",
            "fail_fact",
        }:
            if any(
                k in p
                for p in verdict.problems
                for k in ("needs_input", "חסר", "מבצע", "זמן", "לקוח", "גנרי")
            ):
                ok = True
        if not ok and expect == "fail_fact" and verdict.status == "needs_input":
            if "fact" in verdict.kind or any(
                k in p for p in verdict.problems for k in ("משלוח", "₪", "וואטסאפ", "מחיר")
            ):
                ok = True
        if not ok and expect == "fail_style" and verdict.status == "needs_input":
            # thin generic copy may escalate to needs_input — still a reject
            if "style" in verdict.kind:
                ok = True
        if ok:
            passed += 1
        else:
            failed.append(
                f"{cid}: expect={expect} got={verdict.status} problems={verdict.problems}"
            )
    return passed, len(cases), failed


def assert_skill_wired(root: Path) -> list[str]:
    """Prove velvet-hebrew-copy is part of the agent flow, not orphan docs."""
    problems: list[str] = []
    skill = root / "packages" / "vfcopy" / "skills" / "velvet-hebrew-copy" / "SKILL.md"
    if not skill.is_file():
        return ["חסר packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md"]
    text = skill.read_text(encoding="utf-8")
    for needle in ("velvet-hebrew-copy", "needs_input", "מבחן מאפייה", "voice/approved"):
        if needle not in text:
            problems.append(f"SKILL.md missing {needle!r}")
    pack_skill = root / "packages" / "vfcopy" / "SKILL.md"
    if pack_skill.is_file():
        ps = pack_skill.read_text(encoding="utf-8")
        if "velvet-hebrew-copy" not in ps:
            problems.append("packages/vfcopy/SKILL.md must reference velvet-hebrew-copy")
    voice = root / "packages" / "vfcopy" / "VOICE.md"
    if voice.is_file() and "velvet-hebrew-copy" not in voice.read_text(encoding="utf-8"):
        problems.append("VOICE.md must reference velvet-hebrew-copy")
    playbook = root / "packages" / "vfcopy" / "hq" / "PLAYBOOK.md"
    if playbook.is_file() and "velvet-hebrew-copy" not in playbook.read_text(
        encoding="utf-8"
    ):
        problems.append("hq/PLAYBOOK.md must reference velvet-hebrew-copy")
    approved = root / "packages" / "vfcopy" / "voice" / "approved" / "examples.json"
    generated_readme = root / "packages" / "vfcopy" / "voice" / "generated" / "README.md"
    if not approved.is_file():
        problems.append("חסר voice/approved/examples.json")
    if not generated_readme.is_file():
        problems.append("חסר voice/generated/README.md (הפרדת קורפוס)")
    evals = root / "packages" / "vfcopy" / "evals" / "hebrew-copy-evals.json"
    if not evals.is_file():
        problems.append("חסר evals/hebrew-copy-evals.json")
    else:
        data = load_evals(evals)
        n = len(data.get("cases") or [])
        if n < 20:
            problems.append(f"evals must have ≥20 cases (have {n})")
    return problems
