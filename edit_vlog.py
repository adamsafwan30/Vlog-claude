#!/usr/bin/env python3
"""Suntingan vlog 2 minit (8-13 Sep 2026) daripada footage DJI Osmo dalam Google Drive.

Penggunaan:
    python3 edit_vlog.py <folder_footage> [-o vlog_2minit.mp4] [--vertical]

<folder_footage> mesti ada subfolder `videos/` dan `photos/` (dimuat turun dengan gdown).
Shot dirujuk ikut urutan nama fail: V1 = video pertama, P1 = gambar pertama.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from make_vlog import GRADE, find_font, probe, render_clip, run, text_layer

TOTAL = 120.0
TITLE = "Cuti-cuti Kami"
SUBTITLE = "8 – 13 September 2026"
OUTRO = "Terima kasih kerana menonton!"

# (shot, mula sebagai pecahan durasi video, durasi saat, label babak)
SHOTS = [
    ("V24", 0.30, 5.0, None),  # pembuka: pantai luas, tajuk
    ("P1", None, 2.5, "8 Sep · Malam pertama"),
    ("P4", None, 2.0, None),
    ("P10", None, 2.5, None),
    ("P12", None, 2.0, "9 Sep · Snorkeling"),
    ("P20", None, 2.5, None),
    ("P17", None, 2.0, None),
    ("P26", None, 2.0, None),
    ("P28", None, 2.0, None),
    ("P33", None, 2.0, None),
    ("P36", None, 2.5, None),
    ("V1", 0.25, 3.0, "11 Sep · Jalan-jalan bazar"),
    ("V3", 0.40, 3.0, None),
    ("P41", None, 2.0, None),
    ("V5", 0.40, 3.0, None),
    ("V6", 0.70, 3.5, None),
    ("V7", 0.60, 4.0, "13 Sep · Hari di pantai"),
    ("V8", 0.50, 3.0, None),
    ("V10", 0.55, 4.0, None),
    ("V11", 0.70, 3.0, None),
    ("V13", 0.20, 3.0, None),
    ("V14", 0.50, 3.0, None),
    ("V15", 0.25, 4.0, None),  # kulit kerang
    ("V16", 0.50, 3.0, None),
    ("P74", None, 2.5, None),  # gambar berkumpulan
    ("V20", 0.60, 3.0, None),
    ("V21", 0.50, 3.0, None),
    ("V23", 0.70, 3.0, None),
    ("V25", 0.30, 3.0, None),
    ("V27", 0.40, 4.0, None),  # ombak di kaki
    ("P56", None, 2.0, None),
    ("V29", 0.30, 3.0, None),
    ("V30", 0.50, 4.0, None),
    ("V32", 0.60, 3.0, None),
    ("V26", 0.75, 3.5, None),
    ("V28", 0.70, 5.5, None),  # penutup
]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("footage", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("vlog_2minit.mp4"))
    p.add_argument("--vertical", action="store_true", help="format 1080x1920 (Reels/TikTok)")
    args = p.parse_args()

    videos = sorted((args.footage / "videos").glob("*.mp4"))
    photos = sorted((args.footage / "photos").glob("*.jpg"))
    w, h = (1080, 1920) if args.vertical else (1920, 1080)
    scale = TOTAL / sum(s[2] for s in SHOTS)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts, chapters, t = [], [], 0.0
        for i, (ref, frac, dur, label) in enumerate(SHOTS):
            src = (videos if ref[0] == "V" else photos)[int(ref[1:]) - 1]
            kind = "video" if ref[0] == "V" else "image"
            length = dur * scale
            start = frac * probe(src)[0] if kind == "video" else None
            out = tmp / f"part{i:03d}.mp4"
            print(f"[{i + 1}/{len(SHOTS)}] {ref} {src.name} ({length:.1f}s)")
            render_clip(src, kind, length, w, h, out, start)
            parts.append(out)
            if label:
                chapters.append((label, t))
            t += length

        listfile = tmp / "list.txt"
        listfile.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(joined)])

        big, small = (h // 12, h // 30) if not args.vertical else (w // 14, w // 28)
        bold, regular = find_font(True), find_font(False)
        layers = [
            text_layer(tmp, "title", TITLE, big, f"h*0.42-{big}/2", 0.5, 5.0, bold),
            text_layer(tmp, "subtitle", SUBTITLE, small, f"h*0.42+{big}*0.7", 1.0, 5.0, regular),
            text_layer(tmp, "outro", OUTRO, small * 3 // 2, "h*0.45", TOTAL - 5, TOTAL - 0.3, bold),
        ]
        for n, (label, start) in enumerate(chapters):
            layers.append(text_layer(tmp, f"ch{n}", label, small, "h*0.86", start + 0.3, start + 3.3,
                                     bold, x="w*0.05"))
        fc = f"[0:v]{GRADE},{','.join(layers)}[v];[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        run(["ffmpeg", "-y", "-i", str(joined), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{TOTAL:.3f}",
             "-movflags", "+faststart", str(args.output)])
    dur, _ = probe(args.output)
    print(f"Siap: {args.output} ({dur:.1f}s)")


if __name__ == "__main__":
    main()
