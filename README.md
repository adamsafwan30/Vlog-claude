# Vlog-claude

Skrip untuk menjana vlog berdurasi **2 minit** daripada folder video/gambar.

## Cara guna

1. Muat turun folder Google Drive (contoh dengan `gdown`):
   ```bash
   pip install gdown
   gdown --folder "https://drive.google.com/drive/folders/16VGUS115utPNFMt-SvY7rLJ7MgdOBRO-" -O footage
   ```
2. Jana vlog (perlukan `ffmpeg`):
   ```bash
   python3 make_vlog.py footage -o vlog.mp4            # 1920x1080, 120 saat
   python3 make_vlog.py footage -o vlog.mp4 --vertical # 1080x1920 untuk Reels/TikTok
   python3 make_vlog.py footage --music lagu.mp3       # dengan muzik latar
   ```

Klip disusun ikut nama fail, masa dibahagi sama rata (video pendek guna panjang penuh),
setiap klip ada fade masuk/keluar, gambar diberi kesan zoom perlahan, dan fail audio
dalam folder dijadikan muzik latar secara automatik.

Sentuhan kreatif:
- Gred warna hangat gaya vlog (kontras, saturasi, vignette).
- Latar kabur menggantikan jalur hitam bila nisbah aspek klip berbeza.
- Tajuk pembuka + tarikh, dan teks penutup "Terima kasih kerana menonton!".
  Ubah dengan `--title`, `--subtitle`, `--outro`, atau buang dengan `--no-text`.
