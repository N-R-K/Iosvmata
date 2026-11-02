#!/usr/bin/env python
# Based on the script from https://github.com/shytikov/pragmasevka
#
# Run from the Iosevka checkout after `npm run build -- ttf-unhinted::Iosvmata`.
# Punctuation is swapped in the unhinted fonts and then hinted with the same
# ttfautohint call Iosevka uses, so the copied glyphs get hints too.

import os
import subprocess
import sys
import tomllib

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

plan = "Iosvmata"

chars = "!&()*+,-./:;<=>?[\\]^{|}~"

pairs = [
    ['Regular', 'SemiBold'],
    ['Italic', 'SemiBoldItalic'],
    ['Bold', 'Black'],
    ['BoldItalic', 'BlackItalic'],
]

config = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{plan}.toml")
with open(config, "rb") as f:
    hint_params = tomllib.load(f)["buildPlans"][plan]["hintParams"]

unhinted = f"dist/{plan}/TTF-Unhinted"
hinted = f"dist/{plan}/TTF"
os.makedirs(hinted, exist_ok=True)

for [recipient, donor] in pairs:
    font = f"{unhinted}/{plan}-{recipient}.ttf"

    target = TTFont(font)
    source = TTFont(f"{unhinted}/{plan}-{donor}.ttf")
    if target.getGlyphOrder() != source.getGlyphOrder():
        sys.exit(f"{recipient} and {donor} have different glyph sets")

    glyphs = source.getGlyphSet()
    cmap = target.getBestCmap()
    for c in chars:
        name = cmap[ord(c)]
        # colon and semicolon are composites, copy their donor outline whole
        rec = DecomposingRecordingPen(glyphs)
        glyphs[name].draw(rec)
        pen = TTGlyphPen(None)
        rec.replay(pen)
        target["glyf"][name] = pen.glyph()
        target["hmtx"][name] = source["hmtx"][name]
    target.save(font)

    controls = f".build/TTF/{plan}/{plan}-{recipient}.ttfa.txt"
    subprocess.run(
        ["ttfautohint", *hint_params, "-m", controls, font,
         f"{hinted}/{plan}-{recipient}.ttf"],
        check=True,
    )
