# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-11-20

### Added
- `keystone-html` stage engine: 1920×1080 stage, click steps, presenter view, the product running in phones and laptops, scene scripts with callouts that read live numbers.
- 15 stage scenes (cover, persona, journey, mirror, product, why-now, matrix, model, funnel, timeline, projection, team, ask, closing, html) and the `stage-deck` skill.
- Presentation types in `narrative-arc`: pitch, keynote, class and report.
- `keystone-pptx`: PowerPoint export that records each scene to video and keeps titles as native text; `pptx-export` skill. Morph-based export kept as `build_morph.py`.
- `examples/pitch-asisto`: a full pitch for a fictitious startup.
- `keystone-video`: narrated video from the talk with ElevenLabs voice, one-take narration cut per slide by character timestamps, clicks on spoken cues; `narrated-video` skill.

## [0.1.0] - 2026-11-19

### Added
- `keystone` core plugin with five skills: `narrative-arc`, `evidence-ledger`, `visual-grammar`, `brand-kit` and `render-review`.
- Commands `/keystone:new`, `/keystone:brand` and `/keystone:review`, and the read-only `deck-critic` agent.
- `keystone.py` CLI (Python stdlib only), with subcommands `new`, `check`, `resolve`, `brand list|check|compile`, `talk check` and `evidence check`.
- Brand as W3C Design Tokens, compiled to CSS, Apps Script, TypeScript and Python. WCAG 2.2 contrast checks over declared text pairs.
- Four presets: `neutral`, `ink`, `ocean` and `warm`.
- JSON Schemas for brand, deck and evidence files.
