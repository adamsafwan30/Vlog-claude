#!/usr/bin/env python3
""""East Coast Diaries" - suntingan vlog 2 minit gaya editor profesional.

Penggunaan:
    python3 pro_edit.py <folder_footage> [-o east_coast_diaries.mp4]

<folder_footage> mesti ada subfolder `videos/` dan `photos/` (dimuat turun dengan gdown).
Shot dirujuk ikut urutan nama fail: V1 = video pertama, P1 = gambar pertama.

Apa yang skrip ni buat:
- Muzik "Winter Breeze" (Arulo, Mixkit Free License) dimuat turun automatik dan
  setiap potongan jatuh tepat pada beat (librosa beat tracking).
- Struktur ikut lagu: intro sinematik slow-mo -> drop (snorkeling + bazar, potongan laju)
  -> breakdown santai di pantai -> drop kedua -> penutup senja.
- Slow-motion 0.5x daripada footage 60fps, speed-up 1.5x, zoom punch pada drop,
  push-in / pan Ken Burns pada setiap shot.
- Transition: flash putih, whip blur, zoom, smooth slide, dissolve + SFX whoosh & boom.
- Letterbox 2.39:1 pada intro yang terbuka masa drop, gred teal-orange, grain, vignette.
- Tipografi Montserrat: tajuk animasi, label babak bergerak masuk, penutup.
"""
import argparse
import math
import subprocess
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FPS = 30
W, H = 1920, 1080
TOTAL = 120.0
FONTS = Path(__file__).resolve().parent / "assets" / "fonts"
MUSIC_URL = "https://assets.mixkit.co/music/207/207.mp3"  # Winter Breeze - Arulo
GRADE = ("eq=contrast=1.07:saturation=1.16:gamma=0.98,"
         "colorbalance=rs=-0.05:bs=0.06:rm=0.02:bm=-0.01:rh=0.06:gh=0.02:bh=-0.05,"
         "curves=master='0/0.03 0.5/0.5 1/0.97',unsharp=5:5:0.45")
BAR = 138  # letterbox 2.39:1

# Transition masuk: (jenis xfade, saat). "cut" = potong terus.
CUT = ("cut", 0)
# (shot, beats, mula sebagai pecahan durasi video, laju, gerakan, transition masuk, bunyi asal)
SHOTS = [
    # --- Intro sinematik (beat 0-61) ---
    ("V27", 8, 0.30, 0.5, "in", CUT, 0.6),          # ombak di kaki
    ("V26", 8, 0.70, 0.5, "in", ("fade", 1.0), 0.3),
    ("V31", 8, 0.00, 0.5, "right", ("fade", 1.0), 0.4),
    ("P68", 8, None, 1, "in", ("fade", 1.0), 0),
    ("P1", 4, None, 1, "in", ("fadeblack", 0.6), 0),
    ("P4", 4, None, 1, "left", CUT, 0),
    ("P10", 4, None, 1, "in", ("dissolve", 0.4), 0),
    ("P11", 4, None, 1, "out", CUT, 0),
    ("P12", 4, None, 1, "right", ("hblur", 0.3), 0),
    ("P20", 4, None, 1, "in", CUT, 0),
    ("P22", 2, None, 1, "in", CUT, 0),
    ("P24", 2, None, 1, "punch", CUT, 0),
    ("P38", 1, None, 1, "punch", CUT, 0),
    # --- Drop 1: snorkeling (beat 61-91) ---
    ("P26", 2, None, 1, "punch", ("fadewhite", 0.25), 0),
    ("P17", 2, None, 1, "in", CUT, 0),
    ("P28", 2, None, 1, "punch", CUT, 0),
    ("P16", 2, None, 1, "left", CUT, 0),
    ("P32", 2, None, 1, "in", CUT, 0),
    ("P33", 4, None, 1, "in", ("zoomin", 0.3), 0),  # ikan bawah air
    ("P18", 2, None, 1, "right", CUT, 0),
    ("P30", 2, None, 1, "in", CUT, 0),
    ("P27", 2, None, 1, "punch", CUT, 0),
    ("P21", 2, None, 1, "in", CUT, 0),
    ("P36", 4, None, 1, "right", ("smoothleft", 0.3), 0),
    ("P39", 2, None, 1, "in", CUT, 0),
    ("P31", 2, None, 1, "punch", CUT, 0),
    # --- Drop 1: bazar (beat 91-123) ---
    ("V2", 4, 0.40, 1, "in", ("smoothup", 0.3), 0),
    ("V1", 4, 0.25, 1.5, "none", CUT, 0),
    ("P41", 2, None, 1, "punch", CUT, 0),
    ("P42", 2, None, 1, "in", CUT, 0),
    ("V3", 4, 0.40, 1.5, "none", CUT, 0),
    ("V4", 2, 0.50, 1, "none", ("hblur", 0.25), 0),
    ("V5", 4, 0.40, 1, "in", CUT, 0),
    ("V6", 4, 0.65, 1, "none", CUT, 0),
    ("P43", 2, None, 1, "punch", CUT, 0),
    ("P45", 2, None, 1, "in", CUT, 0),
    ("P44", 2, None, 1, "none", CUT, 0),
    # --- Breakdown: pantai santai (beat 123-171) ---
    ("V7", 8, 0.55, 0.5, "in", ("fadeblack", 0.8), 0.3),
    ("V12", 8, 0.50, 0.5, "left", ("fade", 0.7), 0.3),
    ("V15", 8, 0.20, 0.5, "in", ("fade", 0.7), 0.3),   # kulit kerang
    ("V17", 8, 0.50, 0.5, "right", ("fade", 0.7), 0.3),
    ("V16", 8, 0.50, 0.5, "in", ("fade", 0.7), 0.3),   # buaian
    ("V19", 8, 0.75, 0.5, "out", ("fade", 0.7), 0.3),
    # --- Drop 2: geng di pantai (beat 171-219) ---
    ("V10", 4, 0.55, 1, "punch", ("fadewhite", 0.25), 0),
    ("V8", 2, 0.50, 1, "none", CUT, 0),
    ("V9", 2, 0.50, 1, "none", CUT, 0),
    ("V11", 4, 0.70, 1, "in", CUT, 0),
    ("V13", 2, 0.20, 1, "none", CUT, 0),
    ("V14", 2, 0.50, 1, "none", CUT, 0),
    ("V25", 4, 0.30, 1, "punch", ("zoomin", 0.3), 0),
    ("V23", 2, 0.75, 1, "none", CUT, 0),
    ("P74", 2, None, 1, "punch", CUT, 0),           # papan tanda pulau
    ("P48", 2, None, 1, "in", CUT, 0),
    ("V20", 2, 0.60, 1, "none", CUT, 0),
    ("V21", 4, 0.50, 1, "in", ("hblur", 0.3), 0),
    ("V29", 4, 0.30, 1, "none", CUT, 0),
    ("V30", 4, 0.50, 0.5, "in", CUT, 0),
    ("V32", 4, 0.60, 1, "none", CUT, 0),
    ("V24", 4, 0.30, 0.5, "in", CUT, 0),
    # --- Penutup senja (beat 219-akhir) ---
    ("V28", 8, 0.70, 0.5, "in", ("fade", 1.0), 0.4),
    ("P88", None, None, 1, "in", ("fade", 1.0), 0),  # hingga akhir
]
# (beat, nombor, nama babak)
CHAPTERS = [(32, "01", "NIGHT ONE"), (61, "02", "INTO THE BLUE"), (91, "03", "CITY STROLL"),
            (123, "04", "SALT & SUNSETS"), (171, "05", "GOOD COMPANY")]
DROPS = [61, 171]
OUTRO_BEAT = 219


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg gagal:\n{' '.join(cmd)}\n{r.stderr[-3000:]}")


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def beat_times(music):
    import librosa
    y, sr = librosa.load(str(music), sr=22050)
    _, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    return list(beats)


def zoompan(motion, frames):
    p = f"(on/{max(frames - 1, 1)})"
    ease = f"((1-cos(PI*{p}))/2)"
    centre = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    z, xy = {
        "in": (f"1+0.09*{ease}", centre),
        "out": (f"1.09-0.09*{ease}", centre),
        "left": ("1.12", f"x='(iw-iw/zoom)*(1-{ease})':y='ih/2-(ih/zoom/2)'"),
        "right": ("1.12", f"x='(iw-iw/zoom)*{ease}':y='ih/2-(ih/zoom/2)'"),
        "punch": (f"1+0.2*exp(-on/3.5)+0.05*{p}", centre),
        "none": ("1.03", centre),
    }[motion]
    return f"zoompan=z='{z}':{xy}:d=1:s={W}x{H}:fps={FPS}"


def intermediate_start(shot, src, frames):
    if shot[0][0] == "P":
        return 0.0
    src_len = frames / FPS * shot[3]
    return max(0.0, min(shot[2] * duration(src), duration(src) - src_len - 0.1))


def render_shot(shot, src, frames, out):
    ref, _, frac, speed, motion, _, _ = shot
    secs = frames / FPS
    cover = "scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,setsar=1"
    tail = f"{zoompan(motion, frames)},{GRADE},format=yuv420p"
    if ref[0] == "P":
        cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{secs + 0.5:.3f}",
               "-i", str(src), "-vf", f"{cover},{tail}"]
    else:
        src_len = secs * speed
        start = intermediate_start(shot, src, frames)
        cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{src_len + 0.3:.3f}", "-i", str(src),
               "-vf", f"setpts=(PTS-STARTPTS)/{speed},fps={FPS},{cover},{tail}"]
    cmd += ["-frames:v", str(frames), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
            "-r", str(FPS), str(out)]
    run(cmd)
    return intermediate_start(shot, src, frames)


def text(tmp, name, s, font, size, x, y, t0, t1, fade=0.6, rise=0, colour="white"):
    """drawtext dengan fade + ease-out (gerak masuk sejauh `rise` px)."""
    f = tmp / f"{name}.txt"
    f.write_text(s)
    e = f"(1-pow(1-clip((t-{t0})/{fade}\\,0\\,1)\\,3))"
    alpha = f"min({e}\\,clip(({t1}-t)/{fade}\\,0\\,1))"
    return (f"drawtext=fontfile={FONTS / font}:textfile={f}:fontsize={size}:fontcolor={colour}"
            f":shadowcolor=black@0.35:shadowx=0:shadowy=2"
            f":x={x}:y=({y})+{rise}*(1-{e}):alpha={alpha}:enable=between(t\\,{t0}\\,{t1})")


def spaced(s):
    return " ".join(s)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("footage", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("east_coast_diaries.mp4"))
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--cache", type=Path, help="folder simpan klip perantaraan (render semula lebih laju)")
    args = p.parse_args()
    videos = sorted((args.footage / "videos").glob("*.mp4"))
    photos = sorted((args.footage / "photos").glob("*.jpg"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        music = tmp / "music.mp3"
        urllib.request.urlretrieve(MUSIC_URL, music)
        beats = beat_times(music)
        bt = lambda k: beats[k]  # noqa: E731

        # Garis masa dalam frame: sempadan shot jatuh tepat pada beat.
        total_f = round(TOTAL * FPS)
        bounds, k = [0], 0
        for shot in SHOTS[:-1]:
            k += shot[1]
            bounds.append(round(bt(k) * FPS))
        trans = [0] + [max(2, round(s[5][1] * FPS)) if s[5][0] != "cut" else 1 for s in SHOTS[1:]]
        starts = [b - (d // 2) for b, d in zip(bounds, trans)]
        starts[0] = 0
        ends = [starts[i + 1] + trans[i + 1] for i in range(len(SHOTS) - 1)] + [total_f]
        frames = [e - s for s, e in zip(starts, ends)]
        print(f"Drop 1 @ {bt(DROPS[0]):.2f}s, drop 2 @ {bt(DROPS[1]):.2f}s, {len(SHOTS)} shot")

        cache = args.cache or tmp
        cache.mkdir(parents=True, exist_ok=True)

        def job(i):
            shot = SHOTS[i]
            src = (videos if shot[0][0] == "V" else photos)[int(shot[0][1:]) - 1]
            out = cache / f"s{i:03d}_{shot[0]}_{frames[i]}_{shot[2]}_{shot[3]}_{shot[4]}.mp4"
            shot_files[i] = out
            if out.exists():
                return src, intermediate_start(shot, src, frames[i])
            part = out.with_suffix(".part.mp4")
            start = render_shot(shot, src, frames[i], part)
            part.rename(out)
            print(f"  [{i + 1}/{len(SHOTS)}] {shot[0]:>4} {frames[i] / FPS:5.2f}s {shot[4]}")
            return src, start

        shot_files = {}
        with ThreadPoolExecutor(args.workers) as pool:
            sources = list(pool.map(job, range(len(SHOTS))))

        # --- SFX sintetik ---
        whoosh, boom = tmp / "whoosh.wav", tmp / "boom.wav"
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=color=pink:d=0.6:a=0.9:r=48000",
             "-af", "highpass=f=400,lowpass=f=6000,afade=t=in:d=0.38:curve=exp,"
                    "afade=t=out:st=0.38:d=0.22:curve=exp,volume=0.5,aformat=channel_layouts=stereo",
             str(whoosh)])
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=48:d=1.6:r=48000",
             "-af", "volume=2.2,afade=t=out:st=0.05:d=1.5:curve=exp,lowpass=f=160,"
                    "aformat=channel_layouts=stereo", str(boom)])

        # --- Video: rantai xfade ---
        inputs, fc = [], []
        for i in range(len(SHOTS)):
            inputs += ["-i", str(shot_files[i])]
            fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
        last = "v0"
        for i in range(1, len(SHOTS)):
            kind = SHOTS[i][5][0]
            kind = "fade" if kind == "cut" else kind
            # offset setengah frame lebih awal supaya pembundaran tak melepasi frame sebenar
            fc.append(f"[{last}][v{i}]xfade=transition={kind}:duration={trans[i] / FPS:.6f}"
                      f":offset={(starts[i] - 0.5) / FPS:.6f}[x{i}]")
            last = f"x{i}"

        d1, outro = bt(DROPS[0]), bt(OUTRO_BEAT)
        # 0 = letterbox penuh, 1 = terbuka. Terbuka pada drop 1, tertutup semula pada penutup.
        r = (f"if(lt(t\\,{d1:.3f})\\,0\\,if(lt(t\\,{outro:.3f})\\,min(1\\,(t-{d1:.3f})/0.5)"
             f"\\,1-min(1\\,(t-{outro:.3f})/1.2)))")
        fc.append(f"[{last}]vignette=angle=PI/5,noise=alls=5:allf=t[g0]")
        fc.append(f"color=c=black:s={W}x{BAR}:r={FPS}:d={TOTAL},split[bt][bb]")
        fc.append(f"[g0][bt]overlay=x=0:y=-{BAR}*{r}[g1]")
        fc.append(f"[g1][bb]overlay=x=0:y=H-{BAR}+{BAR}*{r}[g2]")
        base = "g2"

        def line(name, width, x, y, a, b, fade=0.6):
            nonlocal base
            fc.append(f"color=c=white:s={width}x2:r={FPS}:d={TOTAL},format=rgba,colorchannelmixer=aa=0.85,"
                      f"fade=t=in:st={a:.3f}:d={fade}:alpha=1,fade=t=out:st={b - fade:.3f}:d={fade}:alpha=1"
                      f"[{name}]")
            fc.append(f"[{base}][{name}]overlay=x={x}:y={y}:enable=between(t\\,{a:.3f}\\,{b:.3f})[{name}o]")
            base = f"{name}o"

        t0, t1 = bt(9), bt(25)
        line("lt", 520, "(W-w)/2", "H/2+20", t0 + 0.6, t1, 0.9)
        layers = [
            text(tmp, "t1", spaced("SEPTEMBER 2026"), "Montserrat-Light.ttf", 26,
                 "(w-text_w)/2", "h/2-150", t0, t1, 0.8, 20),
            text(tmp, "t2", spaced("EAST COAST"), "Montserrat-SemiBold.ttf", 118,
                 "(w-text_w)/2", "h/2-95", t0 + 0.3, t1, 0.9, 30),
            text(tmp, "t3", spaced("DIARIES"), "Montserrat-ExtraLight.ttf", 58,
                 "(w-text_w)/2", "h/2+45", t0 + 0.7, t1, 0.9, 30),
        ]
        for n, (beat, num, name) in enumerate(CHAPTERS):
            s = bt(beat) + 0.15
            slide = f"60*pow(1-clip((t-{s + 0.1:.3f})/0.6\\,0\\,1)\\,3)"
            line(f"lc{n}", 60, f"120-{slide}", "H-172", s, s + 3.2, 0.5)
            layers += [
                text(tmp, f"c{n}a", num, "Montserrat-Light.ttf", 30, f"120-{slide}", "h-215",
                     s, s + 3.2, 0.5, 0),
                text(tmp, f"c{n}b", spaced(name), "Montserrat-SemiBold.ttf", 40, f"120-{slide}", "h-155",
                     s + 0.1, s + 3.2, 0.6, 0),
            ]
        o0 = outro + 1.5
        layers += [
            text(tmp, "o1", spaced("SEE YOU"), "Montserrat-ExtraLight.ttf", 64,
                 "(w-text_w)/2", "h/2-70", o0, TOTAL - 0.8, 0.9, 25),
            text(tmp, "o2", spaced("ON THE NEXT ONE"), "Montserrat-SemiBold.ttf", 76,
                 "(w-text_w)/2", "h/2+10", o0 + 0.4, TOTAL - 0.8, 0.9, 25),
        ]
        fc.append(f"[{base}]{','.join(layers)},fade=t=in:d=1.2,fade=t=out:st={TOTAL - 1.6}:d=1.6,"
                  f"format=yuv420p[vout]")

        # --- Audio: muzik + bunyi asal terpilih + SFX ---
        n = len(SHOTS)
        ai = n
        inputs += ["-i", str(music), "-i", str(whoosh), "-i", str(boom)]
        mix = []
        fc.append(f"[{ai}:a]atrim=0:{TOTAL},asetpts=PTS-STARTPTS,"
                  f"afade=t=out:st={TOTAL - 4}:d=4,volume=0.9[mus]")
        mix.append("[mus]")
        whips = [i for i in range(1, n) if SHOTS[i][5][0] in ("hblur", "smoothleft", "smoothup", "zoomin")]
        if whips:
            fc.append(f"[{ai + 1}:a]asplit={len(whips)}" + "".join(f"[w{j}]" for j in range(len(whips))))
            for j, i in enumerate(whips):
                ms = max(0, round((bounds[i] / FPS - 0.38) * 1000))
                fc.append(f"[w{j}]adelay={ms}|{ms}[wd{j}]")
                mix.append(f"[wd{j}]")
        fc.append(f"[{ai + 2}:a]asplit={len(DROPS)}" + "".join(f"[b{j}]" for j in range(len(DROPS))))
        for j, beat in enumerate(DROPS):
            ms = round(bt(beat) * 1000)
            fc.append(f"[b{j}]adelay={ms}|{ms}[bd{j}]")
            mix.append(f"[bd{j}]")
        nat_idx = len(inputs) // 2
        for i, shot in enumerate(SHOTS):
            if shot[6] and shot[0][0] == "V":
                src, start = sources[i]
                secs = frames[i] / FPS
                inputs += ["-ss", f"{start:.3f}", "-t", f"{secs:.3f}", "-i", str(src)]
                ms = round(starts[i] / FPS * 1000)
                fc.append(f"[{nat_idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
                          f"afade=t=in:d=0.6,afade=t=out:st={secs - 0.8:.3f}:d=0.8,"
                          f"volume={shot[6]},adelay={ms}|{ms}[n{i}]")
                mix.append(f"[n{i}]")
                nat_idx += 1
        fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,"
                  f"alimiter=limit=0.89,aresample=48000[aout]")

        script = tmp / "graph.txt"
        script.write_text(";\n".join(fc))
        print("Menyusun video akhir...")
        run(["ffmpeg", "-y", *inputs, "-filter_complex_script", str(script),
             "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-t", f"{TOTAL}",
             "-movflags", "+faststart", str(args.output)])
    print(f"Siap: {args.output} ({duration(args.output):.1f}s)")


if __name__ == "__main__":
    main()
