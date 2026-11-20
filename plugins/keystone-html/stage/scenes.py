"""Scene library for the stage engine. Each scene takes a slide dict (from deck.resolved.json) and
returns the HTML body of a 1920x1080 slide. Scenes compose the reusable pieces of high-impact decks:
populations that move, the product live in devices, mirrors, matrices, funnels, timelines, charts
with labelled gaps, use-of-funds donuts and the team.

Conventions inside a slide body:
  .a            enters with the slide (stagger with style="--i:N")
  data-paso=N   enters on click N (class "p")
  data-app      a device that mounts the live product (data-ruta = the product route)
A slide with "layout": "html" passes its own "html" body through: Claude composes it for the argument.
"""

from __future__ import annotations

import html as _h
import math
import re

PERSON = '<svg viewBox="0 0 54 70"><circle cx="27" cy="16" r="13"/><path d="M4 70v-14a23 23 0 0 1 46 0v14z"/></svg>'


def md(t) -> str:
    """Escape; **x** becomes the accent."""
    t = _h.escape(str(t or ""))
    return re.sub(r"\*\*(.+?)\*\*", r"<em>\1</em>", t).replace("\n", "<br>")


def head(s, size=None, width=None):
    st = []
    if size:
        st.append(f"font-size:{size}px")
    if width:
        st.append(f"max-width:{width}ch")
    style = f' style="--i:1;{";".join(st)}"' if st else ' style="--i:1"'
    k = f'<div class="kick a">{md(s["kicker"])}</div>' if s.get("kicker") else ""
    t = f'<div class="tit a"{style}>{md(s.get("title", ""))}</div>' if s.get("title") else ""
    b = f'<div class="bajada a" style="--i:2">{md(s["text"])}</div>' if s.get("text") else ""
    return k + t + b


def tel(app, route, left, top, height):
    return (f'<div class="tel" data-app="{app}" data-ruta="{_h.escape(route)}" '
            f'style="left:{left}px;top:{top}px;height:{height}px;width:{round(height * 414 / 824)}px"></div>')


def laptop(app, route, left, top, width):
    return (f'<div class="laptop" data-app="{app}" data-ruta="{_h.escape(route)}" style="left:{left}px;top:{top}px;width:{width + 32}px">'
            f'<div class="pantalla"><div class="vidrio" style="width:{width}px"></div></div><div class="base"></div></div>')


def _rng(seed):
    st = [seed]

    def r():
        st[0] = (st[0] * 1103515245 + 12345) % 2147483648
        return st[0] / 2147483648
    return r


# ------------------------------------------------------------------ scenes

def cover(s):
    """Promise + the product in a phone. Fields: title, text, logo (svg/html), device_route."""
    phone = tel("tel", s["device_route"], 1290, 130, 820) if s.get("device_route") else ""
    brand = f'<div class="a marca-p" style="--i:0">{s.get("logo", "")}{md(s.get("kicker", ""))}</div>' if s.get("kicker") else ""
    return (f'<div style="position:absolute;left:140px;top:190px;width:1020px">{brand}'
            f'<div class="a" style="--i:1;font-size:104px;font-weight:700;letter-spacing:-.035em;line-height:1.0;margin-top:46px">{md(s.get("title", ""))}</div>'
            f'<div class="bajada a" style="--i:2;font-size:32px;margin-top:30px;max-width:34ch">{md(s.get("text", ""))}</div></div>{phone}')


def persona(s):
    """A named person in a concrete moment, with the product in their phone. Fields: kicker, title, text, chips[], device_route."""
    chips = "".join(f"<span>{md(c)}</span>" for c in s.get("chips", []))
    return (f'<div class="dos" style="grid-template-columns:860px 1fr"><div>{head(s, 64)}'
            f'<div class="chips-m a" style="--i:3">{chips}</div></div><div></div></div>'
            + (tel("tel", s["device_route"], 1240, 130, 820) if s.get("device_route") else ""))


def journey(s):
    """A population that sets out and only part arrives. Fields: total (100), arrive, stages[], goal, proof."""
    total, arrive = int(s.get("total", 100)), int(s.get("arrive", 80))
    stages = s.get("stages", ["Start", "", "", "", "End"])
    r = _rng(4242)
    lost, x = set(), 99
    while len(lost) < total - arrive:
        x = (x * 1103515245 + 12345) % 2147483648
        lost.add(x % total)
    cols = 13 if arrive > 40 else 8
    out, j = [], 0
    for k in range(total):
        x0, y0 = (k % 10) * 26, 60 + (k // 10) * 34
        if k not in lost:
            xf, yf = 1250 + (j % cols) * 30, 150 + (j // cols) * 44
            cls = "pc llega"; j += 1
        else:
            xf, yf = 300 + r() * 980, 330 + r() * 70
            cls = "pc pierde"
        out.append(f'<span class="{cls}" style="left:{x0}px;top:{y0}px;--tx:{xf - x0:.0f}px;--ty:{yf - y0:.0f}px;--d:{k * 18}ms">{PERSON}</span>')
    gap = 1320 / max(len(stages) - 1, 1)
    marks = "".join(f'<span style="left:{40 + n * gap:.0f}px">{md(d)}</span>' for n, d in enumerate(stages))
    proof = f'<div class="prueba a" style="--i:3">{md(s["proof"])}</div>' if s.get("proof") else ""
    return (head(s, 60, 38) + '<div class="camino"><div class="via"></div><div class="meses">' + marks + '</div>'
            f'<div class="meta-c">{md(s.get("goal", ""))}</div>' + "".join(out) + "</div>" + proof)


def _geo_rings(geo):
    """Outer rings of a GeoJSON Feature/FeatureCollection/Geometry as lists of (lon, lat)."""
    out = []
    def geom(g):
        if not g:
            return
        t, c = g.get("type"), g.get("coordinates")
        if t == "Polygon":
            out.append(c[0])
        elif t == "MultiPolygon":
            out.extend(poly[0] for poly in c)
        elif t == "GeometryCollection":
            for x in g.get("geometries", []):
                geom(x)
    if geo.get("type") == "FeatureCollection":
        for f in geo.get("features", []):
            geom(f.get("geometry"))
    elif geo.get("type") == "Feature":
        geom(geo.get("geometry"))
    else:
        geom(geo)
    return out


def map_(s):
    """A territory with points that light up click by click. Fields: outline (GeoJSON file in the deck folder,
    e.g. from Natural Earth), bbox [lon0, lat0, lon1, lat1] to zoom, hub {lon, lat, label}, rings [km], points
    [{lon, lat, label, step}] (step = click that reveals it; lines to the hub draw on reveal), callout {text, step}."""
    import json as _j, math
    from pathlib import Path as _P
    deck_dir = _P(s.get("_deck_dir", "."))
    rings_geo = []
    if s.get("outline"):
        rings_geo = _geo_rings(_j.loads((deck_dir / s["outline"]).read_text(encoding="utf-8")))
    pts, hub = s.get("points", []), s.get("hub")
    lons = [x for r in rings_geo for x, _ in r] + [q["lon"] for q in pts] + ([hub["lon"]] if hub else [])
    lats = [y for r in rings_geo for _, y in r] + [q["lat"] for q in pts] + ([hub["lat"]] if hub else [])
    lon0, lat0, lon1, lat1 = s.get("bbox") or (min(lons), min(lats), max(lons), max(lats))
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    W, H, X0, Y0 = 980, 820, 860, 150
    sc = min(W / max((lon1 - lon0) * kx, 1e-9), H / max(lat1 - lat0, 1e-9))
    ox = X0 + (W - (lon1 - lon0) * kx * sc) / 2
    oy = Y0 + (H - (lat1 - lat0) * sc) / 2
    def xy(lon, lat):
        return ox + (lon - lon0) * kx * sc, oy + (lat1 - lat) * sc
    paths = ""
    for r in rings_geo:
        if not any(lon0 - 2 <= x <= lon1 + 2 and lat0 - 2 <= y <= lat1 + 2 for x, y in r):
            continue
        d = "M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in (xy(x, y) for x, y in r)) + "Z"
        paths += f'<path d="{d}"/>'
    clip = f'<clipPath id="mclip"><rect x="{X0 - 60}" y="{Y0 - 60}" width="{W + 120}" height="{H + 120}" rx="24"/></clipPath>'
    svg = [f'<svg class="mapa-svg" viewBox="0 0 1920 1080" width="1920" height="1080"><defs>{clip}</defs><g class="tierra" clip-path="url(#mclip)">{paths}</g>']
    if hub:
        hx, hy = xy(hub["lon"], hub["lat"])
        for i, km in enumerate(s.get("rings", [])):
            rad = km / 111.32 * sc
            svg.append(f'<circle class="anillo a" style="--i:{i + 2}" cx="{hx:.1f}" cy="{hy:.1f}" r="{rad:.1f}"/>'
                       f'<text class="anillo-t a" style="--i:{i + 2}" x="{hx + rad * .72:.0f}" y="{hy - rad * .72:.0f}">{km} km</text>')
    for q in pts:
        x, y = xy(q["lon"], q["lat"]); st = int(q.get("step", 0))
        cls = f'class="punto p" data-paso="{st}"' if st else 'class="punto a" style="--i:3"'
        line = ""
        if hub:
            line = f'<line class="hilo" x1="{x:.1f}" y1="{y:.1f}" x2="{hx:.1f}" y2="{hy:.1f}"/>'
        svg.append(f'<g {cls}>{line}<circle cx="{x:.1f}" cy="{y:.1f}" r="13"/>'
                   f'<text x="{x + 20:.0f}" y="{y + 7:.0f}">{_h.escape(q.get("label", ""))}</text></g>')
    if hub:
        svg.append(f'<g class="hub a" style="--i:2"><circle cx="{hx:.1f}" cy="{hy:.1f}" r="20"/>'
                   f'<text x="{hx + 30:.0f}" y="{hy + 9:.0f}">{_h.escape(hub.get("label", ""))}</text></g>')
    svg.append("</svg>")
    co = s.get("callout")
    call = ""
    if co:
        st = int(co.get("step", 0))
        attr = f'class="mapa-call p" data-paso="{st}"' if st else 'class="mapa-call a" style="--i:4"'
        call = f'<div {attr}>{md(co["text"])}</div>'
    return f'<div class="mapa-izq">{head(s, 58, 16)}</div>' + "".join(svg) + call


def mirror(s):
    """Problem and solution in mirror, one pair per click. Fields: pairs[{problem, problem_text, answer, answer_text}]."""
    rows = ""
    for n, p in enumerate(s.get("pairs", []), 1):
        rows += (f'<div class="esp-a a" style="--i:{n + 1}"><span>{md(p["problem"])}</span>{md(p.get("problem_text", ""))}</div>'
                 f'<div class="esp-f p" data-paso="{n}">→</div>'
                 f'<div class="esp-b p" data-paso="{n}"><span>{md(p["answer"])}</span>{md(p.get("answer_text", ""))}</div>')
    return head(s, 56, 34) + f'<div class="espejo">{rows}</div>'


def product(s):
    """The product working: laptop + phone side by side. Fields: laptop_route, phone_route."""
    return (f'<div class="cab-app">{head(s)}</div>'
            + laptop("lap", s.get("laptop_route", "#/"), 140, 330, 900)
            + tel("tel", s.get("phone_route", "#/"), 1530, 270, 680))


def why_now(s):
    """Two (or three) reasons side by side. Fields: reasons[{title, text}]."""
    cols = "".join(f'<div class="a" style="--i:{n + 2}"><div class="big">{n + 1}</div><b>{md(r["title"])}</b>{md(r.get("text", ""))}</div>'
                   for n, r in enumerate(s.get("reasons", [])))
    return head(s, 60, 34) + f'<div class="dos-col" style="grid-template-columns:repeat({len(s.get("reasons", [])) or 2},1fr)">{cols}</div>'


def matrix(s):
    """Competition on two axes; ours appears on click. Fields: axes{x_low,x_high,y_low,y_high}, players[{name, note, x, y}], ours{name, note, x, y}, today{...}."""
    ax = s.get("axes", {})
    pts = "".join(f'<div class="pto" style="left:{p["x"] * 100:.0f}%;top:{(1 - p["y"]) * 100:.0f}%">{md(p["name"])}<span>{md(p.get("note", ""))}</span></div>'
                  for p in s.get("players", []))
    if s.get("today"):
        t = s["today"]
        pts += f'<div class="pto gris" style="left:{t["x"] * 100:.0f}%;top:{(1 - t["y"]) * 100:.0f}%">{md(t["name"])}<span>{md(t.get("note", ""))}</span></div>'
    o = s.get("ours", {})
    pts += f'<div class="pto nuestro p" data-paso="1" style="left:{o.get("x", .78) * 100:.0f}%;top:{(1 - o.get("y", .8)) * 100:.0f}%">{md(o.get("name", ""))}<span>{md(o.get("note", ""))}</span></div>'
    q = lambda a, b: f"{md(a)} · {md(b)}"
    return (head(s, 52, 38) + '<div class="cuadrante a" style="--i:2">'
            f'<div class="q q1"><span>{q(ax.get("y_high", ""), ax.get("x_low", ""))}</span></div><div class="q q2"><span>{q(ax.get("y_high", ""), ax.get("x_high", ""))}</span></div>'
            f'<div class="q q3"><span>{q(ax.get("y_low", ""), ax.get("x_low", ""))}</span></div><div class="q q4"><span>{q(ax.get("y_low", ""), ax.get("x_high", ""))}</span></div>'
            '<div class="ej-x"></div><div class="ej-y"></div>'
            f'<div class="et et-arr">{md(ax.get("y_high", ""))} ↑</div><div class="et et-aba">↓ {md(ax.get("y_low", ""))}</div>'
            f'<div class="et et-izq">← {md(ax.get("x_low", ""))}</div><div class="et et-der">{md(ax.get("x_high", ""))} →</div>'
            + pts + "</div>")


def model(s):
    """Free side vs paid side, with the product next to it. Fields: free{who, price, text}, paid{who, price, text}, laptop_route, phone_route."""
    f, p = s.get("free", {}), s.get("paid", {})
    card = lambda c, paid, i: (f'<div class="a" style="--i:{i};{"background:var(--azul);color:#fff;box-shadow:0 20px 40px -14px var(--azul)" if paid else "background:#fff;box-shadow:0 10px 30px rgba(16,33,58,.07)"};border-radius:22px;padding:24px">'
                               f'<div style="font-size:20px;font-weight:700;opacity:.8">{md(c.get("who", ""))}</div>'
                               f'<div style="font-size:64px;font-weight:700;letter-spacing:-.03em">{md(c.get("price", ""))}</div>'
                               f'<div style="font-size:20px;opacity:.85">{md(c.get("text", ""))}</div></div>')
    return (f'<div style="position:absolute;left:140px;top:150px;width:640px">{head(s, 50)}'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:40px">{card(f, False, 2)}{card(p, True, 3)}</div></div>'
            + laptop("lap", s.get("laptop_route", "#/"), 820, 260, 740) + tel("tel", s.get("phone_route", "#/"), 1630, 380, 500))


def funnel(s):
    """Market as the payer's budget. Fields: levels[{value, text}] (the last one appears on click)."""
    lv = s.get("levels", [])
    rows = "".join(f'<div class="{"p" if n == len(lv) - 1 else "a"}" {"data-paso=1" if n == len(lv) - 1 else f"style=--i:{n + 2}"}><b>{md(l["value"])}</b>{md(l.get("text", ""))}</div>'
                   for n, l in enumerate(lv))
    return head(s, 56, 36) + f'<div class="embudo" style="margin-top:50px">{rows}</div>'


def timeline(s):
    """Traction as 'how we did it'. Fields: milestones[{when, value, text}]."""
    ms = "".join(f'<div class="a" style="--i:{n + 2}"><span class="pt"></span><b>{md(m["when"])}</b><div class="cifra">{md(m["value"])}</div>{md(m.get("text", ""))}</div>'
                 for n, m in enumerate(s.get("milestones", [])))
    return head(s, 56, 36) + f'<div class="hitos" style="grid-template-columns:repeat({len(s.get("milestones", [])) or 4},1fr)">{ms}</div>'


def projection(s):
    """Cost vs income per period with the gap labelled on click. Fields: periods[{label, note, cost, income}], gap{period, text}, unit."""
    per = s.get("periods", [])
    unit = s.get("unit", "")
    vmax = max([p["cost"] for p in per] + [p["income"] for p in per] + [1]) * 1.15
    W, H, base = 1000, 600, 500
    y = lambda v: base - v / vmax * 420
    out = [f'<svg class="graf" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    for n, p in enumerate(per):
        x = 150 + n * 290
        out.append(f'<rect class="barra v" x="{x}" y="{y(p["cost"])}" width="96" height="{base - y(p["cost"])}" rx="8" fill="var(--suave-o)" style="transition-delay:{n * 150}ms"/>'
                   f'<text class="val" x="{x + 48}" y="{y(p["cost"]) - 14}" text-anchor="middle">{p["cost"]}{unit}</text>'
                   f'<rect class="barra v" x="{x + 108}" y="{y(p["income"])}" width="96" height="{base - y(p["income"])}" rx="8" fill="var(--menta)" style="transition-delay:{n * 150 + 80}ms"/>'
                   f'<text class="val" x="{x + 156}" y="{y(p["income"]) - 14}" text-anchor="middle">{p["income"]}{unit}</text>'
                   f'<text class="rot" x="{x + 102}" y="{base + 40}" text-anchor="middle">{md(p["label"])}</text>'
                   f'<text class="eje" x="{x + 102}" y="{base + 70}" text-anchor="middle">{md(p.get("note", ""))}</text>')
    g = s.get("gap")
    if g is not None:
        n = g.get("period", 1); p = per[n]; x = 150 + n * 290
        out.append(f'<g class="p" data-paso="1"><path d="M{x + 214} {y(p["cost"])}h20v{y(p["income"]) - y(p["cost"]):.0f}h-20" stroke="var(--ambar-o)" stroke-width="3" fill="none"/>'
                   f'<text x="{x + 48}" y="{min(y(p["cost"]), y(p["income"])) - 52:.0f}" text-anchor="middle" style="font-size:24px;font-weight:700;fill:var(--ambar-o)">{md(g["text"])}</text></g>')
    leg = s.get("legend", ["Cost", "Income"])
    out.append(f'<rect x="640" y="18" width="22" height="22" rx="5" fill="var(--suave-o)"/><text class="eje" x="672" y="36">{md(leg[0])}</text>'
               f'<rect x="770" y="18" width="22" height="22" rx="5" fill="var(--menta)"/><text class="eje" x="802" y="36">{md(leg[1])}</text></svg>')
    return f'<div class="dos" style="grid-template-columns:600px 1fr"><div>{head(s, 58)}</div><div class="a" style="--i:2">{"".join(out)}</div></div>'


def team(s):
    """Fields: people[{initials, name, role, text}]."""
    ppl = s.get("people", [])
    cards = "".join(f'<div class="persona a" style="--i:{n + 2}"><div class="av">{md(p.get("initials", ""))}</div><h3>{md(p["name"])}</h3>'
                    f'<div class="rol">{md(p.get("role", ""))}</div><p>{md(p.get("text", ""))}</p></div>' for n, p in enumerate(ppl))
    return head(s, 54, 36) + f'<div class="equipo" style="grid-template-columns:repeat({min(len(ppl), 4) or 3},1fr)">{cards}</div>'


def ask(s):
    """The ask with use of funds, one slice per click. Fields: amount, text, centre{value, label}, uses[{name, share}]."""
    uses = s.get("uses", [])
    cols = ["var(--azul)", "var(--menta)", "var(--ambar-o)", "var(--suave-o)", "var(--ok)"]
    r, c = 170, 2 * math.pi * 170
    arcs, acc = [], 0
    for n, u in enumerate(uses):
        arcs.append(f'<circle class="arco p" data-paso="{n + 1}" cx="220" cy="220" r="{r}" fill="none" stroke="{cols[n % 5]}" stroke-width="64" '
                    f'stroke-dasharray="{c * u["share"] - 4:.1f} {c:.1f}" stroke-dashoffset="{-c * acc:.1f}" transform="rotate(-90 220 220)"/>')
        acc += u["share"]
    ctr = s.get("centre", {})
    donut = (f'<svg class="graf" width="440" height="440" viewBox="0 0 440 440"><circle cx="220" cy="220" r="{r}" fill="none" stroke="var(--sup-o)" stroke-width="64"/>{"".join(arcs)}'
             f'<text x="220" y="216" text-anchor="middle" style="font-size:72px;font-weight:700;fill:#fff">{md(ctr.get("value", ""))}</text>'
             f'<text x="220" y="258" text-anchor="middle" class="eje">{md(ctr.get("label", ""))}</text></svg>')
    leg = "".join(f'<div class="p" data-paso="{n + 1}"><i style="background:{cols[n % 5]}"></i><b>{int(u["share"] * 100)}%</b>{md(u["name"])}</div>' for n, u in enumerate(uses))
    return (f'<div class="kick a">{md(s.get("kicker", ""))}</div><div class="ask5" style="grid-template-columns:700px 1fr;align-items:center"><div>'
            f'<div class="monto a" style="--i:1;font-size:150px;white-space:nowrap">{md(s.get("amount", ""))}</div>'
            f'<div class="bajada a" style="--i:2;font-size:28px;color:#fff;margin-top:10px">{md(s.get("text", ""))}</div></div>'
            f'<div class="a" style="--i:2"><div class="torta">{donut}<div class="torta-ley">{leg}</div></div></div></div>')


def closing(s):
    """Fields: title, text, device_route."""
    return (f'<div style="position:absolute;left:140px;top:260px;width:1050px"><div class="tit a" style="font-size:92px;max-width:none">{md(s.get("title", ""))}</div>'
            f'<div class="bajada a" style="--i:2;font-size:34px;color:#fff;margin-top:40px">{md(s.get("text", ""))}</div></div>'
            + (tel("tel", s["device_route"], 1340, 140, 800) if s.get("device_route") else ""))


def custom(s):
    """Claude composes the slide body for this argument (same conventions as the scenes)."""
    return s.get("html", "")


SCENES = {"cover": cover, "persona": persona, "journey": journey, "mirror": mirror, "product": product,
          "why-now": why_now, "map": map_, "matrix": matrix, "model": model, "funnel": funnel, "timeline": timeline,
          "projection": projection, "team": team, "ask": ask, "closing": closing, "html": custom}

# Light slides by default for these scenes (the rest are dark), unless the slide sets "theme".
LIGHT = {"mirror", "product", "matrix", "model", "team"}

EXTRA_CSS = """
.mapa-izq { position: absolute; left: 140px; top: 150px; width: 640px; }
.mapa-svg { position: absolute; inset: 0; pointer-events: none; }
.mapa-svg .tierra path { fill: color-mix(in srgb, var(--menta) 10%, transparent); stroke: color-mix(in srgb, var(--menta) 55%, transparent); stroke-width: 2; }
.clara .mapa-svg .tierra path { fill: color-mix(in srgb, var(--azul) 7%, transparent); stroke: color-mix(in srgb, var(--azul) 40%, transparent); }
.mapa-svg .anillo { fill: none; stroke: currentColor; stroke-dasharray: 6 8; opacity: .35; color: var(--tinta-o); }
.clara .mapa-svg .anillo { color: var(--tinta-c); }
.mapa-svg .anillo-t { font-size: 20px; fill: var(--suave-o); }
.clara .mapa-svg .anillo-t { fill: var(--suave-c); }
.mapa-svg .punto circle { fill: var(--menta); stroke: var(--fondo-o); stroke-width: 4; }
.clara .mapa-svg .punto circle { fill: var(--azul); stroke: #fff; }
.mapa-svg .punto text, .mapa-svg .hub text { font-size: 22px; font-weight: 600; fill: var(--tinta-o); }
.clara .mapa-svg .punto text, .clara .mapa-svg .hub text { fill: var(--tinta-c); }
.mapa-svg .hilo { stroke: var(--menta); stroke-width: 3; stroke-dasharray: 600; stroke-dashoffset: 600; transition: stroke-dashoffset 1s var(--curva) .15s; }
.clara .mapa-svg .hilo { stroke: var(--azul); }
.mapa-svg .punto.ver .hilo, .mapa-svg .punto.a .hilo { stroke-dashoffset: 0; }
.mapa-svg .punto.ver circle { animation: late 1.2s var(--curva) 1; transform-box: fill-box; transform-origin: center; }
@keyframes late { 0% { transform: scale(0); } 55% { transform: scale(1.5); } 100% { transform: scale(1); } }
.mapa-svg .hub circle { fill: #F4A93C; stroke: var(--fondo-o); stroke-width: 5; }
.clara .mapa-svg .hub circle { stroke: #fff; }
.mapa-call { position: absolute; left: 140px; bottom: 170px; width: 620px; font-size: 30px; line-height: 1.3; padding: 22px 26px; border-radius: 14px; background: color-mix(in srgb, var(--menta) 14%, transparent); }
.clara .mapa-call { background: color-mix(in srgb, var(--azul) 9%, transparent); }

.disclosure { position: fixed; right: 26px; top: 22px; z-index: 50; font: 500 15px var(--ks-font-body, sans-serif); color: #fff; background: rgba(15, 23, 42, .62); padding: 6px 12px; border-radius: 6px; letter-spacing: .01em; }
.win { transition: transform 1.2s var(--curva); transform-origin: var(--zx, 50%) var(--zy, 50%); }
.big-line { position: absolute; inset: 0; display: grid; place-items: center; font: 700 110px var(--ks-font-display); letter-spacing: -.03em; color: #fff; }
.win { position: absolute; border-radius: 14px; overflow: hidden; background: #fff; box-shadow: 0 40px 90px -30px rgba(11,31,77,.45); border: 1px solid var(--borde-c); }
.wbar { height: 40px; background: #EEF1F5; display: flex; align-items: center; gap: 8px; padding: 0 16px; font-size: 16px; color: #5B6575; }
.wbar i { width: 12px; height: 12px; border-radius: 50%; background: #D5DAE1; } .wbar i:nth-child(1){background:#FF5F57} .wbar i:nth-child(2){background:#FEBC2E} .wbar i:nth-child(3){background:#28C840}
.wbar span { margin-left: 12px; } .wbar.pp { background: #B7472A; color: #fff; }
.wbody { position: relative; overflow: hidden; } .wbody iframe { border: 0; transform-origin: 0 0; position: absolute; left: 0; top: 0; }
.dosmarcas .win { position: absolute; }
.cmd { display: inline-block; margin-top: 46px; font-family: var(--ks-font-mono, monospace); font-size: 30px; padding: 16px 28px; border-radius: 12px; background: rgba(255,255,255,.08); color: var(--menta); }
.lam em { font-style: normal; color: var(--menta); } .lam.clara em { color: var(--azul); }
.marca-p svg { width: 84px; height: 84px; }
.firma svg { border-radius: 9px; } .firma b { color: var(--suave-o); font-weight: 500; font-size: 18px; } .clara .firma b { color: var(--suave-c); }
.fuente { left: 520px !important; }
.marca-p svg { border-radius: 20px; }
.chips-m { display: flex; gap: 12px; margin-top: 34px; }
.chips-m span { font-size: 22px; padding: 8px 18px; border-radius: 999px; background: color-mix(in srgb, var(--menta) 16%, transparent); color: var(--menta); font-weight: 600; }
.camino .pc.pierde svg { fill: var(--suave-o); } .lam.activa .camino .pc.pierde { opacity: .32; }
.camino .meta-c { top: 70px !important; right: 120px !important; font-size: 26px !important; }
.camino .pc.llega svg { fill: #fff; } .lam.activa .camino .pc.llega svg { fill: var(--menta); }
.camino .via { background: linear-gradient(90deg, var(--sup-o), var(--menta)) !important; }
.prueba { position: absolute; left: 140px; bottom: 110px; font-size: 24px; color: var(--suave-o); } .prueba em, .prueba b { color: var(--menta); font-style: normal; }
.espejo { display: grid; grid-template-columns: 680px 110px 680px; gap: 22px 0; margin-top: 50px; align-items: stretch; }
.esp-a, .esp-b { border-radius: 22px; padding: 22px 30px; font-size: 24px; line-height: 1.3; color: var(--suave-c); background: #fff; border: 1px solid var(--borde-c); }
.esp-b { background: var(--azul); color: #fff; border-color: var(--azul); }
.espejo span { display: block; font-size: 32px; font-weight: 700; color: var(--tinta-c); margin-bottom: 4px; }
.espejo .esp-b span { color: #fff; }
.esp-f { font-size: 52px; color: var(--azul); display: grid; place-items: center; font-weight: 700; }
.dos-col { display: grid; gap: 60px; margin-top: 60px; }
.dos-col > div { font-size: 26px; line-height: 1.4; color: var(--suave-o); border-top: 3px solid var(--menta); padding-top: 26px; }
.dos-col .big { font-size: 96px; font-weight: 700; color: var(--menta); line-height: 1; margin-bottom: 10px; }
.dos-col b { display: block; font-size: 40px; color: #fff; margin-bottom: 10px; }
.torta { display: flex; align-items: center; gap: 40px; }
.torta-ley { display: flex; flex-direction: column; gap: 16px; font-size: 22px; color: var(--tinta-o); }
.torta-ley i { display: inline-block; width: 18px; height: 18px; border-radius: 5px; margin-right: 12px; vertical-align: -2px; } .torta-ley b { margin-right: 8px; }
.graf .arco.p { opacity: 0; transition: opacity .6s var(--curva); } .graf .arco.p.ver { opacity: 1; }
"""
