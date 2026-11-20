#!/usr/bin/env python3
"""keystone: checks and compilers for the keystone-deck method. Python stdlib only.

  keystone.py new <dir> [--title T] [--brand preset:neutral] [--engine html]
  keystone.py brand list
  keystone.py brand check <brand.json | preset:NAME>
  keystone.py brand compile <brand.json | preset:NAME> [-o DIR]
  keystone.py talk check <talk.md> [--deck deck.json] [--json]
  keystone.py evidence check <evidence.json> [--deck deck.json]
  keystone.py check [DIR]            run every check on a deck folder
  keystone.py resolve [DIR] [-o F]   deck with figures and refs filled in, for engines

Exit code 0 when there are no errors (warnings do not fail), 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # the plugin root
sys.path.insert(0, str(HERE))

from ks import brand as brand_mod  # noqa: E402
from ks import contrast, deck as deck_mod, evidence, talk  # noqa: E402

PRESETS = ROOT / "presets"
TEMPLATE = ROOT / "templates" / "new"


def brand_path(ref: str, base: Path = Path(".")) -> Path:
    if ref.startswith("preset:"):
        p = PRESETS / ref.split(":", 1)[1] / "brand.json"
    else:
        p = (base / ref).resolve()
    if not p.exists():
        names = ", ".join(sorted(d.name for d in PRESETS.iterdir() if d.is_dir()))
        raise SystemExit(f"brand not found: {ref} (presets: {names})")
    return p


def report(title: str, errors: list[str], warnings: list[str]) -> bool:
    status = "ok" if not errors else f"{len(errors)} error(s)"
    print(f"[{title}] {status}, {len(warnings)} warning(s)")
    for e in errors:
        print(f"  ERROR  {e}")
    for w in warnings:
        print(f"  warn   {w}")
    return not errors


def contrast_rows(b: dict) -> list[dict]:
    return contrast.check_pairs(b["color"], b["textPairs"])


def cmd_brand(a) -> int:
    if a.action == "list":
        for d in sorted(PRESETS.iterdir()):
            if (d / "brand.json").exists():
                b = brand_mod.load(d / "brand.json")
                print(f"preset:{d.name:<10} {b['description']}")
        return 0
    path = brand_path(a.ref)
    try:
        b = brand_mod.load(path)
    except brand_mod.BrandError as e:
        print(f"ERROR {e}")
        return 1
    rows = contrast_rows(b)
    errors = [f"{r['fg']} on {r['bg']} ({r['size']}): {r['ratio']}:1, needs {r['required']}:1"
              for r in rows if not r["ok"]]
    warnings = [] if rows else ["no textPairs declared; contrast was not checked"]
    ok = report(f"brand {b['name']}", errors, warnings)
    if a.action == "check":
        for r in rows:
            print(f"  {'pass' if r['ok'] else 'FAIL'}  {r['fg']:>14} on {r['bg']:<14} "
                  f"{r['ratio']:>5}:1  (needs {r['required']}, {r['size']})")
        return 0 if ok else 1
    if not ok and not a.force:
        print("Refusing to compile a brand that fails contrast. Fix the colours or pass --force.")
        return 1
    out = Path(a.out)
    written = brand_mod.compile_brand(path, out, rows)
    for p in written:
        print(f"  wrote {p}")
    return 0


def cmd_talk(a) -> int:
    doc = talk.parse(a.path)
    ids = None
    if a.deck:
        ids = [s["id"] for s in deck_mod.load(a.deck).get("slides", [])]
    errors, warnings = talk.check(doc, ids)
    if a.json:
        print(json.dumps({"doc": doc, "summary": talk.summary(doc),
                          "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    ok = report("talk", errors, warnings)
    s = talk.summary(doc)
    m, sec = divmod(s["seconds"], 60)
    print(f"  {s['slides']} slides + {s['appendix']} appendix, {m}:{sec:02d} spoken")
    for who, t in s["by_speaker"].items():
        print(f"    {who}: {t // 60}:{t % 60:02d}")
    return 0 if ok else 1


def cmd_evidence(a) -> int:
    ledger = evidence.load(a.path)
    d = deck_mod.load(a.deck) if a.deck else None
    errors, warnings = evidence.check(ledger, d)
    return 0 if report("evidence", errors, warnings) else 1


def cmd_check(a) -> int:
    base = Path(a.dir)
    deck_file = base / "deck.json"
    if not deck_file.exists():
        print(f"no deck.json in {base.resolve()}")
        return 1
    d = deck_mod.load(deck_file)
    ok = True

    b = None
    try:
        b = brand_mod.load(brand_path(d.get("meta", {}).get("brand", "preset:neutral"), base))
        rows = contrast_rows(b)
        bad = [f"{r['fg']} on {r['bg']}: {r['ratio']}:1 < {r['required']}:1" for r in rows if not r["ok"]]
        ok &= report(f"brand {b['name']}", bad, [])
    except (brand_mod.BrandError, SystemExit) as e:
        ok &= report("brand", [str(e)], [])

    ok &= report("deck", *deck_mod.check(d, b["rules"] if b else None))

    talk_file = base / "talk.md"
    if talk_file.exists():
        doc = talk.parse(talk_file)
        ok &= report("talk", *talk.check(doc, [s["id"] for s in d.get("slides", [])]))
    else:
        ok &= report("talk", ["talk.md is missing: the talk is the single source"], [])

    ev_file = base / "evidence.json"
    if ev_file.exists():
        ok &= report("evidence", *evidence.check(evidence.load(ev_file), d))
    else:
        ok &= report("evidence", [], ["no evidence.json; fine only if the deck shows no figures"])
    return 0 if ok else 1


def cmd_resolve(a) -> int:
    base = Path(a.dir)
    d = deck_mod.load(base / "deck.json")
    ev = base / "evidence.json"
    ledger = evidence.load(ev) if ev.exists() else {"figures": {}, "refs": {}}
    out = evidence.resolve(d, ledger)
    tf = base / "talk.md"
    if tf.exists():
        notes = {s["id"]: s for s in talk.parse(tf)["slides"]}
        for s in out["slides"]:
            s["_talk"] = notes.get(s["id"])
    target = Path(a.out) if a.out else base / "build" / "deck.resolved.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {target}")
    return 0


def cmd_new(a) -> int:
    dest = Path(a.dir)
    if dest.exists() and any(dest.iterdir()):
        print(f"{dest} is not empty; pick a new folder")
        return 1
    brand_path(a.brand)  # fail early on a bad brand
    shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True)
    deck_file = dest / "deck.json"
    d = json.loads(deck_file.read_text(encoding="utf-8"))
    d["meta"].update({"title": a.title, "brand": a.brand, "engine": a.engine})
    deck_file.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tf = dest / "talk.md"
    tf.write_text(tf.read_text(encoding="utf-8").replace("{{TITLE}}", a.title), encoding="utf-8")
    print(f"created {dest}/: deck.json, talk.md, evidence.json, data/")
    print("next: write talk.md first (audience, thread, one heading per slide), then deck.json")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="keystone", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="scaffold a deck folder")
    n.add_argument("dir")
    n.add_argument("--title", default="Untitled deck")
    n.add_argument("--brand", default="preset:neutral")
    n.add_argument("--engine", default="html", choices=["html", "slides", "video"])
    n.set_defaults(fn=cmd_new)

    b = sub.add_parser("brand", help="list, check or compile a brand")
    b.add_argument("action", choices=["list", "check", "compile"])
    b.add_argument("ref", nargs="?", default="preset:neutral")
    b.add_argument("-o", "--out", default="build/brand")
    b.add_argument("--force", action="store_true", help="compile even if contrast fails")
    b.set_defaults(fn=cmd_brand)

    t = sub.add_parser("talk", help="check talk.md")
    t.add_argument("action", choices=["check"])
    t.add_argument("path")
    t.add_argument("--deck")
    t.add_argument("--json", action="store_true")
    t.set_defaults(fn=cmd_talk)

    e = sub.add_parser("evidence", help="check evidence.json")
    e.add_argument("action", choices=["check"])
    e.add_argument("path")
    e.add_argument("--deck")
    e.set_defaults(fn=cmd_evidence)

    c = sub.add_parser("check", help="run every check on a deck folder")
    c.add_argument("dir", nargs="?", default=".")
    c.set_defaults(fn=cmd_check)

    r = sub.add_parser("resolve", help="write the resolved deck for an engine")
    r.add_argument("dir", nargs="?", default=".")
    r.add_argument("-o", "--out")
    r.set_defaults(fn=cmd_resolve)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
