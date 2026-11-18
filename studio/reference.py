"""Study the editing style of reference videos (links or files) and draft a style sheet.

python studio/reference.py <out_dir> <url_or_file> [<url_or_file> ...] [--no-transcribe]

For every reference it measures, in code (cheap, no AI tokens):
  pacing      cuts (scene changes), average shot length, cuts in the first 3 s (the hook)
  silences    how much silence is left in (tells you how tight the jump cuts are)
  speech      words per second, caption-sized chunks (needs faster-whisper)
  look        brightness, contrast, saturation, warmth, dominant colours
  audio       loudness (LUFS)
and saves contact sheets (hook frames + one frame per shot) for an agent or a human to LOOK at for
caption style, zooms, B-roll, emojis and motion graphics.

Writes to <out_dir>:  refNN.mp4, refNN_hook.jpg, refNN_shots.jpg, analysis.json, style.draft.json, STYLE.md
Next: review STYLE.md (the brand sheet), approve, then:  python studio/reel.py raw.mp4 out.mp4 --style <out_dir>/style.draft.json
"""
import argparse, json, os, re, shutil, statistics as stx, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import need, ffprobe_dur
from PIL import Image, ImageDraw, ImageStat

def sh(cmd): return subprocess.run(cmd, capture_output=True, text=True)

def fetch(src, out_dir, i):
    dst = os.path.join(out_dir, f"ref{i:02d}.mp4")
    if os.path.exists(dst): return dst
    if os.path.exists(src): shutil.copy(src, dst); return dst
    need("yt-dlp")
    r = sh(["yt-dlp", "-q", "--no-playlist", "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
            "-o", dst, src])
    if r.returncode or not os.path.exists(dst): sys.exit(f"download failed: {src}\n{r.stderr[-800:]}")
    return dst

def cuts(path, thr=0.3):
    err = sh(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"]).stderr
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", err)]

def silences(path):
    err = sh(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-35dB:d=0.3", "-vn", "-f", "null", "-"]).stderr
    return sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", err))

def lufs(path):
    err = sh(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-vn", "-f", "null", "-"]).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err); return float(m[-1]) if m else None

def frame(path, t, w=360):
    import io
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", f"scale={w}:-2",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGB") if png else Image.new("RGB", (w, w * 16 // 9))

def sheet(frames, labels, path, cols=6):
    w, h = frames[0].size; rows = (len(frames) + cols - 1) // cols
    out = Image.new("RGB", (cols * w, rows * (h + 22)), "black"); d = ImageDraw.Draw(out)
    for i, (f, lb) in enumerate(zip(frames, labels)):
        x, y = i % cols * w, i // cols * (h + 22); out.paste(f, (x, y + 22)); d.text((x + 4, y + 4), lb, fill="white")
    out.save(path, quality=85)

def look(frames):
    st = {"brightness": [], "contrast": [], "saturation": [], "warmth": []}; pal = Image.new("RGB", (len(frames) * 64, 64))
    for i, f in enumerate(frames):
        s = ImageStat.Stat(f); r, g, b = s.mean; st["brightness"].append(sum(s.mean) / 3 / 255)
        st["contrast"].append(stx.mean(s.stddev) / 128); st["warmth"].append((r - b) / 255)
        st["saturation"].append(ImageStat.Stat(f.convert("HSV")).mean[1] / 255); pal.paste(f.resize((64, 64)), (i * 64, 0))
    q = pal.quantize(6).convert("RGB").getcolors(64 * 64 * len(frames)) or []
    colors = ["#%02X%02X%02X" % c for _, c in sorted(q, reverse=True)[:6]]
    return {k: round(stx.mean(v), 3) for k, v in st.items()} | {"dominant_colors": colors}

def speech(path):
    try:
        import captions as C
        words = C.transcribe(path)
    except Exception as ex:
        return {"note": f"transcription skipped ({ex.__class__.__name__})"}
    if not words: return {"words": 0}
    span = words[-1]["e"] - words[0]["s"]
    return {"words": len(words), "words_per_sec": round(len(words) / max(span, 0.1), 2),
            "first_3s_text": " ".join(w["w"] for w in words if w["s"] < 3), "first_word_at": words[0]["s"]}

def main():
    p = argparse.ArgumentParser(); p.add_argument("out_dir"); p.add_argument("sources", nargs="+")
    p.add_argument("--no-transcribe", action="store_true"); a = p.parse_args(); need("ffmpeg")
    os.makedirs(a.out_dir, exist_ok=True); refs = []
    for i, src in enumerate(a.sources, 1):
        v = fetch(src, a.out_dir, i); d = ffprobe_dur(v); c = cuts(v); shots = [0.0] + c
        lens = [b - x for x, b in zip(shots, shots[1:] + [d])]
        hook_t = [k * 0.5 for k in range(6) if k * 0.5 < d]
        hook = [frame(v, t) for t in hook_t]; sheet(hook, [f"{t:.1f}s" for t in hook_t], v[:-4] + "_hook.jpg")
        sample = [x + min(l / 2, 0.4) for x, l in zip(shots, lens)][:36]
        fr = [frame(v, t) for t in sample]; sheet(fr, [f"shot {k+1} @{t:.1f}s" for k, t in enumerate(sample)], v[:-4] + "_shots.jpg")
        sil = silences(v)
        r = {"source": src, "file": os.path.basename(v), "duration_s": round(d, 2), "cuts": len(c),
             "avg_shot_s": round(stx.mean(lens), 2), "median_shot_s": round(stx.median(lens), 2),
             "cuts_in_first_3s": sum(1 for x in c if x < 3), "silence_ratio": round(sil / d, 3) if d else 0,
             "loudness_lufs": lufs(v), "look": look(fr), "speech": {} if a.no_transcribe else speech(v)}
        refs.append(r); print(f"ref{i:02d}: {d:.0f}s, {len(c)} cuts, avg shot {r['avg_shot_s']}s, silence {r['silence_ratio']:.0%}")
    json.dump(refs, open(os.path.join(a.out_dir, "analysis.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    m = lambda k: stx.mean(x[k] for x in refs); ml = lambda k: stx.mean(x["look"][k] for x in refs)
    tight = m("silence_ratio") < 0.06
    draft = {"format": "9:16",
             "cuts": {"silence_db": -35, "min_silence": 0.25 if tight else 0.45, "pad": 0.05 if tight else 0.1, "min_keep": 0.2},
             "punch": {"zoom": 1.15 if m("avg_shot_s") < 2 else 1.1, "every": 2},
             "grade": {"contrast": round(min(max(1 + (ml("contrast") - 0.45), 0.95), 1.2), 2),
                       "saturation": round(min(max(ml("saturation") / 0.35, 0.85), 1.35), 2),
                       "brightness": round(min(max((ml("brightness") - 0.45) / 4, -0.05), 0.05), 3),
                       "warmth": round(min(max(ml("warmth") / 2, -0.06), 0.08), 3)},
             "captions": {"words_per_line": 2 if m("avg_shot_s") < 1.5 else 3, "uppercase": True,
                          "highlight": "#FACC15", "emphasis": "#22D3EE", "position": 0.72},
             "audio": {"music_db": -20, "lufs": round(stx.mean(x["loudness_lufs"] for x in refs if x["loudness_lufs"]) or -14)}}
    json.dump(draft, open(os.path.join(a.out_dir, "style.draft.json"), "w"), indent=2)
    rows = "\n".join(f"| {x['file']} | {x['duration_s']}s | {x['cuts']} | {x['avg_shot_s']}s | {x['cuts_in_first_3s']} | "
                     f"{x['silence_ratio']:.0%} | {x['loudness_lufs']} | {x['speech'].get('words_per_sec', '–')} |" for x in refs)
    md = f"""# Style sheet (draft — review before approving)

## Measured (code)
| Ref | Length | Cuts | Avg shot | Cuts in first 3 s | Silence left | LUFS | Words/s |
|---|---|---|---|---|---|---|---|
{rows}

Look (avg): brightness {ml('brightness'):.2f} · contrast {ml('contrast'):.2f} · saturation {ml('saturation'):.2f} · warmth {ml('warmth'):+.2f}
Palette: {', '.join(refs[0]['look']['dominant_colors'])}

## Observed (fill in by looking at refNN_hook.jpg and refNN_shots.jpg)
- **Hook (first 3 s):** what is on screen, first words, text on screen, movement
- **Jump cuts:** tight / natural ({'tight: silences trimmed' if tight else 'some breathing room left'})
- **Zooms / punch-ins:** how often, how strong, on which words
- **Captions:** font, size, colour, position, words per line, animation, which words are emphasised
- **Motion graphics / emojis / pop-ups / B-roll:** what appears and when
- **Colour grade:** overall look
- **Music & SFX:** genre, level under voice, whooshes/pops on cuts

## Our version (inspired, not copied)
- What we keep:
- What we change so it feels original:

## Settings → `style.draft.json`
Rename to `style.json` after approval, then: `python studio/reel.py raw.mp4 out.mp4 --style style.json --music bed.mp3`
"""
    open(os.path.join(a.out_dir, "STYLE.md"), "w", encoding="utf-8").write(md)
    print("wrote", os.path.join(a.out_dir, "STYLE.md"))

if __name__ == "__main__":
    main()
