#!/usr/bin/env python
"""
build_deck_template.py — TEMPLATE. Claude copies this into <lecture>/_build/build_deck.py,
fills the CONFIG + CARDS, and runs it. Backs come from the CLEAN renders made by extract_lecture.py.

Card model: Basic. Front = context-free text question. Back = clean slide screenshot(s),
optionally a cropped region, optionally a small "How to read" note (12pt, color-inherited).
Stable GUIDs -> re-importing UPDATES existing cards instead of duplicating.
"""
import os, json, hashlib
import genanki
from PIL import Image

# ============================== CONFIG (fill these) ==============================
LECTURE_DIR = r"FILL: absolute path to the lecture folder"
DECK_NAME   = "FILL S. Semester::FILL Subject::FILL N. Lecture - FILL Title"
DECK_KEY    = "FILL"     # stable unique key, e.g. "<SUBJ>-L<NN>"  (drives GUIDs + DECK_ID)
OUT_NAME    = "FILL.apkg"  # e.g. "<SUBJ>_L<NN>_<Title>.apkg"
SUBJECT_TAG = "FILL"     # e.g. "<subject-name>"
LECTURE_TAG = "FILL"     # e.g. "lecture-<NN>"
# ================================================================================

BUILD = os.path.join(LECTURE_DIR, "_build")
INDEX = json.load(open(os.path.join(BUILD, "lecture_index.json"), encoding="utf-8"))
SLIDE2CLEAN = {e["slide"]: os.path.join(BUILD, e["clean"]) for e in INDEX["index"]}

OUT = os.path.join(LECTURE_DIR, OUT_NAME)
MEDIA = os.path.join(BUILD, "media"); os.makedirs(MEDIA, exist_ok=True)

MODEL_ID = 1718800500001                                        # shared note type across decks
DECK_ID  = int(hashlib.md5(DECK_KEY.encode()).hexdigest()[:8], 16)

# CARDS: list of (front_html, backs, extra_or_None)
#   backs = list; each item is either
#       "64"                      -> full clean slide 64
#       ("64", (x0,y0,x1,y1))     -> crop of slide 64, coords as fractions 0..1 (left,top,right,bottom)
#   extra = None, or a short "How to read:" string for model/diagram slides (kept night-mode-safe)
CARDS = [
    # ("What are the <b>...</b>?", ["64"], None),
    # ("How to read <b>model X</b>?", ["14"], "How to read: ..."),
    # ("What are the 5 types of XY?", [("25",(0.1,0.3,0.9,0.8)), "26"], None),
]

model = genanki.Model(
    MODEL_ID, "Slide-Back Basic",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{FrontSide}}<hr id='answer'>{{Back}}"}],
    css=".card{font-family:arial;font-size:20px;text-align:center;}\nimg{max-width:100%;height:auto;}",
)
deck = genanki.Deck(DECK_ID, DECK_NAME)


def back_to_file(item, ci, bi):
    slide = item[0] if isinstance(item, tuple) else item
    src = SLIDE2CLEAN[slide]
    im = Image.open(src)
    if isinstance(item, tuple):
        W, H = im.size
        x0, y0, x1, y1 = item[1]
        im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
        fn = f"{DECK_KEY}_c{ci}_{bi}_s{slide}.png"
    else:
        fn = f"{DECK_KEY}_s{slide}.png"
    im.save(os.path.join(MEDIA, fn))
    return fn, slide


media = set()
for ci, (front, backs, extra) in enumerate(CARDS):
    html, slide_tags = "", []
    for bi, item in enumerate(backs):
        fn, slide = back_to_file(item, ci, bi)
        html += f'<img src="{fn}">'
        media.add(os.path.join(MEDIA, fn))
        slide_tags.append(f"slide-{slide}")
    if extra:
        html += f'<div style="margin-top:12px;font-size:12pt;text-align:left;">{extra}</div>'
    deck.add_note(genanki.Note(
        model=model, fields=[front, html],
        guid=genanki.guid_for(DECK_KEY, front),
        tags=[SUBJECT_TAG, LECTURE_TAG] + slide_tags,
    ))

pkg = genanki.Package(deck)
pkg.media_files = sorted(media)
pkg.write_to_file(OUT)
print(f"OK: {len(CARDS)} cards, {len(media)} media -> {OUT}")
