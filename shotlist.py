"""Senarai shot untuk terengganu_edit.py (beat = 1/136 minit, ~0.44s).

Peta lagu (masa video): intro 0-20.9s (beat 0-47) | drop beat 47 | break ~71s | bridge ~78s |
verse 3 ~91s | break ~117s | korus akhir ~122s | outro ~168s.
"""
CUT = ("cut", 0)
OPENING = "OPENING"

# (kunci fail, mula (s), beats, laju, gerakan, transition masuk, bunyi asal)
SHOTS = [
    # --- Intro: opening 3 panel + tajuk, kemudian eskalator (beat 0-24) ---
    (OPENING, 0, 16, 1, "none", CUT, 0),
    ("0911_163954", 4.5, 8, 1, "in", ("smoothup", 0.4), 0),
    # --- Build: 8 Sep perjalanan & tiba di vila (beat 24-47), makin laju ke drop ---
    ("0908_123034", 6.0, 4, 1, "in", ("fadewhite", 0.2), 0),
    ("0908_123356", 21.0, 4, 1, "right", CUT, 0),
    ("0908_164852", 3.0, 4, 1, "none", CUT, 0),
    ("0908_173858", 18.0, 4, 1, "in", ("hblur", 0.25), 0),
    ("0908_184318", 0.0, 2, 1, "in", CUT, 0),
    ("0908_184318", 66.0, 2, 1, "left", CUT, 0),
    ("0908_184740", 3.0, 1, 1, "punch", CUT, 0),
    ("0908_184816", 24.0, 1, 1, "punch", CUT, 0),
    ("0908_190054", 6.0, 1, 1, "punch", CUT, 0),
    # --- DROP (beat 47): malam di kolam vila ---
    ("0908_223804", 21.0, 2, 1, "punch+night", ("fadewhite", 0.2), 0),
    ("0908_222518", 3.0, 2, 1, "left+night", CUT, 0),
    ("0908_223804", 25.0, 2, 1, "in+night", CUT, 0),
    ("0908_224748", 0.0, 2, 1, "punch+night", CUT, 0),
    ("0908_223804", 6.0, 2, 1, "in+night", CUT, 0),
    ("0908_223804", 36.0, 2, 1, "right+night", CUT, 0),
    # --- 9 Sep pagi: jeti & bot ---
    ("0909_091214", 18.0, 4, 1, "in", ("hblur", 0.25), 0),
    ("0909_091400", 15.0, 4, 1, "none", CUT, 0),
    ("0909_093216", 6.0, 4, 1, "in", CUT, 0),
    ("0909_093216", 18.0, 4, 1, "right", CUT, 0),
    ("0909_093536", 6.0, 200, 1, "in", CUT, 0),  # sementara: sambungan selepas preview
]

# (beat, teks kecil, teks besar)
CAPTIONS = [
    (24, "08.09.2026", "DAY 01"),
    (59, "09.09.2026", "DAY 02"),
]
