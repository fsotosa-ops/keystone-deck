---
name: narrated-video
description: Use when a keystone deck should become a narrated video (for LinkedIn, a recorded pitch, a demo, or people who will not attend the talk), or when the user asks to use their voice or ElevenLabs. Generates the narration from talk.md, times each scene to its line and fires clicks on the spoken cue. Also triggers on "video narrado", "con mi voz", "graba la presentación".
---

# Narrated video

```bash
uv run --with playwright --with imageio-ffmpeg \
  python "${CLAUDE_PLUGIN_ROOT}/scripts/build_video.py" <deck-dir> [--brand brand.json] [--out video.mp4]
```

- **Voice:** set `meta.voice` in deck.json: `{"id": "<ElevenLabs voice id>", "model": "eleven_v4", "direction": "accent and tone in a few words"}`. The key comes from `ELEVENLABS_API_KEY` in the environment and is never written to disk. Ask the user before generating: it spends their credits (about one per character).
- **One take:** the whole talk is generated in a single take and cut per slide by character timestamps; short per-slide takes make the model repeat lines (`--per-slide` exists, but avoid it).
- **Clicks:** `**Click:**` markers in talk.md fire the next step when the voice reaches them. `hold` on a slide adds seconds after the voice when a scene needs time to play.
- **Check the voice, do not assume it:** transcribe each cut (local Whisper or ElevenLabs speech-to-text) and compare with talk.md. Look for repeated lines, the direction prompt read aloud, and clipped first words.
- **Without a key** (or `--no-voice`) the video is silent, timed at 2.6 words per second.
