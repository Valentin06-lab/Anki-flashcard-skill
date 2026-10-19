# SETUP.md — instructions for Claude Code

The user wants to install the `anki-flashcards` skill from this package. Do the following,
showing each step and **asking before installing anything** (packages, venvs).

1. **Locate the package.** The skill folder is `anki-flashcards/` (next to this file). It must
   contain `SKILL.md`, `extract_lecture.py`, `build_deck_template.py`.
2. **Ask where to install**, recommend one:
   - *Project-wide* (default): `<current working folder>/.claude/skills/anki-flashcards/` — works
     whenever Claude Code is started in this folder or any folder below it.
   - *Everywhere*: `~/.claude/skills/anki-flashcards/` (Windows: `%USERPROFILE%\.claude\skills\anki-flashcards\`).
3. **Move (not copy) the `anki-flashcards/` folder there.** Create `.claude/skills/` if missing.
   If a folder with that name already exists, show what's in it and ask before replacing it.
   After moving, `SKILL.md` must sit directly in `.../skills/anki-flashcards/SKILL.md`.
4. **Python packages:** follow "First-run setup" in `SKILL.md` (check imports, ask, create venv,
   `pip install pymupdf genanki numpy pillow`).
5. **Tell the user** to restart Claude Code (skills are loaded at start), then use it with e.g.
   *"Build the Anki deck for <Subject> lecture <N>"*. Remind them that it needs a lecture folder
   containing the annotated PDF with `Slides` in the filename (see `README.md`).
6. Optionally offer to delete the now-empty package folder (`README.md`, `SETUP.md`).
