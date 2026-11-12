# usage: words.py <work dir> <start seconds> [length=10]   word timings in absolute source seconds
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, source, ff, whisper

w = work(sys.argv)
if len(sys.argv) < 3:
    sys.exit("usage: words.py <work dir> <start seconds> [length=10]")
at = max(0.0, float(sys.argv[2]))
n = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
wav = os.path.join(tempfile.mkdtemp(), "w.wav")
ff("-ss", str(at), "-i", source(w), "-t", str(n), "-vn", "-ac", "1", "-ar", "16000", wav)
r = whisper(wav, words=True)
for s in r["segments"]:
    print(" ".join(f"{x['word'].strip()}@{x['start'] + at:.2f}-{x['end'] + at:.2f}" for x in s.get("words", [])))
