#!/usr/bin/env python3
"""Build a PowerPoint that keeps the motion of the live HTML deck.

  build_pptx.py <deck-dir> [--out build/deck.pptx] [--brand brand.json] [--only id,id] [--core PATH]

How it works:
  1. keystone-html builds the live deck (build/html/index.html).
  2. Each slide, and each click step, is recorded in a headless browser while it animates
     (Chrome DevTools screencast), with the headline text hidden.
  3. The frames become one MP4 clip per step (30 fps, H.264).
  4. Every clip goes on its own PowerPoint slide, full-bleed, playing automatically. The kicker,
     title and text are measured in the browser and re-created on top as native PowerPoint text,
     so they stay editable. Speaker notes come from talk.md.

Opening the .pptx needs nothing but PowerPoint (or Keynote). Building it needs:
  python-pptx, playwright (+ a Chromium: `playwright install chromium`), and ffmpeg
  (on PATH, in $FFMPEG, or from the imageio-ffmpeg package).
"""

from __future__ import annotations

import argparse
import base64
import functools
import glob
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
PX = 6350  # EMU per CSS px when the 1920 px stage is a 13.333 in slide
TEXT_SEL = ".kick, .tit, .bajada"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
FADE = ('<p:transition xmlns:p="%s" spd="med"><p:fade/></p:transition>' % P_NS)


# ------------------------------------------------------------------ dependencies

def need(mod, pip):
    try:
        return __import__(mod)
    except ImportError:
        raise SystemExit(f"missing dependency: pip install {pip}")


def ffmpeg_bin():
    for c in (os.environ.get("FFMPEG"), shutil.which("ffmpeg")):
        if c and Path(c).exists():
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: install it, set $FFMPEG, or pip install imageio-ffmpeg")


def sibling_script(plugin, rel, env):
    cands = [os.environ.get(env), str(PLUGIN.parent / plugin / rel)]
    cands += sorted(glob.glob(os.path.expanduser(f"~/.claude/plugins/cache/*/{plugin}/*/{rel}")), reverse=True)
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    raise SystemExit(f"{plugin} not found: install it or set ${env}")


def run(*cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"failed: {' '.join(map(str, cmd[:3]))} …")
    return r


# ------------------------------------------------------------------ local server

def serve(directory):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


# ------------------------------------------------------------------ recording

MEASURE_JS = """([id, sel]) => {
  const s = document.getElementById(id)
  return [...s.querySelectorAll(sel)].filter(e => e.innerText.trim()).map(e => {
    const r = e.getBoundingClientRect(), st = getComputedStyle(e), runs = []
    const walk = (n, color, weight) => { for (const c of n.childNodes) {
      if (c.nodeType === 3) { if (c.textContent) runs.push({ t: c.textContent, color, weight }) }
      else if (c.nodeType === 1) { const cs = getComputedStyle(c)
        if (c.tagName === 'BR') runs.push({ t: '\\n', color, weight }); else walk(c, cs.color, cs.fontWeight) } } }
    walk(e, st.color, st.fontWeight)
    // the stage (body) is scaled to the window; convert back to 1920x1080 stage pixels
    const stage = document.body.getBoundingClientRect(), k = 1920 / stage.width
    return { x: (r.x - stage.x) * k, y: (r.y - stage.y) * k, w: r.width * k, h: r.height * k,
             font: st.fontFamily, size: parseFloat(st.fontSize), weight: st.fontWeight, color: st.color,
             lh: parseFloat(st.lineHeight) || null, transform: st.textTransform, align: st.textAlign, runs }
  })
}"""


def record(page, cdp, trigger, max_s=8.0, quiet_s=0.7):
    """Screencast until the page stops changing. Returns [(timestamp, jpeg_bytes)]."""
    frames = []

    def on_frame(ev):
        frames.append((ev["metadata"]["timestamp"], base64.b64decode(ev["data"])))
        try:
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass

    cdp.on("Page.screencastFrame", on_frame)
    cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1080})
    page.wait_for_timeout(250)
    t_trig = time.time()
    trigger()
    start = time.time()
    while True:
        page.wait_for_timeout(100)
        last = frames[-1][0] if frames else t_trig
        if time.time() - start > max_s or (time.time() - start > 0.8 and time.time() - max(last, t_trig) > quiet_s):
            break
    cdp.send("Page.stopScreencast")
    cdp.remove_listener("Page.screencastFrame", on_frame)
    frames.sort(key=lambda f: f[0])
    while len(frames) > 1 and frames[1][0] <= t_trig:
        frames.pop(0)
    if not frames:
        frames = [(t_trig, page.screenshot(type="jpeg", quality=92))]
    return [(max(t, t_trig), d) for t, d in frames]


def encode(frames, out_mp4, ff, tail=0.4):
    with tempfile.TemporaryDirectory() as td:
        lines = []
        for i, (t, data) in enumerate(frames):
            fn = f"f{i:05d}.jpg"
            Path(td, fn).write_bytes(data)
            dur = (frames[i + 1][0] - t) if i + 1 < len(frames) else tail
            lines.append(f"file '{fn}'\nduration {max(0.001, dur):.4f}")
        lines.append(f"file 'f{len(frames) - 1:05d}.jpg'")
        Path(td, "list.txt").write_text("\n".join(lines) + "\n")
        run(ff, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", Path(td, "list.txt"),
            "-r", "30", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "17", "-preset", "slow",
            "-movflags", "+faststart", out_mp4)


def record_deck(url, ids, out_dir, ff):
    need("playwright", "playwright")
    from playwright.sync_api import sync_playwright as pw
    clips = []
    with pw() as p:
        try:
            b = p.chromium.launch(channel="chrome", args=["--window-size=1920,1080"])
        except Exception:
            b = p.chromium.launch(args=["--window-size=1920,1080"])
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url + "/stage-rec/index.html#1")
        page.wait_for_timeout(2000)
        cdp = page.context.new_cdp_session(page)
        all_ids = page.evaluate("window.__deck.ids")
        for sid in ids:
            n = all_ids.index(sid)
            steps = page.evaluate(f"""(() => {{ const l = document.getElementById('{sid}');
                const v = [...l.querySelectorAll('[data-paso]')].map(e => +e.dataset.paso);
                const esc = window.ESCENAS?.[l.dataset.escena];
                return Math.max(v.length ? Math.max(...v) : 0, esc?.pasos?.length || 0) }})()""")
            hide = (f"#{sid} " + f", #{sid} ".join(TEXT_SEL.split(", ")) + " { visibility: hidden !important; }"
                    f" .lam:not(#{sid}) {{ opacity: 0 !important; transition: none !important; }}")
            # measure each step's final text, then record each step
            texts = []
            page.evaluate(f"window.__deck.ir({n}, false)")
            page.wait_for_timeout(2500)
            t0 = page.evaluate(MEASURE_JS, [sid, TEXT_SEL])
            texts = [t0] * (steps + 1)   # headline text does not change across steps
            page.evaluate(f"window.__deck.ir({max(0, n - 1)}, true)")
            page.wait_for_timeout(1500)
            style = page.add_style_tag(content=hide)
            for k in range(steps + 1):
                trig = (lambda: page.evaluate(f"window.__deck.ir({n}, false)")) if k == 0 else (lambda: page.keyboard.press("ArrowRight"))
                frames = record(page, cdp, trig, max_s=9.0, quiet_s=1.0)
                mp4 = out_dir / f"{sid}-{k}.mp4"
                poster = out_dir / f"{sid}-{k}.png"
                encode(frames, mp4, ff)
                page.screenshot(path=str(poster))
                clips.append({"id": sid, "step": k, "steps": steps, "mp4": mp4, "poster": poster, "text": texts[k]})
                print(f"  recorded {sid} step {k}/{steps}: {len(frames)} frames, {frames[-1][0] - frames[0][0]:.1f}s")
            style.evaluate("e => e.remove()")
        b.close()
    return clips


# ------------------------------------------------------------------ PowerPoint

def css_rgb(c):
    from pptx.dml.color import RGBColor
    n = [int(float(x)) for x in re.findall(r"[\d.]+", c)[:3]]
    return RGBColor(*n)


def font_name(family_css, weight, weights_map):
    fam = family_css.split(",")[0].strip("'\" ")
    m = weights_map.get(fam)
    if m:
        w = min(m, key=lambda k: abs(int(k) - int(float(weight))))
        return m[w], False
    return fam, int(float(weight)) >= 600


def autoplay(slide):
    """python-pptx inserts movies as click-to-play; start them with the slide instead."""
    for cond in slide._element.iter(f"{{{P_NS}}}cond"):
        if cond.get("delay") == "indefinite":
            cond.set("delay", "0")
    for ctn in slide._element.iter(f"{{{P_NS}}}cTn"):
        if ctn.get("nodeType") == "clickEffect":
            ctn.set("nodeType", "afterEffect")


def add_fade(slide):
    from lxml import etree
    el = slide._element
    node = etree.fromstring(FADE)
    anchor = el.find(f"{{{P_NS}}}clrMapOvr")
    (anchor if anchor is not None else el.find(f"{{{P_NS}}}cSld")).addnext(node)


def assemble(clips, notes, out, weights_map):
    need("pptx", "python-pptx")
    from pptx import Presentation
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(1920 * PX), Emu(1080 * PX)
    for c in clips:
        s = prs.slides.add_slide(prs.slide_layouts[6])
        mv = s.shapes.add_movie(str(c["mp4"]), 0, 0, prs.slide_width, prs.slide_height,
                                poster_frame_image=str(c["poster"]), mime_type="video/mp4")
        mv.name = f"scene {c['id']} step {c['step']}"
        autoplay(s)
        if c["step"] == 0:
            add_fade(s)
        for i, t in enumerate(c["text"]):
            tb = s.shapes.add_textbox(Emu(int(t["x"] * PX)), Emu(int(t["y"] * PX)),
                                      Emu(int((t["w"] * 1.12 + 24) * PX)), Emu(int(t["h"] * 1.05 * PX)))
            tb.name = f"{c['id']} text {i}"
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.TOP
            align = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}.get(t.get("align"), PP_ALIGN.LEFT)
            p = tf.paragraphs[0]
            p.alignment = align
            if t.get("lh"):
                p.line_spacing = Pt(t["lh"] * 0.5)
            for run_ in t["runs"]:
                for j, part in enumerate(run_["t"].split("\n")):
                    if j > 0:
                        p = tf.add_paragraph()
                        p.alignment = align
                        if t.get("lh"):
                            p.line_spacing = Pt(t["lh"] * 0.5)
                    if not part:
                        continue
                    r = p.add_run()
                    r.text = part.upper() if t.get("transform") == "uppercase" else part
                    r.font.size = Pt(t["size"] * 0.5)
                    name, bold = font_name(t["font"], run_["weight"], weights_map)
                    r.font.name = name
                    r.font.bold = bold or None
                    r.font.color.rgb = css_rgb(run_["color"])
        s.notes_slide.notes_text_frame.text = (notes.get(c["id"], "") if c["step"] == 0
                                               else f"(clic {c['step']} de {c['steps']})")
    prs.save(out)


# ------------------------------------------------------------------ main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--brand", help="render with this brand.json instead of meta.brand")
    ap.add_argument("--only", help="comma-separated slide ids")
    ap.add_argument("--core")
    a = ap.parse_args(argv)

    deck_dir = Path(a.deck).resolve()
    ff = ffmpeg_bin()
    html_build = sibling_script("keystone-html", "scripts/build_stage.py", "KEYSTONE_HTML")
    html_dir = deck_dir / "build" / "stage-rec"
    args = [sys.executable, html_build, deck_dir, "--out", html_dir, "--no-check"]
    if a.core:
        args += ["--core", a.core]
    if a.brand:
        args += ["--brand", a.brand]
    run(*args)

    resolved = json.loads((deck_dir / "build" / "deck.resolved.json").read_text(encoding="utf-8"))
    ids = [s["id"] for s in resolved["slides"]]
    if a.only:
        ids = [i for i in ids if i in a.only.split(",")]
    notes = {}
    for s in resolved["slides"]:
        t = s.get("_talk") or {}
        notes[s["id"]] = "\n\n".join(x for x in (t.get("on_slide"), t.get("spoken"),
                                                  ("→ " + t["leads_to"]) if t.get("leads_to") else "") if x)

    brand_src = Path(a.brand) if a.brand else None
    weights_map = {}
    if brand_src and brand_src.exists():
        ext = json.loads(brand_src.read_text()).get("$extensions", {}).get("keystone", {})
        weights_map = ext.get("pptxFontWeights", {})

    clips_dir = deck_dir / "build" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    srv, url = serve(html_dir.parent)
    try:
        clips = record_deck(url, ids, clips_dir, ff)
    finally:
        srv.shutdown()
    out = Path(a.out) if a.out else deck_dir / "build" / "deck.pptx"
    assemble(clips, notes, out, weights_map)
    print(f"wrote {out}: {len(clips)} slides ({len(ids)} scenes + click steps), video autoplay, native text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
