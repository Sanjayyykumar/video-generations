# voice/ — presenter-grade narration tools

`studio/make.py` voices each scene for you. Use these tools when you want **directed narration** for a longer film: timed lines, breaths and pauses, several characters, polish, and a fit-to-video mix.

| Tool | What it does |
|---|---|
| `speak.py` | One narrator, timed lines, pause markers, voice blends, pronunciation lexicon. Resumable. |
| `speak_cast.py` | Dialogue: a different voice per line (narrator + characters). |
| `polish_vo.py` | Trims silence, warm/clear EQ, gentle compression, room and fade: makes TTS sound recorded. |
| `mix_narration.py` | Places every line on the video, nudges over-long lines (≤ 1.08× tempo), ducks music, writes `.srt`. |
| `el_cache.py` | Optional ElevenLabs route with a cache: every line is paid for **once**, re-runs are free. |
| `lexicon.py` | House pronunciation fixes (`'Arun': 'Aroon'`). |

## Narration file format
```python
VOICE = 'af_heart'                      # or a blend: 'af_heart:0.6,bf_emma:0.4'
LINES = [  # (start_second, speed, text)
    (0.5, 0.95, "Every great video starts with a voice ... and a story worth telling."),
    (5.0, 1.00, "It writes the voice, / times every scene, / and mixes the music."),
]
```
Markers: `/` short breath (0.25 s) · `//` dramatic pause (0.55 s) · `...` held beat (0.8 s)

## Full narration pass
```bash
python voice/speak.py voice/examples/narration_demo.py work/vo            # generate (offline)
python voice/polish_vo.py work/vo work/vo_polished                         # make it sound recorded
python voice/mix_narration.py silent.mp4 music.wav voice/examples/narration_demo.py work/vo_polished final.mp4
```
Dialogue: `python voice/speak_cast.py voice/examples/dialogue_demo.py work/cast`

ElevenLabs (optional): `ELEVENLABS_API_KEY=... python voice/el_cache.py NARRATION.py work/vo [VOICE_ID]`. Spend is logged in `voice/cache/elevenlabs/manifest.csv` (git-ignored).

Pacing tips that make TTS sound like a presenter: [`docs/voice-house-style.md`](../docs/voice-house-style.md).
