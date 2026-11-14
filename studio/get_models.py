"""Download the offline models into models/ (once, ~120 MB; add --captions for +460 MB Whisper).
python studio/get_models.py [--captions]"""
import os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MODELS
KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
os.makedirs(MODELS, exist_ok=True)
for f in ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin"):
    dest = os.path.join(MODELS, f)
    if os.path.exists(dest): print("have", f); continue
    print("downloading", f, "...", flush=True)
    urllib.request.urlretrieve(KOKORO + f, dest + ".part"); os.replace(dest + ".part", dest)
if "--captions" in sys.argv:
    from faster_whisper import download_model
    print("downloading faster-whisper-small ...", flush=True)
    download_model("small", output_dir=os.path.join(MODELS, "faster-whisper-small"))
print("done. next: python studio/doctor.py")
