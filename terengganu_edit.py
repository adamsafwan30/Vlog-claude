#!/usr/bin/env python3
""""TERENGGANU" - travel vlog 3 minit, dipotong ikut lagu Bunkface - Darah Muda.

Penggunaan:
    python3 terengganu_edit.py <folder_footage> --song darah_muda.mp3 [-o terengganu.mp4]
    python3 terengganu_edit.py <folder_footage> --song darah_muda.mp3 --until 30   # preview

- Video sahaja (tiada gambar). Shot dirujuk ikut tarikh_masa dalam nama fail DJI,
  contoh "0911_163954" = dji_mimo_20260911_163954_*.mp4.
- Lagu (4:08) diedit secara muzikal kepada 3:00: bahagian verse/korus kedua dibuang pada
  sempadan bar supaya lagu berakhir dengan outro asal.
- Opening ala template travel vlog: 3 panel masuk satu-satu + tajuk TERENGGANU.
- Setiap potongan jatuh pada beat; scene lompat diperlahankan (slow-mo licin, 60fps sumber).
- Gred warna terang & hangat (golden hour) ikut video rujukan.
"""
import argparse
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pro_edit import duration, run, text, zoompan

FPS = 30
W, H = 1920, 1080
TOTAL = 180.0
FONTS = Path(__file__).resolve().parent / "assets" / "fonts"
GRADE = ("eq=contrast=1.12:saturation=1.38:brightness=0.025:gamma=1.02,"
         "colorbalance=rs=-0.03:bs=0.05:rh=0.07:gh=0.03:bh=-0.06,"
         "curves=master='0/0 0.25/0.21 0.75/0.8 1/1',unsharp=5:5:0.5")
YELLOW, ORANGE = "0xFFD23F", "0xE8590C"

# Edit lagu: [A1, C1) + [C2, END) = 180s. Dikira dengan librosa (beat 3, 181, 313).
SONG_A1, SONG_C1, SONG_C2 = 3.158, 80.922, 139.598

CUT = ("cut", 0)
OPENING = ("OPENING", None)  # klip khas: 3 panel + tajuk
# Setiap shot: (kunci fail, mula (saat), beats, laju, gerakan, transition masuk, bunyi asal)
# laju < 1 = slow-mo; "smooth" pada gerakan = interpolasi frame untuk slow-mo lebih perlahan.
SHOTS = []      # diisi dalam shotlist.py
CAPTIONS = []   # (beat, teks kecil, teks besar)


def footage_index(folder):
    return {p.name[13:24]: p for p in sorted(folder.glob("dji_mimo_*.mp4"))}


def song_edit(song, tmp):
    import librosa
    import numpy as np
    y, sr = librosa.load(str(song), sr=22050)
    _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    end = SONG_C2 + TOTAL - (SONG_C1 - SONG_A1)
    out = tmp / "song.wav"
    f = 0.03
    run(["ffmpeg", "-y", "-i", str(song), "-filter_complex",
         f"[0:a]atrim={SONG_A1}:{SONG_C1 + f},asetpts=PTS-STARTPTS[p1];"
         f"[0:a]atrim={SONG_C2 - f}:{end + 0.1},asetpts=PTS-STARTPTS[p2];"
         f"[p1][p2]acrossfade=d={2 * f}:c1=tri:c2=tri,atrim=0:{TOTAL},afade=t=in:d=0.3,"
         f"afade=t=out:st={TOTAL - 5}:d=5,aresample=48000[a]", "-map", "[a]", "-c:a", "pcm_s16le", str(out)])
    l1 = SONG_C1 - SONG_A1
    grid = [t - SONG_A1 for t in beats if SONG_A1 <= t < SONG_C1]
    grid += [t - SONG_C2 + l1 for t in beats if SONG_C2 <= t < end]
    return out, list(np.round(grid, 4))


def opening_clip(idx, frames, out):
    """3 panel masuk bergilir (atas/bawah/atas) + tajuk TERENGGANU."""
    panels = [("0911_163954", 2.0, 1.0), ("0913_180240", 6.0, 0.5), ("0913_175738", 30.0, 0.5)]
    secs = frames / FPS
    ease = "(1-pow(1-clip((t-{})/0.55\\,0\\,1)\\,3))"
    cmd = ["ffmpeg", "-y"]
    for key, start, speed in panels:
        cmd += ["-ss", f"{start}", "-t", f"{secs * speed + 0.5:.2f}", "-i", str(idx[key])]
    cmd += ["-f", "lavfi", "-i", f"color=c=0x111111:s={W}x{H}:r={FPS}:d={secs + 1}"]
    fc = []
    for i, (_, _, speed) in enumerate(panels):
        fc.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale=-2:{H},crop=630:{H},{GRADE},"
                  f"tpad=stop_mode=clone:stop_duration={secs + 1}[p{i}]")
    beat = secs / 16  # panel masuk pada beat 0, 1, 2 (kira-kira)
    e = [ease.format(f"{k * beat * 1.0:.3f}") for k in range(3)]
    fc.append(f"[3:v][p0]overlay=x=0:y=-{H}*(1-{e[0]})[o1]")
    fc.append(f"[o1][p1]overlay=x=645:y={H}*(1-{e[1]})[o2]")
    fc.append(f"[o2][p2]overlay=x=1290:y=-{H}*(1-{e[2]})[o3]")
    t0 = 3.2 * beat
    tmp = out.parent
    for name, s in (("ot1", "TRAVEL VLOG"), ("ot2", "TERENGGANU"), ("ot3", "8 - 13 SEPTEMBER 2026")):
        (tmp / f"{name}.txt").write_text(s)
    et, es = ease.format(f"{t0:.3f}"), ease.format(f"{t0 + 0.4:.3f}")
    fc.append(
        f"[o3]drawtext=fontfile={FONTS / 'Montserrat-Bold.ttf'}:textfile={tmp / 'ot1.txt'}:fontsize=46"
        f":fontcolor=white:borderw=2:bordercolor=black@0.4:x=(w-text_w)/2:y=330+30*(1-{et}):alpha={et},"
        f"drawtext=fontfile={FONTS / 'Anton-Regular.ttf'}:textfile={tmp / 'ot2.txt'}:fontsize=220"
        f":fontcolor={YELLOW}:borderw=7:bordercolor={ORANGE}:shadowcolor=black@0.45:shadowx=6:shadowy=8"
        f":x=(w-text_w)/2:y=395+60*(1-{et}):alpha={et},"
        f"drawtext=fontfile={FONTS / 'Montserrat-Bold.ttf'}:textfile={tmp / 'ot3.txt'}:fontsize=34"
        f":fontcolor=white:borderw=2:bordercolor=black@0.4:x=(w-text_w)/2:y=705+20*(1-{es}):alpha={es},"
        f"format=yuv420p[v]")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(frames), "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-r", str(FPS), str(out)])


def render_shot(idx, shot, frames, out):
    key, start, _, speed, motion, _, _ = shot
    src = idx[key]
    secs = frames / FPS
    smooth = motion.endswith("+smooth")
    motion = motion.replace("+smooth", "")
    src_len = secs * speed
    start = max(0.0, min(start, duration(src) - src_len - 0.05))
    pre = f"setpts=(PTS-STARTPTS)/{speed}"
    if smooth:  # interpolasi gerakan supaya slow-mo bawah 0.5x kekal licin
        pre = f"fps=60,minterpolate=fps={round(FPS / speed)}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,{pre}"
    cover = "scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,setsar=1"
    vf = (f"{pre},fps={FPS},{cover},tpad=stop_mode=clone:stop_duration=3,"
          f"{zoompan(motion, frames)},{GRADE},format=yuv420p")
    if smooth:  # minterpolate pada 1080p sahaja (laju)
        vf = f"scale=1920:-2,{vf}"
    run(["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{src_len + 0.3:.3f}", "-i", str(src), "-vf", vf,
         "-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
         "-r", str(FPS), str(out)])
    got = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(out)],
                             capture_output=True, text=True, check=True).stdout)
    if got != frames:
        raise RuntimeError(f"{key}: dapat {got} frame, perlu {frames}")
    return src, start


def main():
    from shotlist import CAPTIONS, SHOTS  # noqa: F811
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("footage", type=Path, help="folder video (dji_mimo_*.mp4)")
    p.add_argument("--song", type=Path, required=True)
    p.add_argument("-o", "--output", type=Path, default=Path("terengganu.mp4"))
    p.add_argument("--until", type=float, default=TOTAL, help="render hingga saat ini sahaja (preview)")
    p.add_argument("--cache", type=Path)
    p.add_argument("--workers", type=int, default=3)
    args = p.parse_args()
    idx = footage_index(args.footage)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        song, grid = song_edit(args.song, tmp)
        bt = lambda k: grid[k] if k > 0 else 0.0  # noqa: E731
        total_f = round(TOTAL * FPS)
        bounds, k = [0], 0
        for shot in SHOTS[:-1]:
            k += shot[2]
            bounds.append(round(bt(k) * FPS))
        print(f"{len(SHOTS)} shot, beat terakhir {k}/{len(grid)}")
        trans = [0] + [max(2, round(s[5][1] * FPS)) if s[5][0] != "cut" else 1 for s in SHOTS[1:]]
        starts = [b - (d // 2) for b, d in zip(bounds, trans)]
        starts[0] = 0
        ends = [starts[i + 1] + trans[i + 1] for i in range(len(SHOTS) - 1)] + [total_f]
        frames = [e - s for s, e in zip(starts, ends)]
        limit_f = round(args.until * FPS)
        n = next((i for i, s in enumerate(starts) if s >= limit_f), len(SHOTS))
        cache = args.cache or tmp
        cache.mkdir(parents=True, exist_ok=True)
        files, sources = {}, {}

        def job(i):
            shot = SHOTS[i]
            out = cache / f"t{i:03d}_{shot[0]}_{shot[1]}_{frames[i]}_{shot[3]}_{shot[4]}.mp4"
            files[i] = out
            if not out.exists():
                part = out.with_name("part_" + out.name)
                if shot[0] == "OPENING":
                    opening_clip(idx, frames[i], part)
                else:
                    render_shot(idx, shot, frames[i], part)
                part.rename(out)
            if shot[0] != "OPENING":
                src = idx[shot[0]]
                sources[i] = (src, max(0.0, min(shot[1], duration(src) - frames[i] / FPS * shot[3] - 0.05)))
            print(f"  [{i + 1}/{n}] {shot[0]:>12} {frames[i] / FPS:5.2f}s x{shot[3]} {shot[4]}", flush=True)

        with ThreadPoolExecutor(args.workers) as pool:
            list(pool.map(job, range(n)))

        inputs, fc = [], []
        for i in range(n):
            inputs += ["-i", str(files[i])]
            fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
        last = "v0"
        for i in range(1, n):
            kind = SHOTS[i][5][0]
            kind = "fade" if kind == "cut" else kind
            fc.append(f"[{last}][v{i}]xfade=transition={kind}:duration={trans[i] / FPS:.6f}"
                      f":offset={(starts[i] - 0.5) / FPS:.6f}[x{i}]")
            last = f"x{i}"
        layers = []
        for c, (beat, small, big) in enumerate(CAPTIONS):
            s = bt(beat) + 0.1
            layers += [
                text(tmp, f"k{c}a", small, "Montserrat-Bold.ttf", 30, "110", "h-235", s, s + 3.4, 0.4, 20),
                (text(tmp, f"k{c}b", big, "Anton-Regular.ttf", 92, "105", "h-200", s + 0.12, s + 3.4, 0.4, 30)
                 .replace("fontcolor=white", f"fontcolor={YELLOW}:borderw=4:bordercolor={ORANGE}")),
            ]
        end_t = bt(len(grid) - 24)
        layers += [
            text(tmp, "e1", "SEE YOU AGAIN", "Montserrat-Bold.ttf", 46, "(w-text_w)/2", "h/2-140",
                 end_t, TOTAL - 0.6, 0.6, 25),
            (text(tmp, "e2", "TERENGGANU", "Anton-Regular.ttf", 200, "(w-text_w)/2", "h/2-80",
                  end_t + 0.3, TOTAL - 0.6, 0.6, 50)
             .replace("fontcolor=white", f"fontcolor={YELLOW}:borderw=7:bordercolor={ORANGE}")),
        ]
        vchain = f"[{last}]" + (",".join(layers) + "," if layers else "")
        fc.append(f"{vchain}fade=t=out:st={TOTAL - 1.2}:d=1.2,format=yuv420p[vout]")

        # Audio: lagu + bunyi asal terpilih (ombak dsb.) + whoosh pada transition laju
        inputs += ["-i", str(song)]
        ai = n
        mix = ["[mus]"]
        fc.append(f"[{ai}:a]volume=1.0[mus]")
        nat_i = ai + 1
        for i in range(n):
            shot = SHOTS[i]
            if shot[6] and shot[0] != "OPENING":
                src, start = sources[i]
                secs = frames[i] / FPS
                inputs += ["-ss", f"{start:.3f}", "-t", f"{secs * shot[3]:.3f}", "-i", str(src)]
                ms = round(starts[i] / FPS * 1000)
                fc.append(f"[{nat_i}:a]aresample=48000,aformat=channel_layouts=stereo,"
                          f"atempo={max(0.5, shot[3])},afade=t=in:d=0.3,afade=t=out:st={max(0, secs - 0.5):.3f}:d=0.5,"
                          f"volume={shot[6]},adelay={ms}|{ms}[n{i}]")
                mix.append(f"[n{i}]")
                nat_i += 1
        fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,"
                  f"alimiter=limit=0.89:level=disabled[aout]")
        script = tmp / "graph.txt"
        script.write_text(";\n".join(fc))
        print("Menyusun video...", flush=True)
        run(["ffmpeg", "-y", *inputs, "-filter_complex_script", str(script), "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "256k", "-t", f"{min(args.until, TOTAL)}", "-movflags", "+faststart",
             str(args.output)])
    print(f"Siap: {args.output} ({duration(args.output):.1f}s)")


if __name__ == "__main__":
    main()
