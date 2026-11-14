"""Place voice clips at scene starts, add music (ducked) + SFX, loudness-normalise, optionally burn subtitles.
python studio/mix.py <project> [--music audio/music/x.mp3] [--burn]"""
import argparse, os
from common import load, run, need, ffprobe_dur
need("ffmpeg"); p = argparse.ArgumentParser(); p.add_argument("proj"); p.add_argument("--music"); p.add_argument("--burn", action="store_true")
a = p.parse_args(); P = a.proj; sc = load(os.path.join(P, "scenes.json"))
silent = os.path.join(P, "src", "silent.mp4"); total = ffprobe_dur(silent)
ins, flt, labels, t = ["-i", silent], [], [], 0.0
for i, s in enumerate(sc["scenes"]):
    w = os.path.join(P, "audio", "vo", f"{i:02d}.wav")
    if os.path.exists(w):
        ins += ["-i", w]; k = len(ins) // 2 - 1; ms = int((t + sc.get("lead_s", 0.25)) * 1000)
        flt.append(f"[{k}:a]aresample=48000,adelay={ms}|{ms}[v{k}]"); labels.append(f"[v{k}]")
    for fx in s.get("sfx", []):
        ins += ["-i", os.path.join(P, fx["file"])]; k = len(ins) // 2 - 1; ms = int((t + fx.get("at", 0)) * 1000)
        flt.append(f"[{k}:a]aresample=48000,volume={fx.get('vol', 0.5)},adelay={ms}|{ms}[x{k}]"); labels.append(f"[x{k}]")
    t += s.get("dur", 3)
flt.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad=whole_dur={total}[vo]")
out_a = "[vo]"
if a.music:
    ins += ["-stream_loop", "-1", "-i", os.path.join(P, a.music)]; k = len(ins) // 2 - 1
    flt.append(f"[{k}:a]aresample=48000,volume=0.25,afade=t=in:d=1.5,afade=t=out:st={max(total-2,0)}:d=2[m]")
    flt.append("[vo]asplit[vo1][vo2]"); flt.append("[m][vo1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md]")
    flt.append("[vo2][md]amix=inputs=2:normalize=0[mx]"); out_a = "[mx]"
flt.append(f"{out_a}loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{total}[aout]")
vf = []
srt = os.path.join(P, "out", "final.srt")
if a.burn and os.path.exists(srt):
    esc = srt.replace("\\", "/").replace(":", r"\:")
    vf = ["-vf", f"subtitles='{esc}':force_style='Fontsize=13,Bold=1,Outline=2,Shadow=0,MarginV=70,Alignment=2'"]
out = os.path.join(P, "out", "final.mp4")
run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[aout]", *vf,
     "-c:v", "libx264" if vf else "copy", *(["-preset", "veryfast", "-crf", "20"] if vf else []), "-c:a", "aac", "-b:a", "192k", "-shortest", out])
print("wrote", out, f"{ffprobe_dur(out):.1f}s")
