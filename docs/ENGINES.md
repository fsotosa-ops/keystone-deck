# Engines

| Engine | Output | Status |
|---|---|---|
| keystone-html | Live 1920×1080 deck: step reveals, presenter view, devices that embed a live app, PDF with and without notes, publishing to GitHub Pages | planned for 0.2 |
| keystone-video | Narrated video from `talk.md`. Each scene lasts as long as its voice. Voice comes from a recording or an optional TTS (ElevenLabs via `ELEVENLABS_API_KEY`). Music ducks under the voice; output is checked for loudness, blank frames and a frame strip. | planned for 0.3 |
| keystone-slides | Native, editable Google Slides built by Apps Script from `brand.gs`, run through Playwright | planned for 0.4 |

To write your own engine, follow the contract in [ARCHITECTURE.md](ARCHITECTURE.md#engine-contract).
