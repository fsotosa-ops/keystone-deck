---
name: pptx-export
description: Use when a keystone deck must be delivered as PowerPoint (.pptx) for people who do not use HTML, or must play offline with its animations. Records each scene and click step of the live deck to video and assembles a PowerPoint with autoplay clips, native editable titles and speaker notes. Also triggers on "pásalo a PowerPoint", "exportar a pptx", "para quien no sabe código".
---

# PowerPoint export

```bash
uv run --with playwright --with python-pptx --with imageio-ffmpeg \
  python "${CLAUDE_PLUGIN_ROOT}/scripts/build_pptx.py" <deck-dir> [--brand brand.json] [--out deck.pptx]
```

- Each slide and each click step becomes one PowerPoint slide whose video starts by itself; kicker, title and text are re-created as native text so they stay editable.
- Opening it needs only PowerPoint or Keynote. Building it needs a Chromium for Playwright (`playwright install chromium` if Chrome is missing).
- Verify before delivering: export the .pptx to video from PowerPoint (File › Export) or render frames, and look at a strip of frames mid-transition.
- `build_morph.py` is the fallback when every shape must be editable: native shapes with Morph transitions, simpler visuals.
