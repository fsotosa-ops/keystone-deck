#!/usr/bin/env python3
"""Build a native, editable PowerPoint deck with Morph transitions from a keystone deck folder.

  build_pptx.py <deck-dir> [--out build/deck.pptx] [--brand path/brand.json] [--core PATH] [--no-check]

How motion works: PowerPoint's Morph transition animates every object whose name matches between
two consecutive slides. Every persistent element gets a stable "!!name" (title, kicker, each item,
each dot), so a step reveal is simply the next slide with one more element, and a recolour is the
same dots with a new fill. The result opens in PowerPoint with no add-ins and stays editable.

Requires python-pptx (pip install python-pptx).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from lxml import etree
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt
except ImportError:  # pragma: no cover
    raise SystemExit("python-pptx is required: pip install python-pptx")

PLUGIN = Path(__file__).resolve().parent.parent
SUPPORTED = {"cover", "thesis", "figures", "cards", "flow", "comparison", "quote", "dots", "code", "appendix-thread"}
W, H = Inches(13.333), Inches(7.5)
MX = Inches(0.95)
STRINGS = {"en": {"sources": "Sources", "S": "Includes estimates.", "D": "Includes targets.", "next": "Leads to"},
           "es": {"sources": "Fuentes", "S": "Incluye estimaciones.", "D": "Incluye metas.", "next": "Pasa a"}}

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
      "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
      "p159": "http://schemas.microsoft.com/office/powerpoint/2015/09/main"}
MORPH_XML = (
    '<mc:AlternateContent xmlns:mc="{mc}" xmlns:p="{p}">'
    '<mc:Choice xmlns:p159="{p159}" Requires="p159">'
    '<p:transition xmlns:p14="{p14}" spd="slow" p14:dur="{dur}"><p159:morph option="byObject"/></p:transition>'
    '</mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback>'
    '</mc:AlternateContent>')


# ------------------------------------------------------------------ core + brand

def find_core(explicit):
    cands = [explicit, os.environ.get("KEYSTONE_CORE"), str(PLUGIN.parent / "keystone" / "scripts" / "keystone.py")]
    cands += sorted(glob.glob(os.path.expanduser("~/.claude/plugins/cache/*/keystone/*/scripts/keystone.py")), reverse=True)
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    raise SystemExit("keystone core not found. Install the `keystone` plugin, or pass --core / set KEYSTONE_CORE.")


def core(cli, *args):
    r = subprocess.run([sys.executable, str(cli), *args], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"core step failed: {' '.join(args)}")


def rgb(hex_):
    h = hex_.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Theme:
    """Resolves brand roles for a dark or light slide."""

    def __init__(self, brand, ext, dark):
        c = brand["color"]
        self.dark = dark
        self.bg = c["bg-dark"] if dark else c["bg-light"]
        self.surface = c["surface-dark"] if dark else c["surface-light"]
        self.ink = c["ink-inverse"] if dark else c["ink"]
        self.muted = c["muted-inverse"] if dark else c["muted"]
        self.accent = c.get("accent-inverse", c["accent"]) if dark else c["accent"]
        self.fill = c["accent"]
        self.on_fill = c["on-accent"]
        self.accent2 = c["accent-2"]
        self.highlight = c["highlight"]
        self.on_highlight = c["on-highlight"]
        self.border = c["border"]
        f = brand["font"]
        pf = ext.get("pptxFonts", {})
        self.f_display = pf.get("display", f["display"])
        self.f_emph = pf.get("emphasis", f["display"])
        self.f_body = pf.get("body", f["body"])
        self.f_mono = pf.get("mono", f["mono"])


# ------------------------------------------------------------------ drawing helpers

def name(shape, n):
    shape.name = f"!!{n}"
    return shape


def text(slide, n, x, y, w, h, content, th, size, font=None, color=None, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.08, caps=False, tracking=0):
    """A text box. **x** in content becomes an accent run in the emphasis font."""
    tb = name(slide.shapes.add_textbox(x, y, w, h), n)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = str(content).split("\n")
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        for j, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", para)):
            if not chunk:
                continue
            r = p.add_run()
            r.text = chunk.upper() if caps else chunk
            r.font.size = Pt(size)
            accent = j % 2 == 1
            r.font.name = th.f_emph if accent else (font or th.f_body)
            r.font.color.rgb = rgb(th.accent if accent else (color or th.ink))
            if tracking:
                rPr = r._r.get_or_add_rPr()
                rPr.set("spc", str(tracking))
    return tb


def rect(slide, n, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
    s = name(slide.shapes.add_shape(shape, x, y, w, h), n)
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    return s


def oval(slide, n, x, y, d, fill):
    s = name(slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d), n)
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(fill)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def header(slide, s, th, title_size=40, top=Inches(0.85)):
    if s.get("kicker"):
        text(slide, "kicker", MX, top, Inches(10), Inches(0.4), s["kicker"], th, 14,
             font=th.f_mono, color=th.accent, caps=True, tracking=200)
    if s.get("title"):
        text(slide, "title", MX, top + Inches(0.45), Inches(11.2), Inches(1.6), s["title"], th, title_size,
             font=th.f_display, spacing=1.02)


def footer(slide, s, th, meta, lang):
    parts = [f"[{n}] {t}" for n, t in s.get("_sources", [])]
    for tier in ("S", "D"):
        if tier in s.get("_tiers", []):
            parts.append(STRINGS[lang][tier])
    if parts:
        label = STRINGS[lang]["sources"] + ": " if s.get("_sources") else ""
        text(slide, "source", MX, H - Inches(0.62), Inches(9.5), Inches(0.35), label + "  ".join(parts),
             th, 10, color=th.muted)
    if meta.get("signature"):
        text(slide, "sign", W - MX - Inches(3), H - Inches(0.62), Inches(3), Inches(0.35), meta["signature"],
             th, 10, font=th.f_mono, color=th.muted, align=PP_ALIGN.RIGHT)


# ------------------------------------------------------------------ layouts
# Each returns a list of "frames": callables that draw one slide. Steps become extra frames.

def L_cover(s, th):
    def draw(slide):
        if s.get("kicker"):
            text(slide, "kicker", MX, Inches(2.35), Inches(10), Inches(0.4), s["kicker"], th, 15,
                 font=th.f_mono, color=th.accent, caps=True, tracking=200)
        text(slide, "title", MX, Inches(2.85), Inches(11.4), Inches(2.4), s.get("title", ""), th, 56,
             font=th.f_display, spacing=1.0)
        if s.get("subtitle"):
            text(slide, "subtitle", MX, Inches(5.05), Inches(10), Inches(0.8), s["subtitle"], th, 20, color=th.muted)
    return [draw]


def L_thesis(s, th):
    def draw(slide):
        header(slide, s, th, title_size=50, top=Inches(2.1))
        if s.get("text"):
            text(slide, "text", MX, Inches(4.55), Inches(10), Inches(1.2), s["text"], th, 22, color=th.muted)
    return [draw]


def L_quote(s, th):
    def draw(slide):
        text(slide, "title", MX, Inches(2.0), Inches(11), Inches(3), "“" + s.get("text", "") + "”", th, 40,
             font=th.f_display, spacing=1.1)
        text(slide, "who", MX, Inches(5.3), Inches(10), Inches(0.5), s.get("who", ""), th, 18, color=th.muted)
    return [draw]


def L_figures(s, th):
    figs = s.get("figures", [])
    steps = len(figs) if s.get("reveal") == "items" else 1

    def make(k):
        def draw(slide):
            header(slide, s, th)
            n = len(figs)
            colw = (W - 2 * MX) / max(n, 1)
            shown = figs if steps == 1 else figs[:k + 1]
            longest = max((len(str(f["value"])) for f in figs), default=1)
            # Fit the longest figure on one line: ~0.56 em per character at this display weight.
            size = int(min(88, (colw / 914400 - 0.35) * 72 / (0.56 * longest)))
            for i, f in enumerate(shown):
                x = MX + int(colw * i)
                text(slide, f"fig-{i}", x, Inches(3.2), int(colw) - Inches(0.3), Inches(1.6), f["value"], th, size,
                     font=th.f_display, color=th.accent, spacing=0.95)
                text(slide, f"fig-label-{i}", x, Inches(4.85), int(colw) - Inches(0.4), Inches(1.0), f["label"], th, 18,
                     color=th.muted)
        return draw
    return [make(k) for k in range(steps)]


def L_cards(s, th):
    items = s.get("items", [])
    hl = s.get("highlight")
    hl = set(hl) if isinstance(hl, list) else ({hl} if hl is not None else set())
    steps = len(items) if s.get("reveal") == "items" else 1

    def make(k):
        def draw(slide):
            header(slide, s, th)
            n = max(len(items), 1)
            gap = Inches(0.3)
            cw = int((W - 2 * MX - gap * (n - 1)) / n)
            shown = items if steps == 1 else items[:k + 1]
            for i, it in enumerate(shown):
                x = MX + (cw + gap) * i
                on = i in hl
                rect(slide, f"card-{i}", x, Inches(3.15), cw, Inches(2.9), th.fill if on else th.surface,
                     line=None if on else th.border)
                ink = th.on_fill if on else th.ink
                y = Inches(3.45)
                if it.get("label"):
                    text(slide, f"card-lab-{i}", x + Inches(0.3), y, cw - Inches(0.6), Inches(0.35), it["label"], th, 11,
                         font=th.f_mono, color=th.on_fill if on else th.accent, caps=True, tracking=150)
                    y += Inches(0.45)
                text(slide, f"card-t-{i}", x + Inches(0.3), y, cw - Inches(0.6), Inches(1.0), it.get("title", ""), th, 24,
                     font=th.f_emph, color=ink, spacing=1.05)
                if it.get("text"):
                    text(slide, f"card-d-{i}", x + Inches(0.3), y + Inches(1.05), cw - Inches(0.6), Inches(1.2), it["text"],
                         th, 15, color=th.on_fill if on else th.muted)
        return draw
    return [make(k) for k in range(steps)]


def L_flow(s, th):
    items = s.get("items", [])
    hl = s.get("highlight")
    steps = len(items) if s.get("reveal") == "items" else 1

    def make(k):
        def draw(slide):
            header(slide, s, th)
            n = max(len(items), 1)
            cw = int((W - 2 * MX) / n)
            shown = items if steps == 1 else items[:k + 1]
            d = Inches(0.62)
            for i, it in enumerate(shown):
                x = MX + cw * i
                if i > 0:
                    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x - cw + d + Inches(0.12), Inches(3.56),
                                                    x - Inches(0.12), Inches(3.56))
                    ln.name = f"!!flow-line-{i}"
                    ln.line.color.rgb = rgb(th.border if not th.dark else th.muted)
                    ln.line.width = Pt(2)
                c = oval(slide, f"flow-n-{i}", x, Inches(3.25), d, th.highlight if i == hl else th.fill)
                tf = c.text_frame
                tf.margin_left = tf.margin_right = 0
                r = tf.paragraphs[0].add_run()
                r.text = str(i + 1)
                tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                r.font.size = Pt(20)
                r.font.name = th.f_emph
                r.font.color.rgb = rgb(th.on_highlight if i == hl else th.on_fill)
                text(slide, f"flow-t-{i}", x, Inches(4.15), cw - Inches(0.35), Inches(0.9), it.get("title", ""), th, 24,
                     font=th.f_emph, spacing=1.05)
                if it.get("text"):
                    text(slide, f"flow-d-{i}", x, Inches(5.0), cw - Inches(0.45), Inches(1.0), it["text"], th, 15,
                         color=th.muted)
        return draw
    return [make(k) for k in range(steps)]


def L_comparison(s, th):
    hl = s.get("highlight")

    def draw(slide):
        header(slide, s, th)
        gap = Inches(0.35)
        cw = int((W - 2 * MX - gap) / 2)
        for i, side in enumerate((s.get("left", {}), s.get("right", {}))):
            x = MX + (cw + gap) * i
            on = i == hl
            rect(slide, f"side-{i}", x, Inches(3.1), cw, Inches(3.3), th.fill if on else th.surface,
                 line=None if on else th.border)
            ink = th.on_fill if on else th.ink
            text(slide, f"side-t-{i}", x + Inches(0.35), Inches(3.35), cw - Inches(0.7), Inches(0.6),
                 side.get("title", ""), th, 24, font=th.f_emph, color=ink)
            body = "\n".join("–  " + x_ for x_ in side.get("items", []))
            text(slide, f"side-l-{i}", x + Inches(0.35), Inches(4.05), cw - Inches(0.7), Inches(2.2), body, th, 16,
                 color=ink, spacing=1.35)
    return [draw]


def L_dots(s, th):
    """A population of `total` (default 100). Frame 1: everyone. Frame 2: `highlight` of them recoloured.
    Same shape names in both frames, so Morph animates the change of colour."""
    total = int(s.get("total", 100))
    marked = int(s.get("highlight", 0))
    cols = 20 if total >= 40 else 10
    rows = -(-total // cols)

    def make(step):
        def draw(slide):
            header(slide, s, th)
            d, gap = Inches(0.27), Inches(0.13)
            x0, y0 = MX, Inches(3.3)
            for i in range(total):
                r, c = divmod(i, cols)
                on = step == 1 and i < marked
                color = th.fill if on else (th.border if not th.dark else th.surface)
                oval(slide, f"dot-{i}", x0 + (d + gap) * c, y0 + (d + gap) * r, d, color)
            right = x0 + (d + gap) * cols + Inches(0.5)
            if step == 1 and s.get("value"):
                text(slide, "dots-value", right, Inches(3.15), W - right - MX, Inches(1.3), s["value"], th, 72,
                     font=th.f_display, color=th.accent)
                text(slide, "dots-label", right, Inches(4.45), W - right - MX, Inches(1.3), s.get("label", ""), th, 18,
                     color=th.muted)
        return draw
    return [make(0), make(1)]


def L_code(s, th):
    def draw(slide):
        header(slide, s, th)
        box = rect(slide, "code", MX, Inches(3.1), W - 2 * MX, Inches(3.4), "#0C0D10", radius=0.03)
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.4)
        tf.margin_top = Inches(0.3)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for i, line in enumerate(str(s.get("code", "")).splitlines()):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = p.add_run()
            r.text = line
            r.font.size = Pt(16)
            r.font.name = th.f_mono
            col = "#E6E7EA"
            if line.startswith("$"):
                col = "#8A8F98"
            elif "ERROR" in line:
                col = "#FF8A80"
            elif line.strip().startswith("warn"):
                col = "#F2C46D"
            r.font.color.rgb = rgb(col)
    return [draw]


def L_appendix_thread(s, th):
    def draw(slide):
        header(slide, s, th)
        body = "\n".join("→  " + q for q in s.get("questions", []))
        text(slide, "thread", MX, Inches(3.1), Inches(11), Inches(3.5), body, th, 22, spacing=1.5)
    return [draw]


LAYOUTS = {"cover": L_cover, "thesis": L_thesis, "quote": L_quote, "figures": L_figures, "cards": L_cards,
           "flow": L_flow, "comparison": L_comparison, "dots": L_dots, "code": L_code,
           "appendix-thread": L_appendix_thread}


# ------------------------------------------------------------------ assembly

def add_morph(slide, ms=900):
    el = slide._element
    xml = MORPH_XML.format(dur=ms, **NS)
    node = etree.fromstring(xml)
    clr = el.find("{%s}clrMapOvr" % NS["p"])
    anchor = clr if clr is not None else el.find("{%s}cSld" % NS["p"])
    anchor.addnext(node)


def notes_for(s, lang, frame_i, frames):
    t = s.get("_talk") or {}
    if frame_i > 0:
        return f"(paso {frame_i + 1} de {frames})" if lang == "es" else f"(step {frame_i + 1} of {frames})"
    out = []
    if t.get("on_slide"):
        out.append(t["on_slide"])
    if t.get("spoken"):
        out.append(t["spoken"])
    if t.get("leads_to"):
        out.append(f"{STRINGS[lang]['next']}: {t['leads_to']}")
    return "\n\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--brand", help="render with this brand.json instead of meta.brand")
    ap.add_argument("--core")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args(argv)

    deck_dir = Path(a.deck).resolve()
    cli = find_core(a.core)
    if not a.no_check:
        core(cli, "check", str(deck_dir))
    core(cli, "resolve", str(deck_dir))
    meta = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))["meta"]
    bref = a.brand or meta.get("brand", "preset:neutral")
    if not bref.startswith("preset:"):
        bref = str((Path(a.brand).resolve() if a.brand else deck_dir / bref))
    bdir = deck_dir / "build" / "brand-pptx"
    core(cli, "brand", "compile", bref, "-o", str(bdir))
    sys.path.insert(0, str(bdir))
    brand = __import__("palette").BRAND
    brand_json = json.loads(Path(bref).read_text()) if not bref.startswith("preset:") else \
        json.loads((cli.parent.parent / "presets" / bref.split(":", 1)[1] / "brand.json").read_text())
    ext = brand_json.get("$extensions", {}).get("keystone", {})
    brand["font"] = {k: v[0] for k, v in brand["fontStack"].items()}

    resolved = json.loads((deck_dir / "build" / "deck.resolved.json").read_text(encoding="utf-8"))
    lang = meta.get("lang", "en") if meta.get("lang") in STRINGS else "en"
    default_dark = meta.get("theme", "light") == "dark"

    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]
    count = 0
    for s in resolved["slides"]:
        layout = s.get("layout")
        if layout not in SUPPORTED:
            raise SystemExit(f"{s.get('id')}: layout {layout!r} is not supported by keystone-pptx "
                             f"(supported: {', '.join(sorted(SUPPORTED))})")
        dark = (s.get("theme") == "dark") if s.get("theme") else default_dark
        th = Theme(brand, ext, dark)
        frames = LAYOUTS[layout](s, th)
        for fi, draw in enumerate(frames):
            slide = prs.slides.add_slide(blank)
            bg = slide.background.fill
            bg.solid()
            bg.fore_color.rgb = rgb(th.bg)
            draw(slide)
            footer(slide, s, th, meta, lang)
            slide.notes_slide.notes_text_frame.text = notes_for(s, lang, fi, len(frames))
            if count > 0:
                add_morph(slide, 700 if fi > 0 else 1000)
            count += 1

    out = Path(a.out) if a.out else deck_dir / "build" / "deck.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    print(f"wrote {out} ({count} slides from {len(resolved['slides'])} in deck.json, Morph on every transition, "
          f"brand {brand['name']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
