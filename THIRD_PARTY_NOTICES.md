# Third-party notices

The code in this repository is MIT-licensed (see `LICENSE`). It bundles or downloads these third-party components, each under its own licence:

| Component | Where | Licence |
|---|---|---|
| [Inter](https://github.com/rsms/inter) typeface | `assets/fonts/` (bundled) | SIL Open Font License 1.1 — `assets/fonts/OFL.txt` |
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) voice model, via [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | `models/` (downloaded by `studio/get_models.py`) | Apache-2.0 (model) · MIT (kokoro-onnx) |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) + Whisper small | `models/` (optional, downloaded) | MIT |
| [FFmpeg](https://ffmpeg.org) | installed separately | LGPL/GPL |

Music, sound effects and images you add to a project keep their own licences: record them in the project's `SOURCES.md`.
Voices from cloud services (e.g. ElevenLabs via `voice/el_cache.py`) are governed by your plan with that provider.
