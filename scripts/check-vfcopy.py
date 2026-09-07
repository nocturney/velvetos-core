#!/usr/bin/env python3
"""Content quality sensor for vfcopy publishable captions.

Model (not whole-file scan):
- Publishable body = fenced code blocks after caption headings (להדבקה / ארבעה פריימים).
- Instructions, negative examples, and history outside those fences are not captions.
- Hook = first non-empty line of each publishable body (even if a document title precedes).
- HANDOFF gates: STORIES-FIX + PREFLIGHT only for schedule-ready stories that are not yet
  locked/scheduled; reels do not need STORIES-FIX; blocked/future candidates may stay
  incomplete without failing the repo; historical live posts do not invent new artifact
  demands; ready-but-unlocked items must pass required gates.

Static lint only: no network, no send, no invented approvals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]

FORBIDDEN_PHRASES = [
    "בעידן הדיגיטלי",
    "בעולם שבו",
    "נשמח לעמוד לשירותך",
    "חוויה ייחודית",
    "פתרון מקיף",
    "game-changer",
    "unlock",
]

DM_ONLY = re.compile(r"שלחו(?:\s+)?DM", re.IGNORECASE)
FORBIDDEN_OPENING_NEG = re.compile(r"^\s*(לא|בלי|אין)\b")
CAPTION_HEADING = re.compile(
    r"^#{1,3}\s+.*(להדבקה|ארבעה פריימים)",
    re.IGNORECASE,
)
GID_RE = re.compile(r"\bG0\d{2,3}\b")
TABLE_ROW = re.compile(r"^\|\s*\d+\s*\|")


@dataclass
class CaptionBlock:
    path: Path
    heading: str
    body: str
    start_line: int


@dataclass
class HandoffItem:
    gid: str
    format: str  # reel | stories | carousel | unknown
    status: str  # ready | locked | blocked | historical | mention
    raw: str = ""
    needs_stories_fix: bool = False
    needs_preflight: bool = False


@dataclass
class LintResult:
    problems: list[str] = field(default_factory=list)

    def extend(self, items: list[str]) -> None:
        self.problems.extend(items)

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def vfcopy(self) -> Path:
        return self.root / "packages" / "vfcopy"

    @property
    def vfgrowth(self) -> Path:
        return self.root / "packages" / "vfgrowth"

    @property
    def handoff(self) -> Path:
        return self.vfgrowth / "HANDOFF-he.md"

    @property
    def preflight_dir(self) -> Path:
        return self.vfgrowth / "preflight"


def first_fences_in(section: str) -> list[tuple[int, str]]:
    lines = section.splitlines()
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```"):
            body_lines: list[str] = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                body_lines.append(lines[j])
                j += 1
            out.append((i, "\n".join(body_lines).strip()))
            i = j + 1
            continue
        i += 1
    return out


def extract_publishable_captions(path: Path, text: str | None = None) -> list[CaptionBlock]:
    """Extract only caption fences under paste/stories headings."""
    raw = text if text is not None else path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    blocks: list[CaptionBlock] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if CAPTION_HEADING.search(line):
            heading = line.strip()
            section_lines = [line]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if CAPTION_HEADING.search(nxt):
                    break
                if nxt.startswith("## ") and not any(
                    k in nxt for k in ("להדבקה", "ארבעה פריימים", "על הפריים")
                ):
                    if any(l.strip().startswith("```") for l in section_lines):
                        break
                section_lines.append(nxt)
                j += 1
            section = "\n".join(section_lines)
            for fence_line, body in first_fences_in(section):
                if not body.strip():
                    continue
                blocks.append(
                    CaptionBlock(
                        path=path,
                        heading=heading,
                        body=body.strip(),
                        start_line=i + fence_line + 1,
                    )
                )
            i = j
            continue
        i += 1
    return blocks


def hook_line(body: str) -> str:
    for line in body.splitlines():
        if line.strip():
            return line.strip()
    return ""


def lint_caption_body(body: str, *, label: str) -> list[str]:
    """Lint a single publishable caption body (not instructions)."""
    problems: list[str] = []
    if not body.strip():
        return [f"ריק: {label}"]
    hook = hook_line(body)
    if FORBIDDEN_OPENING_NEG.search(hook):
        problems.append(f"פתיחה מתנצלת/מקטינה ב-{label}: {hook!r}")
    emojis = re.findall(r"[\U0001F300-\U0001FAFF]", hook)
    if len(emojis) > 1:
        problems.append(f"יותר מדי אמוג׳ים בהוק ב-{label}: {hook!r}")
    lower = body.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in lower:
            problems.append(f"ביטוי AI/שיווק ריק ב-{label}: {phrase!r}")
    if DM_ONLY.search(body):
        problems.append(f"CTA 'שלחו DM' אסור ב-{label}")
    return problems


def classify_format(cell: str) -> str:
    c = cell.strip()
    if "סטוריז" in c or "stories" in c.lower():
        return "stories"
    if "ריל" in c or "reel" in c.lower():
        return "reel"
    if "קרוסלה" in c or "carousel" in c.lower():
        return "carousel"
    return "unknown"


def _locked(status_cell: str) -> bool:
    return "משובץ" in status_cell or "נעול" in status_cell


def parse_handoff(text: str) -> list[HandoffItem]:
    """Parse HANDOFF into items with format + pipeline stage."""
    items: list[HandoffItem] = []
    ranked: dict[str, HandoffItem] = {}

    def put(item: HandoffItem) -> None:
        rank = {"historical": 1, "mention": 2, "blocked": 3, "locked": 4, "ready": 5}
        prev = ranked.get(item.gid)
        if prev is None or rank.get(item.status, 0) >= rank.get(prev.status, 0):
            ranked[item.gid] = item

    for m in re.finditer(r"חי כבר:[^\n]+", text):
        line = m.group(0)
        for gid in GID_RE.findall(line):
            put(
                HandoffItem(
                    gid=gid,
                    format="unknown",
                    status="historical",
                    raw=line,
                    needs_stories_fix=False,
                    needs_preflight=False,
                )
            )

    section = "none"
    for line in text.splitlines():
        if "### מוכן" in line or line.strip().startswith("## מוכן"):
            section = "ready"
            continue
        if "### חסום" in line or "מועמד — לא לשבץ" in line or "### מועמד" in line:
            section = "blocked"
            continue
        if line.startswith("## ") and section != "none":
            if any(k in line for k in ("G003 נעול", "אחרי עליית", "קופי", "מה דולג", "חבילת")):
                section = "none"
            continue
        if not TABLE_ROW.search(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        fmt = classify_format(cells[2] if len(cells) > 2 else "")
        candidate = cells[3] if len(cells) > 3 else ""
        status_cell = " ".join(cells[4:]) if len(cells) > 4 else ""
        gids = GID_RE.findall(candidate)
        if not gids:
            gids = GID_RE.findall(line)
        # Expand G007–G012 ranges into individual IDs only when explicit en-dash range
        expanded: list[str] = []
        range_m = re.search(r"(G0\d{2,3})\s*[–\-]\s*(G0\d{2,3})", candidate)
        if range_m:
            a = int(range_m.group(1)[1:])
            b = int(range_m.group(2)[1:])
            for n in range(min(a, b), max(a, b) + 1):
                expanded.append(f"G{n:03d}")
            gids = expanded
        for gid in gids:
            if section == "ready":
                if _locked(status_cell):
                    status = "locked"
                    needs_pf = False
                    needs_sf = False
                else:
                    status = "ready"
                    needs_pf = True
                    needs_sf = fmt == "stories"
            elif section == "blocked":
                # Incomplete candidates do not fail the repo by mere mention.
                claims_ready = (
                    "מוכן לשיבוץ" in status_cell
                    or ("מוכן להדבקה" in status_cell and "חסום" not in status_cell)
                )
                if claims_ready and "נכשל" not in status_cell and "חסום" not in status_cell:
                    status = "ready"
                    needs_pf = True
                    needs_sf = fmt == "stories"
                else:
                    status = "blocked"
                    needs_pf = False
                    needs_sf = False
            else:
                status = "mention"
                needs_pf = False
                needs_sf = False
            put(
                HandoffItem(
                    gid=gid,
                    format=fmt,
                    status=status,
                    raw=line,
                    needs_stories_fix=needs_sf,
                    needs_preflight=needs_pf,
                )
            )
    return list(ranked.values())


def is_schedule_ready_doc(text: str) -> bool:
    if "לא משבצים" in text or "לא מאושר" in text:
        return False
    if "משובץ" in text:
        return True
    if "מוכן להדבקה" in text and "חסום" not in text[:500]:
        return True
    return False


def lint_path_captions(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    blocks = extract_publishable_captions(path, text)
    problems: list[str] = []
    if not blocks:
        if is_schedule_ready_doc(text) and path.name.startswith("G0"):
            problems.append(f"חסר בלוק להדבקה ב-{path.name} (מסומן מוכן)")
        return problems
    for block in blocks:
        label = f"{path.name}:{block.start_line}"
        problems.extend(lint_caption_body(block.body, label=label))
    return problems


def parse_rubric(preflight_text: str) -> dict | None:
    """Parse CONTENT-RUBRIC table from a preflight artifact. None = missing table."""
    # Look for a markdown table row with 6+ numeric cells after a Rubric heading
    lines = preflight_text.splitlines()
    in_rubric = False
    for i, line in enumerate(lines):
        if "Rubric" in line or "CONTENT-RUBRIC" in line or "## ה ·" in line or "## ה " in line:
            in_rubric = True
        if not in_rubric:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # Expect: 5 scores + total + decision (or 5 scores + total)
        nums: list[int] = []
        for c in cells:
            if re.fullmatch(r"\d{1,2}", c):
                nums.append(int(c))
            elif re.fullmatch(r"\d{1,2}\s*/\s*25", c):
                nums.append(int(c.split("/")[0].strip()))
        if len(nums) >= 5:
            scores = nums[:5]
            total = nums[5] if len(nums) > 5 else sum(scores)
            decision = ""
            for c in cells:
                if "עבור" in c or "חוזר" in c:
                    decision = c
                    break
            return {"scores": scores, "total": total, "decision": decision, "sum": sum(scores)}
    return None


def lint_ready_preflight(paths: Paths, item: HandoffItem) -> list[str]:
    """Ready (unlocked) items must have rubric + digest; structure ≠ design pass."""
    problems: list[str] = []
    preflight = paths.preflight_dir / f"{item.gid}.md"
    if not preflight.is_file():
        return problems  # missing file already reported
    text = preflight.read_text(encoding="utf-8")
    if "נכשל-סגור" in text or "**נכשל" in text:
        problems.append(f"{item.gid} מסומן מוכן לשיבוץ אך preflight נכשל-סגור")
        return problems
    rubric = parse_rubric(text)
    if rubric is None:
        problems.append(f"{item.gid} מוכן לשיבוץ אך חסרה טבלת Rubric מלאה ב-preflight")
        return problems
    if any(s < 1 or s > 5 for s in rubric["scores"]):
        problems.append(f"{item.gid} Rubric עם ציון מחוץ לטווח 1–5")
    if 1 in rubric["scores"]:
        problems.append(f"{item.gid} Rubric עם ציר=1 (דגל אדום / נכשל)")
    if rubric["total"] != rubric["sum"]:
        problems.append(
            f"{item.gid} Rubric סה״כ שגוי: כתוב {rubric['total']} אך סכום={rubric['sum']}"
        )
    if rubric["total"] < 20:
        problems.append(f"{item.gid} Rubric מתחת לסף 20/25 (סה״כ {rubric['total']})")
    if "עבור" not in (rubric.get("decision") or "") and "עבור" not in text.split("## ה")[-1][:400]:
        # decision cell or section gate
        if "החלטה" in text and "עבור" not in text:
            problems.append(f"{item.gid} Rubric בלי החלטת עבור")
    # Artifact digest — version lock
    if "caption_sha256" not in text and "artifact_digest" not in text and "sha256" not in text.lower():
        problems.append(f"{item.gid} מוכן לשיבוץ אך חסר digest לגרסת תוצר (שער ו)")
    # Visual evidence note
    if "edit_url" not in text and "png" not in text.lower() and "ראייה" not in text and "thumbnail" not in text.lower():
        problems.append(f"{item.gid} מוכן לשיבוץ אך חסרה ראיית ויזואל ב-preflight")
    return problems


def gate_handoff_requirements(paths: Paths, items: list[HandoffItem] | None = None) -> list[str]:
    if items is None:
        if not paths.handoff.is_file():
            return []
        items = parse_handoff(paths.handoff.read_text(encoding="utf-8"))
    problems: list[str] = []
    for item in items:
        if item.status in {"historical", "blocked", "mention", "locked"}:
            continue
        if item.needs_stories_fix:
            stories = paths.vfcopy / f"{item.gid}-STORIES-FIX.md"
            if not stories.is_file():
                problems.append(
                    f"חסר {stories.relative_to(paths.root)} לסטוריז {item.gid} המסומן מוכן לשיבוץ"
                )
        if item.needs_preflight:
            preflight = paths.preflight_dir / f"{item.gid}.md"
            if not preflight.is_file():
                problems.append(
                    f"חסר {preflight.relative_to(paths.root)} ל-{item.gid} המסומן מוכן לשיבוץ"
                )
            else:
                problems.extend(lint_ready_preflight(paths, item))
    return problems


def check_vfcopy(root: Path | None = None) -> LintResult:
    paths = Paths(root or HERE)
    result = LintResult()
    if not paths.vfcopy.is_dir():
        return result

    for path in sorted(paths.vfcopy.glob("G0*.md")):
        result.extend(lint_path_captions(path))

    if paths.handoff.is_file():
        result.extend(gate_handoff_requirements(paths))

    return result


def main() -> int:
    # Behavioral fixtures first — prove the model, then lint the live tree.
    test_rc = run_tests(quiet=True)
    if test_rc != 0:
        print("FAIL vfcopy behavioral tests")
        return test_rc
    result = check_vfcopy()
    if not result.ok:
        print("FAIL vfcopy content lint:")
        for line in result.problems:
            print("-", line)
        return 1
    print("OK vfcopy captions+stories linted (behavioral=7)")
    return 0


class VfcopyLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vfcopy = self.root / "packages" / "vfcopy"
        self.vfgrowth = self.root / "packages" / "vfgrowth"
        self.preflight = self.vfgrowth / "preflight"
        self.vfcopy.mkdir(parents=True)
        self.preflight.mkdir(parents=True)
        (self.vfcopy / "VOICE.md").write_text("# VOICE\n", encoding="utf-8")
        (self.vfcopy / "VOICE-CHART.md").write_text("# chart\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_handoff(self, body: str) -> None:
        (self.vfgrowth / "HANDOFF-he.md").write_text(body, encoding="utf-8")

    def test_a_internal_instruction_is_not_caption(self) -> None:
        """א. הוראה פנימית אינה מזוהה ככיתוב."""
        path = self.vfcopy / "G090.md"
        path.write_text(
            "# G090\n\nבלי «שלחו DM». CTA: וואטסאפ.\n\n## להדבקה\n\n```\n"
            "ורוד על השידה\n\nוואטסאפ 050-2517000\n```\n",
            encoding="utf-8",
        )
        self.write_handoff(
            "# מסירה\n\n### חסום / מועמד — לא לשבץ עד שחרור\n\n"
            "| # | מתי | מה | מועמד | למה |\n|---|---|---|---|---|\n"
            "| 1 | מחר | קרוסלה | G090 | חסר גלם |\n"
        )
        problems = lint_path_captions(path)
        self.assertEqual(problems, [], problems)
        full = check_vfcopy(self.root)
        self.assertTrue(full.ok, full.problems)

    def test_b_real_bad_caption_is_blocked(self) -> None:
        """ב. כיתוב פסול אמיתי נחסם."""
        path = self.vfcopy / "G091.md"
        path.write_text(
            "# G091\n\n## להדבקה\n\n```\n"
            "שלחו DM עכשיו לחוויה ייחודית\n```\n",
            encoding="utf-8",
        )
        problems = lint_path_captions(path)
        self.assertTrue(any("שלחו DM" in p for p in problems), problems)
        self.assertTrue(any("חוויה ייחודית" in p for p in problems), problems)

    def test_c_hook_checked_despite_document_title(self) -> None:
        """ג. ההוק נבדק גם כשיש כותרת מסמך לפניו."""
        path = self.vfcopy / "G092.md"
        path.write_text(
            "# G092 · כותרת מסמך ארוכה שלא הוק\n\nהקדמה.\n\n## להדבקה\n\n```\n"
            "לא משקולת זה מחזיק\n\nגוף\n```\n",
            encoding="utf-8",
        )
        problems = lint_path_captions(path)
        self.assertTrue(any("פתיחה" in p for p in problems), problems)

    def test_d_reel_does_not_require_stories_fix(self) -> None:
        """ד. ריל אינו נדרש לתיקון סטוריז."""
        (self.vfcopy / "G093.md").write_text(
            "# G093\nמשובץ\n\n## להדבקה\n\n```\nמה יוצא מהמדפסת?\n\nוואטסאפ 050-2517000\n```\n",
            encoding="utf-8",
        )
        self.write_handoff(
            "# מסירה\n\n### מוכן / משובץ\n\n"
            "| # | מתי | מה | מועמד | מצב |\n|---|---|---|---|---|\n"
            "| 1 | היום 16:00 | ריל | **G093** כדור | **נעול · משובץ** |\n"
        )
        result = check_vfcopy(self.root)
        self.assertTrue(result.ok, result.problems)
        self.assertFalse((self.vfcopy / "G093-STORIES-FIX.md").is_file())

    def test_e_ready_story_missing_approvals_blocked(self) -> None:
        """ה. סטורי שמסומן מוכן וחסרים לו אישורים נחסם."""
        (self.vfcopy / "G094.md").write_text(
            "# G094\n\n## להדבקה\n\n```\nורוד על השידה\n\nוואטסאפ 050-2517000\n```\n",
            encoding="utf-8",
        )
        self.write_handoff(
            "# מסירה\n\n### מוכן / משובץ\n\n"
            "| # | מתי | מה | מועמד | מצב |\n|---|---|---|---|---|\n"
            "| 1 | היום 20:30 | סטוריז | **G094** מוצר | מוכן לשיבוץ |\n"
        )
        result = check_vfcopy(self.root)
        self.assertFalse(result.ok, "expected failures")
        blob = "\n".join(result.problems)
        self.assertIn("STORIES-FIX", blob)
        self.assertIn("preflight", blob)

    def test_g_ready_story_bad_rubric_blocked(self) -> None:
        """Rubric missing scores / under threshold / wrong total blocks ready item."""
        (self.vfcopy / "G095.md").write_text(
            "# G095\n\n## להדבקה\n\n```\nורוד על השידה\n\nוואטסאפ 050-2517000\n```\n",
            encoding="utf-8",
        )
        (self.vfcopy / "G095-STORIES-FIX.md").write_text(
            "# fix\n\n## ארבעה פריימים — להדבקה\n\n```\nורוד על השידה\n\nוואטסאפ 050-2517000\n```\n",
            encoding="utf-8",
        )
        (self.preflight / "G095.md").write_text(
            "# pf\nשער: עבור\n\n## ה · Rubric\n\n"
            "| קהל | הוק/בהירות | קול | אמינות/חוק | פעולה | סה״כ | החלטה |\n"
            "|---:|---:|---:|---:|---:|---:|---|\n"
            "| 3 | 3 | 3 | 3 | 3 | 20/25 | עבור |\n",  # sum=15 but total claims 20
            encoding="utf-8",
        )
        self.write_handoff(
            "# מסירה\n\n### מוכן / משובץ\n\n"
            "| # | מתי | מה | מועמד | מצב |\n|---|---|---|---|---|\n"
            "| 1 | היום 20:30 | סטוריז | **G095** | מוכן לשיבוץ |\n"
        )
        result = check_vfcopy(self.root)
        self.assertFalse(result.ok, result.problems)
        blob = "\n".join(result.problems)
        self.assertTrue("סה״כ שגוי" in blob or "מתחת לסף" in blob or "digest" in blob, blob)

    def test_f_historical_publish_no_new_demand(self) -> None:
        """ו. פרסום היסטורי אינו יוצר דרישה חדשה ללא הצדקה."""
        self.write_handoff(
            "# מסירה\n\nחי כבר: G001 `DcqkjOLlYVX` · G002 `DcvuJLxCJgU` — **לא מחליפים**.\n\n"
            "### חסום / מועמד — לא לשבץ עד שחרור\n\n"
            "| # | מתי | מה | מועמד | למה חסום |\n|---|---|---|---|---|\n"
            "| 6 | W38 | ריל / סטוריז | G007–G012 | חסר מועמד/מדיה/כיתוב |\n"
        )
        result = check_vfcopy(self.root)
        blob = "\n".join(result.problems)
        self.assertNotIn("G001-STORIES-FIX", blob)
        self.assertNotIn("G002-STORIES-FIX", blob)
        self.assertNotIn("preflight/G001", blob)
        for n in range(7, 13):
            self.assertNotIn(f"G{n:03d}-STORIES-FIX", blob)
            self.assertNotIn(f"preflight/G{n:03d}", blob)
        self.assertTrue(result.ok, result.problems)


def run_tests(*, quiet: bool = False) -> int:
    import io

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(VfcopyLintTests)
    stream: object = io.StringIO() if quiet else sys.stderr
    verbosity = 0 if quiet else 2
    result = unittest.TextTestRunner(stream=stream, verbosity=verbosity).run(suite)
    if quiet and not result.wasSuccessful():
        sys.stderr.write(getattr(stream, "getvalue", lambda: "")())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"test", "--test"}:
        raise SystemExit(run_tests())
    raise SystemExit(main())
