#!/usr/bin/env python3
"""Compose VF-G005 Instagram carousel slides at 1080×1350.

New stills + Hebrew type via Pillow/Noto. Lines map onto vfcopy / vfconvert /
vfgrowth facts. No invented ₪. No «אין משלוח» opener.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = Path("/opt/cursor/artifacts/assets")
WORK = ROOT / "work"
SLIDES = ROOT / "slides"
W, H = 1080, 1350

GOLD = (212, 175, 55, 255)
CREAM = (246, 238, 216, 255)
CREAM_DIM = (246, 238, 216, 200)
NAVY = (7, 11, 20, 255)

FONT_SERIF = "/usr/share/fonts/truetype/croscore/Tinos-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"
FONT_SANS_B = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"

CROPS = {
    "g005_bg_01_cover.png": (0, 256, 1024, 1536),
    "g005_bg_02_idea.png": (0, 220, 1024, 1500),
    "g005_bg_03_file.png": (0, 256, 1024, 1536),
    "g005_bg_04_measure.png": (0, 240, 1024, 1520),
    "g005_bg_05_slice.png": (0, 80, 1024, 1360),
    "g005_bg_06_pickup.png": (0, 128, 1024, 1408),
    "g005_bg_07_cta.png": (0, 256, 1024, 1536),
}

SLIDES_SPEC = [
    {
        "bg": "g005_bg_01_cover.png",
        "out": "VF-G005-01-cover.jpg",
        "layout": "cover",
        "kicker": "VELVET FACTORY · שדרות",
        "title": "5 דברים שכדאי לדעת",
        "sub": "לפני שמזמינים הדפסת תלת־ממד",
        "foot": "קרוסלה · איסוף מהסטודיו",
    },
    {
        "bg": "g005_bg_02_idea.png",
        "out": "VF-G005-02-idea.jpg",
        "layout": "side",
        "num": "01 / 05",
        "title": "מה מייצרים",
        "body": "מתחילים מהרעיון — חפץ, מתנה, חלק, או משהו שרואים בתמונה.",
    },
    {
        "bg": "g005_bg_03_file.png",
        "out": "VF-G005-03-file.jpg",
        "layout": "top",
        "num": "02 / 05",
        "title": "קובץ או תמונה",
        "body": "STL, STEP, או צילום. הסטודיו ממשיך משם.",
    },
    {
        "bg": "g005_bg_04_measure.png",
        "out": "VF-G005-04-use.jpg",
        "layout": "card",
        "num": "03 / 05",
        "title": "מידות ושימוש",
        "body": "איך זה יישב, ואיפה זה יחיה. החומר נבחר לפי השימוש.",
    },
    {
        "bg": "g005_bg_05_slice.png",
        "out": "VF-G005-05-slice.jpg",
        "layout": "top",
        "num": "04 / 05",
        "title": "הסלייס סוגר את התאריך",
        "body": "אחרי הסלייס והתור ברצפה נקבע מתי זה מוכן לאיסוף.",
    },
    {
        "bg": "g005_bg_06_pickup.png",
        "out": "VF-G005-06-pickup.jpg",
        "layout": "bottom",
        "num": "05 / 05",
        "title": "איסוף בשדרות",
        "body": "מגיעים לסטודיו. וואטסאפ 050-2517000",
    },
    {
        "bg": "g005_bg_07_cta.png",
        "out": "VF-G005-07-cta.jpg",
        "layout": "cta",
        "kicker": "VELVET FACTORY",
        "title": "050-2517000",
        "sub": "וואטסאפ · איסוף משדרות",
        "foot": "@velvets_cloud",
    },
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def crop_bg(name: str) -> Image.Image:
    im = Image.open(ASSETS / name).convert("RGB")
    return im.crop(CROPS[name]).resize((W, H), Image.Resampling.LANCZOS)


def gradient(size: tuple[int, int], kind: str) -> Image.Image:
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    px = overlay.load()
    for y in range(h):
        t = y / (h - 1)
        for x in range(w):
            u = x / (w - 1)
            if kind == "cover":
                a = int(255 * (0.08 + 0.82 * max(0, (t - 0.42) / 0.58) ** 1.15))
            elif kind == "side":
                a = int(255 * (0.90 * max(0, (u - 0.28) / 0.72) ** 0.85))
            elif kind == "top":
                a = int(255 * (0.86 * max(0, 1 - t / 0.46) ** 1.1 + 0.18 * t))
            elif kind == "card":
                a = int(255 * (0.22 + 0.50 * ((u - 0.5) ** 2 + (t - 0.4) ** 2) ** 0.55))
            elif kind == "bottom":
                a = int(255 * (0.10 + 0.80 * max(0, (t - 0.48) / 0.52) ** 1.2))
            else:  # cta
                a = int(255 * (0.35 + 0.50 * max(0, (t - 0.35) / 0.65)))
            px[x, y] = (7, 11, 20, min(230, a))
    return overlay


def wrap_logical(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for word in words:
        trial = " ".join(cur + [word])
        if fnt.getlength(trial) <= max_w or not cur:
            cur.append(word)
        else:
            lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill,
    *,
    anchor: str = "ra",
    rtl: bool = True,
) -> None:
    kw = dict(font=fnt, fill=fill, anchor=anchor)
    if rtl:
        kw["direction"] = "rtl"
        kw["language"] = "he"
    draw.text(xy, text, **kw)


def draw_lines(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: list[str],
    fnt: ImageFont.FreeTypeFont,
    fill,
    *,
    align: str = "right",
    leading: float = 1.2,
) -> int:
    ascent, descent = fnt.getmetrics()
    lh = int((ascent + descent) * leading)
    for i, line in enumerate(lines):
        if align == "center":
            draw_text(draw, (x, y + i * lh), line, fnt, fill, anchor="ma")
        else:
            draw_text(draw, (x, y + i * lh), line, fnt, fill, anchor="ra")
    return y + len(lines) * lh


def rule(draw: ImageDraw.ImageDraw, x_right: int, y: int, width: int = 88) -> None:
    draw.rectangle((x_right - width, y, x_right, y + 3), fill=GOLD)


def frame(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((36, 36, W - 37, H - 37), outline=(212, 175, 55, 80), width=1)


def rounded_rect(base: Image.Image, box: tuple[int, int, int, int], fill, radius=18) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(box, radius=radius, fill=fill)
    base.alpha_composite(overlay)


def compose(spec: dict) -> Image.Image:
    bg = crop_bg(spec["bg"]).convert("RGBA")
    layout = spec["layout"]
    bg.alpha_composite(gradient((W, H), layout if layout != "cta" else "cta"))
    draw = ImageDraw.Draw(bg)
    frame(draw)

    sans_k = font(FONT_SANS_B, 22)
    sans_n = font(FONT_SANS_B, 20)
    sans_b = font(FONT_SANS, 30)
    serif = font(FONT_SERIF, 64)
    serif_lg = font(FONT_SERIF, 70)
    sans_phone = font(FONT_SANS_B, 68)

    if layout == "cover":
        x = W - 88
        y = 860
        draw_text(draw, (x, y), spec["kicker"], sans_k, GOLD)
        rule(draw, x, y + 28)
        title_lines = wrap_logical(spec["title"], serif_lg, 900)
        y = draw_lines(draw, x, y + 48, title_lines, serif_lg, CREAM, leading=1.12)
        y = draw_lines(draw, x, y + 8, [spec["sub"]], font(FONT_SANS, 32), CREAM)
        draw_lines(draw, x, y + 18, [spec["foot"]], font(FONT_SANS, 22), CREAM_DIM)

    elif layout == "side":
        x = W - 88
        y = 170
        draw_text(draw, (x, y), spec["num"], sans_n, GOLD, rtl=False)
        title_lines = wrap_logical(spec["title"], serif, 500)
        y = draw_lines(draw, x, y + 36, title_lines, serif, CREAM, leading=1.1)
        rule(draw, x, y + 10)
        body_lines = wrap_logical(spec["body"], sans_b, 500)
        draw_lines(draw, x, y + 32, body_lines, sans_b, CREAM)

    elif layout == "top":
        x = W - 88
        y = 92
        draw_text(draw, (x, y), spec["num"], sans_n, GOLD, rtl=False)
        title_lines = wrap_logical(spec["title"], serif, 880)
        y = draw_lines(draw, x, y + 32, title_lines, serif, CREAM, leading=1.1)
        rule(draw, x, y + 8)
        body_lines = wrap_logical(spec["body"], sans_b, 860)
        draw_lines(draw, x, y + 30, body_lines, sans_b, CREAM)

    elif layout == "card":
        box = (80, 168, W - 80, 620)
        rounded_rect(bg, box, (7, 11, 20, 168), radius=8)
        draw = ImageDraw.Draw(bg)
        draw.rounded_rectangle(box, radius=8, outline=(212, 175, 55, 100), width=1)
        x = W - 120
        y = 210
        draw_text(draw, (x, y), spec["num"], sans_n, GOLD, rtl=False)
        title_lines = wrap_logical(spec["title"], serif, 820)
        y = draw_lines(draw, x, y + 36, title_lines, serif, CREAM, leading=1.1)
        rule(draw, x, y + 10)
        body_lines = wrap_logical(spec["body"], sans_b, 800)
        draw_lines(draw, x, y + 32, body_lines, sans_b, CREAM)

    elif layout == "bottom":
        box = (64, 980, W - 64, 1248)
        rounded_rect(bg, box, (7, 11, 20, 186), radius=4)
        draw = ImageDraw.Draw(bg)
        draw.rectangle((64, 980, 68, 1248), fill=GOLD)
        x = W - 108
        y = 1008
        draw_text(draw, (x, y), spec["num"], sans_n, GOLD, rtl=False)
        y = draw_lines(draw, x, y + 28, [spec["title"]], serif, CREAM)
        rule(draw, x, y + 6)
        body_lines = wrap_logical(spec["body"], sans_b, 820)
        draw_lines(draw, x, y + 24, body_lines, sans_b, CREAM)

    elif layout == "cta":
        x = W // 2
        y = 980
        draw_text(draw, (x, y), spec["kicker"], sans_k, GOLD, anchor="ma", rtl=False)
        draw.rectangle((x - 44, y + 28, x + 44, y + 31), fill=GOLD)
        draw_text(draw, (x, y + 56), spec["title"], sans_phone, CREAM, anchor="ma", rtl=False)
        draw_text(draw, (x, y + 140), spec["sub"], sans_b, CREAM, anchor="ma")
        draw_text(draw, (x, y + 196), spec["foot"], font(FONT_SANS_B, 26), GOLD, anchor="ma", rtl=False)

    return bg.convert("RGB")


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    SLIDES.mkdir(parents=True, exist_ok=True)
    for spec in SLIDES_SPEC:
        im = compose(spec)
        dest = SLIDES / spec["out"]
        im.save(dest, "JPEG", quality=93, optimize=True, progressive=True)
        print(dest.name, im.size, dest.stat().st_size)


if __name__ == "__main__":
    main()
