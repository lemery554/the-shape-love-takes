# Front Matter and End Matter

Status: **Draft copy for author approval.** Supports issue #31 (launch prep) and the Phase 11 checklist. This is the editorial source for the pages that wrap the story. Nothing here is final until you sign off on the byline, the ISBN, and the personal passages.

Style rules apply here as in the manuscript: no em dashes or en dashes, straight ASCII quotes (the build smartens them), American English. Do not reveal the ending, Anna's nature, or the illness's cause anywhere a reader sees before the story.

## How this maps to the build

`production/build_book.py` already generates several of these pages from code constants. Each block below is tagged:

- **[in build]** the build already renders this; the copy here is the approved wording to keep the constant in sync.
- **[add to build]** not currently rendered; adding it changes the interior and therefore the page count, so fold it in before the Georgia build, not after.

Relevant constants today: `TITLE`, `AUTHOR = "Jesse Lemery"`, `BOOK_POSITION = "Book One"`, `PUBLICATION_YEAR = "2026"`, `EDITION = "First edition"`, `FRONT_MATTER_PAGES = 4`.

## Byline decision (resolved: Option A)

**Decision (author, 2026-08-23):** Jesse Lemery is the **author**, and the separate "Edited by" line is **dropped**. A self-applied editor credit on one's own novel reads oddly, so the copyright page carries the author line only.

Action items this creates:
- Set `AUTHOR = "Jesse Lemery"` (already the value in `build_book.py`) and **remove** the "Edited by {AUTHOR}" line from both the PDF copyright block and the EPUB copyright section.
- `publishing/METADATA.md` still lists "Edited by Jesse Lemery" as a public credit and leaves the author name to confirm; reconcile it to match this decision (author = Jesse Lemery, no separate editor credit).
- Amazon KDP's AI-assistance disclosure is a separate backend step at setup and is unaffected by the byline; answer it truthfully given the AI-assisted line edit and copyedit.

Everywhere below, `[AUTHOR]` = **Jesse Lemery**. The `[EDITOR CREDIT]` slots are struck.

---

# FRONT MATTER

## 1. Half-title page **[in build]**

Recto, title only, no author.

```
THE SHAPE LOVE TAKES
Book One
```

## 2. Blank / "Also by" page **[in build: blank]**

Currently blank (verso). This is Book One, so there is nothing to list yet. When Book Two is announced, this becomes:

```
Also by [AUTHOR]

[Book Two title] (forthcoming)
```

Leave blank for this edition.

## 3. Title page **[in build]**

Recto.

```
THE SHAPE LOVE TAKES
Book One

[AUTHOR]
```

Optional imprint line at the foot if you create an imprint name (self-publishers often do; it is not required):

```
[IMPRINT NAME]
```

## 4. Copyright page **[in build, needs the ISBN and credit lines added]**

Verso. The build renders the copyright, rights, and fiction-disclaimer paragraphs today. It does **not** yet print an ISBN line, a cover-credit line, or an imprint. Add the marked lines before the build so the page is complete and the pagination is final.

```
Copyright (c) 2026 [AUTHOR]

All rights reserved. No part of this book may be reproduced or
transmitted in any form or by any means without written permission
from the author, except for brief quotations used in reviews.

This is a work of fiction. Names, characters, places, organizations,
and incidents are products of the author's imagination or are used
fictitiously. Any resemblance to actual persons, living or dead, or
actual events is coincidental.

First edition, 2026

ISBN (paperback): [ISBN - assign after Bowker purchase]        [add to build]

[IMPRINT NAME / "Independently published"]                      [add to build, optional]

Printed in the United States of America                         [add to build, optional]
```

Notes:
- **No cover-credit line for now** (author decision, 2026-08-23). Omit it from the copyright page; add "Cover design by [name]" later only if a credit is needed.
- Per the Option A byline decision, there is **no** "Edited by" line. Remove the existing `Edited by {AUTHOR}` line from the build's copyright block.
- The single Bowker ISBN goes on both the KDP and IngramSpark paperback. The ebook does not require an ISBN on KDP; leave the ebook without one unless you buy a second.
- Keep the ISBN line even in the proof build with the placeholder text, so its line does not shift pagination when the real number replaces it (same character-length ballpark).

## 5. Dedication **[add to build]**

**Decision (author, 2026-08-23): keep.** Recto, its own page, verso blank. Final dedication:

```
For anyone who was told to be grateful.
```

It reaches straight into the book's core: Brooke, adopted and told to be grateful, and the wider question of love that arrives as an obligation. Short is strongest for a dedication, so this stands as one line. Swap in a personal `For [NAME].` later if you would rather, but this is the locked default.

## 6. Epigraph **[skipped]**

**Decision (author, 2026-08-23): skip.** The Prologue already sets tone, and an epigraph would over-signal. No epigraph page in this edition.

---

# END MATTER

## 7. Author's note **[add to build, optional]**

Placed after the last chapter, before "About the Author." For a book that handles a child's illness and death, coercive family love, and an adoption wound, a short, non-spoilery note lands well with readers and reviewers. Keep it brief and do not explain the plot. Template with slots for anything only you can supply:

```
A note from the author

This is a book about love that does not know when to stop, and about
being the one person in a room who sees what everyone else needs not
to. If you have ever loved someone who came back different, or been
loved in a way that felt more like being kept, some of this may sit
close.

[Optional, one or two sentences of personal context if you want it:
what pulled you to write about family, memory, or adoption. Keep it
honest and short. Delete this paragraph if you would rather let the
story stand alone.]

The story continues.
```

If you keep the last line, it is your only public signal that Book Two is coming; it stays vague on purpose.

## 8. Acknowledgments **[add to build, optional]**

After the author's note. Template; fill or cut the slots that do not apply:

```
Acknowledgments

Thank you to [the readers who read early and told me the truth], to
[NAME(S)] for [specific help], and to [the beta and sensitivity readers]
who checked the pages that had to be right. Any remaining faults are
mine.

[Optional line for family / people who lived alongside the writing.]
```

If you ran the human beta round from the `beta/` package (the adoption lens especially), thank those readers here without naming their private feedback.

## 9. About the author **[in build]**

The build renders this today. Approved wording, adjust to the byline you choose:

```
About the author

[AUTHOR] writes stories about family, memory, love, and what hides
beneath ordinary life. The Shape Love Takes is Book One of an
intentionally continuing psychological-horror story.

[Optional: one line of place or voice. "They live in [PLACE]."]
```

Keep this consistent with the bio in `publishing/METADATA.md`.

## 10. Content note **[add to build, optional; recommended]**

Horror readers and the adoption lens both make a short content note advisable. It can sit at the very front (after the copyright page) or at the back before the author's note. Matches `publishing/METADATA.md`:

```
Content note

This novel contains a child's terminal illness and death (offstage),
other community deaths, coercive family control, a cruel remark that
weaponizes adoption and abandonment, medical distress, and a firearm
discharged inside a home. There is no sexual content. Some threads are
left unresolved on purpose.
```

Front placement warns; back placement avoids coloring the opening. Recommended: **front**, on its own short page after copyright, since the adoption line in particular is one some readers will want to know about going in.

---

## Assembly order (recommended)

Front: half-title, blank, title, copyright, content note, [dedication]. Then Prologue and chapters. End: author's note, acknowledgments, about the author.

## What to do before the Georgia build

Any block tagged **[add to build]** that you decide to keep must be added to `build_book.py` (both the PDF story and the EPUB spine) **before** you run the build, because each one changes the interior length and therefore the page count that drives the cover spine. Decide the set, add them, then build once. I can make those `build_book.py` edits on request; the copy above is ready to drop in.
