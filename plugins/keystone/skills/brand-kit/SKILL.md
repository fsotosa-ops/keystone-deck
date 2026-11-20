---
name: brand-kit
description: Use when the user wants a deck, figure or video in their own colours, fonts or brand guide, asks to change the palette or theme, provides a brand guide (PDF, images, website), or starts a deck without a brand. Creates or imports brand.json (W3C Design Tokens), checks contrast, and compiles it to CSS, Apps Script, Remotion and Python. Also triggers on "paleta", "colores de marca", "guía de marca", "tema", "branding".
---

# Brand kit

Every engine reads one file, `brand.json`. Change it and the HTML deck, the Slides deck, the video and the figures all change together; the content does not move.

## Four ways in

Ask which one fits. Do not guess colours.

1. **Preset.** Run `keystone.py brand list`. There are four: `neutral`, `ink`, `ocean` and `warm`. Set `"brand": "preset:ocean"` in deck.json.
2. **From a website.** Open the site with Playwright and read the computed styles of `body`, headings, links, primary buttons and cards: background, text, accent and font families. Map them to roles (see below). Ask before visiting a site the user did not name.
3. **From a brand guide** (PDF or images). Read the pages *as images*: text extraction loses swatches. Take the hex values stated in the guide; never sample them from compressed images when the guide states them.
4. **Six questions.** Ask for the main colour, a second colour, light or dark preferred, a display font, a body font and the logo files. Derive the rest: dark and light backgrounds, ink, muted, border, `on-accent`, and the status colours.

## Roles, not swatches

`brand.json` names what each colour *does*. The required roles are:

| Group | Roles |
|---|---|
| Backgrounds | `bg-dark`, `bg-light`, `surface-dark`, `surface-light` |
| Text | `ink`, `ink-inverse`, `muted`, `muted-inverse` |
| Accents | `accent`, `on-accent`, `accent-2`, `highlight`, `on-highlight` |
| Status | `ok`, `bad`, `warn` |
| Other | `border`, `ai` |

`accent-inverse` is optional: an accent tuned for dark backgrounds, which falls back to `accent`. Fonts have three roles, `display`, `body` and `mono`, each given as a fallback stack.

`$extensions.keystone` holds:
- `name`;
- `fontsUrl` (Google Fonts);
- `assets` (`logo-light`, `logo-dark`, `mark`);
- `rules` (`maxAccentsPerSlide`, `highlightPieces`);
- `textPairs`: every text/background pair the brand allows, marked `normal` or `large`.

Aliases work: `"on-highlight": {"$value": "{color.ink}"}`. Schema: `${CLAUDE_PLUGIN_ROOT}/schemas/brand.schema.json`. Full reference: `docs/BRAND-TOKENS.md` in the repo.

## Procedure

1. Write `brand/brand.json` in the deck folder. Start by copying the preset closest to the guide: `${CLAUDE_PLUGIN_ROOT}/presets/<name>/brand.json`.
2. Check contrast:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" brand check brand/brand.json
   ```
   A failing pair is fixed by adjusting the colour, or by declaring it `large`-only if it is only ever used at 24 px and above. Never by deleting the pair.
3. Compile:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" brand compile brand/brand.json -o build/brand
   ```
   This writes `brand.css`, `brand.gs`, `theme.ts`, `palette.py` and `brand-sheet.html`.
4. **Render `brand-sheet.html` and look at it** (see render-review), then show it to the user. A brand is only used after the user approves the sheet.
5. Point deck.json at it: `"brand": "brand/brand.json"`.

## Rules

- Engines read colours only through the compiled outputs (`var(--ks-accent)`, `BRAND.color.accent`). A hex code typed into a template is a bug.
- Respect a guide's stated restrictions (for example, "never set the green as text on white") by leaving that pair out of `textPairs`.
- Do not use logos, names or trade dress of organisations the user does not own or represent.
