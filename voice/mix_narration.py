"""Fit + mix presenter narration onto a video.
Usage: python mix_narration.py VIDEO.mp4 MUSIC.wav NARRATION.py POLISHED_DIR OUT.mp4 [max_tempo=1.08]
Places each line at its start; an over-long line is sped up gently (<= max_tempo), then later lines
shift only as needed. Music ducks under the voice. Writes OUT.srt (clean text, markers removed)."""
import re, sys, subprocess, importlib.util, soundfile as sf
video, music, nfile, vdir, out = sys.argv[1:6]
cap = float(sys.argv[6]) if len(sys.argv) > 6 else 1.08
sp = importlib.util.spec_from_file_location('n', nfile); n = importlib.util.module_from_spec(sp); sp.loader.exec_module(n)
total = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video]).decode())
plan, prev = [], 0
for i, (st, speed, text) in enumerate(n.LINES):
    f = f'{vdir}/vo_{i+1:02}.wav'; d = sf.info(f).duration
    s = max(st, prev + .35); nxt = n.LINES[i + 1][0] if i + 1 < len(n.LINES) else total - .4
    avail = nxt - s - .3; tp = min(cap, d / avail) if d > avail else 1.0
    plan.append((s, tp, d / tp, text, f, s - st)); prev = s + d / tp
for i, p in enumerate(plan):
    if p[5] > .05 or p[1] > 1.0: print(f'line {i+1:2}: shift {p[5]:+.2f}s  tempo {p[1]:.2f}')
print('ends at', round(prev, 2), 'of', round(total, 2))
clean = lambda t: re.sub(r'\s*(\.\.\.|//|/)\s*', ' ', t).replace('  ', ' ').strip()
ts = lambda x: f'{int(x//3600):02}:{int(x%3600//60):02}:{x%60:06.3f}'.replace('.', ',')
open(out.rsplit('.', 1)[0] + '.srt', 'w', encoding='utf-8').write(''.join(f'{i+1}\n{ts(a)} --> {ts(a+dd)}\n{clean(t)}\n\n' for i, (a, tp, dd, t, f, dr) in enumerate(plan)))
inp = ['-i', video, '-i', music]; parts = []
for i, (a, tp, dd, t, f, dr) in enumerate(plan):
    inp += ['-i', f]; ms = int(a * 1000)
    parts.append(f'[{i+2}:a]aresample=48000,atempo={tp:.3f},adelay={ms}|{ms},volume=1.5[v{i}]')
fc = ';'.join(parts + [''.join(f'[v{i}]' for i in range(len(plan))) + f'amix=inputs={len(plan)}:normalize=0,aformat=channel_layouts=stereo,apad=whole_dur={total},asplit=2[vo1][vo2]',
                       '[1:a]aformat=channel_layouts=stereo,volume=0.75[mus]',
                       '[mus][vo1]sidechaincompress=threshold=0.015:ratio=10:attack=20:release=600[duck]',
                       '[duck][vo2]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5[a]'])
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inp, '-filter_complex', fc, '-map', '0:v', '-map', '[a]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(total), out], check=True)
print('done', out)
