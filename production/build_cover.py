#!/usr/bin/env python3
"""Build the proof-stage ebook cover and KDP paperback wrap.

The text-free art plate is the visual source. Typography and wrap geometry are
applied deterministically so retailer-facing text remains consistent.
"""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
COVER_DIR = ROOT / "production" / "cover"
TMP_DIR = ROOT / "tmp" / "production"
ART_PATH = COVER_DIR / "the-shape-love-takes-art-plate-v1.png"
EBOOK_PATH = COVER_DIR / "the-shape-love-takes-ebook-cover.jpg"
KDP_WRAP_JPG = TMP_DIR / "the-shape-love-takes-kdp-paperback-proof.jpg"
KDP_WRAP_PDF = COVER_DIR / "the-shape-love-takes-kdp-paperback-proof.pdf"
MANIFEST_PATH = COVER_DIR / "cover-manifest.json"

TITLE = "THE SHAPE LOVE TAKES"
AUTHOR = "JESSE LEMERY"
BOOK_POSITION = "BOOK ONE"
TAGLINE_PREFIX = "SOMETHING IS WRONG WITH "
TAGLINE_ACCENT = "THEM."

PAGE_COUNT = 234
TRIM_WIDTH_IN = 5.25
TRIM_HEIGHT_IN = 8.0
BLEED_IN = 0.125
KDP_CREAM_CALIPER_IN = 0.0025
SPINE_WIDTH_IN = PAGE_COUNT * KDP_CREAM_CALIPER_IN
DPI = 300

FONT_DIR = Path(r"C:\Windows\Fonts")
TITLE_FONT = FONT_DIR / "BELL.TTF"
TITLE_FONT_BOLD = FONT_DIR / "BELLB.TTF"
BODY_FONT = FONT_DIR / "georgia.ttf"
BODY_FONT_BOLD = FONT_DIR / "georgiab.ttf"

CREAM = "#E7DDC8"
RED = "#B51F22"
WHITE = "#F3F0E8"
NAVY = "#07101A"

BACK_COPY = [
    "Seventeen-year-old Brooke Bennett trusts what her camera can prove.",
    "When a violent stomach illness sweeps through her town, the people who recover seem healthy. They remember every private joke, password, argument, and regret. They still say they love you. They simply no longer understand why love should ever let someone leave.",
    "As Brooke documents the changes in her sister, her mother, and the world outside their front door, her evidence draws frightened strangers, along with someone patient enough to learn that the safest way to reach Brooke is not to chase her, but to become the person she will choose to follow.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def crop_to_ratio(image: Image.Image, width: int, height: int) -> Image.Image:
    target_ratio = width / height
    source_ratio = image.width / image.height
    if source_ratio > target_ratio:
        new_width = round(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = round(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    if not path.exists():
        raise RuntimeError(f"Required cover font is unavailable: {path}")
    return ImageFont.truetype(str(path), size=size)


def text_width(draw: ImageDraw.ImageDraw, text: str, face, tracking: int = 0) -> int:
    if not text:
        return 0
    return sum(draw.textlength(char, font=face) for char in text) + tracking * (len(text) - 1)


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    face,
    fill: str,
    tracking: int = 0,
    anchor: str = "mm",
    stroke_width: int = 0,
    stroke_fill: str | None = None,
) -> None:
    x, y = xy
    width = text_width(draw, text, face, tracking)
    if anchor.startswith("m"):
        x -= width / 2
    elif anchor.startswith("r"):
        x -= width
    for char in text:
        draw.text(
            (x, y),
            char,
            font=face,
            fill=fill,
            anchor="lm",
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        x += draw.textlength(char, font=face) + tracking


def fit_font(draw, text: str, path: Path, max_size: int, max_width: int, tracking: int = 0):
    size = max_size
    while size > 20:
        face = font(path, size)
        if text_width(draw, text, face, tracking) <= max_width:
            return face
        size -= 2
    raise RuntimeError(f"Unable to fit cover text: {text}")


def add_front_typography(image: Image.Image) -> Image.Image:
    result = image.convert("RGB")
    draw = ImageDraw.Draw(result)
    width, height = result.size

    # A subtle central veil protects title legibility without flattening the art.
    veil = Image.new("RGBA", result.size, (0, 0, 0, 0))
    veil_draw = ImageDraw.Draw(veil)
    veil_draw.rectangle(
        (int(width * 0.12), int(height * 0.22), int(width * 0.88), int(height * 0.67)),
        fill=(0, 0, 0, 31),
    )
    veil = veil.filter(ImageFilter.GaussianBlur(radius=36))
    result = Image.alpha_composite(result.convert("RGBA"), veil).convert("RGB")
    draw = ImageDraw.Draw(result)

    tagline_size = max(25, round(width * 0.026))
    tagline_font = font(BODY_FONT, tagline_size)
    tagline_tracking = max(2, round(width * 0.0028))
    full_width = text_width(draw, TAGLINE_PREFIX + TAGLINE_ACCENT, tagline_font, tagline_tracking)
    start_x = (width - full_width) / 2
    tagline_y = round(height * 0.055)
    draw_tracked(
        draw,
        (start_x, tagline_y),
        TAGLINE_PREFIX,
        tagline_font,
        WHITE,
        tagline_tracking,
        anchor="lm",
        stroke_width=1,
        stroke_fill="#101010",
    )
    prefix_width = text_width(draw, TAGLINE_PREFIX, tagline_font, tagline_tracking)
    draw_tracked(
        draw,
        (start_x + prefix_width, tagline_y),
        TAGLINE_ACCENT,
        tagline_font,
        RED,
        tagline_tracking,
        anchor="lm",
        stroke_width=1,
        stroke_fill="#101010",
    )

    center_x = width / 2
    title_tracking = max(1, round(width * 0.0012))
    title_specs = [
        ("THE", 0.235, 0.075),
        ("SHAPE", 0.315, 0.165),
        ("LOVE", 0.435, 0.18),
        ("TAKES", 0.555, 0.145),
    ]
    for word, y_ratio, size_ratio in title_specs:
        face = fit_font(
            draw,
            word,
            TITLE_FONT,
            max_size=round(width * size_ratio),
            max_width=round(width * 0.79),
            tracking=title_tracking,
        )
        draw_tracked(
            draw,
            (center_x, round(height * y_ratio)),
            word,
            face,
            CREAM,
            title_tracking,
            stroke_width=max(1, round(width / 900)),
            stroke_fill="#17130F",
        )

    position_font = font(BODY_FONT, round(width * 0.033))
    draw_tracked(
        draw,
        (center_x, round(height * 0.805)),
        BOOK_POSITION,
        position_font,
        RED,
        tracking=round(width * 0.007),
        stroke_width=1,
        stroke_fill="#120C0C",
    )

    author_font = fit_font(
        draw,
        AUTHOR,
        BODY_FONT,
        max_size=round(width * 0.072),
        max_width=round(width * 0.82),
        tracking=round(width * 0.010),
    )
    draw_tracked(
        draw,
        (center_x, round(height * 0.91)),
        AUTHOR,
        author_font,
        RED,
        tracking=round(width * 0.010),
        stroke_width=1,
        stroke_fill="#120C0C",
    )
    return result


def wrap_lines(draw, text: str, face, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=face) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_back_panel(art: Image.Image, width: int, height: int) -> Image.Image:
    # Derive a quiet, related texture from the house/trees without repeating the front.
    crop = art.crop((0, 0, max(1, art.width // 2), art.height))
    crop = crop.resize((width, height), Image.Resampling.LANCZOS)
    crop = crop.filter(ImageFilter.GaussianBlur(radius=max(3, width // 180)))
    crop = ImageEnhance.Brightness(crop).enhance(0.34)
    overlay = Image.new("RGB", (width, height), NAVY)
    panel = Image.blend(crop.convert("RGB"), overlay, 0.62)
    draw = ImageDraw.Draw(panel)

    margin = round(0.43 * DPI)
    max_width = width - 2 * margin
    heading_font = font(BODY_FONT, round(0.12 * DPI))
    heading_tracking = round(0.010 * DPI)
    heading = "LOVE SHOULD KNOW WHEN TO LET GO."
    draw_tracked(
        draw,
        (width / 2, round(0.55 * DPI)),
        heading,
        heading_font,
        CREAM,
        tracking=heading_tracking,
        stroke_width=1,
        stroke_fill="#03070B",
    )

    body_font = font(BODY_FONT, round(0.105 * DPI))
    body_bold = font(BODY_FONT_BOLD, round(0.105 * DPI))
    y = round(1.12 * DPI)
    leading = round(0.155 * DPI)
    for index, paragraph in enumerate(BACK_COPY):
        face = body_bold if index == 0 else body_font
        for line in wrap_lines(draw, paragraph, face, max_width):
            draw.text((margin, y), line, font=face, fill=WHITE, anchor="la")
            y += leading
        y += round(0.13 * DPI)

    # Reserved for the platform-generated ISBN/EAN barcode.
    barcode_width = round(2.0 * DPI)
    barcode_height = round(1.2 * DPI)
    barcode_right = width - round(0.25 * DPI)
    barcode_bottom = height - round(0.25 * DPI)
    draw.rectangle(
        (
            barcode_right - barcode_width,
            barcode_bottom - barcode_height,
            barcode_right,
            barcode_bottom,
        ),
        fill="#FFFFFF",
    )
    return panel


def build() -> None:
    if not ART_PATH.exists():
        raise RuntimeError(f"Missing approved art plate: {ART_PATH}")
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    art = Image.open(ART_PATH).convert("RGB")

    ebook_art = crop_to_ratio(art, 1600, 2560)
    ebook_cover = add_front_typography(ebook_art)
    ebook_cover.save(EBOOK_PATH, quality=95, subsampling=0, dpi=(300, 300))

    full_width_in = BLEED_IN + TRIM_WIDTH_IN + SPINE_WIDTH_IN + TRIM_WIDTH_IN + BLEED_IN
    full_height_in = BLEED_IN + TRIM_HEIGHT_IN + BLEED_IN
    wrap_width = round(full_width_in * DPI)
    wrap_height = round(full_height_in * DPI)
    back_width = round((BLEED_IN + TRIM_WIDTH_IN) * DPI)
    spine_width = round(SPINE_WIDTH_IN * DPI)
    front_width = wrap_width - back_width - spine_width

    print_art = crop_to_ratio(art, front_width, wrap_height)
    front_panel = add_front_typography(print_art)
    back_panel = make_back_panel(art, back_width, wrap_height)

    wrap = Image.new("RGB", (wrap_width, wrap_height), NAVY)
    wrap.paste(back_panel, (0, 0))
    wrap.paste(front_panel, (back_width + spine_width, 0))
    draw = ImageDraw.Draw(wrap)

    spine_x = back_width
    draw.rectangle((spine_x, 0, spine_x + spine_width, wrap_height), fill=NAVY)
    spine_layer = Image.new("RGBA", (wrap_height, spine_width), (0, 0, 0, 0))
    spine_draw = ImageDraw.Draw(spine_layer)
    spine_title_font = fit_font(
        spine_draw,
        "THE SHAPE LOVE TAKES",
        BODY_FONT_BOLD,
        max_size=round(0.105 * DPI),
        max_width=round(5.65 * DPI),
        tracking=round(0.006 * DPI),
    )
    draw_tracked(
        spine_draw,
        (spine_layer.width / 2, round(spine_layer.height * 0.49)),
        "THE SHAPE LOVE TAKES",
        spine_title_font,
        CREAM,
        tracking=round(0.006 * DPI),
    )
    spine_author_font = font(BODY_FONT, round(0.078 * DPI))
    draw_tracked(
        spine_draw,
        (spine_layer.width / 2, round(spine_layer.height * 0.88)),
        AUTHOR,
        spine_author_font,
        RED,
        tracking=round(0.006 * DPI),
    )
    spine_layer = spine_layer.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    wrap.alpha_composite(spine_layer, (spine_x, 0)) if wrap.mode == "RGBA" else wrap.paste(
        spine_layer, (spine_x, 0), spine_layer
    )

    wrap.convert("CMYK").save(KDP_WRAP_JPG, quality=95, subsampling=0, dpi=(DPI, DPI))

    pdf = canvas.Canvas(
        str(KDP_WRAP_PDF),
        pagesize=(full_width_in * 72, full_height_in * 72),
        pageCompression=1,
    )
    pdf.setTitle("The Shape Love Takes - KDP paperback proof cover")
    pdf.setAuthor(AUTHOR.title())
    pdf.setCreator(f"Edited and produced by {AUTHOR.title()}")
    pdf.drawImage(
        ImageReader(str(KDP_WRAP_JPG)),
        0,
        0,
        width=full_width_in * 72,
        height=full_height_in * 72,
        preserveAspectRatio=False,
        mask=None,
    )
    pdf.showPage()
    pdf.save()
    KDP_WRAP_JPG.unlink(missing_ok=True)
    try:
        TMP_DIR.rmdir()
        TMP_DIR.parent.rmdir()
    except OSError:
        pass

    manifest = {
        "title": "The Shape Love Takes",
        "author": "Jesse Lemery",
        "production_stage": "Phase 8 proof cover; not a final master",
        "public_credit": "Edited by Jesse Lemery",
        "front_art_source": str(ART_PATH.relative_to(ROOT)).replace("\\", "/"),
        "ebook": {
            "file": str(EBOOK_PATH.relative_to(ROOT)).replace("\\", "/"),
            "pixels": {"width": 1600, "height": 2560},
            "sha256": sha256(EBOOK_PATH),
        },
        "kdp_paperback": {
            "file": str(KDP_WRAP_PDF.relative_to(ROOT)).replace("\\", "/"),
            "trim_inches": {"width": TRIM_WIDTH_IN, "height": TRIM_HEIGHT_IN},
            "pages": PAGE_COUNT,
            "paper": "cream",
            "spine_inches": SPINE_WIDTH_IN,
            "bleed_inches": BLEED_IN,
            "full_cover_inches": {"width": full_width_in, "height": full_height_in},
            "sha256": sha256(KDP_WRAP_PDF),
        },
        "ingramspark": {
            "status": "Awaiting purchased Bowker ISBN and official ISBN-specific cover template",
            "reason": "The official IngramSpark template generator requires the assigned ISBN.",
        },
        "barcode": "Reserved blank area; platform barcode not yet generated",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {EBOOK_PATH.relative_to(ROOT)}")
    print(f"Built {KDP_WRAP_PDF.relative_to(ROOT)}")
    print(f"KDP spine: {SPINE_WIDTH_IN:.3f} inches")
    print(f"KDP full cover: {full_width_in:.3f} x {full_height_in:.3f} inches")


if __name__ == "__main__":
    build()
