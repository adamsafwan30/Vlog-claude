#!/usr/bin/env python3
"""Build 2-minute vertical vlog synced to 'Memori Tercipta'.

Output time T. Song edit: song[0, 65.32] + song[129.06, 183.74]  (part2: T = s - 63.74)
Song cues (T): intro 0-6.5 | verse1 6.5-35.9 | CHORUS1 35.9-65.3 |
               bridge 68.1-82 | FINAL CHORUS 87.1-116.4 | fade 116-120
"""
import json, os, subprocess, sys

S = "/tmp/claude-0/-home-user-Vlog-claude/7ac34c93-de73-549f-87c9-4a1ad456c38c/scratchpad"
V = f"{S}/drive/Video"
SRC = {
    "c1": f"{V}/dji_mimo_20261111_073552_0021_1794379754832_video.mp4",
    "c2": f"{V}/dji_mimo_20261111_110022_0023_1794379819467_video.mp4",
    "c3": f"{V}/dji_mimo_20261111_110820_0026_1794379820291_video.mp4",
    "c4": f"{V}/dji_mimo_20261111_110948_0029_1794367142197_video.mp4",
    "c5": f"{V}/dji_mimo_20261111_111634_0034_1794379823273_video.mp4",
    "c6": f"{V}/dji_mimo_20261111_161816_0041_1794386258981_video.mp4",
}
KF = {"c1": f"{S}/mezz/kf1.mp4", "c2": f"{S}/mezz/kf2.mp4"}
OUT = f"{S}/segs169"
FPS = 30
os.makedirs(OUT, exist_ok=True)

# ---- beat grid in output time -------------------------------------------
BEATS = json.load(open(f"{S}/work/beats.json"))
TB = [b for b in BEATS if b < 65.32] + [b - 63.74 for b in BEATS if b >= 129.06]

def snap(t):
    return min(TB, key=lambda b: abs(b - t)) if 0 < t < 119 else t

# ---- segment primitives -----------------------------------------------------
pieces = []  # (src, a, b, out_dur, cx)

RAMP = [12, 6, 3, 1.6]       # speeds stepping down toward a 1x hero moment
RSTEP = 0.3                  # output seconds per ramp step

def add(src, a, b, dur, cx):
    pieces.append(dict(src=src, a=a, b=b, dur=dur, cx=cx))

def shot(src, a, b, T0, T1, cx, hero=None, ramp_out_end=False, ramp_in_start=False):
    """Hyperlapse a..b over T0..T1 with optional 1x hero (h0,h1) and ramps."""
    T0, T1 = snap(T0), snap(T1)
    D = T1 - T0
    plan = []  # list of ('fast', srcspan) or ('fix', a, b, dur)
    cur = a
    if ramp_in_start:
        # 1x -> fast
        for sp in [1.6, 3, 6, 12]:
            plan.append(("fix", cur, cur + sp * RSTEP, RSTEP)); cur += sp * RSTEP
    if hero:
        h0, h1 = hero
        down = sum(sp * RSTEP for sp in RAMP)
        plan.append(("fast", cur, h0 - down)); cur = h0 - down
        for sp in RAMP:
            plan.append(("fix", cur, cur + sp * RSTEP, RSTEP)); cur += sp * RSTEP
        plan.append(("fix", h0, h1, h1 - h0)); cur = h1
        for sp in RAMP[::-1]:
            plan.append(("fix", cur, cur + sp * RSTEP, RSTEP)); cur += sp * RSTEP
    if ramp_out_end:
        down = sum(sp * RSTEP for sp in RAMP)
        plan.append(("fast", cur, b - down)); cur = b - down
        for sp in RAMP:
            plan.append(("fix", cur, cur + sp * RSTEP, RSTEP)); cur += sp * RSTEP
    else:
        plan.append(("fast", cur, b))
    fixed = sum(p[3] for p in plan if p[0] == "fix")
    fast_src = sum(p[2] - p[1] for p in plan if p[0] == "fast")
    tf = D - fixed
    assert tf > 0.2, (src, a, b, D, fixed)
    speed = fast_src / tf
    print(f"  shot {src} {a}-{b} T{T0:.2f}-{T1:.2f} fast speed {speed:.1f}x", file=sys.stderr)
    for p in plan:
        if p[0] == "fix":
            add(src, p[1], p[2], p[3], cx)
        elif p[2] - p[1] > 0.01:
            add(src, p[1], p[2], (p[2] - p[1]) / speed, cx)
    return T1

def rt(src, a, T0, T1, cx, speed=1.0):
    """Real-time (or constant speed) clip starting at source a, filling T0..T1."""
    T0, T1 = snap(T0), snap(T1)
    add(src, a, a + (T1 - T0) * speed, T1 - T0, cx)
    return T1

# ---- TIMELINE ---------------------------------------------------------------
# INTRO + VERSE 1 : a day at work (overhead-style hyperlapse, like the reference)
shot("c1", 2, 330, 0.0, 12.1, 0.42, hero=(157.3, 160.6), ramp_in_start=True)
shot("c2", 0, 125, 12.1, 21.0, 0.55, hero=(43.0, 46.0))
shot("c1", 330, 640, 21.0, 30.4, 0.38, hero=(372.5, 376.0))
shot("c2", 125, 215, 30.4, 35.9, 0.68, ramp_out_end=True)

# CHORUS 1 : "Di sini jiwa, memori tercipta..." – jokes & laughs with the team
rt("c1", 816.2, 35.9, 39.6, 0.50)          # selfie, smiling face
rt("c2", 393.0, 39.6, 43.9, 0.50)          # team at station looks at cam
rt("c1", 836.0, 43.9, 47.6, 0.50)          # two of them selfie, laughing
rt("c2", 402.6, 47.6, 49.8, 0.48)          # big laugh close-up
rt("c2", 397.3, 49.8, 51.5, 0.50)          # team looks at cam
rt("c1", 900.0, 51.5, 58.5, 0.50, 1.6)     # "mungkin di sini kita akan terpisah" – laughing at counter
rt("c2", 407.5, 58.5, 61.8, 0.50)          # smile to camera
rt("c1", 840.6, 61.8, 65.32, 0.50)         # face close-up, end of chorus

# INSTRUMENTAL + BRIDGE : "Yang terpahit jua termanis, semuanya bagiku terindah"
shot("c1", 912, 1405, 65.32, 76.5, 0.50, hero=(1218.0, 1221.0))
shot("c2", 215, 372, 76.5, 82.6, 0.55, ramp_out_end=True)
rt("c2", 421.5, 82.6, 87.1, 0.50)          # after shift: food arrives at the table

# FINAL CHORUS : together at the table, then goodbye wave
rt("c4", 0.3, 87.1, 91.0, 0.50)             # whole team seated
rt("c4", 4.3, 91.0, 94.1, 0.5)             # smiles
rt("c3", 0.0, 94.1, 97.4, 0.58)             # trays of food
rt("c3", 3.4, 97.4, 101.0, 0.5)            # top-down food
rt("c4", 7.6, 101.0, 105.0, 0.38)           # drinks raised
rt("c5", 3.4, 105.0, 109.2, 0.42)          # sip, chatting
rt("c5", 9.0, 109.2, 113.5, 0.52)          # the team together
add("c6", 0.98, 4.37, 4.37 - 0.98, 0.48)    # selfie walk + wave (ends ~116.9)

total = sum(p["dur"] for p in pieces)
print(f"pieces={len(pieces)} total={total:.2f}", file=sys.stderr)
json.dump(pieces, open(f"{S}/work/pieces.json", "w"), indent=1)
