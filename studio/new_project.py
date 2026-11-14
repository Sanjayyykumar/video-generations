"""Scaffold a job folder:  python studio/new_project.py "my topic" [--format 9:16|16:9|1:1] [--length 30]"""
import argparse, datetime, os, re, shutil
from common import ROOT, save
p = argparse.ArgumentParser(); p.add_argument("title"); p.add_argument("--format", default="9:16"); p.add_argument("--length", type=int, default=30)
p.add_argument("--voice", default="kokoro:af_heart"); p.add_argument("--lang", default="en")
a = p.parse_args()
slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:40]
d = os.path.join(ROOT, "projects", f"{datetime.date.today():%Y-%m-%d}_{slug}")
for sub in ("assets", "audio/sfx", "audio/music", "src", "stills", "out"): os.makedirs(os.path.join(d, sub), exist_ok=True)
save(os.path.join(d, "brief.json"), {"goal": a.title, "audience": "", "format": a.format, "length_s": a.length,
     "language": a.lang, "style": "", "voice": a.voice, "music": "none", "sfx": False,
     "branding": {"handle": "", "end_card": True}, "deliverables": ["mp4", "srt", "thumbnail.png"]})
tpl = os.path.join(ROOT, "templates")
for f in ("scenes.json", "STORYBOARD.md", "LOG.md", "SOURCES.md"):
    if os.path.exists(os.path.join(tpl, f)): shutil.copy(os.path.join(tpl, f), d)
print("created", d, "\nnext: edit scenes.json, then  python studio/make.py", f'"{d}"')
