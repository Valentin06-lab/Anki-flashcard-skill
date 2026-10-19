#!/usr/bin/env python
"""
extract_lecture.py — deterministic first pass for the Anki-flashcards skill.

Usage:
    python extract_lecture.py "<path to the lecture-slides PDF>"

What it does (single-file scheme; see SKILL.md):
  * Renders every page twice into <lecture>/_build/:
        raw/   = full render WITH all marks   (for Claude to READ pink bubbles/notes/recipes)
        clean/ = render with pink PEN/TYPED comms ERASED (these are the card backs)
  * Erases the saturated pink PEN + TYPED pink (handwriting/printed/typed messages to Claude).
    It KEEPS: non-pink ink/highlights, AND the lighter highlighter "bubble" (importance flag).
  * Detects marks RELIABLY by TWO calibrated signals (not generic pink, which over-flags
    colourful diagrams):
        - pen/typed writing anywhere  (saturated magenta)        -> "WRITING" (read it)
        - light bubble in TOP-LEFT corner (highlighter tap)       -> "BUBBLE" (important slide)
        - light bubble-pink OUTSIDE the corner (vertical line)    -> "EMPHASIS?" (item must be on a
          card; best-effort — a pink diagram fill can trigger it, so verify the raw image)
  * Extracts the SMALL PRINTED slide number (count-onward fallback; pdf index if none).
  * Flags learning-objective slides.
  * Writes <lecture>/_build/lecture_index.json (consumed by build_deck.py).

Calibrated on GoodNotes exports:
    pen/handwriting ~[255,0,161]   printed-by-hand ~[255,62,183]   typed ~[255,0,161]   (ERASE)
    bubble (highlighter) ~[255,145,217]                                                  (KEEP)
"""
import sys, os, json, re
import numpy as np
import fitz
from PIL import Image, ImageFilter

# --- saturated pink PEN / TYPED comms to ERASE (G<=120 catches printed-pink edges; bubble G~145 stays) ---
PEN_R_MIN, PEN_G_MAX, PEN_B_MIN, PEN_B_MAX = 225, 120, 90, 210
# --- light highlighter BUBBLE (importance flag) — detected only in the TOP-LEFT corner, KEPT on backs ---
BUB_R_MIN, BUB_G_LO, BUB_G_HI, BUB_B_MIN = 235, 105, 190, 188
CORNER_W, CORNER_H = 0.26, 0.24      # top-left corner fraction scanned for a bubble
BUBBLE_MIN_PX = 250                  # light-pink px in corner to count as a bubble
WRITING_MIN_PX = 700                 # pen px to count as pink writing/comms
EMPHASIS_MIN_PX = 600                # bubble-pink px OUTSIDE the corner -> a vertical emphasis line (best-effort)
DPI = 200
ZOOM = DPI / 72.0


def render(page):
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()


def pen_mask(a):
    """Saturated magenta pen / typed pink = comms -> erase. Grown 1px for clean edges."""
    R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    m = (R >= PEN_R_MIN) & (G <= PEN_G_MAX) & (B >= PEN_B_MIN) & (B <= PEN_B_MAX)
    grown = Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))
    return np.array(grown) > 0


def _bubble_band(a):
    """Boolean mask of light highlighter (bubble/emphasis) pink across the whole page."""
    R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    return (R >= BUB_R_MIN) & (G >= BUB_G_LO) & (G <= BUB_G_HI) & (B >= BUB_B_MIN)


def bubble_corner_px(a):
    """Light highlighter bubble in the top-left corner = 'important slide' flag (kept, not erased)."""
    H, W, _ = a.shape
    m = _bubble_band(a[:int(CORNER_H * H), :int(CORNER_W * W)])
    return int(m.sum())


def emphasis_px(a):
    """Bubble-pink highlighter OUTSIDE the top-left corner = a vertical emphasis line beside content
    ('this item is important -> must be on a card'). Kept, not erased. BEST-EFFORT: a pink diagram
    fill can also land in this band, so a flagged slide must be confirmed visually before acting."""
    H, W, _ = a.shape
    m = _bubble_band(a).copy()
    m[:int(CORNER_H * H), :int(CORNER_W * W)] = False   # exclude the corner bubble (counted separately)
    return int(m.sum())


def printed_number(page):
    """Small printed slide number = a 1-3 digit integer isolated in the BOTTOM-RIGHT corner.
    Restricting to the corner avoids grabbing list numbers in the body. None -> caller counts onward."""
    try:
        d = page.get_text("dict")
    except Exception:
        return None
    W, H = page.rect.width, page.rect.height
    best = None
    for blk in d.get("blocks", []):
        for ln in blk.get("lines", []):
            for sp in ln.get("spans", []):
                t = sp["text"].strip()
                if re.fullmatch(r"\d{1,3}", t):
                    x0, y0 = sp["bbox"][0], sp["bbox"][1]
                    if x0 > 0.78 * W and y0 > 0.80 * H:
                        key = (y0, x0)
                        if best is None or key > best[1]:
                            best = (int(t), key)
    return best[0] if best else None


def main():
    pdf = sys.argv[1]
    folder = os.path.dirname(os.path.abspath(pdf))
    build = os.path.join(folder, "_build")
    raw_dir, clean_dir = os.path.join(build, "raw"), os.path.join(build, "clean")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(clean_dir, exist_ok=True)

    doc = fitz.open(pdf)
    index, last_printed, offset = [], None, 0
    for i, pg in enumerate(doc):
        a = render(pg)
        pm = pen_mask(a)
        clean = a.copy(); clean[pm] = [255, 255, 255]

        pnum = printed_number(pg)
        if pnum is not None:
            slide, last_printed, offset = str(pnum), pnum, 0
        elif last_printed is not None:
            offset += 1; slide = f"{last_printed}+{offset}"
        else:
            slide = f"p{i + 1}"

        Image.fromarray(a).save(os.path.join(raw_dir, f"raw_{i + 1:02d}_s{slide}.png"))
        Image.fromarray(clean).save(os.path.join(clean_dir, f"s{slide}.png"))

        pen_px = int(pm.sum())
        bub_px = bubble_corner_px(a)
        emph_px = emphasis_px(a)
        has_writing = pen_px >= WRITING_MIN_PX
        has_bubble = bub_px >= BUBBLE_MIN_PX
        has_emphasis = emph_px >= EMPHASIS_MIN_PX
        bbox = None
        if has_writing:
            ys, xs = np.where(pm)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        index.append(dict(pdf_index=i + 1, slide=slide, printed=pnum,
                          pen_px=pen_px, bubble_px=bub_px, emphasis_px=emph_px,
                          has_writing=has_writing, has_bubble=has_bubble,
                          has_emphasis=has_emphasis, writing_bbox=bbox,
                          clean=f"clean/s{slide}.png", raw=f"raw/raw_{i + 1:02d}_s{slide}.png"))

    los = [index[i]["slide"] for i, pg in enumerate(doc)
           if re.search(r"learning objective|lernziel", pg.get_text(), re.I)]
    meta = dict(pdf=os.path.basename(pdf), pages=len(doc),
                slides=[e["slide"] for e in index],
                learning_objective_slides=los, dpi=DPI, index=index)
    json.dump(meta, open(os.path.join(build, "lecture_index.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    print(f"PDF: {meta['pdf']}  pages={meta['pages']}")
    print(f"clean backs -> {clean_dir}")
    print(f"raw (with marks) -> {raw_dir}")
    print(f"learning-objective slides: {los}")
    print("MARKED slides (BUBBLE = important; EMPHASIS? = pink line beside content, verify; "
          "WRITING = READ the raw/*.png with vision):")
    for e in index:
        if e["has_bubble"] or e["has_writing"] or e["has_emphasis"]:
            tags = []
            if e["has_bubble"]:
                tags.append("BUBBLE")
            if e["has_emphasis"]:
                tags.append(f"EMPHASIS?(px={e['emphasis_px']})")
            if e["has_writing"]:
                tags.append(f"WRITING(pen_px={e['pen_px']})")
            print(f"  slide {e['slide']:>6} (pdf p{e['pdf_index']}): {' + '.join(tags)}")
    print("\nSlide-number map (pdf_index -> printed/resolved):")
    print("  " + ", ".join(f"p{e['pdf_index']}->{e['slide']}" for e in index))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
