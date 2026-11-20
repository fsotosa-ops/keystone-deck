# keystone-deck

A Claude Code plugin marketplace: `keystone` (method and brand), `keystone-html` (stage engine), `keystone-pptx` (PowerPoint export) and `keystone-video` (narrated video). Architecture in `docs/ARCHITECTURE.md`.

## Before every push

- `python3 -m unittest discover tests/unit` passes.
- `bash scripts/scrub_check.sh` is clean. It reads a private denylist outside the repo; contributors without one still get the absolute-path check.
- No absolute home paths, personal voice ids, API keys or real people's data in tracked files, recordings or examples.

## Versioning

Bump the version in `.claude-plugin/marketplace.json` and every `plugins/*/.claude-plugin/plugin.json` whenever plugin content changes, and add a `CHANGELOG.md` entry. Installed plugins only update when the version changes.

## Engines and content

- The stage engine (`plugins/keystone-html/scripts/build_stage.py`) is the default for every deck. A deck made only of `figures` and `cards` reads like any other presentation: use scenes that move people, places or the product.
- Every figure comes from `evidence.json` and carries its source; never type a number into a slide.
- New scenes go in `plugins/keystone-html/stage/scenes.py`, are registered in `SCENES` and in `LAYOUTS` (`plugins/keystone/scripts/ks/deck.py`), documented in the `stage-deck` skill and shown in a rendered example.
- Examples are fictitious initiatives with public sources, and say on the slide what is invented.

## Video

- ElevenLabs key and voice id come from `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID`. Generating voice spends the user's credits: ask first.
- Verify a rendered video by measuring, not by eye: the build fails on silences over 0.8 s; also check the video stream length (`ffmpeg -map 0:v -c copy -f null -`) and look at a one-frame-per-second contact sheet.
- Terminal sessions shown in a demo are real recordings (asciicast), replayed with `terminal.html`; redact home paths and account banners before committing them.

## Writing

English in code and docs, with `README.es.md` kept in sync. Plain sentences: no em dashes, no slogans, no claims the code does not back.
