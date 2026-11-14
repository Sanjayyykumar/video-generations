# Voice pace: a house style that sounds like a presenter, not a robot

Tuned over several conference-film iterations with Kokoro. Use it as a starting point.

- **Voice:** Kokoro `af_kore` or `af_heart`. Speed 1.00 by default, 1.02 for long lists, 0.95–0.97 for taglines and closings, 0.93 only for the single emotional hook.
- **Pauses:** at most one `...` held beat per line, only at the emotional turn. Use `/` sparingly; commas usually breathe better.
- **Measured rate:** about 2.6–2.8 words per second. Budget per line = words / 2.7 + 0.35 s tail. Check the fit *before* generating.
- **Planned silences** of 1–1.5 s after the problem build-up and after the payoff.
- **Density:** about 230–250 words for a 2.5-minute film; no scene silent for more than ~3 s except planned silences.
- **Running long?** Add visual beats (cards or chips that pop on each mention) and shift later scenes; don't slow the animation.
- **Workflow:** write → estimate → fix overruns in the text → generate once (`voice/speak.py`) → `voice/polish_vo.py` → `voice/mix_narration.py` → check drift (aim for < 0.5 s).
- **Names:** respell anything the engine mispronounces in `voice/lexicon.py` (e.g. `Arun` → `Aroon`), and test one line first.
