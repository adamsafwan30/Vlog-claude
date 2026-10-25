#!/usr/bin/env python3
"""Cantumkan video & gambar dalam satu folder menjadi vlog berdurasi tetap (default 2 minit).

Penggunaan:
    python3 make_vlog.py <folder_media> [-o vlog.mp4] [-d 120] [--vertical] [--music lagu.mp3]

- Video dan gambar disusun ikut nama fail.
- Durasi dibahagi sama rata antara klip; setiap video diambil bahagian tengahnya.
- Gambar dipaparkan dengan kesan zoom perlahan.
- Jika fail audio (mp3/m4a/wav) ada dalam folder atau diberi melalui --music,
  ia dijadikan muzik latar dan audio asal video diperlahankan.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".3gp"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".aac", ".ogg"}
FPS = 30
FADE = 0.4


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


def render_clip(src, kind, length, w, h, out):
    fade = f"fade=t=in:st=0:d={FADE},fade=t=out:st={length - FADE:.3f}:d={FADE}"
    scale = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
             f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1")
    if kind == "image":
        frames = int(length * FPS)
        vf = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=decrease,"
              f"pad={w * 2}:{h * 2}:(ow-iw)/2:(oh-ih)/2:color=black,"
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
        if music:
            print(f"Muzik latar: {music.name}")
            af = (f"[0:a]volume=0.35[orig];"
                  f"[1:a]volume=0.8,afade=t=in:st=0:d=2,afade=t=out:st={d - 3}:d=3[bg];"
                  f"[orig][bg]amix=inputs=2:duration=first:normalize=0[a]")
            run(["ffmpeg", "-y", "-i", str(joined), "-stream_loop", "-1", "-i", str(music),
                 "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-t", f"{d:.3f}", "-movflags", "+faststart",
                 str(args.output)])
        else:
            run(["ffmpeg", "-y", "-i", str(joined), "-c", "copy", "-t", f"{d:.3f}",
                 "-movflags", "+faststart", str(args.output)])
    dur, _ = probe(args.output)
    print(f"Siap: {args.output} ({dur:.1f}s)")


if __name__ == "__main__":
    main()
