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

The build refuses to run if the 30 source chapters no longer equal the locked 63,546 whitespace-delimited words. It produces:

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

## Rebuilding after a manuscript change (Phase 8 refresh)

The manuscript changed after the original 62,961-word lock: #99 added the hidden infection-model seeds and #100 added two Ch 17 / Ch 21 beats. The current lock is **63,546 whitespace-delimited words** across the 30 chapter files, and `EXPECTED_SOURCE_WORDS` in `build_book.py` has been updated to match. The original 234-page / 0.585-inch-spine proof files (PR #98) are stale.

To regenerate the proofs (must run in the Georgia environment; the build embeds Windows Georgia and refuses substitutes):

1. `python production/build_book.py` — rebuilds the interior PDF and EPUB from the current manuscript and re-emits `build-manifest.json`. Note the **new interior page count** it reports.
2. Update the values that depend on that page count, which cannot be known until step 1 runs:
   - `build_cover.py` → `PAGE_COUNT` (drives `SPINE_WIDTH_IN`).
   - `validate_production.py` → the `234` page-count assertions, the `0.585` spine assertion, and the printed summary strings (`manuscript lock: <commit> / 63,546 words`, page count, spine).
3. `python production/build_cover.py` — regenerates the ebook cover and the KDP wrap at the corrected spine.
4. `python production/validate_production.py` — must pass against the regenerated files.
5. Refresh PR #98 (or open a successor) with the regenerated binaries and manifests.

The IngramSpark wrap still requires the platform's ISBN-specific template after the Bowker ISBN is purchased; its generator rejects a placeholder.
