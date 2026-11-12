# usage: cut.py <work dir> [--only name[,name]] [--jobs 3]
# Cuts every clip in plan.json to <work>/clips/, plus the trimmed full episode if plan.episode is set.
import os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, source, plan, ff, duration

w = work(sys.argv)
p = plan(w)
src = source(w)
total = duration(src)
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
pre, post = p.get("pad", [0.3, 0.8])
os.makedirs(os.path.join(w, "clips"), exist_ok=True)
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart"]


def cut(name, s, e, out):
    s, e = max(0.0, s), min(total, e)
    d = e - s
    fade = f"afade=t=in:d=0.05,afade=t=out:st={max(0.0, d - 0.25):.3f}:d=0.25"
    ff("-ss", f"{s:.3f}", "-i", src, "-t", f"{d:.3f}", *ENC, "-af", fade, out)
    return f"ok {name} {d:.1f}s"


tasks = []
for c in p["clips"]:
    if only and c["name"] not in only:
        continue
    tasks.append((c["name"], c["start"] - pre, c["end"] + post, os.path.join(w, "clips", c["name"] + ".mp4")))
ep = p.get("episode")
if ep and (not only or "episode" in only):
    tasks.append(("full_episode", ep.get("trim_start") or 0.0, ep.get("trim_end") or total,
                  os.path.join(w, "full_episode.mp4")))
if only and not tasks:
    sys.exit(f"--only matched nothing: {sorted(only)}")
with ThreadPoolExecutor(jobs) as ex:
    for r in ex.map(lambda t: cut(*t), tasks):
        print(r, flush=True)
