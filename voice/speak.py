"""Presenter-style speech from a marked-up narration file (Kokoro, offline, resumable).

Usage: python3 speak.py NARRATION.py OUT_DIR [VOICE_SPEC] [line numbers...]
  NARRATION.py defines LINES = [(start_s, speed, text), ...] and optionally VOICE.
  Markers in text:  /  short breath (0.25 s)   //  dramatic pause (0.55 s)   ...  held beat (0.8 s)
  VOICE_SPEC: 'af_kore' or a blend 'hm_omega:0.6,am_onyx:0.4'. KOKORO_DIR = model folder (default: ../models).
Each phrase is spoken separately (continuing phrases end with a comma for an open, rising-flat tone;
the last phrase ends with a full stop for a falling finish), trimmed, and joined with the marked silence.
Output: OUT_DIR/vo_01.wav ... (24 kHz mono). Re-run to resume; finished lines are skipped.
"""
import os, re, sys, importlib.util
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

spec_file, out = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('narr', spec_file); narr = importlib.util.module_from_spec(spec); spec.loader.exec_module(narr)
voice = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].isdigit() else getattr(narr, 'VOICE', 'af_kore')
only = {int(x) for x in sys.argv[3:] if x.isdigit()}
md = os.environ.get('KOKORO_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models'))
k = Kokoro(os.path.join(md, 'kokoro-v1.0.int8.onnx'), os.path.join(md, 'voices-v1.0.bin'))
style = sum(float(w) * k.get_voice_style(v) for v, w in (p.split(':') for p in voice.split(','))) if ':' in voice else voice
PAUSE = {'/': .25, '//': .55, '...': .80}

# Pronunciation dictionary: voice/lexicon.py LEXICON = {'word': 'respelling'} plus optional LEXICON in the narration file.
LEX = {}
_lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lexicon.py')
if os.path.exists(_lp):
    _s = importlib.util.spec_from_file_location('lex', _lp); _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m); LEX.update(_m.LEXICON)
LEX.update(getattr(narr, 'LEXICON', {}))
def respell(t):
    for w, r in sorted(LEX.items(), key=lambda x: -len(x[0])):
        t = re.sub(r'(?<![\w.])' + re.escape(w) + r'(?![\w])', r.replace('\\', '\\\\'), t, flags=re.I)
    return t

def phrases(text):
    toks = re.split(r'\s*(\.\.\.|//|/)\s*', text.strip())
    items, pause = [], 0
    for t in toks:
        if t in PAUSE: items[-1][1] = PAUSE[t] if items else 0; continue
        if t: items.append([t, 0])
    return items

def trim(a, sr):
    idx = np.where(np.abs(a) > 0.008)[0]
    if not len(idx): return a
    a = a[max(0, idx[0] - int(.02 * sr)): idx[-1] + int(.05 * sr)]
    n = int(.012 * sr); a[:n] *= np.linspace(0, 1, n); a[-n:] *= np.linspace(1, 0, n)
    return a

os.makedirs(out, exist_ok=True)
for i, (st, speed, text) in enumerate(narr.LINES, 1):
    if only and i not in only: continue
    f = os.path.join(out, f'vo_{i:02}.wav')
    if os.path.exists(f): continue
    parts, sr = [], 24000
    items = phrases(respell(text))
    for j, (p, gap) in enumerate(items):
        last = j == len(items) - 1
        q = p if p[-1] in '.,?!' else (p + ('.' if last else ','))
        a, sr = k.create(q, voice=style, speed=speed, lang='en-us')
        parts += [trim(a, sr), np.zeros(int(gap * sr))]
    a = np.concatenate(parts)
    sf.write(f, a, sr); print(i, round(len(a) / sr, 2), flush=True)
