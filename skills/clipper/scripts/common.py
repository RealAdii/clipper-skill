import glob, json, os, subprocess, sys

MODEL = "mlx-community/whisper-large-v3-turbo"
DASHES = ("—", "–")


def work(argv):
    if len(argv) < 2:
        sys.exit(f"usage: {os.path.basename(argv[0])} <work dir> ...")
    w = os.path.abspath(os.path.expanduser(argv[1]))
    if not os.path.isdir(w):
        sys.exit(f"no such work dir: {w}")
    return w


def source(w):
    f = [p for p in glob.glob(os.path.join(w, "source.*")) if not p.endswith(".part")]
    if not f:
        sys.exit("no source.* in work dir, run fetch.sh first")
    return f[0]


def plan(w):
    p = os.path.join(w, "plan.json")
    if not os.path.exists(p):
        sys.exit("no plan.json, write it from transcript.txt first (see SKILL.md step 3)")
    d = json.load(open(p))
    no_dashes(json.dumps(d, ensure_ascii=False), "plan.json")
    names = [c["name"] for c in d["clips"]]
    if len(set(names)) != len(names):
        sys.exit("duplicate clip names in plan.json")
    for c in d["clips"]:
        if c["end"] <= c["start"]:
            sys.exit(f"{c['name']}: end <= start")
    return d


def no_dashes(text, where):
    if any(x in text for x in DASHES):
        sys.exit(f"em/en dash found in {where}, rewrite it with a comma, colon or period")


def mmss(t):
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def duration(path):
    # ffmpeg only (ffprobe is not always installed next to it)
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    h, m, s = err.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def ff(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def whisper(path, words=False):
    import mlx_whisper
    return mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, language="en", word_timestamps=words)
