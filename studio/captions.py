"""Word-timed captions: transcribe (faster-whisper, offline) and write social-style .ass captions
with the current word highlighted and key words emphasised. Also writes .srt and words.json.

python studio/captions.py <audio_or_video> <out_base> [--style style.json] [--lang en]
  -> out_base.ass, out_base.srt, out_base.words.json      (burn with: ffmpeg -vf "ass=out_base.ass:fontsdir=assets/fonts")
"""
import argparse, json, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "assets", "fonts")
DEFAULT = {  # every key can be overridden by the "captions" block of a style.json
    "words_per_line": 3, "font": "Inter Display", "size": 0.055,  # size = fraction of video height
    "color": "#FFFFFF", "highlight": "#FACC15", "emphasis": "#22D3EE", "outline": "#000000",
    "outline_px": 0.006, "position": 0.72,  # vertical centre of the caption, 0=top 1=bottom
    "uppercase": True, "bold": True, "pop": True,  # pop = active word scales up slightly
    "emphasis_words": [], "auto_emphasis": True,   # numbers, long words, money, % get the emphasis colour
}

def transcribe(path, lang=None):
    from faster_whisper import WhisperModel
    models = os.path.join(os.environ.get("VIDEO_ROOT") or os.path.dirname(HERE), "models")
    local = os.path.join(models, "faster-whisper-small")
    m = WhisperModel(local if os.path.exists(os.path.join(local, "model.bin")) else "small", device="auto", compute_type="int8")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, language=lang, vad_filter=True)
    return [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for s in segs for w in s.words if w.word.strip()]

def _ass_color(hexc):  # #RRGGBB -> &H00BBGGRR
    h = hexc.lstrip("#"); return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()

def _emph(word, st):
    core = re.sub(r"[^\w%$₹€£.-]", "", word).lower()
    if core in {x.lower() for x in st["emphasis_words"]}: return True
    return st["auto_emphasis"] and (bool(re.search(r"\d|%|\$|₹|€|£", core)) or len(core) >= 8)

def lines(words, n):
    """Group into caption lines of <= n words, breaking early on sentence ends and long pauses."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = words[i + 1]["s"] - w["e"] if i + 1 < len(words) else 9
        if len(cur) >= n or gap > 0.45 or w["w"][-1:] in ".?!":
            out.append(cur); cur = []
    return out + ([cur] if cur else [])

def write_ass(words, path, w, h, style=None):
    st = {**DEFAULT, **(style or {})}
    fs = round(h * st["size"]); ol = max(1, round(h * st["outline_px"])); y = round(h * st["position"])
    t = lambda x: f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
            "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Cap,{st['font']},{fs},{_ass_color(st['color'])},&H000000FF,{_ass_color(st['outline'])},&H64000000,"
            f"{-1 if st['bold'] else 0},0,0,0,100,100,0,0,1,{ol},0,5,40,40,0,1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = []
    for ln in lines(words, st["words_per_line"]):
        for k, cur in enumerate(ln):  # one event per active word: whole line visible, active word highlighted
            s = cur["s"]; e = ln[k + 1]["s"] if k + 1 < len(ln) else cur["e"] + 0.12
            parts = []
            txts = [x["w"].upper() if st["uppercase"] else x["w"] for x in ln]
            est = lambda ws: sum(len(t) for t in ws) * fs * 0.62 + fs * 0.3 * (len(ws) - 1)  # rough bold-caps width
            brk = len(ln) if est(txts) <= w * 0.86 else max(1, (len(ln) + 1) // 2)  # wrap onto 2 rows if too wide
            widest = max(est(txts[:brk]), est(txts[brk:]) if brk < len(ln) else 0)
            fit = r"\fs%d" % (fs * w * 0.86 // widest) if widest > w * 0.86 else ""
            for j, x in enumerate(ln):
                txt = x["w"].upper() if st["uppercase"] else x["w"]
                col = st["highlight"] if j == k else (st["emphasis"] if _emph(x["w"], st) else st["color"])
                pop = r"\fscx112\fscy112" if (j == k and st["pop"]) else ""
                parts.append(("\\N" if j == brk and j else (" " if j else "")) + f"{{\\c{_ass_color(col)}{pop}}}{txt}{{\\fscx100\\fscy100}}")
            ev.append(f"Dialogue: 0,{t(s)},{t(max(e, s + 0.05))},Cap,,0,0,0,,{{\\pos({w//2},{y}){fit}}}" + "".join(parts))
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

def write_srt(words, path, n=3):
    ts = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x*1000%1000):03d}"
    with open(path, "w", encoding="utf-8") as f:
        for i, ln in enumerate(lines(words, n), 1):
            f.write(f"{i}\n{ts(ln[0]['s'])} --> {ts(ln[-1]['e'])}\n{' '.join(x['w'] for x in ln)}\n\n")

def burn_filter(ass_path):
    esc = lambda p: p.replace("\\", "/").replace(":", r"\:")
    return f"ass='{esc(ass_path)}':fontsdir='{esc(FONTS)}'"

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("src"); p.add_argument("out_base")
    p.add_argument("--style"); p.add_argument("--lang"); p.add_argument("--size", default="1080x1920")
    a = p.parse_args()
    st = json.load(open(a.style, encoding="utf-8")).get("captions", {}) if a.style else {}
    words = transcribe(a.src, a.lang)
    W, H = map(int, a.size.split("x"))
    json.dump(words, open(a.out_base + ".words.json", "w", encoding="utf-8"), ensure_ascii=False)
    write_ass(words, a.out_base + ".ass", W, H, st); write_srt(words, a.out_base + ".srt", st.get("words_per_line", 3))
    print("wrote", a.out_base + ".ass/.srt", len(words), "words")
