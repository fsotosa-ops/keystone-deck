---
name: stage-deck
description: Use when building a high-impact live deck (pitch, keynote, product demo) that needs motion, the product shown working, or slides at the level of a funded startup's pitch. Composes deck.json from stage scenes (cover, persona, journey, mirror, product, why-now, matrix, model, funnel, timeline, projection, team, ask, closing, html) and builds it with build_stage.py. Also triggers on "pitch deck", "deck con animaciones", "que se vea pro", "efecto wow".
---

# Stage deck

The stage engine renders each slide as a composed scene on a 1920×1080 stage, with click steps, a presenter view (P) and the product running inside phones and laptops. Use it when a slide must *show*, not list.

## Before writing deck.json
1. Write talk.md with **narrative-arc**, and pick the type (`meta.type`: pitch, keynote, class, report). For a pitch, follow `references/pitch.md` of narrative-arc: it maps each slide to a scene.
2. Put every figure in evidence.json (**evidence-ledger**); scenes reference them as `{{fig:id}}`.

## Scenes (layout → fields)

| Scene | Use it for | Fields |
|---|---|---|
| `cover` | promise + product | `kicker` (brand name), `title`, `text`, `device_route` |
| `persona` | a named person on a concrete day | `kicker`, `title`, `text`, `chips[]`, `device_route` |
| `journey` | a population; only part arrives | `title`, `total`, `arrive`, `stages[]`, `goal`, `proof` |
| `mirror` | each cause → its answer, per click | `pairs[{problem, problem_text, answer, answer_text}]` |
| `product` | the live product, driven by clicks | `laptop_route`, `phone_route`, plus a `scene` script |
| `why-now` | 2-3 reasons side by side | `reasons[{title, text}]` |
| `matrix` | competition on two axes | `axes{x_low,x_high,y_low,y_high}`, `players[{name,note,x,y}]`, `today`, `ours` (0-1 coords) |
| `model` | free side vs paid side + product | `free{who,price,text}`, `paid{…}`, routes |
| `funnel` | market as the payer's budget | `levels[{value, text}]` (last appears on click) |
| `timeline` | traction, "how we did it" | `milestones[{when, value, text}]` |
| `projection` | cost vs income, gap labelled | `periods[{label,note,cost,income}]`, `gap{period,text}`, `unit`, `legend` |
| `team` | why these people | `people[{initials,name,role,text}]` |
| `ask` | amount + use of funds | `amount`, `text`, `centre{value,label}`, `uses[{name, share}]` |
| `closing` | the last line, the person resolved | `title`, `text`, `device_route` |
| `html` | anything the argument needs that no scene covers | `html`: the slide body (see conventions) |

Common fields: `kicker`, `title` (thesis; `**x**` = accent), `theme` (`dark`/`light`), `scene` (name of a script in scenes.js), `source_note`.

## The product in devices
- Put the product, or a faithful mock, in `app/index.html`; set `meta.app` (default `../app/index.html`) and `meta.app_reset_keys` (localStorage keys cleared per slide).
- The app should expose `window.__app` with whatever the scripts need (reset, actions).
- `scenes.js` defines `window.ESCENAS[name] = { preparar(apps, slide, H), pasos: [async (apps, slide, H) => …] }`. Helpers `H`: `rotulo(slide, app, selector, {dato, texto, lado, ancho, dx, dy, vivo})` draws a ring and a callout that can read live numbers; `clic(slide, app, selector)` clicks visibly; `espera(ms)`.
- See `examples/pitch-asisto/` in the repo for a complete pitch.

## Conventions for `html` slides
`.kick`, `.tit` (with `<em>` accent), `.bajada`; `.a` enters with the slide (`style="--i:N"` staggers); `class="p" data-paso="N"` enters on click N; colours only via CSS variables.

## Build and review
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_stage.py" <deck-dir> [--brand brand.json]
python3 -m http.server 8770 --directory <deck-dir>/build   # open /stage/
```
Then **render-review**: open every slide with all steps, look for overlaps between devices, callouts and text, and check people/figures stay inside their areas. Callouts go in free lanes (between devices), never over data.
