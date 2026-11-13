# usage: check.py <work dir> [--only name[,name]]
# For every clip: duration, the words in its first and last 5 s, first/last frames, then check/contact.jpg.
import glob, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, plan, ff, whisper, duration

w = work(sys.argv)
p = plan(w)
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
chk = os.path.join(w, "check")
os.makedirs(chk, exist_ok=True)
for c in p["clips"]:
    n = c["name"]
    if only and n not in only:
        continue
    f = os.path.join(w, "clips", n + ".mp4")
    if not os.path.exists(f):
        print(f"MISSING {n}: run cut.py")
        continue
    d = duration(f)
    ff("-ss", "0.5", "-i", f, "-frames:v", "1", "-vf", "scale=320:-2", os.path.join(chk, n + "_a.jpg"))
    ff("-sseof", "-0.6", "-i", f, "-frames:v", "1", "-vf", "scale=320:-2", os.path.join(chk, n + "_b.jpg"))
    ff("-i", f, "-t", "5", "-vn", "-ac", "1", "-ar", "16000", os.path.join(chk, n + "_head.wav"))
    ff("-sseof", "-5", "-i", f, "-vn", "-ac", "1", "-ar", "16000", os.path.join(chk, n + "_tail.wav"))
    head = whisper(os.path.join(chk, n + "_head.wav"))["text"].strip()
    tail = whisper(os.path.join(chk, n + "_tail.wav"))["text"].strip()
    flag = "  <-- long" if d > 150 else ("  <-- short" if d < 15 else "")
    print(f"{n}  {d:.1f}s{flag}\n  head: {head}\n  tail: {tail}\n", flush=True)
frames = sorted(glob.glob(os.path.join(chk, "*_[ab].jpg")))
if frames:
    rows = math.ceil(len(frames) / 4)
    # concat list rather than -pattern_type glob, which Windows builds of ffmpeg do not support
    lst = os.path.join(chk, "frames.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines("file '{}'\n".format(x.replace("\\", "/").replace("'", "'\\''")) for x in frames)
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", f"scale=320:-2,tile=4x{rows}",
       "-frames:v", "1", os.path.join(chk, "contact.jpg"))
    print("contact sheet:", os.path.join(chk, "contact.jpg"), "(pairs: first frame, last frame)")
