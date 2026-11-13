# usage: fetch.py <url or local file> <work dir>
# Local files are linked as source.<ext> (symlink, else hard link, else used in place via source_ref.txt).
# URLs go through yt-dlp (CLIPPER_COOKIES=chrome if a login is needed).
import glob, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401  (UTF-8 console on Windows)

if len(sys.argv) < 3:
    sys.exit("usage: fetch.py <url|file> <work dir>")
src, work = sys.argv[1], os.path.abspath(os.path.expanduser(sys.argv[2]))
os.makedirs(work, exist_ok=True)
for f in glob.glob(os.path.join(work, "source.*")):
    os.remove(f)
ref = open(os.path.join(work, "source_ref.txt"), "w", encoding="utf-8")

if os.path.isfile(os.path.expanduser(src)):
    a = os.path.abspath(os.path.expanduser(src))
    link = os.path.join(work, "source" + os.path.splitext(a)[1].lower())
    try:
        os.symlink(a, link)        # Windows needs Developer Mode or admin for this
    except OSError:
        try:
            os.link(a, link)       # same drive: a hard link, no copy
        except OSError:
            link = a               # common.source() falls back to source_ref.txt
    ref.write(a + "\n")
else:
    ytdlp = [shutil.which("yt-dlp")] if shutil.which("yt-dlp") else [sys.executable, "-m", "yt_dlp"]
    cook = ["--cookies-from-browser", os.environ["CLIPPER_COOKIES"]] if os.environ.get("CLIPPER_COOKIES") else []
    r = subprocess.run([*ytdlp, "--no-warnings", *cook, "-f", "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b",
                        "--merge-output-format", "mp4", "-o", os.path.join(work, "source.%(ext)s"), src])
    if r.returncode:
        sys.exit(r.returncode)
    ref.write(src + "\n")
    got = [f for f in glob.glob(os.path.join(work, "source.*")) if not f.endswith(".part")]
    if not got:
        sys.exit(f"no source file landed in {work}")
    link = got[0]
ref.close()

err = subprocess.run(["ffmpeg", "-hide_banner", "-i", link], capture_output=True,
                     encoding="utf-8", errors="replace").stderr
for line in err.splitlines():
    if "Duration" in line or "Stream #" in line:
        print(line.strip())
print(f"size: {os.path.getsize(link) / 1e6:.0f} MB")
print("source:", link)
