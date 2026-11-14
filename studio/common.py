import json, os, shutil, subprocess, sys
ROOT = os.environ.get("VIDEO_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")
def run(cmd, **kw):
    print("$", " ".join(map(str, cmd))[:300]); r = subprocess.run(cmd, **kw)
    if r.returncode: sys.exit(f"command failed ({r.returncode})")
def ffprobe_dur(p):
    out = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout
    return float(out.strip() or 0)
def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
def need(tool):
    if not shutil.which(tool): sys.exit(f"missing {tool}: run: python studio/doctor.py")
