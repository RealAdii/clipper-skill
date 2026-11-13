# usage: transcribe.py <work dir>   -> full.wav, segments.json, transcript.txt
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, source, ff, whisper, mmss, duration

w = work(sys.argv)
wav = os.path.join(w, "full.wav")
ff("-i", source(w), "-vn", "-ac", "1", "-ar", "16000", wav)
r = whisper(wav)
total = duration(wav)
segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
        for s in r["segments"] if s["text"].strip() and s["start"] < total - 0.5]
# whisper sometimes loops on the tail ("and that's it." x20): collapse runs of the same line
out = []
for s in segs:
    if len(out) >= 2 and s["text"] == out[-1]["text"] == out[-2]["text"]:
        out[-1]["end"] = s["end"]
        continue
    out.append(s)
segs = out
json.dump(segs, open(os.path.join(w, "segments.json"), "w", encoding="utf-8"), indent=0)
with open(os.path.join(w, "transcript.txt"), "w", encoding="utf-8") as f:
    for s in segs:
        f.write(f"[{mmss(s['start'])} {s['start']:.1f}-{s['end']:.1f}] {s['text']}\n")
print(f"{len(segs)} segments, {mmss(segs[-1]['end']) if segs else '0:00'} of speech -> {w}/transcript.txt")
