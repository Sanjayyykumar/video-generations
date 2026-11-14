# hello-studio

The 20-second demo from the main README, as a project you can render yourself:

```bash
python studio/make.py examples/hello-studio
```

- `brief.json` — format (`16:9`), branding handle, deliverables.
- `scenes.json` — five scenes: on-screen `title` / `body`, the spoken `say` line, per-scene gradient `bg` and `accent`.

Output: `out/final.mp4`, `out/final.srt` (if faster-whisper is installed) and `stills/` for a quick visual check. `vo.py` writes the measured voice length back into `scenes.json` (`vo_s`, `dur`) so re-runs are instant.
