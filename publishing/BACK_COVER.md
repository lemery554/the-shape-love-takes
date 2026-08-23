# Back Cover and Spine Layout

Status: **Draft copy and layout spec for author approval.** Supports issue #31 (launch prep) and the Phase 11 checklist. This documents what `production/build_cover.py` already places on the paperback wrap, the exact geometry it uses, and the copy plus the small additions that finish a trade-standard back cover.

Style rules apply: no em dashes or en dashes, straight ASCII quotes, American English. **Do not** put the twist, Anna's nature, or the illness's cause on the cover. The back cover sells the premise, not the reveal.

## Wrap geometry (from `build_cover.py`, do not guess)

The wrap is one flat image: back panel, spine, front panel, left to right, with bleed on the outer edges.

| Element | Value |
|---|---|
| Trim | 5.25 x 8.0 in |
| Bleed | 0.125 in on every outer edge |
| Spine width | `PAGE_COUNT * 0.0025 in` (KDP cream caliper). At the current placeholder `PAGE_COUNT = 234`, that is 0.585 in. **Re-derive after the interior build.** |
| Full wrap width | bleed + 5.25 + spine + 5.25 + bleed |
| Full wrap height | 0.125 + 8.0 + 0.125 = 8.25 in |
| Resolution | 300 DPI |
| Safe margin (text keep-out) | 0.25 in inside every trim edge; the back-panel text margin is set to 0.43 in, which is safely inside that |

The spine width, and therefore the whole wrap width, is a function of the final page count. **The cover cannot be finalized until the Georgia interior build produces the real page count and `PAGE_COUNT` is updated.** Any interior change (including the optional front-matter pages) shifts this.

## Back panel, top to bottom

### 1. Heading **[in build]**
A single tracked line, cream, above the blurb:

```
LOVE SHOULD KNOW WHEN TO LET GO.
```

This is the back-cover echo of the front tagline ("SOMETHING IS WRONG WITH THEM."). Keep the two in the same family; do not repeat the front tagline verbatim on the back.

### 2. Blurb **[in build]**
Three paragraphs, first paragraph bold, white on the darkened panel. Current approved copy:

```
Seventeen-year-old Brooke Bennett trusts what her camera can prove.

When a violent stomach illness sweeps through her town, the people who
recover seem healthy. They remember every private joke, password,
argument, and regret. They still say they love you. They simply no
longer understand why love should ever let someone leave.

As Brooke documents the changes in her sister, her mother, and the
world outside their front door, her evidence draws frightened
strangers, along with someone patient enough to learn that the safest
way to reach Brooke is not to chase her, but to become the person she
will choose to follow.
```

Note: this cover blurb is intentionally different from, and longer than, the ~90-word retail blurb in `publishing/METADATA.md`. That is normal. The cover blurb and the online description serve different surfaces and can differ, as long as the premise, the tagline family, and the do-not-spoil rule stay consistent across both. **Decide which is canonical for each surface**; both are approved drafts.

### 3. Author line and series line **[recommended add]**
The current back panel has no author credit or series marker. A trade back cover usually carries a short author line and the series signal. Recommended addition below the blurb:

```
Jesse Lemery writes psychological horror about ordinary love turned
strange. The Shape Love Takes is their debut novel and the first book
in a planned series.

Book One
```

Keep this bio to one or two lines on the cover; the full bio lives in the front/back matter and the retail page. Byline is Jesse Lemery per the Option A decision in `FRONT_MATTER.md`.

### 4. Category line **[skipped]**
**Decision (author, 2026-08-23): skip.** KDP and IngramSpark set category through metadata, so a printed category line on the back panel is redundant. Keep the back panel clean; no category line.

### 5. Barcode reserve **[in build]**
A white rectangle, 2.0 x 1.2 in, in the bottom-right corner, 0.25 in from the trim edges. This is correct: KDP prints the ISBN/EAN barcode into this zone automatically, so **leave it clear** and do not draw the ISBN by hand there. IngramSpark expects the barcode in the same area against its ISBN-specific template.

### 6. Price box **[optional, IngramSpark only]**
KDP does not need a printed price. If you distribute through IngramSpark and want a retail price printed, it goes inside or just above the barcode zone. Leave it off unless you specifically want a printed price; a bare barcode is the more flexible choice.

### Do not put on the back cover
- The ending, Anna's nature, or the cause of the illness.
- The content note (that belongs in the front matter; see `FRONT_MATTER.md`).
- Comp titles (positioning tools for metadata, not cover copy).

## Spine **[in build]**

Navy spine with text. Standard order, read top to bottom:

```
Jesse Lemery   THE SHAPE LOVE TAKES        [optional imprint mark at foot]
```

Spine text only fits legibly above roughly 0.06 in of width (about 100 pages). At the current 0.585 in it is comfortable. **Confirm the spine text still fits after the real page count sets the final spine width.** If the count drops significantly, re-check legibility.

## Front cover **[in build, for reference]**
Handled by `add_front_typography`: the art plate, the title, and the split tagline "SOMETHING IS WRONG WITH " + "THEM." (the accent word in red). No changes requested here; listed so the three panels stay coherent.

## What to do before the final wrap

1. Run the Georgia interior build; read off the true page count.
2. Set `PAGE_COUNT` in `build_cover.py` to that number (this resets spine width and full wrap width).
3. Decide whether to add the author/series line (recommended), the category line, and any price box; I can make those `build_cover.py` edits on request.
4. Rebuild the cover, then export the IngramSpark wrap against its official ISBN-specific 5.25x8 cream template once the Bowker ISBN is assigned.
5. Order a physical proof and confirm the barcode zone, spine text, and bleed survived print.
