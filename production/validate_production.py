#!/usr/bin/env python3
"""Technical validation for Phase 8 proof-stage production files."""

from __future__ import annotations

import json
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
INTERIOR = ROOT / "production" / "print" / "the-shape-love-takes-5.25x8-proof.pdf"
EPUB = ROOT / "production" / "ebook" / "the-shape-love-takes-proof.epub"
EBOOK_COVER = ROOT / "production" / "cover" / "the-shape-love-takes-ebook-cover.jpg"
KDP_COVER = ROOT / "production" / "cover" / "the-shape-love-takes-kdp-paperback-proof.pdf"
BUILD_MANIFEST = ROOT / "production" / "build-manifest.json"
COVER_MANIFEST = ROOT / "production" / "cover" / "cover-manifest.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_manuscript_lock() -> None:
    manuscript_files = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "manuscript").glob("[0-9][0-9]_*.md")
    )
    result = subprocess.run(
        ["git", "diff", "--quiet", "003b7b8", "--", *manuscript_files], cwd=ROOT
    )
    require(result.returncode == 0, "Manuscript differs from the PRODUCTION MANUSCRIPT")


def validate_interior() -> None:
    reader = PdfReader(str(INTERIOR))
    require(not reader.is_encrypted, "Interior PDF must not be encrypted")
    # 234 is the pre-front-matter page count. Adding the content note, dedication,
    # author's note, and acknowledgments raises it; set this to the real count the
    # Georgia build reports, and keep build_cover.PAGE_COUNT and the manifest checks
    # below in sync with it.
    require(len(reader.pages) == 234, f"Unexpected interior page count: {len(reader.pages)}")
    empty_pages = []
    visible_fonts: dict[str, bool] = {}
    for page_number, page in enumerate(reader.pages, 1):
        require(abs(float(page.mediabox.width) - 378.0) < 0.01, f"Bad width on page {page_number}")
        require(abs(float(page.mediabox.height) - 576.0) < 0.01, f"Bad height on page {page_number}")
        if not (page.extract_text() or "").strip():
            empty_pages.append(page_number)
        resources = page.get("/Resources")
        if not resources:
            continue
        resources = resources.get_object()
        fonts = resources.get("/Font", {})
        if hasattr(fonts, "get_object"):
            fonts = fonts.get_object()
        for reference in fonts.values():
            item = reference.get_object()
            name = str(item.get("/BaseFont"))
            descriptor = item.get("/FontDescriptor")
            embedded = False
            if descriptor:
                descriptor = descriptor.get_object()
                embedded = any(
                    key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")
                )
            visible_fonts[name] = visible_fonts.get(name, False) or embedded
    require(empty_pages == [2], f"Unexpected empty interior pages: {empty_pages}")
    georgia_fonts = {name: embedded for name, embedded in visible_fonts.items() if "Georgia" in name}
    require(georgia_fonts and all(georgia_fonts.values()), f"Georgia subsets not embedded: {georgia_fonts}")


def validate_cover() -> None:
    cover = Image.open(EBOOK_COVER)
    require(cover.size == (1600, 2560), f"Unexpected ebook cover dimensions: {cover.size}")
    require(cover.mode == "RGB", f"Unexpected ebook cover mode: {cover.mode}")

    reader = PdfReader(str(KDP_COVER))
    require(len(reader.pages) == 1, "KDP cover must be a single-page PDF")
    page = reader.pages[0]
    require(abs(float(page.mediabox.width) - 816.12) < 0.02, "KDP cover width is incorrect")
    require(abs(float(page.mediabox.height) - 594.0) < 0.02, "KDP cover height is incorrect")
    resources = page["/Resources"].get_object()
    xobjects = resources["/XObject"].get_object()
    images = [item.get_object() for item in xobjects.values() if item.get_object().get("/Subtype") == "/Image"]
    require(len(images) == 1, f"Expected one flattened KDP cover image; found {len(images)}")
    image = images[0]
    require((int(image["/Width"]), int(image["/Height"])) == (3401, 2475), "KDP cover image is not 300-DPI geometry")
    require(str(image["/ColorSpace"]) == "/DeviceCMYK", "KDP cover image must be CMYK")


def validate_epub() -> None:
    with zipfile.ZipFile(EPUB) as archive:
        require(archive.namelist()[0] == "mimetype", "EPUB mimetype must be first")
        require(archive.getinfo("mimetype").compress_type == zipfile.ZIP_STORED, "EPUB mimetype must be uncompressed")
        require(archive.read("mimetype") == b"application/epub+zip", "Bad EPUB mimetype")
        require(archive.testzip() is None, "EPUB ZIP integrity failed")
        for name in archive.namelist():
            if name.endswith((".xhtml", ".xml", ".opf", ".ncx")):
                ElementTree.fromstring(archive.read(name))
        opf = ElementTree.fromstring(archive.read("OEBPS/content.opf"))
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        manifest = {
            item.attrib["id"]: item.attrib["href"]
            for item in opf.findall("opf:manifest/opf:item", ns)
        }
        for item_id, href in manifest.items():
            require(f"OEBPS/{href}" in archive.namelist(), f"Missing manifest item {item_id}: {href}")
        for itemref in opf.findall("opf:spine/opf:itemref", ns):
            require(itemref.attrib["idref"] in manifest, f"Unknown spine item {itemref.attrib['idref']}")
        cover = Image.open(BytesIO(archive.read("OEBPS/images/cover.jpg")))
        require(cover.size == (1600, 2560), "Embedded EPUB cover dimensions are incorrect")
        chapter_docs = [name for name in archive.namelist() if name.startswith("OEBPS/text/") and name.endswith(".xhtml")]
        require(len(chapter_docs) == 38, f"Unexpected EPUB reading documents: {len(chapter_docs)}")


def validate_manifests() -> None:
    build = json.loads(BUILD_MANIFEST.read_text(encoding="utf-8"))
    cover = json.loads(COVER_MANIFEST.read_text(encoding="utf-8"))
    require(build["source_word_count"] == 63_546, "Build manifest word count is incorrect")
    # 234 pages and the 0.585-inch spine are the pre-front-matter values; refresh
    # both from the Georgia rebuild output (the spine is PAGE_COUNT * 0.0025).
    require(build["print"]["pages"] == 234, "Build manifest page count is incorrect")
    require(build["epub"]["cover_included"] is True, "Build manifest does not record the EPUB cover")
    require(abs(cover["kdp_paperback"]["spine_inches"] - 0.585) < 0.0001, "Cover manifest spine is incorrect")


def main() -> None:
    validate_manuscript_lock()
    validate_interior()
    validate_cover()
    validate_epub()
    validate_manifests()
    print("Production validation passed")
    print("- manuscript lock: 003b7b8 / 63,546 words")
    print("- interior: 234 pages at 5.25 x 8 inches; embedded Georgia subsets")
    print("- ebook cover: 1600 x 2560 RGB")
    print("- KDP wrap: 11.335 x 8.25 inches; 300-DPI CMYK; 0.585-inch spine")
    print("- EPUB: package, XML, manifest, spine, navigation assets, and cover verified")


if __name__ == "__main__":
    main()
