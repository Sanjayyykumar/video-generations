"""One command: voice → render cards → full VO track → subtitles → mix → QC.
python studio/make.py <project> [--music audio/music/x.mp3] [--no-burn] [--skip-render]
For other engines (Remotion, Manim, HyperFrames, Lemo OpusCar, GPU Wan) render src/silent.mp4 yourself, then run with --skip-render."""
import argparse, os, subprocess, sys
from common import load, run, ffprobe_dur
p = argparse.ArgumentParser(); p.add_argument("proj"); p.add_argument("--music"); p.add_argument("--no-burn", action="store_true"); p.add_argument("--skip-render", action="store_true")
a = p.parse_args(); P = os.path.abspath(a.proj); here = os.path.dirname(os.path.abspath(__file__)); py = sys.executable
run([py, os.path.join(here, "vo.py"), P])
if not a.skip_render: run([py, os.path.join(here, "cards.py"), P])
# VO-only track for subtitles
sc = load(os.path.join(P, "scenes.json")); parts, t = [], 0.0
lst = os.path.join(P, "audio", "vo_track.wav")
ins, flt, lab = [], [], []
for i, s in enumerate(sc["scenes"]):
    w = os.path.join(P, "audio", "vo", f"{i:02d}.wav")
    if os.path.exists(w):
        ins += ["-i", w]; k = len(ins) // 2 - 1; ms = int((t + sc.get("lead_s", 0.25)) * 1000)
        flt.append(f"[{k}:a]aresample=48000,adelay={ms}|{ms}[a{k}]"); lab.append(f"[a{k}]")
    t += s.get("dur", 3)
if lab:
    flt.append(f"{''.join(lab)}amix=inputs={len(lab)}:normalize=0[o]")
    run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(flt), "-map", "[o]", lst])
    os.makedirs(os.path.join(P, "out"), exist_ok=True)
    r = subprocess.run([py, os.path.join(here, "subs.py"), lst, os.path.join(P, "out", "final.srt"), "--lang", sc.get("lang", "en-us")[:2]])
    if r.returncode: print("!! subtitles skipped (faster-whisper/model unavailable) — video is still made, just without captions")
mix = [py, os.path.join(here, "mix.py"), P] + (["--music", a.music] if a.music else []) + ([] if a.no_burn else ["--burn"])
run(mix)
out = os.path.join(P, "out", "final.mp4"); d = ffprobe_dur(out)
lo = subprocess.run(["ffmpeg", "-nostats", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
I = [l for l in lo.splitlines() if l.strip().startswith("I:")]
print(f"\nQC: duration {d:.1f}s | loudness {I[-1].strip() if I else '?'} | stills in stills/ — look at every one before delivering")
