import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
S="/tmp/claude-0/-home-user-Vlog-claude/7ac34c93-de73-549f-87c9-4a1ad456c38c/scratchpad"
exec(open(f"{S}/work/build.py").read().split("# ---- beat grid")[0])
P=json.load(open(f"{S}/work/pieces.json"))
cum=0; jobs=[]
for i,p in enumerate(P):
    f0=round(cum*FPS); cum+=p["dur"]; f1=round(cum*FPS); n=f1-f0
    if n<=0: continue
    speed=(p["b"]-p["a"])/p["dur"]
    if speed>=29.5 and p["src"] in KF:
        inp=["-ss",f"{p['a']:.3f}","-to",f"{p['b']:.3f}","-i",KF[p["src"]]]
    else:
        inp=["-ss",f"{p['a']:.3f}","-t",f"{p['b']-p['a']+0.5:.3f}","-i",SRC[p["src"]]]
    cx=p["cx"]
    vf=(f"setpts=(PTS-STARTPTS)/{speed:.6f},fps={FPS},"
        f"crop=w='trunc(ih*9/16/2)*2':h=ih:x='max(0,min(iw-ow,{cx}*iw-ow/2))':y=0,"
        f"scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=1")
    out=f"{OUT}/p{i:03d}.mp4"
    cmd=["ffmpeg","-v","error","-y",*inp,"-map","0:v:0","-vf",vf,"-frames:v",str(n),
         "-c:v","libx264","-preset","medium","-crf","16","-r",str(FPS),"-an",out]
    jobs.append((i,n,out,cmd))
def run(j):
    i,n,out,cmd=j
    key=" ".join(cmd)
    if os.path.exists(out) and os.path.exists(out+".cmd") and open(out+".cmd").read()==key:
        return i,n,str(n),""
    r=subprocess.run(cmd,capture_output=True,text=True)
    open(out+".cmd","w").write(key)
    got=subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams","v:0","-show_entries","stream=nb_read_frames","-of","csv=p=0",out],capture_output=True,text=True).stdout.strip()
    return i,n,got,r.stderr[-300:]
with ThreadPoolExecutor(int(sys.argv[1]) if len(sys.argv)>1 else 4) as ex:
    for i,n,got,err in ex.map(run,jobs):
        print(i,n,got,("ERR "+err) if err or str(n)!=got else "",flush=True)
open(f"{OUT}/list.txt","w").write("".join(f"file '{j[2]}'\n" for j in jobs))
