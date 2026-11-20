# Brand tokens reference

`brand.json` follows the [W3C Design Tokens Community Group format](https://tr.designtokens.org/format/). Tokens have a `$value` and can inherit `$type` from their group. Aliases use `{group.token}`.

## Colour roles

| Role | Used for | Must contrast with |
|---|---|---|
| `bg-dark`, `bg-light` | slide backgrounds, for argument and for evidence | |
| `surface-dark`, `surface-light` | cards on each background | |
| `ink`, `ink-inverse` | main text on light and on dark | `bg-light`, `surface-light` / `bg-dark`, `surface-dark` |
| `muted`, `muted-inverse` | secondary text, source lines | the matching background |
| `border` | card borders, rules | |
| `accent` | kicker, big figures, the highlighted piece's fill | `bg-light` (large text) |
| `accent-inverse` *(optional)* | kicker and figures on dark | `bg-dark` |
| `on-accent` | text on an accent fill | `accent` |
| `accent-2` | a second series in charts; never as a second emphasis | |
| `highlight`, `on-highlight` | the single exception per deck: a target or a warning | each other |
| `ok`, `bad`, `warn` | status, always paired with a word | `bg-light` |
| `ai` | content an AI proposed and a person has not approved | |

## Fonts

`font.display`, `font.body` and `font.mono` are each a `fontFamily` stack, with the first entry preferred. `$extensions.keystone.fontsUrl` is loaded by HTML outputs. Google Slides only accepts a single family name, so the Slides engine uses the first entry of each stack.

## Shape and motion

`shape.radius`, `shape.border-width` (`dimension`), `motion.ease` (`cubicBezier`) and `motion.step` (`duration`). They compile to `--ks-radius`, `--ks-border-width`, `--ks-ease` and `--ks-step`.

## `$extensions.keystone`

| Key | Meaning |
|---|---|
| `name` | display name |
| `fontsUrl` | stylesheet URL for the fonts |
| `assets` | `logo-light`, `logo-dark` and `mark`, as paths relative to brand.json |
| `rules.maxAccentsPerSlide` | default 1 |
| `rules.highlightPieces` | default 1; `keystone check` enforces it |
| `textPairs` | `[fg, bg]` or `[fg, bg, "large"]`: every pair the brand allows as text. Checked against WCAG 2.2: 4.5:1 for normal text, 3:1 for large text. |

## Compiled outputs

| File | Shape |
|---|---|
| `brand.css` | `@import` of the fonts, plus `:root { --ks-<role>: … }` |
| `brand.gs` | `var BRAND = { color, font, fontStack, shape, motion, assets, rules }` |
| `theme.ts` | `export const brand = {…} as const` |
| `palette.py` | `BRAND = {…}`; `COLOR = BRAND['color']` |
| `brand-sheet.html` | swatches, a dark and a light sample slide, and the contrast table |
