"""Health check: is this machine ready to make videos?   python studio/doctor.py"""
import importlib, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MODELS
ok = lambda b: "OK " if b else "-- "
bad = []
print("[tools]")
for t in ("ffmpeg", "ffprobe"):
    print(ok(shutil.which(t)), t); bad += [] if shutil.which(t) else [t]
print("\n[python packages]  pip install -r requirements.txt")
for m, need in (("numpy", 1), ("PIL", 1), ("soundfile", 1), ("kokoro_onnx", 1), ("faster_whisper", 0)):
    try: importlib.import_module(m); print("OK ", m)
    except Exception: print("-- ", m, "" if need else "(optional: captions)"); bad += [m] if need else []
print("\n[models]  python studio/get_models.py")
for f, need in (("kokoro-v1.0.int8.onnx", 1), ("voices-v1.0.bin", 1), ("faster-whisper-small/model.bin", 0)):
    e = os.path.exists(os.path.join(MODELS, f)); print(ok(e), f, "" if need or e else "(optional: auto-downloads on first caption run)")
    bad += [] if e or not need else [f]
print("\nREADY: try  python studio/make.py examples/hello-studio" if not bad else f"\nMISSING: {', '.join(bad)}")
sys.exit(1 if bad else 0)
