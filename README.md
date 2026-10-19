# Anki-flashcard-skill

A [Claude Code](https://claude.com/claude-code) skill that turns an annotated lecture-slide PDF
into a ready-to-import Anki deck (`.apkg`).

## The idea: a "pink channel" to Claude

You annotate lecture slides (tested with GoodNotes) and export a flattened PDF.
**Saturated magenta is reserved for messages to Claude.** Everything else (black, blue, yellow
highlights) is real content and stays on the card.

| Pink mark | Meaning |
|---|---|
| Light highlighter tap in the **top-left corner** | This slide is important, so make card(s) |
| Highlighter bar beside an item | That item must appear on a card, possibly its own |
| Handwritten / typed pink text | A message to Claude, e.g. a question to use verbatim as the card front |
| Circle around part of a diagram | Emphasis: that part is the focus of the card |

Cards: **front** = context-free question (key term in bold), **back** = clean slide screenshot
(pink messages erased automatically), optional short "How to read" note under diagrams. Claude
shows you the full card list for approval **before** building anything. Re-importing a deck
updates cards instead of duplicating them.

## Install (about 5 minutes)

**You need:** [Claude Code](https://claude.com/claude-code) and Python 3.9+ on a Mac, Windows or
Linux computer. (Not usable on iPhone/iPad, since it runs scripts locally.)

### Option A: let Claude do it (recommended)
1. Download the ZIP from the **Releases** page (or **Code → Download ZIP**) and unzip it.
2. Move the unzipped folder anywhere **inside your uni / study folder**. It's a normal, visible
   folder, so you can drag it in.
3. Open a terminal in that study folder and start Claude Code (`claude`).
4. Type:
   > Read `SETUP.md` in the anki-flashcards-skill folder and set up the skill.

   Claude moves the skill into `.claude/skills/`, checks Python, and asks before installing the
   packages (`pymupdf`, `genanki`, `numpy`, `pillow`).
5. Restart Claude Code.

### Option B: manual
1. Unzip the download. Copy the `anki-flashcards` folder (the one containing `SKILL.md`) to:
   - **Project-wide:** `<your study folder>/.claude/skills/anki-flashcards/`
   - **Everywhere:** Mac/Linux `~/.claude/skills/anki-flashcards/`, Windows `C:\Users\<you>\.claude\skills\anki-flashcards\`

   (`.claude` is a hidden folder. Mac: `Cmd+Shift+.` in Finder shows it. Windows: View → Show →
   Hidden items. Or create it in the terminal with `mkdir -p`.)
2. Install the packages:
   - Mac/Linux:
     ```bash
     python3 -m venv ~/.venvs/anki
     ~/.venvs/anki/bin/pip install pymupdf genanki numpy pillow
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv $env:USERPROFILE\.venvs\anki
     & $env:USERPROFILE\.venvs\anki\Scripts\pip install pymupdf genanki numpy pillow
     ```
3. Restart Claude Code.

## Use it
Put each lecture in its own folder with the annotated PDF named with `Slides` in the filename,
e.g. `Marketing/Lecture 4/Slides.pdf`. Start Claude Code in your study folder and ask:

> Build the Anki deck for Marketing lecture 4

Claude extracts the slides, drafts cards, shows them for your review, then builds
`<lecture folder>/<name>.apkg`. Import **only** that `.apkg` file into Anki (double-click, or
File → Import).

## Files
| File | Purpose |
|---|---|
| `anki-flashcards/SKILL.md` | The skill: workflow, pink-mark vocabulary, card design rules, first-run setup |
| `anki-flashcards/extract_lecture.py` | Renders slides, erases pink messages, detects marks, writes an index |
| `anki-flashcards/build_deck_template.py` | Template Claude fills with the approved cards and runs |
| `SETUP.md` | Install instructions that Claude follows in Option A |

## Notes
- The pink colour thresholds are calibrated for GoodNotes exports. For other apps, sample a
  rendered slide and adjust the `PEN_*` / `BUB_*` constants in `extract_lecture.py`.
- Lecture slides and generated decks are not included. Slides are usually copyrighted.
- Built for my own studies (BWL at TUM). Feedback and issues welcome.
