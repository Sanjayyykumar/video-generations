"""Word-timed subtitles with faster-whisper (offline). python studio/subs.py <audio.wav> <out.srt> [--lang en] [--words 3]"""
import argparse, os
from common import MODELS
p = argparse.ArgumentParser(); p.add_argument("audio"); p.add_argument("out"); p.add_argument("--lang"); p.add_argument("--words", type=int, default=3)
a = p.parse_args()
from faster_whisper import WhisperModel
local = os.path.join(MODELS, "faster-whisper-small")
m = WhisperModel(local if os.path.exists(os.path.join(local, "model.bin")) else "small", device="auto", compute_type="int8")  # "small" = download once from Hugging Face
import subprocess, numpy as np  # decode with ffmpeg: avoids PyAV version issues
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", a.audio, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, language=a.lang)
ws = [w for s in segs for w in s.words]
ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x*1000%1000):03d}"
with open(a.out, "w", encoding="utf-8") as f:
    for i in range(0, len(ws), a.words):
        g = ws[i:i + a.words]; f.write(f"{i//a.words+1}\n{ts(g[0].start)} --> {ts(g[-1].end)}\n{''.join(w.word for w in g).strip()}\n\n")
print("wrote", a.out, len(ws), "words")
