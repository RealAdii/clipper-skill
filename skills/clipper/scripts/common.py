import glob, json, os, platform, subprocess, sys

MODEL = "mlx-community/whisper-large-v3-turbo"        # mlx backend (Apple Silicon)
FW_MODEL = os.environ.get("CLIPPER_MODEL", "large-v3-turbo")  # faster-whisper backend (Windows, Linux, Intel Mac)
DASHES = ("—", "–")

# Windows consoles default to a legacy code page; transcripts and captions are UTF-8.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def work(argv):
    if len(argv) < 2:
        sys.exit(f"usage: {os.path.basename(argv[0])} <work dir> ...")
    w = os.path.abspath(os.path.expanduser(argv[1]))
    if not os.path.isdir(w):
        sys.exit(f"no such work dir: {w}")
    return w


def source(w):
    f = [p for p in glob.glob(os.path.join(w, "source.*")) if not p.endswith(".part")]
    if f:
        return f[0]
    # fetch.py could not link a local file (no symlink rights, different drive): use it in place
    ref = os.path.join(w, "source_ref.txt")
    if os.path.exists(ref):
        p = open(ref, encoding="utf-8").read().strip()
        if os.path.isfile(p):
            return p
    sys.exit("no source.* in work dir, run fetch.py first")


def plan(w):
    p = os.path.join(w, "plan.json")
    if not os.path.exists(p):
        sys.exit("no plan.json, write it from transcript.txt first (see SKILL.md step 3)")
    d = json.load(open(p, encoding="utf-8"))
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
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path], capture_output=True,
                         encoding="utf-8", errors="replace").stderr
    h, m, s = err.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def ff(*args):
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def apple_silicon():
    return sys.platform == "darwin" and platform.machine() == "arm64"


def backend():
    """mlx on Apple Silicon, faster-whisper everywhere else. CLIPPER_BACKEND=mlx|faster-whisper overrides."""
    b = os.environ.get("CLIPPER_BACKEND")
    if b:
        return b
    return "mlx" if apple_silicon() else "faster-whisper"


def whisper(path, words=False):
    """Transcribe an audio file. Returns the mlx_whisper result shape on every backend:
    {"text": str, "segments": [{"start", "end", "text", "words": [{"word", "start", "end"}]}]}"""
    if backend() == "mlx":
        import mlx_whisper
        return mlx_whisper.transcribe(path, path_or_hf_repo=MODEL, language="en", word_timestamps=words)
    segs, _ = _fw_model().transcribe(path, language="en", word_timestamps=words)
    out = []
    for s in segs:  # a generator: decoding happens here
        d = {"start": s.start, "end": s.end, "text": s.text}
        if words:
            d["words"] = [{"word": x.word, "start": x.start, "end": x.end} for x in (s.words or [])]
        out.append(d)
    return {"text": "".join(s["text"] for s in out), "segments": out}


_FW = None


def _cuda_dlls():
    # Windows: the nvidia-cublas-cu12 / nvidia-cudnn-cu12 pip wheels ship their DLLs in site-packages/nvidia/*/bin,
    # which ctranslate2 does not search on its own.
    if sys.platform != "win32":
        return
    import site
    roots = site.getsitepackages() + [site.getusersitepackages()]
    for r in roots:
        for d in glob.glob(os.path.join(r, "nvidia", "*", "bin")):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def _fw_model():
    global _FW
    if _FW is not None:
        return _FW
    from faster_whisper import WhisperModel
    import ctranslate2
    dev = os.environ.get("CLIPPER_DEVICE") or ("cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu")
    if dev == "cuda":
        _cuda_dlls()
        try:
            _FW = WhisperModel(FW_MODEL, device="cuda", compute_type="float16")
            list(_FW.transcribe(_silence(), language="en")[0])  # loads cuBLAS/cuDNN now, not mid-episode
            return _FW
        except Exception as e:  # missing CUDA libraries: carry on, slower
            print(f"faster-whisper: CUDA unavailable ({(str(e) or type(e).__name__).splitlines()[0]}), using CPU", file=sys.stderr)
    _FW = WhisperModel(FW_MODEL, device="cpu", compute_type="int8")
    return _FW


def _silence():
    import numpy as np
    return np.zeros(16000, dtype=np.float32)
