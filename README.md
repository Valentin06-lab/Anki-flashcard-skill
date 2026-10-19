# Anki-flashcard-skill

A [Claude Code](https://claude.com/claude-code) skill that turns an annotated lecture-slide PDF into a ready-to-import Anki deck (`.apkg`).

I built it for my own studies (BWL at TUM). It replaces the slow part of making flashcards, deciding what matters and formatting the cards, while I stay in control of what gets made.

## The idea: a "pink channel" to Claude

I annotate lecture slides in GoodNotes and export a flattened PDF. **Saturated magenta is reserved for messages to Claude.** Everything else (black, blue, yellow highlights) is real content and stays on the card.

| Pink mark | Meaning |
|---|---|
| Highlighter tap in the top-left corner | This slide is important, so make card(s) |
| Highlighter bar beside an item | That item must appear on a card, possibly its own |
| Handwritten / typed pink text | A message to Claude, e.g. a question to use verbatim as the card front |
| Circle around part of a diagram | Emphasis: that part is the focus of the card |

## What the cards look like

- **Front:** a context-free question with the key term in bold, so you have to recall without hints.
- **Back:** a clean screenshot of the slide (or a crop), with the pink messages erased automatically.
- Optional short "How to read" note under diagrams and models.
- Cards are atomic, with one idea each.
- Stable GUIDs, so re-importing updates cards instead of duplicating them.

## How it works

1. **Extract** (`extract_lecture.py`): renders every slide twice, once raw (with marks) and once clean (pink erased). It detects bubbles, emphasis bars and pink writing, resolves the printed slide numbers and writes a `lecture_index.json`.
2. **Read and draft** (Claude): reads the marked slides with vision and drafts cards. Marked slides come first, then slides Claude judges important, flagged as "added by Claude (unmarked)".
3. **Review gate:** Claude shows the full draft (front, slide, crop) and nothing is built until I approve or correct it.
4. **Build** (`build_deck_template.py`): generates the `.apkg` with [genanki](https://github.com/kerrickstaley/genanki).
5. **Verify:** checks the note count, deck name and that all images are packaged.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The skill definition: workflow, pink-mark vocabulary, card design rules |
| `extract_lecture.py` | Renders slides, erases pink comms, detects marks, writes the index |
| `build_deck_template.py` | Template that Claude fills with the approved cards and runs |

## Setup

Requires Python 3 with `pymupdf`, `genanki`, `numpy` and `pillow`:

```bash
python3 -m venv ~/.venvs/anki
~/.venvs/anki/bin/pip install pymupdf genanki numpy pillow
```

Place the folder in `.claude/skills/anki-flashcards/` (project or home directory), then ask Claude Code, for example:

> Build the Anki deck for *Marketing* lecture 4

Each lecture lives in its own folder containing the annotated PDF with `Slides` in the filename. Import the resulting `.apkg` into Anki.

## Notes

- The pink colour thresholds are calibrated for GoodNotes exports. For other apps, sample a rendered slide and adjust the `PEN_*` / `BUB_*` constants in `extract_lecture.py`.
- Lecture slides and generated decks are not included, since the slides are university material.
