#!/bin/zsh
# Print the path of a python that has mlx-whisper. Reuses ~/liveclip/.venv, else builds ~/.cache/clipper-venv.
for p in "$CLIPPER_PY" ~/liveclip/.venv/bin/python ~/.cache/clipper-venv/bin/python; do
  [ -n "$p" ] && [ -x "$p" ] && "$p" -c "import mlx_whisper" 2>/dev/null && { echo "$p"; exit 0; }
done
for t in ffmpeg yt-dlp; do command -v $t >/dev/null || echo "missing: $t (brew install $t)" >&2; done
python3 -m venv ~/.cache/clipper-venv >&2 && ~/.cache/clipper-venv/bin/pip install -q mlx-whisper >&2 || { echo "venv setup failed" >&2; exit 1; }
echo ~/.cache/clipper-venv/bin/python
