#!/usr/bin/env python3
"""Build a high-impact live deck with the stage engine (scenes, live product in devices, callouts).

  build_stage.py <deck-dir> [--out build/stage] [--brand brand.json] [--core PATH] [--no-check]

deck.json slides use scene layouts (cover, persona, journey, mirror, product, why-now, matrix, model,
funnel, timeline, projection, team, ask, closing) or "html" for a slide Claude composes itself.
Optional in the deck folder:
  app/            the product (or a mock) that devices mount; meta.app = path to its index.html
  scenes.js       per-slide click scripts: window.ESCENAS[slide.scene] = { preparar, pasos: [...] }
  assets/         images
Output: <out>/index.html with deck.js, deck.css, brand.css, presenter.html, and copies of app/ and assets/.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
STAGE = PLUGIN / "stage"
sys.path.insert(0, str(STAGE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import scenes  # noqa: E402
from build import core, find_core  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--out")
    ap.add_argument("--brand")
    ap.add_argument("--core")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args(argv)

    deck_dir = Path(a.deck).resolve()
    out = Path(a.out).resolve() if a.out else deck_dir / "build" / "stage"
    cli = find_core(a.core)
    if not a.no_check:
        core(cli, "check", str(deck_dir))
    core(cli, "resolve", str(deck_dir))
    meta = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))["meta"]
    bref = str(Path(a.brand).resolve()) if a.brand else meta.get("brand", "preset:neutral")
    if not bref.startswith("preset:") and not Path(bref).is_absolute():
        bref = str((deck_dir / bref).resolve())
    core(cli, "brand", "compile", bref, "-o", str(deck_dir / "build" / "brand"))
    resolved = json.loads((deck_dir / "build" / "deck.resolved.json").read_text(encoding="utf-8"))

    out.mkdir(parents=True, exist_ok=True)
    for f in ("deck.js", "deck.css", "presenter.html"):
        shutil.copy(STAGE / f, out / f)
    shutil.copy(deck_dir / "build" / "brand" / "brand.css", out / "brand.css")
    for sub in ("app", "assets"):
        if (deck_dir / sub).is_dir():
            shutil.copytree(deck_dir / sub, out.parent / sub if sub == "app" else out / sub, dirs_exist_ok=True)
    if (deck_dir / "scenes.js").exists():
        shutil.copy(deck_dir / "scenes.js", out / "escenas.js")
    else:
        (out / "escenas.js").write_text("window.ESCENAS = {}\n")

    sig = html.escape(meta.get("signature", ""))
    logo = meta.get("logo_svg", "")
    firma = f'<div class="firma">{logo}{html.escape(meta.get("brand_name", ""))} <b>{sig}</b></div><div class="num-l"></div>'
    secs = []
    for s in resolved["slides"]:
        layout = s.get("layout")
        if layout not in scenes.SCENES:
            raise SystemExit(f"{s.get('id')}: layout {layout!r} is not a stage scene ({', '.join(scenes.SCENES)})")
        theme = s.get("theme") or ("light" if layout in scenes.LIGHT else "dark")
        body = scenes.SCENES[layout]({**s, "logo": logo})
        src = " ".join(f"[{n}] {t}" for n, t in s.get("_sources", []))
        tiers = [x for x in s.get("_tiers", []) if x in ("S", "D")]
        note = s.get("source_note") or (("Fuentes: " + src) if src else "") or ("Cifras ilustrativas." if tiers else "")
        foot = f'<div class="fuente">{html.escape(note)}</div>' if note else ""
        t = s.get("_talk") or {}
        esc = f' data-escena="{html.escape(s["scene"])}"' if s.get("scene") else ""
        secs.append(f'<section class="lam {"clara" if theme == "light" else ""}" id="{s["id"]}"{esc} data-quien="{html.escape(t.get("speaker", ""))}" '
                    f'data-tiempo="" data-notas="{html.escape(t.get("spoken", ""), quote=True)}">{body}{foot}\n  {firma}\n</section>')

    app = meta.get("app", "../app/index.html")
    reset = ",".join(meta.get("app_reset_keys", []))
    page = f"""<!doctype html>
<html lang="{meta.get('lang', 'en')}">
<head>
<meta charset="utf-8">
<title>{html.escape(meta.get('title', 'Deck'))}</title>
<link rel="stylesheet" href="brand.css">
<link rel="stylesheet" href="deck.css">
<style>{scenes.EXTRA_CSS}</style>
</head>
<body data-app="{html.escape(app)}" data-channel="keystone-{html.escape(deck_dir.name)}" data-reset="{html.escape(reset)}">
{chr(10).join(secs)}
<script src="escenas.js"></script>
<script src="deck.js"></script>
</body>
</html>
"""
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {out / 'index.html'} ({len(secs)} slides, stage engine)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
