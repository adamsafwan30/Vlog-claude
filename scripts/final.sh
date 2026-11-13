ffmpeg -v error -y -f concat -safe 0 -i /tmp/claude-0/-home-user-Vlog-claude/7ac34c93-de73-549f-87c9-4a1ad456c38c/scratchpad/segs169/list.txt -i song.mp3 -filter_complex "
[0:v]tpad=stop_mode=clone:stop_duration=3.2,trim=0:120,setpts=PTS-STARTPTS,
eq=contrast=1.05:saturation=1.12:gamma=0.98,vignette=PI/5,
fade=t=in:st=0:d=0.6,fade=t=out:st=117.2:d=2.0,
drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf:text='Memori Tercipta':fontsize=100:fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:x=(w-tw)/2:y=h*0.40:alpha='if(lt(t,0.9),0,if(lt(t,1.6),(t-0.9)/0.7,if(lt(t,4.8),1,if(lt(t,5.5),(5.5-t)/0.7,0))))',
drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf:text='sehari bersama mereka  ·  11.11.2026':fontsize=48:fontcolor=white:shadowcolor=black@0.6:shadowx=2:shadowy=2:x=(w-tw)/2:y=h*0.40+140:alpha='if(lt(t,0.9),0,if(lt(t,1.6),(t-0.9)/0.7,if(lt(t,4.8),1,if(lt(t,5.5),(5.5-t)/0.7,0))))',
drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf:text='kenangan bersama…':fontsize=64:fontcolor=white:x=(w-tw)/2:y=(h-th)/2:alpha='if(lt(t,117.4),0,if(lt(t,118.4),(t-117.4),1))'[v];
[1:a]atrim=0:65.47,asetpts=PTS-STARTPTS[a1];[1:a]atrim=128.91:183.74,asetpts=PTS-STARTPTS[a2];
[a1][a2]acrossfade=d=0.3:c1=tri:c2=tri,afade=t=in:d=0.3,afade=t=out:st=116:d=4,atrim=0:120[a]" \
-map "[v]" -map "[a]" -c:v libx264 -preset slow -b:v 6000k -maxrate 9000k -bufsize 12000k -profile:v high -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k "$1"
