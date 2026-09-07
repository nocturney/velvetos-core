#!/usr/bin/env python3
"""Compose VF-G004 Instagram Stories at 1080×1920 — vfcovers evidence pass.

Uses studio photos already exported from Canva (no invented rings, no invented ₪).
Navy/gold hex come from the owner brief on the Canva job, not a guessed kit.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
CANVA = Path("/opt/cursor/artifacts/g004-stories-fix/canva")
OUT = Path("/opt/cursor/artifacts/g004-stories-fix/vfcovers")
W, H = 1080, 1920

NAVY = (11, 29, 54, 255)  # #0B1D36 owner brief
GOLD = (201, 168, 108, 255)  # #C9A86C owner brief
CREAM = (246, 238, 216, 255)

FONT_SERIF = "/usr/share/fonts/truetype/croscore/Tinos-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"
FONT_SANS_B = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def load_rgb(name: str) -> Image.Image:
    return Image.open(CANVA / name).convert("RGB")


def crop_center(im: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    return im.crop(box).resize((W, H), Image.Resampling.LANCZOS)


def navy_wash(base: Image.Image, top: float, bottom: float) -> Image.Image:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(H):
        t = y / (H - 1)
        if t < top:
            a = int(230 * (1 - t / max(top, 0.01)))
        elif t > bottom:
            a = int(235 * ((t - bottom) / max(1 - bottom, 0.01)))
        else:
            a = 36
        for x in range(W):
            px[x, y] = (11, 29, 54, min(230, a))
    out = base.convert("RGBA")
    out.alpha_composite(overlay)
    return out


def draw_he(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill,
    *,
    anchor: str = "ma",
) -> None:
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor, direction="rtl", language="he")


def gold_rule(draw: ImageDraw.ImageDraw, cx: int, y: int, half: int = 72) -> None:
    draw.rectangle((cx - half, y, cx + half, y + 3), fill=GOLD)


def frame(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((36, 36, W - 37, H - 37), outline=(201, 168, 108, 90), width=1)
    draw.rectangle((48, 48, W - 49, H - 49), outline=(201, 168, 108, 40), width=1)


def story1() -> Image.Image:
    # Full-bleed open kettlebell from the 4-page copy-edit (studio photo as shot).
    src = load_rgb("copyedit-1.png") if (CANVA / "copyedit-1.png").is_file() else load_rgb("story-1.png")
    base = crop_center(src, (0, 220, 1080, 1700) if src.size[1] >= 1700 else (0, 0, src.size[0], src.size[1]))
    rgba = navy_wash(base, 0.22, 0.78)
    draw = ImageDraw.Draw(rgba)
    frame(draw)
    x, y = W // 2, 280
    draw_he(draw, (x, y), "מחזיק טבעות לזמן אימון", font(FONT_SERIF, 58), GOLD)
    gold_rule(draw, x, y + 92)
    note = font(FONT_SANS, 24)
    draw_he(draw, (x, H - 380), "מדבקת סקר · כן / לא", note, (201, 168, 108, 200))
    draw_he(draw, (x, H - 340), "יש לכן איפה לשים טבעות באימון?", note, CREAM)
    return rgba.convert("RGB")


def story2() -> Image.Image:
    src = load_rgb("copyedit-2.png") if (CANVA / "copyedit-2.png").is_file() else load_rgb("story-2.png")
    base = src.resize((W, H), Image.Resampling.LANCZOS)
    rgba = navy_wash(base, 0.08, 0.52)
    draw = ImageDraw.Draw(rgba)
    frame(draw)
    x = W // 2
    y = 300
    draw_he(draw, (x, y), "קטן, ורוד, והמון אופי", font(FONT_SERIF, 54), GOLD)
    gold_rule(draw, x, y + 78)
    draw_he(
        draw,
        (x, y + 120),
        "נפתח מלמעלה — והתכשיטים נשארים בפנים",
        font(FONT_SANS, 32),
        CREAM,
    )
    return rgba.convert("RGB")


def story3() -> Image.Image:
    src = load_rgb("copyedit-3.png") if (CANVA / "copyedit-3.png").is_file() else load_rgb("story-3.png")
    base = src.resize((W, H), Image.Resampling.LANCZOS)
    rgba = navy_wash(base, 0.08, 0.55)
    draw = ImageDraw.Draw(rgba)
    frame(draw)
    x = W // 2
    y = 300
    draw_he(draw, (x, y), "למי שמתאמנת", font(FONT_SERIF, 64), GOLD)
    gold_rule(draw, x, y + 86)
    draw_he(draw, (x, y + 130), "ולא רוצה לחפש טבעות על המזרן", font(FONT_SANS, 34), CREAM)
    return rgba.convert("RGB")


def story4() -> Image.Image:
    rgba = Image.new("RGBA", (W, H), NAVY)
    # Subtle grain from a blurred navy field — no extra logistics lines.
    grain = Image.new("L", (W, H), 0)
    gdraw = ImageDraw.Draw(grain)
    gdraw.ellipse((180, 520, 900, 1400), fill=28)
    grain = grain.filter(ImageFilter.GaussianBlur(80))
    wash = Image.new("RGBA", (W, H), (201, 168, 108, 0))
    wash.putalpha(grain.point(lambda p: int(p * 0.55)))
    rgba.alpha_composite(wash)
    draw = ImageDraw.Draw(rgba)
    frame(draw)
    x = W // 2
    y = 860
    draw_he(draw, (x, y), "וואטסאפ 050-2517000", font(FONT_SANS_B, 46), GOLD)
    gold_rule(draw, x, y + 70, half=88)
    return rgba.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    makers = {
        "story-1.png": story1,
        "story-2.png": story2,
        "story-3.png": story3,
        "story-4.png": story4,
    }
    for name, fn in makers.items():
        im = fn()
        dest = OUT / name
        im.save(dest, "PNG")
        print(dest, im.size, dest.stat().st_size)


if __name__ == "__main__":
    main()
