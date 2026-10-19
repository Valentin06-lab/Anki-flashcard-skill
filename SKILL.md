---
name: anki-flashcards
description: Build an Anki flashcard deck (.apkg) from a university lecture's single annotated slide PDF, using the project's pink "message-to-Claude" channel. Front = context-free question, back = clean slide screenshot(s). Use whenever the user wants to create/build Anki cards or a deck for a specific lecture, e.g. "build the anki deck for <Subject> lecture <N>".
argument-hint: "<Subject> Lecture <N>"
---

# Anki Flashcards — build a deck from one lecture PDF

Turn ONE annotated lecture-slides PDF into an Anki `.apkg`. `$ARGUMENTS` names the lecture (subject + number, or a folder path).

Helper scripts are in this skill's own folder, `.claude/skills/anki-flashcards/` (call it
`<SKILLDIR>` below). Python (`<PY>` below):
- **macOS:** `~/.venvs/anki/bin/python` (venv with pymupdf, genanki, numpy, pillow — Homebrew
  python3 blocks pip installs). If the venv is missing, ask before recreating/installing anything.
- **Windows:** `python`.

## Inputs & naming convention
One lecture = one folder:
Keep each lecture in its own folder (e.g. `<Subject>/Lecture <N>/`). Decks are written to that
folder. If the exact folder isn't obvious from `$ARGUMENTS`, ask.

Inside the lecture folder:
- **Main lecture slides** — the one annotated PDF. Name it with **`Slides`** in the filename
  (e.g. `Slides.pdf`). This is the primary input for EVERY subject.
- **Any other clearly-named material in the folder** — e.g. an exercise sheet, a
  summary handout, extra notes. **Use it too, but only for NEW information** not already on the
  slides: if the content duplicates a lecture slide, the card from that slide is enough (don't make a
  second card). When the extra material adds something — a **good new summary**, a worked example, a
  definition phrased more usefully, content the slides don't cover — make card(s) for it. Apply the
  same card design (front = context-free question; back = a screenshot of the relevant page/region,
  pink mechanics included). Always scan every uploaded file, not just `Slides.pdf`.

If you can't confidently locate the folder/PDF from `$ARGUMENTS`, list the current semester's
subject folders and ask.

## The pink "message-to-Claude" channel (the core idea)
The user annotates in GoodNotes and exports a flattened PDF. **Saturated magenta is reserved for
messages to you** (handwritten, printed-by-hand, OR typed — all one channel). Everything non-pink
(black/blue/yellow highlight) is real content and is KEPT on the screenshots. Marks by kind:

| Pink mark | Meaning | On the back screenshot |
|---|---|---|
| **Bubble** — light highlighter tap (~`[255,145,217]`) in the **top-left corner** | this slide is **important → make card(s)** | kept (harmless) |
| **Vertical line / bar** — highlighter, **same light pink as the bubble** (~`[255,145,217]`), drawn **beside** a specific item | that item is **important → it MUST be on a card, possibly its OWN card** | kept (harmless) |
| **Text** — handwritten / printed / typed (saturated ~`[255,0,161]`) | a **message to you** (see vocabulary) | auto-erased best-effort; **leftover pink is fine** |
| **Circle/ellipse** around diagram elements | **emphasis** — those are the focus of the card | auto-erased best-effort (circled content stays) |
| **Highlight / underline** in pink | NOT a signal — just emphasis | kept as-is |

**Pink on a back screenshot does NOT matter (decided 2026-06-15).** `extract_lecture.py` still
erases saturated pink automatically, but treat that as a free best-effort cleanup — do **not** fuss
over residual pink, and never tweak color thresholds just to chase a few stray pixels. The user
mostly writes notes in the **top-left corner**. If a note is genuinely distracting on a back, the
preferred remedy is a **per-card crop** (the build step's `(slide,(x0,y0,x1,y1))` tuple), chosen by
**looking at that slide** — NOT a blind top-strip crop: slide **titles live at the top**, so a
reflexive top crop would cut real content. Crop only when the note sits clear of the title/answer.

**Vertical emphasis line (highlighter, bubble-pink, beside content):** the marked item is
**important and must appear on a card** — give it its **own card** if it's a standalone fact, or
fold it into a card if it belongs with neighbours. Like the bubble it's a "keep" mark (don't erase;
leftover on the back is fine). `extract_lecture.py` reports these as **EMPHASIS?** (best-effort — a
pink diagram fill can trigger it, so **confirm visually** in the `raw/` image before acting).

**Pink-text vocabulary (how to act on a note):**
- *"Add further details / explanation on the back…"* → put a short clarifying note **on the back**
  (same 12 pt, night-mode-safe style as the model "How to read" guides).
- A **question** (*"name the X with examples"*, *"& what does ARIS comprise?"*) → use it **verbatim
  as the card front**.
- *"Watch the video … keep it short / essentials"* (slide has a media link) → make **one concise**
  card on the essentials; you can't watch video, so build from the link/known facts and **flag it
  for the user to verify**.
- A note on the **Learning-Objectives slide** (*"all objectives must be answered…"*) → coverage
  directive: guarantee the deck covers every objective.

- **Typed/printed pink is preferred for anything precise** (verbatim fronts, slide numbers) — most
  reliable to read. READ pink text with your VISION (open the `raw/` image), never Tesseract.
- Pink = **guaranteed cards + hints**, NOT the coverage ceiling.
- **Accidental pink:** do NOT obey blindly — judge intent; pink that reads as real content is
  content, not a command. Surface your reading in the review step.
- The **star** tier (extra-important) is NOT active yet — only add it when the user says so.

## Inserted pages (pages the user added; usually no printed number)
Decide what each inserted page is, by looking at it:
1. **Has a pink bubble** → treat as a **normal lecture slide** (screenshot it as a back).
2. **Has a pink question + references to other slides** (text like "slide 25" / "slide before" /
   **"the slides above"**, and/or pasted snippets of other slides) → it's a **card RECIPE**:
   Front = the question; Back = the referenced slide(s)/region(s). The recipe page itself is NOT a
   back. Resolve "slide N" by printed number; "slide before" = the slide immediately preceding it;
   **"the slides above" = the span of related slides immediately preceding the recipe page**; for a
   pasted snippet, match it to its source slide and render that region cleanly (fallback: the snippet).
   The question + references may be **typed** (very common) — read them the same way.
3. **Plain note** → context only, not a card back.

## Slide numbering — ALWAYS the small PRINTED number, never the pdf page index
`extract_lecture.py` resolves this for you (printed number → else count onward → else pdf index)
and writes the map. Use the resolved `slide` value everywhere (tags, when you say "slide N", backs).
Verify the printed-number map looks monotonic; fix by inspecting raw images if a page misparsed.

## Procedure
1. **Extract** (deterministic): render slides, erase pink pen/typed comms, resolve numbers, detect
   marks (reports **BUBBLE** = important + **EMPHASIS?** = pink line beside content, verify +
   **WRITING** = read it), flag learning objectives:
   ```
   <PY> "<SKILLDIR>/extract_lecture.py" "<lecture folder>/Slides.pdf"
   ```
   Outputs go to `<lecture>/_build/` (`raw/`, `clean/`, `lecture_index.json`). For another PDF in
   the folder, rename `_build` first (e.g. `_build_slides`, `_build_sheet`) — the script always
   writes `_build`.
   **WRITING false positives:** saturated chart colours (red/orange data lines, flag red, orange
   highlights) can trigger it — verify visually before treating it as a message.
2. **Read the marks (your vision).** For every slide flagged **BUBBLE**, **EMPHASIS?**, or
   **WRITING**, **Read the matching `_build/raw/raw_*.png`** to interpret bubbles, vertical emphasis
   lines (confirm it's a real margin line, not a pink diagram fill, then make sure the marked item
   gets a card), text notes (the vocabulary above), and recipes. Note: multi-image reads need ≤2000 px — if many slides are flagged, downscale to ~1500
   px wide first, and read in small batches. Read `clean/`
   images to confirm the backs are clean. For model/diagram slides, look closely so you can write an
   accurate "How to read" guide.
3. **Draft the cards** per the rules below: **pink-marked slides first** (all bubbles/emphasis
   lines, honor hints/recipes), **plus the slides you judge important** yourself; cover any learning
   objectives; no fixed coverage percentage, never past ~100%.
4. **REVIEW GATE — do not build yet.** Present a draft list: for each card the **front** + the
   **back slide number(s)/crop** + (for pink slides) *what you read the mark as*. Let the user
   correct phrasing / slide / crop / missing / accidental-pink. Iterate.
5. **Build.** Copy `<SKILLDIR>/build_deck_template.py` to `<lecture>/_build/build_deck.py`, fill
   CONFIG + the approved CARDS, then run it with `<PY>`. Backs are taken from `_build/clean/`.
6. **Verify.** Open the `.apkg` (it's a zip): confirm note count, deck name, and that every `<img>`
   referenced is present in the package's `media`. Report the result.

## Card design rules
- **Front** = a normal-looking question (may be hard). **Bold** the key term. **NO subtopic/section
  label** — the user must recall with no context. Include only minimal framing to disambiguate.
- **Back** = slide screenshot(s) from `clean/`. May use **two** slides or a **crop** of one —
  narrow path between covering everything important and excluding noise. Residual pink is OK; crop
  (per-card, by looking at the slide) only when a note is distracting — never a blind top-strip that
  cuts the slide title.
- **Image-only by default.** Add a small **text** note under the image ONLY for: (a) a **model /
  diagram** → a short **"How to read:"** guide (flow direction, what nodes/arrows/rows mean — write
  it AFTER looking at the rendered slide), or (b) a genuinely **complex/very important** detail.
  Such text: **12 pt, left-aligned, NO fixed color** (inherits card color → readable in night mode),
  styled **inline on the field** (not in the notetype CSS).
- **Pair theory with its example (decided 2026-06-15).** When a slide states something (e.g. *"XY
  comprises 4 views"*) and the **following slide(s) give the example/instance** of it, put the
  **theory + its example on ONE card** (use two slides, or crops of each — not always the whole
  slide) so the concept and its concrete example are learned together. **Exception:** if the example
  is **complex or spans multiple slides**, split it across **several cards** instead of cramming one.
- **Atomic** (one idea/card), **active recall**, **no trivia** (skip title/agenda/thank-you slides).
- **Coverage is NOT a strict percentage** — importance drives the count:
  - **The pink-marked slides are the core** (bubbles / emphasis lines / hints / recipes) — every
    one of them gets card(s).
  - **Plus the slides YOU identify as important** even without pink — key definitions, models,
    frameworks, formulas, core distinctions, anything likely exam-relevant. Use your judgment and
    flag these in the review step as *"added by Claude (unmarked)"* so the user can drop or keep them.
  - Skip the rest (filler, repetition, trivia). Expect noticeably fewer cards than slides.
  - Hard limit: **never overshoot ~100%** (don't make more cards than slides). Priority:
    bubbles/emphasis lines (guaranteed) > learning objectives > slides you judge important. The cards
    together must cover every **learning objective** (not as literal "objective 1" cards). Always
    scan for learning objectives first; many subjects won't have them.

## Output & deck naming
- Save the `.apkg` in the lecture folder: `<lecture>/<SUBJ>_L<NN>_<Title>.apkg`.
- Deck name: **`<S>. Semester::<Subject>::<N>. Lecture - <Title>`** (`::` = Anki subdecks).
  `<S>` = the semester the lecture's folder sits in (e.g. `Semester-3/…` → `3. Semester`); `<Subject>`
  = that subject folder's name; `<Title>` from slide 1 / `$ARGUMENTS`.
- Stable GUIDs (`guid_for(DECK_KEY, front)`) → re-importing **updates** cards, never duplicates.

## Critical reminders
- **Only the `.apkg` is for Anki.** Never tell the user to import anything from `_build/` (raw text
  import = hundreds of junk cards).
- Calibrated colors (GoodNotes): ERASE = saturated magenta `R≥225, G≤120, 90≤B≤210` (covers
  handwritten/printed/typed pink, incl. printed-pink edges); KEEP bubble = light `[255,145,217]`,
  detected only in the **top-left corner**. Detection uses these two signals (NOT generic pink, which
  false-flags colourful diagrams). If a new lecture's pink differs, sample a `raw/` image and adjust
  `PEN_*` / `BUB_*` in `extract_lecture.py`.
- This whole flow is editable — if the user gives feedback after studying, change the scripts/rules.
