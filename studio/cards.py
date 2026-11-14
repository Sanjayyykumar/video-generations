"""Code renderer: animated text/image cards → silent MP4. Fast on any CPU, no GPU.
python studio/cards.py <project>   — reads scenes.json (+ brief format), writes src/silent.mp4 and stills/NN.png.
Scene fields: title, body, image (path in assets/), bg ["#hex","#hex"], accent "#hex", dur (s)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from common import load, need
need("ffmpeg"); proj = sys.argv[1]; sc = load(os.path.join(proj, "scenes.json")); br = load(os.path.join(proj, "brief.json"))
W, H = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}[br.get("format", "9:16")]
FPS = 30; S = min(W, H) / 1080
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
def font(sz, bold=True):  # bundled Inter (OFL) first, so every OS renders the same
    for f in ([os.path.join(FONTS, "InterDisplay-Bold.otf"), "C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
              [os.path.join(FONTS, "Inter-Regular.otf"), "C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
        if os.path.exists(f): return ImageFont.truetype(f, int(sz * S))
    return ImageFont.load_default()
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])
def grad(c1, c2):
    g = Image.new("RGB", (1, 256)); px = g.load(); a, b = hexc(c1), hexc(c2)
    for y in range(256): px[0, y] = tuple(int(a[i] + (b[i] - a[i]) * y / 255) for i in range(3))
    return g.resize((W, H))
ease = lambda t: 1 - (1 - min(max(t, 0), 1)) ** 3
handle = (br.get("branding") or {}).get("handle", "")
fT, fB, fH = font(92), font(52, False), font(34)
for _d in ("stills", "src"): os.makedirs(os.path.join(proj, _d), exist_ok=True)
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", os.path.join(proj, "src", "silent.mp4")], stdin=subprocess.PIPE)
for i, s in enumerate(sc["scenes"]):
    bg = grad(*(s.get("bg") or sc.get("bg") or ["#0f172a", "#1e3a8a"])); acc = hexc(s.get("accent") or sc.get("accent") or "#38bdf8")
    img = None
    if s.get("image"):
        im = Image.open(os.path.join(proj, "assets", s["image"])).convert("RGB"); im.thumbnail((int(W * .84), int(H * .42))); img = im
    n = int(s.get("dur", 3) * FPS)
    for f in range(n):
        t = f / FPS; fr = bg.copy(); d = ImageDraw.Draw(fr); y = int(H * (0.30 if img else 0.38))
        if img:
            k = ease(t / .6); fr.paste(img, ((W - img.width) // 2, int(H * .08 + 40 * (1 - k))))
            y = int(H * .08) + img.height + int(80 * S)
        a = ease(t / .5)
        for ln in wrap(d, s.get("title", ""), fT, W * .84):
            d.text(((W - d.textlength(ln, font=fT)) / 2, y + 30 * (1 - a)), ln, font=fT, fill=tuple(int(255 * a) for _ in range(3))); y += int(110 * S)
        if s.get("title"): d.rectangle([W / 2 - 80 * S * ease((t - .2) / .5), y + 10, W / 2 + 80 * S * ease((t - .2) / .5), y + 10 + 8 * S], fill=acc); y += int(60 * S)
        b = ease((t - .35) / .6)
        for ln in wrap(d, s.get("body", ""), fB, W * .80):
            d.text(((W - d.textlength(ln, font=fB)) / 2, y), ln, font=fB, fill=tuple(int(c * b) for c in (226, 232, 240))); y += int(70 * S)
        if handle: d.text((int(40 * S), int(40 * S)), handle, font=fH, fill=(203, 213, 225))
        if f == min(n - 1, int(1.2 * FPS)): fr.save(os.path.join(proj, "stills", f"{i:02d}.png"))
        proc.stdin.write(fr.tobytes())
    print("scene", i, s.get("title", "")[:40], f"{s.get('dur',3)}s")
proc.stdin.close(); proc.wait()
