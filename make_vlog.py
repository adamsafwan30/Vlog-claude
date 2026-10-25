#!/usr/bin/env python3
"""Cantumkan video & gambar dalam satu folder menjadi vlog berdurasi tetap (default 2 minit).

Penggunaan:
    python3 make_vlog.py <folder_media> [-o vlog.mp4] [-d 120] [--vertical] [--music lagu.mp3]

- Video dan gambar disusun ikut nama fail.
- Durasi dibahagi sama rata antara klip; setiap video diambil bahagian tengahnya.
- Gambar dipaparkan dengan kesan zoom perlahan.
- Jika fail audio (mp3/m4a/wav) ada dalam folder atau diberi melalui --music,
  ia dijadikan muzik latar dan audio asal video diperlahankan.
- Gred warna "vlog" yang hangat, tajuk pembuka dan teks penutup (--no-text untuk buang).
"""
import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".3gp"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac", ".ogg"}
FPS = 30
FADE = 0.4
BULAN = ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
         "Ogos", "September", "Oktober", "November", "Disember"]
GRADE = "eq=contrast=1.06:saturation=1.18:gamma=1.02,colorbalance=rs=0.03:bs=-0.03,vignette=PI/5"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    return duration, has_audio


def fill(w, h):
    """Muatkan ke w x h dengan latar kabur (bukan jalur hitam) bila nisbah aspek berbeza."""
    return (f"split[a][b];[a]scale={w // 4}:{h // 4}:force_original_aspect_ratio=increase,"
            f"crop={w // 4}:{h // 4},boxblur=10:2,scale={w}:{h},eq=brightness=-0.08[bg];"
            f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")


def render_clip(src, kind, length, w, h, out):
    fade = f"fade=t=in:st=0:d={FADE},fade=t=out:st={length - FADE:.3f}:d={FADE}"
    scale = fill(w, h)
    if kind == "image":
        frames = int(length * FPS)
        vf = (f"{fill(w * 2, h * 2)},"
              f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:s={w}x{h}:fps={FPS}"
              f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',setsar=1,{fade}")
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(src),
             "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
             "-t", f"{length:.3f}", "-vf", vf, "-r", str(FPS),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)])
        return
    duration, has_audio = probe(src)
    start = max(0.0, (duration - length) / 2)
    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(src)]
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", f"{length:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    afade = f"afade=t=in:st=0:d={FADE},afade=t=out:st={length - FADE:.3f}:d={FADE}"
    cmd += ["-map", "0:v:0", "-map", "0:a:0" if has_audio else "1:a:0",
            "-vf", f"{scale},fps={FPS},{fade}", "-af", f"aresample=44100,{afade}",
            "-ac", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-t", f"{length:.3f}", str(out)]
    run(cmd)


def find_font(bold=True):
    pattern = "Inter:style=Bold" if bold else "Inter:style=Regular"
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", pattern],
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except (OSError, subprocess.CalledProcessError):
        return None


def text_layer(tmp, name, text, size, y, start, end, font):
    """drawtext dengan fade masuk/keluar; teks ditulis ke fail supaya tak perlu escape."""
    textfile = tmp / f"{name}.txt"
    textfile.write_text(text)
    alpha = (f"if(lt(t,{start}),0,if(lt(t,{start + 0.8}),(t-{start})/0.8,"
             f"if(lt(t,{end - 0.8}),1,if(lt(t,{end}),({end}-t)/0.8,0))))")
    font_opt = f"fontfile={font}:" if font else ""
    return (f"drawtext={font_opt}textfile={textfile}:fontsize={size}:fontcolor=white"
            f":shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-text_w)/2:y={y}:alpha='{alpha}'")


def allocate(media, total):
    """Bahagi masa sama rata; video pendek guna panjang sebenar, baki diberi kepada klip lain."""
    caps = [probe(src)[0] if kind == "video" else float("inf") for src, kind in media]
    lengths = [0.0] * len(media)
    open_idx = list(range(len(media)))
    remaining = total
    while open_idx:
        share = remaining / len(open_idx)
        short = [i for i in open_idx if caps[i] < share]
        if not short:
            for i in open_idx:
                lengths[i] = share
            return lengths
        for i in short:
            lengths[i] = caps[i]
            remaining -= caps[i]
            open_idx.remove(i)
    if remaining > 0.01:
        print(f"Amaran: jumlah media hanya {total - remaining:.1f}s, kurang daripada {total:.0f}s.")
    return lengths


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=Path)
    p.add_argument("-o", "--output", type=Path, default=Path("vlog.mp4"))
    p.add_argument("-d", "--duration", type=float, default=120.0, help="durasi saat (default 120)")
    p.add_argument("--vertical", action="store_true", help="format 1080x1920 (Reels/TikTok)")
    p.add_argument("--music", type=Path, help="fail muzik latar")
    p.add_argument("--title", default="Vlog Saya", help="tajuk pembuka")
    p.add_argument("--subtitle", help="sari kata tajuk (default: tarikh hari ini)")
    p.add_argument("--outro", default="Terima kasih kerana menonton!", help="teks penutup")
    p.add_argument("--no-text", action="store_true", help="tanpa tajuk/penutup")
    args = p.parse_args()

    out_path = args.output.resolve()
    files = sorted(f for f in args.folder.rglob("*") if f.is_file() and f.resolve() != out_path)
    media = [(f, "video") for f in files if f.suffix.lower() in VIDEO_EXT]
    media += [(f, "image") for f in files if f.suffix.lower() in IMAGE_EXT]
    media.sort(key=lambda m: m[0].name.lower())
    if not media:
        sys.exit(f"Tiada video/gambar dalam {args.folder}")
    music = args.music or next((f for f in files if f.suffix.lower() in AUDIO_EXT), None)

    w, h = (1080, 1920) if args.vertical else (1920, 1080)
    if args.duration / len(media) < 1.5:
        media = media[:int(args.duration // 1.5)]
        print(f"Terlalu banyak fail; guna {len(media)} fail pertama sahaja.")
    lengths = allocate(media, args.duration)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, ((src, kind), length) in enumerate(zip(media, lengths)):
            out = tmp / f"part{i:03d}.mp4"
            print(f"[{i + 1}/{len(media)}] {src.name} ({kind}, {length:.1f}s)")
            render_clip(src, kind, length, w, h, out)
            parts.append(out)
        listfile = tmp / "list.txt"
        listfile.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = tmp / "joined.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-c", "copy", str(joined)])

        d = args.duration
        vf = GRADE
        if not args.no_text:
            today = date.today()
            subtitle = args.subtitle or f"{today.day} {BULAN[today.month - 1]} {today.year}"
            big, small = (h // 12, h // 30) if not args.vertical else (w // 14, w // 28)
            bold, regular = find_font(True), find_font(False)
            vf += "," + ",".join([
                text_layer(tmp, "title", args.title, big, f"h*0.42-{big}/2", 0.5, 5.0, bold),
                text_layer(tmp, "subtitle", subtitle, small, f"h*0.42+{big}*0.7", 1.0, 5.0, regular),
                text_layer(tmp, "outro", args.outro, small * 3 // 2, "h*0.45", d - 5, d - 0.3, bold),
            ])
        cmd = ["ffmpeg", "-y", "-i", str(joined)]
        if music:
            print(f"Muzik latar: {music.name}")
            cmd += ["-stream_loop", "-1", "-i", str(music)]
            fc = (f"[0:v]{vf}[v];[0:a]volume=0.35[orig];"
                  f"[1:a]volume=0.8,afade=t=in:st=0:d=2,afade=t=out:st={d - 3}:d=3[bg];"
                  f"[orig][bg]amix=inputs=2:duration=first:normalize=0[a]")
        else:
            fc = f"[0:v]{vf}[v];[0:a]anull[a]"
        cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-t", f"{d:.3f}", "-movflags", "+faststart",
                str(args.output)]
        run(cmd)
    dur, _ = probe(args.output)
    print(f"Siap: {args.output} ({dur:.1f}s)")


if __name__ == "__main__":
    main()
