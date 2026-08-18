#!/usr/bin/env python3
"""Build proof-stage print and EPUB files for The Shape Love Takes.

The manuscript Markdown remains the editorial source of truth. This script only
applies production typography and packaging; it does not rewrite manuscript text.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import uuid
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = ROOT / "manuscript"
PRINT_DIR = ROOT / "production" / "print"
EBOOK_DIR = ROOT / "production" / "ebook"
TMP_DIR = ROOT / "tmp" / "production"
MANIFEST_PATH = ROOT / "production" / "build-manifest.json"
PRINT_PATH = PRINT_DIR / "the-shape-love-takes-5.25x8-proof.pdf"
EPUB_PATH = EBOOK_DIR / "the-shape-love-takes-proof.epub"
EBOOK_COVER_PATH = ROOT / "production" / "cover" / "the-shape-love-takes-ebook-cover.jpg"

TITLE = "The Shape Love Takes"
AUTHOR = "Jesse Lemery"
BOOK_POSITION = "Book One"
LANGUAGE = "en-US"
PUBLICATION_YEAR = "2026"
EDITION = "First edition"
EXPECTED_SOURCE_WORDS = 63_546
PRODUCTION_MANUSCRIPT_COMMIT = "44e1ed3"

TRIM_WIDTH = 5.25 * inch
TRIM_HEIGHT = 8 * inch
PAGE_SIZE = portrait((TRIM_WIDTH, TRIM_HEIGHT))
FRONT_MATTER_PAGES = 4


@dataclass(frozen=True)
class Block:
    kind: str
    text: str


@dataclass(frozen=True)
class Chapter:
    slug: str
    label: str
    title: str
    blocks: tuple[Block, ...]


def manuscript_paths() -> list[Path]:
    paths = sorted(MANUSCRIPT_DIR.glob("[0-9][0-9]_*.md"))
    if len(paths) != 30:
        raise RuntimeError(f"Expected 30 manuscript files; found {len(paths)}")
    return paths


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def source_word_count(paths: list[Path]) -> int:
    return sum(len(path.read_text(encoding="utf-8").split()) for path in paths)


def smarten(text: str) -> str:
    """Apply conservative English book typography without changing wording."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"(?<=\w)'(?=\w)", "’", text)
    text = re.sub(r"(^|[\s([{])'(?=\w)", r"\1‘", text)
    text = text.replace("'", "’")
    text = re.sub(r'(^|[\s([{])"', r"\1“", text)
    text = text.replace('"', "”")
    return text


def inline_markup(text: str) -> str:
    """Convert the manuscript's limited inline Markdown to ReportLab markup."""
    pieces: list[str] = []
    cursor = 0
    pattern = re.compile(r"\*\*([^*]+)\*\*|\*([^*]+)\*")
    for match in pattern.finditer(text):
        pieces.append(html.escape(smarten(text[cursor : match.start()])))
        if match.group(1) is not None:
            pieces.append(f"<b>{html.escape(smarten(match.group(1)))}</b>")
        else:
            pieces.append(f"<i>{html.escape(smarten(match.group(2)))}</i>")
        cursor = match.end()
    pieces.append(html.escape(smarten(text[cursor:])))
    return "".join(pieces).replace("  \n", "<br/>")


def xhtml_inline(text: str) -> str:
    return inline_markup(text).replace("<br/>", "<br />")


def join_markdown_lines(lines: list[str]) -> str:
    output = ""
    for line in lines:
        if not output:
            output = line.rstrip()
        elif output.endswith("  "):
            output = output.rstrip() + "  \n" + line.rstrip()
        else:
            output += " " + line.strip()
    return output


def parse_blocks(lines: list[str]) -> tuple[Block, ...]:
    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue

        if lines[index].startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].startswith(">"):
                quote_lines.append(lines[index][1:].lstrip())
                index += 1
            paragraphs: list[list[str]] = [[]]
            for line in quote_lines:
                if not line.strip():
                    if paragraphs[-1]:
                        paragraphs.append([])
                else:
                    paragraphs[-1].append(line)
            for paragraph in paragraphs:
                if paragraph:
                    blocks.append(Block("blockquote", join_markdown_lines(paragraph)))
            continue

        paragraph_lines: list[str] = []
        while index < len(lines) and lines[index].strip() and not lines[index].startswith(">"):
            paragraph_lines.append(lines[index])
            index += 1
        text = join_markdown_lines(paragraph_lines)
        if re.fullmatch(r"\*[^*].*\*", text, flags=re.DOTALL):
            kind = "artifact"
        elif re.fullmatch(r"\*\*[^*].*\*\*", text, flags=re.DOTALL):
            kind = "artifact"
        elif text.strip() in {"* * *", "***"}:
            kind = "scene_break"
        else:
            kind = "body"
        blocks.append(Block(kind, text))
    return tuple(blocks)


def load_chapters(paths: list[Path]) -> list[Chapter]:
    chapters: list[Chapter] = []
    heading_re = re.compile(r"^# (Prologue|Chapter \d+): (.+)$")
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            raise RuntimeError(f"Empty manuscript file: {path}")
        match = heading_re.fullmatch(lines[0].strip())
        if not match:
            raise RuntimeError(f"Unexpected chapter heading in {path}: {lines[0]!r}")
        chapters.append(
            Chapter(
                slug=path.stem,
                label=match.group(1),
                title=match.group(2),
                blocks=parse_blocks(lines[1:]),
            )
        )
    return chapters


def register_fonts() -> None:
    font_dir = Path(r"C:\Windows\Fonts")
    fonts = {
        "Georgia": font_dir / "georgia.ttf",
        "Georgia-Bold": font_dir / "georgiab.ttf",
        "Georgia-Italic": font_dir / "georgiai.ttf",
        "Georgia-BoldItalic": font_dir / "georgiaz.ttf",
    }
    for name, path in fonts.items():
        if not path.exists():
            raise RuntimeError(f"Required production font is unavailable: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "Georgia",
        normal="Georgia",
        bold="Georgia-Bold",
        italic="Georgia-Italic",
        boldItalic="Georgia-BoldItalic",
    )


def paragraph_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=sample["BodyText"],
        fontName="Georgia",
        fontSize=9.4,
        leading=12.15,
        textColor=colors.HexColor("#171717"),
        alignment=TA_LEFT,
        firstLineIndent=0.2 * inch,
        spaceBefore=0,
        spaceAfter=0,
        allowWidows=0,
        allowOrphans=0,
    )
    return {
        "body": body,
        "body_first": ParagraphStyle("BodyFirst", parent=body, firstLineIndent=0),
        "artifact": ParagraphStyle(
            "Artifact",
            parent=body,
            fontSize=8.8,
            leading=11.45,
            firstLineIndent=0,
            leftIndent=0.23 * inch,
            rightIndent=0.18 * inch,
            spaceBefore=4,
            spaceAfter=4,
        ),
        "blockquote": ParagraphStyle(
            "Blockquote",
            parent=body,
            fontSize=8.6,
            leading=11.2,
            firstLineIndent=0,
            leftIndent=0.28 * inch,
            rightIndent=0.22 * inch,
            borderColor=colors.HexColor("#9B9B9B"),
            borderWidth=0.45,
            borderPadding=(0, 0, 0, 8),
            spaceBefore=3,
            spaceAfter=3,
        ),
        "chapter_label": ParagraphStyle(
            "ChapterLabel",
            fontName="Georgia",
            fontSize=8.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4A4A4A"),
            spaceAfter=9,
            uppercase=True,
        ),
        "chapter_title": ParagraphStyle(
            "ChapterTitle",
            fontName="Georgia",
            fontSize=16.5,
            leading=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111111"),
            spaceAfter=28,
        ),
        "front_title": ParagraphStyle(
            "FrontTitle",
            fontName="Georgia",
            fontSize=23,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111111"),
        ),
        "front_position": ParagraphStyle(
            "FrontPosition",
            fontName="Georgia",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceBefore=13,
        ),
        "front_author": ParagraphStyle(
            "FrontAuthor",
            fontName="Georgia",
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#222222"),
            spaceBefore=54,
        ),
        "copyright": ParagraphStyle(
            "Copyright",
            fontName="Georgia",
            fontSize=7.7,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#333333"),
            spaceAfter=8,
        ),
        "about": ParagraphStyle(
            "About",
            parent=body,
            firstLineIndent=0,
            spaceAfter=8,
        ),
    }


def draw_body_page(canvas, doc) -> None:
    display_page = canvas.getPageNumber() - FRONT_MATTER_PAGES
    if display_page < 1:
        return
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#5B5B5B"))
    canvas.setFont("Georgia", 6.9)
    header = AUTHOR if display_page % 2 == 0 else TITLE
    canvas.drawCentredString(TRIM_WIDTH / 2, TRIM_HEIGHT - 0.42 * inch, header.upper())
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.setFont("Georgia", 7.4)
    canvas.drawCentredString(TRIM_WIDTH / 2, 0.38 * inch, str(display_page))
    canvas.restoreState()


def draw_chapter_page(canvas, doc) -> None:
    display_page = canvas.getPageNumber() - FRONT_MATTER_PAGES
    if display_page < 1:
        return
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#444444"))
    canvas.setFont("Georgia", 7.4)
    canvas.drawCentredString(TRIM_WIDTH / 2, 0.38 * inch, str(display_page))
    canvas.restoreState()


def pdf_story(chapters: list[Chapter], styles: dict[str, ParagraphStyle]):
    story = []

    story.extend(
        [
            Spacer(1, 2.55 * inch),
            Paragraph(TITLE.upper(), styles["front_title"]),
            Paragraph(BOOK_POSITION.upper(), styles["front_position"]),
            PageBreak(),
            Spacer(1, 1),
            PageBreak(),
            Spacer(1, 1.72 * inch),
            Paragraph(TITLE.upper(), styles["front_title"]),
            Paragraph(BOOK_POSITION.upper(), styles["front_position"]),
            Paragraph(AUTHOR.upper(), styles["front_author"]),
            PageBreak(),
            Spacer(1, 2.95 * inch),
            Paragraph(f"Copyright © {PUBLICATION_YEAR} {AUTHOR}", styles["copyright"]),
            Paragraph("All rights reserved.", styles["copyright"]),
            Paragraph(
                "No part of this book may be reproduced or transmitted in any form or by any means without written permission from the author, except for brief quotations used in reviews.",
                styles["copyright"],
            ),
            Paragraph(
                "This is a work of fiction. Names, characters, places, organizations, and incidents are products of the author’s imagination or are used fictitiously. Any resemblance to actual persons, living or dead, or actual events is coincidental.",
                styles["copyright"],
            ),
            Paragraph(f"{EDITION}<br/>Edited by {AUTHOR}", styles["copyright"]),
            NextPageTemplate("chapter"),
            PageBreak(),
        ]
    )

    for chapter_index, chapter in enumerate(chapters):
        if chapter_index:
            story.extend([NextPageTemplate("chapter"), PageBreak()])
        story.extend(
            [
                Spacer(1, 1.31 * inch),
                Paragraph(chapter.label.upper(), styles["chapter_label"]),
                Paragraph(html.escape(chapter.title), styles["chapter_title"]),
            ]
        )
        first_body = True
        for block in chapter.blocks:
            if block.kind == "scene_break":
                story.append(Spacer(1, 10))
                story.append(Paragraph("* * *", styles["artifact"]))
                story.append(Spacer(1, 8))
                first_body = True
                continue
            if block.kind == "body":
                style = styles["body_first"] if first_body else styles["body"]
                first_body = False
            else:
                style = styles[block.kind]
                first_body = True
            story.append(Paragraph(inline_markup(block.text), style))

    story.extend(
        [
            NextPageTemplate("chapter"),
            PageBreak(),
            Spacer(1, 1.31 * inch),
            Paragraph("ABOUT THE AUTHOR", styles["chapter_label"]),
            Paragraph(AUTHOR, styles["chapter_title"]),
            Paragraph(
                "Jesse Lemery writes stories about family, memory, love, and what hides beneath ordinary life. <i>The Shape Love Takes</i> is Book One of an intentionally continuing psychological-horror story.",
                styles["about"],
            ),
        ]
    )
    return story


def build_pdf(chapters: list[Chapter]) -> int:
    register_fonts()
    styles = paragraph_styles()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    draft_path = TMP_DIR / "interior-draft.pdf"

    frame = Frame(
        0.7 * inch,
        0.66 * inch,
        TRIM_WIDTH - 1.4 * inch,
        TRIM_HEIGHT - 1.34 * inch,
        id="text",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    document = BaseDocTemplate(
        str(draft_path),
        pagesize=PAGE_SIZE,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.66 * inch,
        title=TITLE,
        author=AUTHOR,
        subject=f"{BOOK_POSITION} proof-stage print interior",
        creator=f"Edited and produced by {AUTHOR}",
    )
    document.addPageTemplates(
        [
            PageTemplate(id="front", frames=[frame], autoNextPageTemplate="front"),
            PageTemplate(
                id="chapter",
                frames=[frame],
                onPage=draw_chapter_page,
                autoNextPageTemplate="body",
            ),
            PageTemplate(id="body", frames=[frame], onPage=draw_body_page),
        ]
    )
    document.build(pdf_story(chapters, styles))

    reader = PdfReader(str(draft_path))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    if len(reader.pages) % 2:
        writer.add_blank_page(width=TRIM_WIDTH, height=TRIM_HEIGHT)
    with PRINT_PATH.open("wb") as output:
        writer.write(output)
    draft_path.unlink(missing_ok=True)
    return len(PdfReader(str(PRINT_PATH)).pages)


def epub_document(title: str, body: str, stylesheet_href: str = "styles/book.css") -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="{stylesheet_href}" />
</head>
<body>
{body}
</body>
</html>
'''


def chapter_xhtml(chapter: Chapter) -> str:
    pieces = [
        '<section class="chapter">',
        f'<p class="chapter-label">{html.escape(chapter.label)}</p>',
        f'<h1>{html.escape(chapter.title)}</h1>',
    ]
    first_body = True
    for block in chapter.blocks:
        if block.kind == "scene_break":
            pieces.append('<p class="scene-break">* * *</p>')
            first_body = True
            continue
        class_name = block.kind
        if block.kind == "body" and first_body:
            class_name = "body first"
        if block.kind == "body":
            first_body = False
        else:
            first_body = True
        tag = "blockquote" if block.kind == "blockquote" else "p"
        pieces.append(f'<{tag} class="{class_name}">{xhtml_inline(block.text)}</{tag}>')
    pieces.append("</section>")
    return epub_document(f"{chapter.label}: {chapter.title}", "\n".join(pieces))


def epub_css() -> str:
    return """@charset "UTF-8";
body { margin: 0 5%; font-family: Georgia, "Times New Roman", serif; line-height: 1.45; color: #171717; }
.chapter { page-break-before: always; }
.chapter-label { margin: 24% 0 0.7em; text-align: center; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75em; color: #555; text-indent: 0; }
h1 { margin: 0 0 2.2em; text-align: center; font-size: 1.45em; font-weight: normal; }
p { margin: 0; text-indent: 1.25em; widows: 2; orphans: 2; }
p.first, h1 + p { text-indent: 0; }
p.artifact { margin: 0.55em 7%; text-indent: 0; font-size: 0.93em; }
blockquote { margin: 0.6em 8%; padding-left: 0.75em; border-left: 1px solid #888; text-indent: 0; font-size: 0.91em; }
.scene-break { margin: 1.1em 0; text-align: center; text-indent: 0; }
.front { page-break-after: always; text-align: center; }
.front h1 { margin-top: 30%; margin-bottom: 0.6em; text-transform: uppercase; }
.book-position { text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.8em; }
.author { margin-top: 4em; text-transform: uppercase; letter-spacing: 0.1em; }
.copyright { page-break-after: always; margin-top: 36%; font-size: 0.78em; }
.copyright p, .about p { margin: 0 0 0.8em; text-indent: 0; }
.about { page-break-before: always; }
.about h1 { margin-top: 25%; }
.cover { margin: 0; padding: 0; text-align: center; page-break-after: always; }
.cover img { display: block; width: 100%; height: auto; margin: 0 auto; }
nav ol { list-style-type: none; padding-left: 0; }
nav li { margin: 0.45em 0; }
a { color: inherit; text-decoration: none; }
"""


def validate_epub(path: Path, expected_xhtml: int) -> None:
    with zipfile.ZipFile(path) as archive:
        if archive.namelist()[0] != "mimetype":
            raise RuntimeError("EPUB mimetype is not the first archive entry")
        if archive.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("EPUB mimetype is invalid")
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt EPUB member: {bad}")
        xhtml_names = [name for name in archive.namelist() if name.endswith(".xhtml")]
        if len(xhtml_names) != expected_xhtml:
            raise RuntimeError(
                f"Expected {expected_xhtml} XHTML documents; found {len(xhtml_names)}"
            )
        for name in xhtml_names:
            ElementTree.fromstring(archive.read(name))
        ElementTree.fromstring(archive.read("META-INF/container.xml"))
        opf = ElementTree.fromstring(archive.read("OEBPS/content.opf"))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {
            item.attrib["id"]: item.attrib["href"]
            for item in opf.findall("opf:manifest/opf:item", ns)
        }
        for item_id, href in manifest.items():
            member = f"OEBPS/{href}"
            if member not in archive.namelist():
                raise RuntimeError(f"Manifest item {item_id} is missing: {member}")
        for itemref in opf.findall("opf:spine/opf:itemref", ns):
            if itemref.attrib["idref"] not in manifest:
                raise RuntimeError(f"Unknown spine idref: {itemref.attrib['idref']}")


def build_epub(chapters: list[Chapter]) -> None:
    EBOOK_DIR.mkdir(parents=True, exist_ok=True)
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, TITLE + AUTHOR)}"
    chapter_items = []
    spine_items = ["title", "copyright"]
    nav_items = []
    for index, chapter in enumerate(chapters):
        item_id = f"chapter-{index:02d}"
        href = f"text/{chapter.slug}.xhtml"
        chapter_items.append(
            f'    <item id="{item_id}" href="{href}" media-type="application/xhtml+xml" />'
        )
        spine_items.append(item_id)
        nav_items.append(
            f'      <li><a href="{href}">{html.escape(chapter.label)}: {html.escape(chapter.title)}</a></li>'
        )
    spine_items.append("about")

    cover_manifest = ""
    cover_meta = ""
    cover_bytes = None
    if EBOOK_COVER_PATH.exists():
        cover_bytes = EBOOK_COVER_PATH.read_bytes()
        cover_manifest = '    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image" />\n    <item id="cover-page" href="text/cover.xhtml" media-type="application/xhtml+xml" />\n'
        cover_meta = '    <meta name="cover" content="cover-image" />\n'
        spine_items.insert(0, "cover-page")

    content_opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{identifier}</dc:identifier>
    <dc:title>{TITLE}</dc:title>
    <dc:creator>{AUTHOR}</dc:creator>
    <dc:language>{LANGUAGE}</dc:language>
    <dc:rights>Copyright © {PUBLICATION_YEAR} {AUTHOR}. All rights reserved.</dc:rights>
    <meta property="dcterms:modified">{date.today().isoformat()}T00:00:00Z</meta>
{cover_meta}  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="css" href="styles/book.css" media-type="text/css" />
    <item id="title" href="text/title.xhtml" media-type="application/xhtml+xml" />
    <item id="copyright" href="text/copyright.xhtml" media-type="application/xhtml+xml" />
{cover_manifest}{chr(10).join(chapter_items)}
    <item id="about" href="text/about.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine toc="ncx">
{chr(10).join(f'    <itemref idref="{item}" />' for item in spine_items)}
  </spine>
</package>
'''
    nav = epub_document(
        "Contents",
        f'''<nav epub:type="toc" xmlns:epub="http://www.idpf.org/2007/ops" id="toc">
  <h1>Contents</h1>
  <ol>
{chr(10).join(nav_items)}
  </ol>
</nav>''',
    )
    ncx = f'''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{identifier}" />
    <meta name="dtb:depth" content="1" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
  </head>
  <docTitle><text>{TITLE}</text></docTitle>
  <navMap>
{chr(10).join(f'    <navPoint id="nav-{i}" playOrder="{i + 1}"><navLabel><text>{html.escape(ch.label)}: {html.escape(ch.title)}</text></navLabel><content src="text/{ch.slug}.xhtml" /></navPoint>' for i, ch in enumerate(chapters))}
  </navMap>
</ncx>
'''
    title_xhtml = epub_document(
        TITLE,
        f'''<section class="front">
  <h1>{TITLE.upper()}</h1>
  <p class="book-position">{BOOK_POSITION.upper()}</p>
  <p class="author">{AUTHOR.upper()}</p>
</section>''',
    )
    copyright_xhtml = epub_document(
        "Copyright",
        f'''<section class="copyright">
  <p>Copyright © {PUBLICATION_YEAR} {AUTHOR}</p>
  <p>All rights reserved.</p>
  <p>No part of this book may be reproduced or transmitted in any form or by any means without written permission from the author, except for brief quotations used in reviews.</p>
  <p>This is a work of fiction. Names, characters, places, organizations, and incidents are products of the author’s imagination or are used fictitiously. Any resemblance to actual persons, living or dead, or actual events is coincidental.</p>
  <p>{EDITION}<br />Edited by {AUTHOR}</p>
</section>''',
    )
    about_xhtml = epub_document(
        "About the Author",
        f'''<section class="about">
  <h1>About the Author</h1>
  <p>{AUTHOR} writes stories about family, memory, love, and what hides beneath ordinary life. <i>{TITLE}</i> is Book One of an intentionally continuing psychological-horror story.</p>
</section>''',
    )
    container_xml = '''<?xml version="1.0" encoding="utf-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>
'''

    with zipfile.ZipFile(EPUB_PATH, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container_xml)
        archive.writestr("OEBPS/content.opf", content_opf)
        archive.writestr("OEBPS/nav.xhtml", nav)
        archive.writestr("OEBPS/toc.ncx", ncx)
        archive.writestr("OEBPS/styles/book.css", epub_css())
        if cover_bytes is not None:
            archive.writestr(
                "OEBPS/text/cover.xhtml",
                epub_document(
                    "Cover",
                    f'''<section class="cover">
  <img src="../images/cover.jpg" alt="Cover of {TITLE} by {AUTHOR}" />
</section>''',
                ),
            )
        archive.writestr("OEBPS/text/title.xhtml", title_xhtml)
        archive.writestr("OEBPS/text/copyright.xhtml", copyright_xhtml)
        for chapter in chapters:
            archive.writestr(
                f"OEBPS/text/{chapter.slug}.xhtml", chapter_xhtml(chapter)
            )
        archive.writestr("OEBPS/text/about.xhtml", about_xhtml)
        if cover_bytes is not None:
            archive.writestr("OEBPS/images/cover.jpg", cover_bytes)

    # Navigation, title, copyright, about, optional cover, and one document per chapter.
    validate_epub(
        EPUB_PATH,
        expected_xhtml=len(chapters) + 4 + int(cover_bytes is not None),
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(word_count: int, page_count: int) -> None:
    manifest = {
        "title": TITLE,
        "author": AUTHOR,
        "book_position": BOOK_POSITION,
        "production_stage": "Phase 8 proof candidate; not a final master",
        "production_manuscript_commit": PRODUCTION_MANUSCRIPT_COMMIT,
        "build_head": git_head(),
        "source_word_count": word_count,
        "trim_inches": {"width": 5.25, "height": 8.0},
        "print": {
            "file": str(PRINT_PATH.relative_to(ROOT)).replace("\\", "/"),
            "pages": page_count,
            "sha256": sha256(PRINT_PATH),
        },
        "epub": {
            "file": str(EPUB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(EPUB_PATH),
            "cover_included": EBOOK_COVER_PATH.exists(),
        },
        "production_credit": f"Edited by {AUTHOR}",
        "isbn": None,
        "notes": [
            "The author selected one Bowker ISBN for the identical KDP/IngramSpark paperback.",
            "The ISBN is intentionally absent until purchased and assigned.",
            "These files require Phase 9 digital and physical proof approval before designation as masters.",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    paths = manuscript_paths()
    word_count = source_word_count(paths)
    if word_count != EXPECTED_SOURCE_WORDS:
        raise RuntimeError(
            f"Production manuscript word-count drift: expected {EXPECTED_SOURCE_WORDS:,}; found {word_count:,}"
        )
    if not git_head().startswith(PRODUCTION_MANUSCRIPT_COMMIT):
        # A production branch naturally advances beyond the frozen manuscript commit,
        # but the frozen commit must remain in its ancestry.
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", PRODUCTION_MANUSCRIPT_COMMIT, "HEAD"],
            cwd=ROOT,
            check=True,
        )
    chapters = load_chapters(paths)
    page_count = build_pdf(chapters)
    build_epub(chapters)
    write_manifest(word_count, page_count)
    print(f"Built {PRINT_PATH.relative_to(ROOT)} ({page_count} pages)")
    print(f"Built {EPUB_PATH.relative_to(ROOT)}")
    print(f"Verified source word count: {word_count:,}")


if __name__ == "__main__":
    main()
