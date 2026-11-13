# Vlog-claude

`vlog_memori_tercipta.mp4` — 2:00 landscape vlog (1920x1080 16:9, 30fps), music: *Memori Tercipta* (Shila Amzah).

Structure (synced to the song):
| Time | Song | Footage |
|---|---|---|
| 0:00–0:36 | Intro + verse 1 | Overhead-style hyperlapse of the shift with speed ramps to 1x when someone looks at the camera (style of the reference video) |
| 0:36–1:05 | Chorus 1 | Real-time: jokes, laughs and selfies with the team |
| 1:05–1:27 | Bridge ("Yang terpahit jua termanis…") | Late-shift hyperlapse → food arriving at the table |
| 1:27–2:00 | Final chorus + fade | Eating & drinking together, the team at the table, goodbye wave |

The song is edited as `song[0:65.47] + song[128.91:183.74]` (beat-matched crossfade), cuts are snapped to the beat grid.
`scripts/` holds the ffmpeg pipeline used to build it (build.py → pieces, render.py → clips, final.sh → grade/titles/audio).
