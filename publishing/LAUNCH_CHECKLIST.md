# Production-to-Launch Checklist

Status: Working checklist. Maps the remaining phases (#82 production files, #83 proofing, #84 distribution/ISBN, #31 launch prep, #85 release). Ownership is marked: **[you]** = author-only / external / paid; **[agent]** = I can draft or do it in-repo; **[done]** = complete.

Guiding constraint: any change that alters page count invalidates the cover spine/wrap and requires a rebuild + new proof (see `production/README.md`).

## Phase 8 — Production files (#82 / PR #98, #101)

- [done] **[agent]** Re-lock the build word count to 63,546 and refresh the tooling (PR #101).
- [done] **[agent]** Proofread the post-copyedit additions (#99/#100); source is clean straight-ASCII, no fixes needed.
- [ ] **[you]** Run the build in the Georgia/Windows environment: `build_book.py` → note new page count → update `build_cover.py PAGE_COUNT` and `validate_production.py` assertions → `build_cover.py` → `validate_production.py`.
- [ ] **[you]** Refresh PR #98 (or a successor) with the regenerated interior PDF, EPUB, ebook cover, and KDP wrap.
- [ ] **[you]** Merge PR #101 first (or fold it into the rebuild) so the tooling and lock are current.

## Phase 9 — Proofreading & physical proofs (#83)

- [done] **[agent]** Text proofread of the new material; conforms to the copyedit style sheet.
- [ ] **[agent]** Optional: one more full cold proofread pass of the whole manuscript on request.
- [ ] **[you]** Order and approve a **physical proof** from KDP and from IngramSpark.
- [ ] **[you]** Preview the EPUB on representative devices/apps (Kindle, Apple Books, Kobo).
- [ ] **[you]** Sign off that no correction changed pagination after the proof (if it did, rebuild the cover).

## Phase 10 — ISBN, metadata & distribution setup (#84)

- [done] **[agent]** Draft the metadata package (`publishing/METADATA.md`): blurb, long description, BISAC, keywords, comps, pricing suggestions, content notes.
- [ ] **[you]** Confirm author name / pen name and bio.
- [ ] **[you]** Purchase the single author-owned **Bowker ISBN** for the paperback (identical across KDP and IngramSpark).
- [ ] **[you]** Export the **IngramSpark wrap** against its official ISBN-specific 5.25x8 / cream template (its generator rejects a placeholder ISBN).
- [ ] **[you]** Create/confirm KDP and IngramSpark titles; paste approved metadata; set categories, keywords, price, and territories.
- [ ] **[you]** Enroll the ebook in KDP Select for the planned 90-day Kindle Unlimited test.
- [ ] **[you]** Confirm the final asset/font-rights record (Georgia embedding license, cover art rights).

## Phase 11 — Positioning, ARC & prelaunch (#31)

- [ ] **[agent]** Draft back-cover copy layout, an author's-note/acknowledgments page, and front-matter (title page, copyright placeholders) on request.
- [ ] **[agent]** Draft an ARC reader note and a short pitch/one-sheet on request.
- [ ] **[you]** Decide launch date and preorder window.
- [ ] **[you]** Recruit ARC readers / early reviewers; distribute the finished EPUB.
- [ ] **[you]** Optional: a small human beta/sensitivity round using the `beta/` package (the adoption lens especially), if desired before launch.

## Phase 12 — Release & launch-day (#85)

- [ ] **[you]** Publish on KDP (ebook + paperback) and IngramSpark; verify live listings, "look inside," and that both print sources match.
- [ ] **[you]** Verify the ebook renders on devices post-publish; confirm categories/keywords took.
- [ ] **[you]** Announce; seed the first reviews from ARC readers.

## Phase 13 — Post-launch (#86)

- [ ] **[you]** Monitor sales/reviews; adjust categories, keywords, and price as data comes in.
- [ ] **[agent]** Begin Book Two when you're ready — the hidden `bible/infection/INFECTION_MODEL.md` is the runway; the sequel owns the reveal.

## What is blocking, and why

Everything left in Phases 8–12 is gated on **your environment or your account**: the Georgia build, a purchased ISBN, KDP/IngramSpark account actions, physical proofs, and pricing. I can draft any copy, checklist, or front-matter you want, and I can run another full proofread — but I can't run the deterministic build, buy the ISBN, or operate the retail accounts. Hand me any of the **[agent]** items and I'll do them.
