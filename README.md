<div align="center">

<img src="docs/assets/icon.png" width="88" alt="">

# keystone-deck

**High-impact presentations as code for Claude Code.** Write the talk first, back every number with a source, keep each slide to one claim, and render it all in your own brand.

[![Version](https://img.shields.io/badge/version-0.2.0-informational)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/fsotosa-ops/keystone-deck/actions/workflows/ci.yml/badge.svg)](https://github.com/fsotosa-ops/keystone-deck/actions/workflows/ci.yml)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757)](https://docs.claude.com/en/docs/claude-code/plugins)

[English](README.md) · [Español](README.es.md)

<img src="docs/assets/hero.png" width="860" alt="The same slide rendered with four brand presets: neutral, ink, ocean and warm">

</div>

---

## Why

Most AI-generated decks fail the same way. The slides are lists of topics, the numbers have no source, everything is highlighted, and the speaker reads the slide aloud. keystone-deck packages a method that avoids those failures into skills Claude follows on its own, and adds checks that fail the build when the method is broken.

1. **The talk comes first.** `talk.md` is the single source for slide order, speaker notes and timing. Each slide answers the question the previous one left open.
2. **Every figure is computed and sourced.** Numbers live in an evidence ledger, tagged as verified, project, assumption or decision, and reach slides only through `{{fig:id}}`.
3. **The form says the relation.** A cycle repeats, a funnel filters, a matrix positions. Each slide has one accent, one highlighted piece and about 25 visible words.
4. **Bring your own brand.** One `brand.json` (W3C Design Tokens) is contrast-checked and compiled for every renderer. Change the brand and every output follows; the content does not move.

## Install

In Claude Code:

```text
/plugin marketplace add fsotosa-ops/keystone-deck
/plugin install keystone@keystone-deck
/plugin install keystone-html@keystone-deck
/plugin install keystone-pptx@keystone-deck
```

The core plugin needs Python 3.10 or later and nothing else. The engines need Chrome or Chromium; the PowerPoint export also uses `python-pptx`, `playwright` and `imageio-ffmpeg` (run it with `uv run --with …`).

**Claude Code and claude.ai.** The method (skills and commands) works in both. Building decks runs local scripts and a browser, so the engines need Claude Code.

## Example

`examples/pitch-asisto/` is a complete investor pitch for a fictitious startup: `talk.md`, `deck.json`, `evidence.json`, a mock product in `app/` and the click scripts in `scenes.js`. Build it with `build_stage.py`, present it in the browser, or export it with `build_pptx.py`.

## Quickstart

```text
/keystone:new quarterly-review --brand preset:ocean
```

Claude asks who the audience is and what they must decide, writes `talk.md`, and shows you the slide sequence before it writes `deck.json`. Then:

```text
/keystone:brand path/to/brand-guide.pdf     # or a website, or preset:ink
/keystone:review quarterly-review           # every check, plus an independent critic
```

## What's inside

### Plugins

| Plugin | Status | What it does | Requires |
|---|---|---|---|
| `keystone` | **0.1** | Method, brand kit, checks, scaffolding | Python 3.10+ |
| `keystone-html` | **0.2** | Live 1920×1080 decks built from high-impact scenes: populations that move, the product running in phones and laptops with live callouts, mirrors, matrices, projections with labelled gaps, use of funds | Python, Chrome |
| `keystone-pptx` | **0.2** | PowerPoint that keeps the motion: each scene recorded to video, titles as native editable text, speaker notes | Python, Chrome, ffmpeg |
| `keystone-video` | planned | Narrated video from the talk, with optional voice | Node, ffmpeg |

### Skills (`keystone`)

Skills load automatically when a request matches. They respond to requests in English and Spanish.

| Skill | Triggers when you… |
|---|---|
| `narrative-arc` | plan or fix a talk, pitch or deck, or the flow feels like a list |
| `evidence-ledger` | put numbers, projections or citations on slides |
| `visual-grammar` | design or critique a slide, choose a diagram, or feel it is crowded |
| `brand-kit` | want your colours, fonts or guide, or change the theme |
| `render-review` | finish any visual change, before calling it done |
| `stage-deck` (keystone-html) | want a pitch or keynote with motion and the product shown working |
| `pptx-export` (keystone-pptx) | need the deck as PowerPoint for people who don't use HTML |

### Commands and agents

| | Name | Purpose |
|---|---|---|
| command | `/keystone:new <folder>` | Scaffold `talk.md`, `deck.json`, `evidence.json`, `data/` |
| command | `/keystone:brand [source]` | Create, import, check and compile a brand |
| command | `/keystone:review [folder]` | Run every check and an independent review |
| agent | `deck-critic` | Read-only reviewer of argument, evidence and rendering |

## Bring your own brand

A brand is a set of colour *roles* the method needs, plus three font roles:

```jsonc
{
  "color": {
    "$type": "color",
    "bg-dark":  { "$value": "#0A1A2A" },
    "accent":   { "$value": "#1E74B8" },
    "on-accent":{ "$value": "#FFFFFF" },
    "on-highlight": { "$value": "{color.ink}" }   // aliases resolve
    // … 15 more roles
  },
  "font": { "display": { "$value": ["Plus Jakarta Sans", "Arial", "sans-serif"] } },
  "$extensions": { "keystone": {
    "textPairs": [["ink", "bg-light"], ["accent", "bg-light", "large"]]
  } }
}
```

There are four ways to get one:
- a **preset** (`neutral`, `ink`, `ocean`, `warm`);
- **imported from a website**, by reading its computed styles;
- **read from a brand-guide PDF**;
- **six questions** Claude asks you.

`brand check` verifies every declared text pair against WCAG 2.2, and `brand compile` refuses a brand that fails.

```text
brand.json ──► brand.css    CSS custom properties   (HTML decks, figures)
           ├─► brand.gs     Apps Script constant    (Google Slides)
           ├─► theme.ts     typed object            (Remotion video)
           ├─► palette.py   dict                    (matplotlib, openpyxl)
           └─► brand-sheet.html  swatches + sample slides, for approval
```

The full reference is in [docs/BRAND-TOKENS.md](docs/BRAND-TOKENS.md).

## How it works

```text
            content            evidence             brand
          ┌──────────┐      ┌─────────────┐     ┌────────────┐
          │ talk.md  │      │ data/*.py   │     │ brand.json │
          │ deck.json│      │ evidence.json│    │  (tokens)  │
          └────┬─────┘      └──────┬──────┘     └─────┬──────┘
               └──────── keystone check / resolve ────┘
                                   │
               build/deck.resolved.json  +  build/brand/*
                                   │
           ┌───────────────┬───────┴───────┬────────────────┐
       keystone-html   keystone-slides  keystone-video   your engine
```

Engines are renderers over three contracts, so they are interchangeable. A shared vocabulary of twelve layouts (`cover`, `thesis`, `figures`, `cards`, `flow`, `cycle`, `funnel`, `comparison`, `matrix`, `device`, `quote`, `appendix-thread`) keeps one `deck.json` portable across them. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design.

## The CLI

Skills call the CLI for you, and you can also run it directly:

```bash
K=plugins/keystone/scripts/keystone.py
python3 $K new my-deck --brand preset:warm
python3 $K check my-deck          # brand contrast, deck rules, talk, evidence
python3 $K resolve my-deck        # build/deck.resolved.json for engines
python3 $K brand compile preset:ink -o build/brand
```

It exits non-zero on errors; warnings never fail. Typical output:

```text
[brand Ocean] ok, 0 warning(s)
[deck] ok, 1 warning(s)
  warn   market: title 'Market' reads like a label; state the claim
[talk] 1 error(s), 0 warning(s)
  ERROR  traction: no **Leads to:** (the question the next slide answers)
[evidence] ok, 1 warning(s)
  warn   problem: typed number '340'; compute it in the ledger and use {{fig:...}}
```

## Quality

- `python3 -m unittest discover tests/unit`: brand loading, alias resolution, contrast, compile targets, talk parsing, deck and evidence rules, and the scaffold.
- `claude plugin validate .`: marketplace and plugin manifests.
- Every preset passes WCAG 2.2 AA for its declared pairs. CI enforces this.

## Roadmap

- [x] 0.1: core method, brand kit, checks, four presets
- [x] 0.2: stage engine with scenes, presentation types (pitch, keynote, class, report), PowerPoint export, a full pitch example (`examples/pitch-asisto`)
- [ ] 0.3: narrated video from the talk
- [ ] 1.0: golden-image tests and trigger evals for the engines

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). New layouts or engines must keep the three contracts unchanged.

## Security

The plugins run local scripts only. Optional integrations, such as a voice API in `keystone-video`, read keys from environment variables and never store them. Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
