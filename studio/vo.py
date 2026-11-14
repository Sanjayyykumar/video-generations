"""Voice every scene line with Kokoro (offline). Resumable: existing clips are skipped.
python studio/vo.py <project>   — reads scenes.json, writes audio/vo/NN.wav and updates scene durations."""
import os, sys, soundfile as sf
from common import MODELS, load, save
proj = sys.argv[1]; sc = load(os.path.join(proj, "scenes.json"))
voice = sc.get("voice", "af_heart"); speed = sc.get("speed", 1.0); lang = sc.get("lang", "en-us")
os.makedirs(os.path.join(proj, "audio", "vo"), exist_ok=True)
k = None
for i, s in enumerate(sc["scenes"]):
    if not s.get("say"): continue
    out = os.path.join(proj, "audio", "vo", f"{i:02d}.wav")
    if not os.path.exists(out):
        if k is None:
            from kokoro_onnx import Kokoro
            k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.int8.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
        audio, sr = k.create(s["say"], voice=s.get("voice", voice), speed=speed, lang=lang); sf.write(out, audio, sr)
        print("voiced", i, s["say"][:50])
    s["vo_s"] = round(sf.info(out).duration, 2)
    s["dur"] = max(s.get("dur", 0), round(s["vo_s"] + sc.get("pad_s", 0.6), 2))
save(os.path.join(proj, "scenes.json"), sc)
