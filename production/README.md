# Book production

This directory contains the Phase 8 source and proof-stage production files for *The Shape Love Takes*.

## Locked specifications

- Format: paperback and reflowable EPUB
- Paperback trim: 5.25 x 8 inches
- Interior: black text, cream-paper assumption, no bleed
- Positioning: adult psychological horror with strong upper-YA crossover appeal; explicitly Book One
- Print distribution: identical paperback through KDP and IngramSpark
- Ebook distribution: KDP, beginning with one 90-day KDP Select / Kindle Unlimited test
- ISBN: one author-owned Bowker ISBN for the identical paperback; number not yet assigned
- Public production credit: `Edited by Jesse Lemery`

## Build

Run:

```powershell
python production/build_book.py
```

The build refuses to run if the 30 source chapters no longer equal the locked 62,961 whitespace-delimited words. It produces:

- `print/the-shape-love-takes-5.25x8-proof.pdf`
- `ebook/the-shape-love-takes-proof.epub`
- `build-manifest.json`

The cover build uses the approved text-free art plate and produces deterministic typography and KDP wrap geometry:

```powershell
python production/build_cover.py
```

- `cover/the-shape-love-takes-ebook-cover.jpg`
- `cover/the-shape-love-takes-kdp-paperback-proof.pdf`
- `cover/cover-manifest.json`

Run all deterministic technical checks with:

```powershell
python production/validate_production.py
```

The PDF uses Georgia with embedded font subsets, chapter-opening pages without running heads, restrained found-media styling, and an even final page count. The EPUB includes EPUB 3 navigation plus an NCX fallback for older reading systems.

## Production status

These are **proof candidates**, not final masters. Phase 9 must validate the EPUB on representative devices and approve physical proofs from both KDP and IngramSpark. Any correction that changes pagination requires updated cover templates and another layout-sensitive proof.

The high-resolution ebook cover and 234-page KDP wrap remain proof-stage assets until thumbnail review, asset-rights review, and physical proofing. The IngramSpark wrap must be exported against the platform's official ISBN-specific template after the purchased Bowker ISBN is available; its generator does not accept an unassigned placeholder.
