"""Speaker polish for voice clips: trims edge silence, warm/clear EQ, gentle compression,
subtle room, smooth fade-out tail. Usage: python polish_vo.py IN_DIR OUT_DIR"""
import os, sys, subprocess, soundfile as sf, numpy as np
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
CHAIN = ('highpass=f=75,equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,'
         'equalizer=f=9000:t=q:w=1:g=1.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=140:makeup=2,'
         'aecho=0.85:0.5:32:0.05')
for f in sorted(os.listdir(src)):
    if not f.endswith('.wav'): continue
    a, sr = sf.read(os.path.join(src, f))
    if a.ndim > 1: a = a.mean(1)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(0, idx[0] - int(.03 * sr)): idx[-1] + int(.08 * sr)] if len(idx) else a
    a = np.concatenate([a, np.zeros(int(.35 * sr))])                    # room for the tail
    tmp = os.path.join(dst, '_' + f); sf.write(tmp, a, sr)
    d = len(a) / sr
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af',
                    CHAIN + f',afade=t=in:d=0.02,afade=t=out:st={d-0.32:.3f}:d=0.32,aresample=48000',
                    os.path.join(dst, f)], check=True)
    os.remove(tmp)
print('polished', dst)
