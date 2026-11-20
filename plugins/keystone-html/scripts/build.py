#!/usr/bin/env python3
"""Build a live HTML deck from a keystone deck folder.

  build.py <deck-dir> [--out build/html] [--core PATH/keystone.py] [--shots]

Steps: run the core's `check`, `resolve` and `brand compile`, render each slide by layout,
and write index.html, presenter.html, deck.js, deck.css and brand.css to --out.
With --shots, also save one PNG per slide (all steps open) to <out>/shots/ using headless Chrome.
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
RUNTIME = PLUGIN / "runtime"
SIZES = {"16:9": ("s16x9", 1920, 1080), "4:5": ("s4x5", 1080, 1350), "1:1": ("s1x1", 1080, 1080)}
SUPPORTED = {"cover", "thesis", "figures", "cards", "flow", "cycle", "funnel", "comparison",
             "matrix", "device", "quote", "appendix-thread", "code", "dots", "bars"}
STRINGS = {
    "en": {"sources": "Sources", "S": "Includes estimates.", "D": "Includes targets.", "back": "and back to the start"},
    "es": {"sources": "Fuentes", "S": "Incluye estimaciones.", "D": "Incluye metas.", "back": "y vuelta al inicio"},
}


def find_core(explicit: str | None) -> Path:
    candidates = [explicit, os.environ.get("KEYSTONE_CORE"),
                  str(PLUGIN.parent / "keystone" / "scripts" / "keystone.py")]
    candidates += sorted(glob.glob(os.path.expanduser(
        "~/.claude/plugins/cache/*/keystone/*/scripts/keystone.py")), reverse=True)
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise SystemExit("keystone core not found. Install the `keystone` plugin, or pass --core / set KEYSTONE_CORE.")


def core(cli: Path, *args) -> None:
    r = subprocess.run([sys.executable, str(cli), *args], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"core step failed: {' '.join(args)}")


# ------------------------------------------------------------------ text

def md(text) -> str:
    """Escape, then allow **accent** and line breaks."""
    t = html.escape(str(text or ""))
    t = re.sub(r"\*\*(.+?)\*\*", r"<em>\1</em>", t)
    return t.replace("\n", "<br>")


def cls_step(slide, i=None) -> str:
    return "step" if slide.get("reveal") == "items" else "a"


def hl_set(slide) -> set:
    h = slide.get("highlight")
    if h is None:
        return set()
    return set(h) if isinstance(h, list) else {h}


def head(s, hero=False) -> str:
    k = f'<div class="kicker a">{md(s["kicker"])}</div>' if s.get("kicker") else ""
    t = f'<h2 class="title{" hero" if hero else ""} a">{md(s.get("title", ""))}</h2>' if s.get("title") else ""
    x = f'<p class="text a">{md(s["text"])}</p>' if s.get("text") else ""
    return f'<div class="head">{k}{t}{x}</div>'


# ------------------------------------------------------------------ layouts

def L_cover(s, _):
    k = f'<div class="kicker a">{md(s["kicker"])}</div>' if s.get("kicker") else ""
    sub = f'<p class="text a">{md(s["subtitle"])}</p>' if s.get("subtitle") else ""
    return f'<div class="head">{k}<h1 class="title a">{md(s.get("title"))}</h1>{sub}</div>'


def L_thesis(s, _):
    return head(s, hero=True)


def L_quote(s, _):
    return (f'<div class="head"><p class="q a">{md(s.get("text"))}</p>'
            f'<p class="who muted a">{md(s.get("who"))}</p></div>')


def L_figures(s, _):
    st, hl = cls_step(s), hl_set(s)
    n = max(len(s.get("figures", [])), 1)
    longest = max((len(str(f["value"])) for f in s.get("figures", [])), default=1)
    fit = f' style="font-size:min(var(--t-fig), {int(1700 / n / (0.5 * longest))}px)"'
    figs = "".join(f'<div class="fig {st}{" hl" if i in hl else ""}"><div class="v"{fit}>{md(f["value"])}</div>'
                   f'<div class="l">{md(f["label"])}</div></div>' for i, f in enumerate(s.get("figures", [])))
    return head(s) + f'<div class="figs">{figs}</div>'


def L_cards(s, _):
    st, hl, items = cls_step(s), hl_set(s), s.get("items", [])
    cards = "".join(
        f'<div class="card {st}{" hl" if i in hl else ""}">'
        + (f'<div class="lab">{md(c["label"])}</div>' if c.get("label") else "")
        + f'<div class="t">{md(c.get("title"))}</div>'
        + (f'<div class="d">{md(c["text"])}</div>' if c.get("text") else "") + "</div>"
        for i, c in enumerate(items))
    return head(s) + f'<div class="cards" style="--n:{min(len(items), 4) or 1}">{cards}</div>'


def L_flow(s, lang, cycle=False):
    st, hl = cls_step(s), hl_set(s)
    nodes = "".join(
        f'<div class="node {st}{" hl" if i in hl else ""}"><div class="num">{i + 1}</div><div>'
        f'<div class="t">{md(n.get("title"))}</div>'
        + (f'<div class="d">{md(n["text"])}</div>' if n.get("text") else "") + "</div></div>"
        for i, n in enumerate(s.get("items", [])))
    back = f'<div class="cycle-back muted a">{md(s.get("back") or STRINGS[lang]["back"])}</div>' if cycle else ""
    return head(s) + f'<div class="flow">{nodes}</div>{back}'


def L_cycle(s, lang):
    return L_flow(s, lang, cycle=True)


def L_funnel(s, _):
    st, hl, items = cls_step(s), hl_set(s), s.get("items", [])
    n = max(len(items), 1)
    bars = "".join(f'<div class="bar {st}{" hl" if i in hl else ""}" style="--w:{100 - i * (55 / n):.0f}%">'
                   f'<span>{md(it.get("label"))}</span><b>{md(it.get("value", ""))}</b></div>'
                   for i, it in enumerate(items))
    return head(s) + f'<div class="funnel">{bars}</div>'


def L_comparison(s, _):
    st, hl = cls_step(s), hl_set(s)

    def side(i, d):
        lis = "".join(f"<li>{md(x)}</li>" for x in d.get("items", []))
        return f'<div class="side {st}{" hl" if i in hl else ""}"><h3>{md(d.get("title"))}</h3><ul>{lis}</ul></div>'
    return head(s) + f'<div class="cmp">{side(0, s.get("left", {}))}{side(1, s.get("right", {}))}</div>'


def L_matrix(s, _):
    hl, ax = hl_set(s), s.get("axes", {})
    pts = "".join(f'<div class="pt a{" hl" if i in hl else ""}" style="left:{it["x"] * 100:.0f}%;bottom:{it["y"] * 100:.0f}%">'
                  f'{md(it["label"])}</div>' for i, it in enumerate(s.get("items", [])))
    return head(s) + (f'<div class="matrix a"><span class="ax x muted">{md(ax.get("x"))} →</span>'
                      f'<span class="ax y muted">{md(ax.get("y"))} →</span>{pts}</div>')


def L_device(s, _):
    kind = s.get("device", "phone")
    src = html.escape(s.get("src", ""))
    inner = (f'<img src="{src}" alt="{html.escape(s.get("alt", ""))}">' if re.search(r"\.(png|jpe?g|webp|gif|svg)$", src, re.I)
             else f'<iframe src="{src}" loading="lazy"></iframe>')
    cap = f'<p class="text a">{md(s["caption"])}</p>' if s.get("caption") else ""
    return (f'<div class="device-row"><div class="head" style="flex:1">'
            + (f'<div class="kicker a">{md(s["kicker"])}</div>' if s.get("kicker") else "")
            + f'<h2 class="title a">{md(s.get("title"))}</h2>{cap}</div>'
            f'<div class="{kind} a">{inner}</div></div>')


def L_appendix_thread(s, _):
    lis = "".join(f'<li class="{cls_step(s)}">{md(q)}</li>' for q in s.get("questions", []))
    return head(s) + f'<ul class="thread">{lis}</ul>'


TERM_RULES = [(r"^(\$ .*)$", "p"), (r"(ERROR.*)$", "err"), (r"(warn .*)$", "warn"),
              (r"(\] ok,.*|^.*\bpass\b.*|^.*\bwrote\b.*)$", "ok")]


def L_code(s, _):
    lines = []
    for raw in str(s.get("code", "")).splitlines():
        line = html.escape(raw)
        for pat, c in TERM_RULES:
            if re.search(pat, line):
                line = f'<span class="{c}">{line}</span>'
                break
        lines.append(line)
    return head(s) + f'<div class="term a">{chr(10).join(lines)}</div>'


def L_dots(s, _):
    """A population of N. Click: the marked ones light up and move into their own group."""
    total, marked = int(s.get("total", 100)), int(s.get("highlight", 0))
    G = 38  # grid pitch, px
    out = []
    for i in range(total):
        x0, y0 = (i % 20) * G, (i // 20) * G                      # everyone, one grid
        if i < marked:                                               # the marked group, on the right
            j = i; x1, y1 = 470 + (j % 8) * G, (j // 8) * G
        else:                                                        # the rest, compacted on the left
            j = i - marked; x1, y1 = (j % 11) * G, (j // 11) * G
        out.append(f'<i class="{"m" if i < marked else ""}" style="--x0:{x0}px;--y0:{y0}px;--x1:{x1}px;--y1:{y1}px;'
                   f'--d:{(i % 20) * 12 + (i // 20) * 40}ms"></i>')
    dots = "".join(out)
    value = (f'<div class="dots-fig step"><div class="v">{md(s["value"])}</div><div class="l">{md(s.get("label", ""))}</div></div>'
             if s.get("value") else "")
    return head(s) + f'<div class="dots-wrap"><div class="dots" style="--n:{total};--m:{marked}">{dots}</div>{value}</div>'


def L_bars(s, _):
    """Grouped bars that grow on entry, a legend, and an optional bracket that labels a gap."""
    cats, series = s.get("categories", []), s.get("series", [])
    vmax = max((v for se in series for v in se.get("values", [])), default=1) or 1
    H = 420
    groups = []
    for ci, cat in enumerate(cats):
        bars = []
        for si, se in enumerate(series):
            v = se["values"][ci] if ci < len(se.get("values", [])) else None
            if v is None:
                continue
            h = int(H * v / vmax)
            bars.append(f'<div class="colbar s{si}" style="--h:{h}px;--d:{ci * 260 + si * 120}ms">'
                        f'<b>{md(se.get("format", "{}").format(v))}</b></div>')
        sub = s.get("sublabels", [""] * len(cats))[ci] if s.get("sublabels") else ""
        gap_note = ""
        if s.get("note") and s["note"].get("category") == ci:
            gap_note = f'<div class="gap step">{md(s["note"].get("text", ""))}</div>'
        groups.append(f'<div class="grp">{gap_note}<div class="bars">{"".join(bars)}</div><div class="cat">{md(cat)}</div>'
                      f'<div class="sub">{md(sub)}</div></div>')
    legend = "".join(f'<span class="s{si}"><i></i>{md(se.get("name", ""))}</span>' for si, se in enumerate(series))
    note = ""
    return (head(s) + f'<div class="chart" style="--n:{len(cats)};--H:{H}px"><div class="legend">{legend}</div>'
            f'<div class="plot">{"".join(groups)}{note}</div></div>')


LAYOUT_FN = {"cover": L_cover, "thesis": L_thesis, "quote": L_quote, "figures": L_figures, "cards": L_cards,
             "flow": L_flow, "cycle": L_cycle, "funnel": L_funnel, "comparison": L_comparison, "matrix": L_matrix,
             "device": L_device, "appendix-thread": L_appendix_thread, "code": L_code, "dots": L_dots, "bars": L_bars}


def source_line(s, lang) -> str:
    parts = [f"[{n}] {html.escape(t)}" for n, t in s.get("_sources", [])]
    for tier in ("S", "D"):
        if tier in s.get("_tiers", []):
            parts.append(STRINGS[lang][tier])
    if not parts:
        return ""
    label = STRINGS[lang]["sources"] + ": " if s.get("_sources") else ""
    return f'<div class="source">{label}{" ".join(parts)}</div>'


def render_slide(s, meta, brand, lang, default_theme, i) -> str:
    layout = s.get("layout")
    if layout not in SUPPORTED:
        raise SystemExit(f"{s.get('id')}: layout {layout!r} is not supported by keystone-html")
    theme = s.get("theme") or default_theme
    body = LAYOUT_FN[layout](s, lang)
    talk = s.get("_talk") or {}
    mark = brand.get("assets", {}).get("mark")
    sign = (f'<div class="sign"><img src="{html.escape(mark)}" alt=""></div>' if mark
            else f'<div class="sign">{html.escape(meta.get("signature", ""))}</div>')
    attrs = {
        "data-title": s.get("title") or s.get("text") or s.get("id"),
        "data-notes": talk.get("spoken", ""), "data-on-slide": talk.get("on_slide", ""),
        "data-leads-to": talk.get("leads_to", ""), "data-seconds": talk.get("seconds") or 0,
        "data-speaker": talk.get("speaker", ""),
    }
    a = " ".join(f'{k}="{html.escape(str(v))}"' for k, v in attrs.items())
    return (f'<section class="slide {theme} layout-{layout}" id="{html.escape(s["id"])}" {a}>'
            f"{body}{source_line(s, lang)}{sign}</section>")


def chrome() -> str | None:
    for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(c)
        if p:
            return p
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return mac if Path(mac).exists() else None


def shots(out: Path, n: int, w: int, h: int) -> list[Path]:
    exe = chrome()
    if not exe:
        print("no Chrome found; skipping screenshots")
        return []
    d = out / "shots"
    d.mkdir(exist_ok=True)
    files = []
    for i in range(1, n + 1):
        f = d / f"{i:02d}.png"
        subprocess.run([exe, "--headless=new", "--hide-scrollbars", f"--window-size={w},{h}",
                        "--virtual-time-budget=4000", f"--screenshot={f}",
                        f"{(out / 'index.html').resolve().as_uri()}?record&all#{i}"],
                       capture_output=True)
        files.append(f)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--core")
    ap.add_argument("--shots", action="store_true")
    ap.add_argument("--brand", help="render with this brand.json instead of meta.brand")
    ap.add_argument("--no-check", action="store_true", help="skip `keystone check` (not recommended)")
    a = ap.parse_args(argv)

    deck_dir = Path(a.deck).resolve()
    out = Path(a.out).resolve() if a.out else deck_dir / "build" / "html"
    cli = find_core(a.core)
    if not a.no_check:
        core(cli, "check", str(deck_dir))
    core(cli, "resolve", str(deck_dir))
    meta = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))["meta"]
    brand_ref = a.brand and str(Path(a.brand).resolve()) or meta.get("brand", "preset:neutral")
    if not brand_ref.startswith("preset:") and not Path(brand_ref).is_absolute():
        brand_ref = str((deck_dir / brand_ref).resolve())
    core(cli, "brand", "compile", brand_ref, "-o", str(deck_dir / "build" / "brand"))

    resolved = json.loads((deck_dir / "build" / "deck.resolved.json").read_text(encoding="utf-8"))
    sys.path.insert(0, str(deck_dir / "build" / "brand"))
    brand = json.loads(json.dumps(__import__("palette").BRAND))
    size_cls, w, h = SIZES.get(meta.get("size", "16:9"), SIZES["16:9"])
    lang = meta.get("lang", "en") if meta.get("lang") in STRINGS else "en"
    theme = meta.get("theme", "dark")

    out.mkdir(parents=True, exist_ok=True)
    for f in ("deck.js", "deck.css", "presenter.html"):
        shutil.copy(RUNTIME / f, out / f)
    shutil.copy(deck_dir / "build" / "brand" / "brand.css", out / "brand.css")
    if (deck_dir / "assets").is_dir():
        shutil.copytree(deck_dir / "assets", out / "assets", dirs_exist_ok=True)

    slides = "\n".join(render_slide(s, meta, brand, lang, theme, i) for i, s in enumerate(resolved["slides"]))
    channel = "keystone-" + re.sub(r"[^a-z0-9]+", "-", meta.get("title", "deck").lower()).strip("-")
    page = f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(meta.get("title", "Deck"))}</title>
<link rel="stylesheet" href="brand.css"><link rel="stylesheet" href="deck.css">
</head><body data-channel="{channel}">
<div id="stage" class="{size_cls}" data-w="{w}" data-h="{h}">
{slides}
<div id="progress"></div>
</div>
<script src="deck.js"></script>
</body></html>
"""
    (out / "index.html").write_text(page, encoding="utf-8")
    n = len(resolved["slides"])
    print(f"wrote {out / 'index.html'} ({n} slides, {meta.get('size', '16:9')}, {brand['name']})")
    if a.shots:
        files = shots(out, n, w, h)
        print(f"wrote {len(files)} screenshots to {out / 'shots'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
