"""ElevenLabs narration cache: never pay twice for the same line.

Usage:
    export ELEVENLABS_API_KEY=...        (Windows: set ELEVENLABS_API_KEY=...)
    python voice/el_cache.py NARRATION.py OUT_DIR [VOICE_ID] [MODEL_ID]

NARRATION.py uses the house format: LINES = [(start_s, speed, text), ...], optional VOICE_EL = '<voice id>'.
Every line is keyed by sha1(voice_id | model_id | settings | text). On a hit the saved mp3 is copied
for free; on a miss ElevenLabs is called once and the result is stored in voice/cache/elevenlabs/.
Pause markers (/ // ...) are turned into punctuation for ElevenLabs. manifest.csv records every
clip (text, voice, date, characters billed) so you can see what you've spent.
Output: OUT_DIR/vo_01.mp3 ... ready for polish_vo.py / mix_narration.py (convert with ffmpeg if needed).
Only use voices and outputs your ElevenLabs plan licenses; this cache only reuses your own paid generations.
"""
import csv, hashlib, importlib.util, json, os, re, shutil, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'elevenlabs')
MANIFEST = os.path.join(CACHE, 'manifest.csv')
DEFAULT_VOICE = os.environ.get('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')   # 'Rachel' premade voice; pass VOICE_ID to change
DEFAULT_MODEL = 'eleven_multilingual_v2'
SETTINGS = {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.0, 'use_speaker_boost': True}

def el_text(t):
    t = re.sub(r'\s*\.\.\.\s*', '... ', t); t = re.sub(r'\s*//\s*', ' — ', t); t = re.sub(r'\s*/\s*', ', ', t)
    return re.sub(r'\s+', ' ', t).strip()

def key(voice, model, text, speed):
    s = json.dumps([voice, model, SETTINGS, round(speed, 2), text], sort_keys=True)
    return hashlib.sha1(s.encode()).hexdigest()[:16]

def generate(voice, model, text, speed, dest):
    api = os.environ.get('ELEVENLABS_API_KEY')
    if not api: sys.exit('Cache miss and ELEVENLABS_API_KEY is not set: ' + text[:60])
    body = {'text': text, 'model_id': model, 'voice_settings': dict(SETTINGS, speed=max(0.7, min(1.2, speed)))}
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128',
                                 data=json.dumps(body).encode(), method='POST',
                                 headers={'xi-api-key': api, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as f: f.write(r.read())

def main():
    spec_file, out = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location('narr', spec_file); narr = importlib.util.module_from_spec(spec); spec.loader.exec_module(narr)
    voice = sys.argv[3] if len(sys.argv) > 3 else getattr(narr, 'VOICE_EL', DEFAULT_VOICE)
    model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
    os.makedirs(os.path.join(CACHE, voice), exist_ok=True); os.makedirs(out, exist_ok=True)
    new = not os.path.exists(MANIFEST); billed = hits = 0
    with open(MANIFEST, 'a', newline='', encoding='utf-8') as mf:
        w = csv.writer(mf)
        if new: w.writerow(['key', 'voice', 'model', 'speed', 'chars', 'date', 'text'])
        for i, (st, speed, raw) in enumerate(narr.LINES, 1):
            text = el_text(raw); k = key(voice, model, text, speed)
            cached = os.path.join(CACHE, voice, k + '.mp3')
            if os.path.exists(cached): hits += 1; tag = 'cache'
            else:
                generate(voice, model, text, speed, cached); billed += len(text); tag = 'NEW (billed)'
                w.writerow([k, voice, model, speed, len(text), time.strftime('%Y-%m-%d %H:%M'), text]); mf.flush()
            shutil.copyfile(cached, os.path.join(out, f'vo_{i:02}.mp3'))
            print(f'{i:02} {tag:13} {text[:70]}', flush=True)
    print(f'\n{hits} lines from cache (free), {billed} characters billed this run.')

if __name__ == '__main__': main()
