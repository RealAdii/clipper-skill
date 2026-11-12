# usage: python3 setup.py   (python setup.py on Windows)
# Prints the path of a python that has the transcription backend: mlx-whisper on Apple Silicon, faster-whisper
# everywhere else. Reuses $CLIPPER_PY, ~/liveclip/.venv, ~/.cache/clipper-venv or this python, else builds
# ~/.cache/clipper-venv. Everything except the final path goes to stderr.
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import backend

mod, pkg = ("mlx_whisper", "mlx-whisper") if backend() == "mlx" else ("faster_whisper", "faster-whisper")
venv_py = lambda d: os.path.join(d, "Scripts", "python.exe") if os.name == "nt" else os.path.join(d, "bin", "python")
cache = os.path.expanduser("~/.cache/clipper-venv")

for p in (os.environ.get("CLIPPER_PY"), venv_py(os.path.expanduser("~/liveclip/.venv")), venv_py(cache), sys.executable):
    if p and os.path.isfile(p) and subprocess.run([p, "-c", f"import {mod}"], capture_output=True).returncode == 0:
        print(p)
        sys.exit(0)

for t, win_id in (("ffmpeg", "Gyan.FFmpeg"), ("yt-dlp", "yt-dlp.yt-dlp")):
    if not shutil.which(t):
        fix = f"brew install {t}" if sys.platform == "darwin" else (
            f"winget install {win_id}" if os.name == "nt" else f"install {t} with your package manager")
        print(f"missing: {t} ({fix})", file=sys.stderr)

pip = [venv_py(cache), "-m", "pip", "install", "-q"]
try:
    subprocess.run([sys.executable, "-m", "venv", cache], check=True, stdout=sys.stderr)
    subprocess.run([*pip, pkg], check=True, stdout=sys.stderr)
    if mod == "faster_whisper" and os.name == "nt" and shutil.which("nvidia-smi"):
        # CUDA 12 cuBLAS + cuDNN 9 for GPU transcription; common.py adds their DLL folders at runtime
        subprocess.run([*pip, "nvidia-cublas-cu12", "nvidia-cudnn-cu12==9.*"], check=True, stdout=sys.stderr)
except subprocess.CalledProcessError:
    sys.exit("venv setup failed")
print(venv_py(cache))
