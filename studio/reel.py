"""Edit a raw talking-head clip into a finished reel in one command:
silence-trimmed jump cuts -> punch-in zooms -> crop to format -> colour grade -> word-highlight captions
-> music ducked under speech -> loudness normalised.

python studio/reel.py <raw.mp4> <out.mp4> [--style style.json] [--music bed.mp3] [--no-captions] [--lang en]

style.json (all optional; `python studio/reference.py` drafts one from videos you like):
{
  "format": "9:16",
  "cuts":   {"silence_db": -35, "min_silence": 0.35, "pad": 0.08, "min_keep": 0.25},
  "punch":  {"zoom": 1.12, "every": 2},
  "grade":  {"contrast": 1.06, "saturation": 1.12, "brightness": 0.0, "warmth": 0.04},
  "captions": {"words_per_line": 3, "highlight": "#FACC15", "uppercase": true},
  "audio":  {"music_db": -20, "lufs": -14}
}
"""
import argparse, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import need, run, ffprobe_dur
import captions as C

FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}

def speech_segments(src, db, min_sil, pad, min_keep):
    """Keep everything that is not a silence of >= min_sil seconds (with `pad` of breathing room)."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"silencedetect=n={db}dB:d={min_sil}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    total = ffprobe_dur(src); keep, t = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s - t > 0: keep.append((max(0, t - pad), min(total, s + pad)))
        t = e
    if total - t > 0: keep.append((max(0, t - pad), total))
    merged = []
    for a, b in keep:
        if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], b)
        elif b - a >= min_keep: merged.append((a, b))
    return merged or [(0, total)]

def probe_wh(src):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x", src], capture_output=True, text=True).stdout.strip()
    return map(int, o.split("x")[:2])

def main():
    p = argparse.ArgumentParser(); p.add_argument("src"); p.add_argument("out"); p.add_argument("--style")
    p.add_argument("--music"); p.add_argument("--no-captions", action="store_true"); p.add_argument("--lang")
    a = p.parse_args(); need("ffmpeg")
    st = json.load(open(a.style, encoding="utf-8")) if a.style else {}
    W, H = FORMATS[st.get("format", "9:16")]
    cu = {"silence_db": -35, "min_silence": 0.35, "pad": 0.08, "min_keep": 0.25, **st.get("cuts", {})}
    pu = {"zoom": 1.12, "every": 2, **st.get("punch", {})}
    gr = {"contrast": 1.06, "saturation": 1.12, "brightness": 0.0, "warmth": 0.04, **st.get("grade", {})}
    au = {"music_db": -20, "lufs": -14, **st.get("audio", {})}

    segs = speech_segments(a.src, cu["silence_db"], cu["min_silence"], cu["pad"], cu["min_keep"])
    before = ffprobe_dur(a.src); after = sum(b - s for s, b in segs)
    print(f"jump cuts: {len(segs)} segments, {before:.1f}s -> {after:.1f}s ({before-after:.1f}s of silence removed)")

    sw, sh = probe_wh(a.src)
    # crop source to the target aspect (centre), then optional punch-in, then scale
    tw, th = (sw, round(sw * H / W)) if sw / sh < W / H else (round(sh * W / H), sh)
    tw, th = tw - tw % 2, th - th % 2
    w_, b_ = gr["warmth"], gr["warmth"]
    grade = (f"eq=contrast={gr['contrast']}:saturation={gr['saturation']}:brightness={gr['brightness']},"
             f"colorbalance=rm={w_:.3f}:bm={-b_:.3f}")
    f, cat = [], ""
    for i, (s, e) in enumerate(segs):
        z = pu["zoom"] if pu["every"] and i % pu["every"] == pu["every"] - 1 else 1.0
        zw, zh = round(tw / z) // 2 * 2, round(th / z) // 2 * 2
        f.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS,crop={tw}:{th},crop={zw}:{zh},scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
        f.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(e-s-0.012,0):.3f}:d=0.012[a{i}]")
        cat += f"[v{i}][a{i}]"
    f.append(f"{cat}concat=n={len(segs)}:v=1:a=1[vc][ac]"); f.append(f"[vc]{grade},format=yuv420p[vg]")
    tmp = tempfile.mkdtemp(prefix="reel_"); cut = os.path.join(tmp, "cut.mp4")
    script = os.path.join(tmp, "graph.txt"); open(script, "w").write(";\n".join(f))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.src, "-filter_complex_script", script, "-map", "[vg]", "-map", "[ac]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", cut])

    vf = None; base = os.path.splitext(a.out)[0]
    if not a.no_captions:
        try:
            words = C.transcribe(cut, a.lang)
            C.write_ass(words, base + ".ass", W, H, st.get("captions")); C.write_srt(words, base + ".srt", st.get("captions", {}).get("words_per_line", 3))
            vf = C.burn_filter(os.path.abspath(base + ".ass")); print(f"captions: {len(words)} words")
        except Exception as ex:
            print("!! captions skipped:", ex)

    dur = ffprobe_dur(cut); ins = ["-i", cut]
    if a.music:
        ins += ["-stream_loop", "-1", "-i", a.music]
        af = (f"[1:a]aresample=48000,volume={au['music_db']}dB,afade=t=in:d=1,afade=t=out:st={max(dur-1.5,0):.2f}:d=1.5[m];"
              f"[0:a]asplit[v1][v2];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[md];"
              f"[v2][md]amix=inputs=2:normalize=0,loudnorm=I={au['lufs']}:TP=-1.5:LRA=11,atrim=0:{dur:.3f}[aout]")
    else:
        af = f"[0:a]loudnorm=I={au['lufs']}:TP=-1.5:LRA=11[aout]"
    run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", af, "-map", "0:v", "-map", "[aout]",
         *(["-vf", vf] if vf else []), "-c:v", "libx264" if vf else "copy", *(["-preset", "veryfast", "-crf", "19"] if vf else []),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", a.out])
    print(f"wrote {a.out}  {ffprobe_dur(a.out):.1f}s  {W}x{H}")

if __name__ == "__main__":
    main()
