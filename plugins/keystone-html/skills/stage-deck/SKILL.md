---
name: stage-deck
description: Use for every live deck — pitch, project or initiative proposal, keynote, class, report — whenever the user wants a presentation, a deck or slides. It is the default engine: scenes with motion, the product shown working and figures that cite their source. Composes deck.json from stage scenes (cover, persona, journey, mirror, product, why-now, matrix, model, funnel, timeline, projection, team, ask, closing, html) and builds it with build_stage.py. Also triggers on "pitch deck", "deck con animaciones", "que se vea pro", "efecto wow".
---

# Stage deck

The stage engine renders each slide as a composed scene on a 1920×1080 stage, with click steps, a presenter view (P) and the product running inside phones and laptops. Use it by default for any deck; the basic `build.py` engine is only for plain documents the user asks to keep simple.

Every figure that comes from the ledger shows its reference as a superscript (42%¹), and the slide lists the numbered sources at the foot. Keep it that way: never type a figure by hand, and give each external number a `source` in evidence.json.

## Before writing deck.json
1. Write talk.md with **narrative-arc**, and pick the type (`meta.type`: pitch, keynote, class, report). For a pitch, follow `references/pitch.md` of narrative-arc: it maps each slide to a scene.
2. Put every figure in evidence.json (**evidence-ledger**); scenes reference them as `{{fig:id}}`.

## Pick the scene that shows it

- A population where only part makes it (students who finish, producers who sell direct, patients who come back): **`journey`**, the people that drop out, never a percentage in a box.
- Anything that happens in a place (distance, coverage, who is near whom): **`map`**. Get the outline with
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/geo.py" <ISO3> --level ADM1 [--name REGION] -o <deck>/assets/<name>.geojson`
  and cite the line it prints (geoBoundaries, CC BY) in the slide's `source_note`.
- The product doing its job: **`product`**, driven by a scene script, never a screenshot.
- Two quantities that diverge over time: **`projection`**, with the gap labelled.

A deck where every slide is `figures` or `cards` reads like any other presentation; use at least one scene that moves people, places or the product.

## Scenes (layout → fields)

| Scene | Use it for | Fields |
|---|---|---|
| `cover` | promise + product | `kicker` (brand name), `title`, `text`, `device_route` |
| `persona` | a named person on a concrete day | `kicker`, `title`, `text`, `chips[]`, `device_route` |
| `journey` | a population; only part arrives | `title`, `total`, `arrive`, `stages[]`, `goal`, `proof` |
| `map` | where things are: people, producers, schools in a territory | `outline` (GeoJSON from `scripts/geo.py`), `bbox`, `hub{lon,lat,label}`, `rings[km]`, `points[{lon,lat,label,step}]`, `callout{text,step}` |
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
