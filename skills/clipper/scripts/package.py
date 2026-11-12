# usage: package.py <work dir> [--dest ~/Desktop] [--name "folder name"]
# Copies clips, full episode, transcript and clips.txt into <dest>/<name>/ and zips it to <dest>/<name>.zip.
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, plan, mmss, duration, no_dashes

w = work(sys.argv)
p = plan(w)
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
dest = os.path.expanduser(arg("--dest", "~/Desktop"))
name = arg("--name", p["slug"])
out = os.path.join(dest, name)
marker = os.path.join(out, ".clipper")
if os.path.exists(out) and not os.path.exists(marker):
    sys.exit(f"{out} exists and was not made by clipper, pick another --name")
if os.path.exists(out):
    shutil.rmtree(out)
os.makedirs(out)
open(marker, "w").write(w + "\n")

src_ref = open(os.path.join(w, "source_ref.txt")).read().strip() if os.path.exists(os.path.join(w, "source_ref.txt")) else ""
lines = [p["title"] + ", clips", f"source: {p.get('source_url') or src_ref}", ""]
ep = p.get("episode")
if ep and os.path.exists(os.path.join(w, "full_episode.mp4")):
    epname = p["slug"] + "_full_episode.mp4"
    shutil.copy2(os.path.join(w, "full_episode.mp4"), os.path.join(out, epname))
    lines += [epname, f"  length {mmss(duration(os.path.join(out, epname)))}", ""]
    if ep.get("caption"):
        lines += ["  caption:", *["    " + x for x in ep["caption"].split("\n")], ""]
    if ep.get("timestamps"):
        lines += ["  timestamps:", *[f"    {t} {l}" for t, l in ep["timestamps"]], ""]
for c in p["clips"]:
    f = os.path.join(w, "clips", c["name"] + ".mp4")
    if not os.path.exists(f):
        sys.exit(f"missing clip {c['name']}, run cut.py")
    shutil.copy2(f, out)
    lines += [c["name"] + ".mp4",
              f"  source {mmss(c['start'])} to {mmss(c['end'])}, length {mmss(duration(f))}"]
    if c.get("hook"):
        lines.append("  " + c["hook"])
    if c.get("caption"):
        lines += ["  caption:", *["    " + x for x in c["caption"].split("\n")]]
    lines.append("")
text = "\n".join(lines)
no_dashes(text, "clips.txt")
open(os.path.join(out, "clips.txt"), "w").write(text)
if os.path.exists(os.path.join(w, "transcript.txt")):
    shutil.copy2(os.path.join(w, "transcript.txt"), out)
z = out + ".zip"
if os.path.exists(z):
    os.remove(z)
subprocess.run(["zip", "-qr", "-X", z, name, "-x", "*.DS_Store", "-x", "*/.clipper"], cwd=dest, check=True)
print("folder:", out)
print("zip:   ", z, f"({os.path.getsize(z) / 1e6:.0f} MB)")
