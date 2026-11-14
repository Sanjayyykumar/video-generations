"""Multi-voice Kokoro speaker for dialogue (narrator + characters). Offline, resumable.
Usage: python voice/speak_cast.py CAST.py OUT_DIR   ->  OUT_DIR/<key>.wav
CAST.py defines LINES = [(key, voice, speed, text), ...]  (see voice/examples/dialogue_demo.py).
Same pause markers as speak.py:  /  //  ...   KOKORO_DIR = model folder (default: ../models)."""
import os, re, sys, importlib.util
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
spec = importlib.util.spec_from_file_location('narr', sys.argv[1]); narr = importlib.util.module_from_spec(spec); spec.loader.exec_module(narr)
out = sys.argv[2]; md = os.environ.get('KOKORO_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models'))
k = Kokoro(os.path.join(md, 'kokoro-v1.0.int8.onnx'), os.path.join(md, 'voices-v1.0.bin'))
PAUSE = {'/': .2, '//': .45, '...': .6}
def phrases(text):
    items = []
    for t in re.split(r'\s*(\.\.\.|//|/)\s*', text.strip()):
        if t in PAUSE:
            if items: items[-1][1] = PAUSE[t]
        elif t: items.append([t, 0])
    return items
def trim(a, sr):
    idx = np.where(np.abs(a) > 0.008)[0]
    if not len(idx): return a
    a = a[max(0, idx[0] - int(.02 * sr)): idx[-1] + int(.05 * sr)]
    n = int(.012 * sr); a[:n] *= np.linspace(0, 1, n); a[-n:] *= np.linspace(1, 0, n); return a
os.makedirs(out, exist_ok=True)
for key, voice, speed, text in narr.LINES:
    f = os.path.join(out, key + '.wav')
    if os.path.exists(f): continue
    parts, sr = [], 24000; items = phrases(text)
    for j, (p, gap) in enumerate(items):
        q = p if p[-1] in '.,?!:' else p + ('.' if j == len(items) - 1 else ',')
        a, sr = k.create(q, voice=voice, speed=speed, lang='en-us')
        parts += [trim(a, sr), np.zeros(int(gap * sr))]
    a = np.concatenate(parts); sf.write(f + '.tmp.wav', a, sr); os.replace(f + '.tmp.wav', f)
    print(key, round(len(a) / sr, 2), flush=True)
