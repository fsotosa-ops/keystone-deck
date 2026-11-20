# Architecture

## Thesis

The value is in the method, not in any renderer. The method is a small set of rules: talk first, one question per slide, computed and sourced figures, form that encodes the relation, and one accent. keystone-deck separates three contracts, so that renderers can be swapped without touching content.

| Contract | Files | Owner skill | Checked by |
|---|---|---|---|
| Content | `talk.md`, `deck.json` | narrative-arc, visual-grammar | `keystone check` (talk, deck) |
| Evidence | `data/`, `evidence.json` | evidence-ledger | `keystone check` (evidence) |
| Brand | `brand.json` | brand-kit | `keystone brand check` |

## Repository layout

```
.claude-plugin/marketplace.json     lists the plugins in this repo
plugins/
  keystone/                         core: method, brand, checks (Python stdlib only)
    .claude-plugin/plugin.json
    skills/<name>/SKILL.md          narrative-arc, evidence-ledger, visual-grammar, brand-kit, render-review
    commands/                       /keystone:new, /keystone:brand, /keystone:review
    agents/deck-critic.md           read-only reviewer
    schemas/                        JSON Schemas for brand, deck, evidence
    presets/<name>/brand.json       neutral, ink, ocean, warm
    scripts/keystone.py             CLI; modules in scripts/ks/
    templates/new/                  what /keystone:new copies
  keystone-html/ keystone-slides/ keystone-video/   engines (planned)
docs/  tests/  scripts/scrub_check.sh
```

## The pipeline

1. `talk.md` is written and agreed with the user before any slide.
2. `deck.json` lists slides by `id` and `layout`. Text references figures as `{{fig:id}}` and sources as `{{ref:key}}`.
3. `keystone check` validates all three contracts. Errors fail the run; warnings are editorial advice.
4. `keystone resolve` writes `build/deck.resolved.json`:
   - placeholders are filled in;
   - references are numbered by first use;
   - each slide gets `_sources`, `_tiers` and its `_talk` (on-slide, spoken, leads-to, clicks, seconds).
5. `keystone brand compile` writes `build/brand/`.
6. An engine reads only `build/`. It never reads `talk.md` or `brand.json` directly, so every engine sees the same resolved truth.

## Engine contract

An engine plugin:
- declares the layouts it supports in `skills/<engine>/references/layouts.md`. An unsupported layout is an error, never a silent fallback;
- reads colours and fonts only from the compiled brand outputs;
- renders speaker notes from `_talk.spoken` and a source line from `_sources`;
- ships a render-and-look step that follows the core's render-review skill;
- keeps paths relative to the deck folder or `${CLAUDE_PLUGIN_ROOT}`, and detects binaries (Chrome, ffmpeg) at run time.

## Why these choices

- **JSON, not YAML,** for deck and ledger files: the core stays dependency-free, and editors validate against the published schemas.
- **DTCG tokens** for the brand: it is a W3C community standard, tools such as Figma and Style Dictionary already speak it, and aliases come for free.
- **Roles, not swatches:** the method needs "the colour for the single highlighted piece", not "blue 500". Roles make a brand portable across engines and checkable for contrast.
- **A marketplace of small plugins:** installing the deck method does not pull video dependencies.
