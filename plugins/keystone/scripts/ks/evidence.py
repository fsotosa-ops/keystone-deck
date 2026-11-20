"""The evidence ledger: every figure on a slide is computed, tiered and sourced.

evidence.json:
{
  "figures": {
    "enrolment-rate": {"value": 47.9, "display": "47.9%", "tier": "V",
                       "source": "stats-office-2025", "asOf": "2025",
                       "method": "optional: how it was computed"}
  },
  "refs": {
    "stats-office-2025": {"text": "Statistics Office. (2025). Annual report. https://..."}
  }
}

Tiers:
  V  verified: published by a primary source; needs a ref
  P  project: measured or computed by you; needs a method or a ref
  S  assumption: an estimate; the slide must say so
  D  decision: a target or choice the team made; the slide must say so

Slides reference figures as {{fig:id}} and references as {{ref:key}}.
References are numbered by first appearance in the deck.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

TIERS = {"V": "verified", "P": "project", "S": "assumption", "D": "decision"}
PLACEHOLDER = re.compile(r"\{\{(fig|ref):([A-Za-z0-9_.-]+)\}\}")
# A number typed into slide text rather than pulled from the ledger.
TYPED_NUMBER = re.compile(r"(?<![\w{:.-])\d[\d.,]*\s?(%|k|K|M|B|x)?(?![\w}])")


def load(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data.setdefault("figures", {})
    data.setdefault("refs", {})
    return data


def _texts(node):
    """Yield every string inside a slide, however nested."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k not in ("id", "layout", "src", "image", "notes", "code", "theme", "reveal", "alt", "device"):
                yield from _texts(v)
    elif isinstance(node, list):
        for v in node:
            yield from _texts(v)


def check(ledger: dict, deck: dict | None = None) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    figs, refs = ledger["figures"], ledger["refs"]
    for fid, f in figs.items():
        tier = f.get("tier")
        if tier not in TIERS:
            errors.append(f"figure {fid}: tier must be one of {'/'.join(TIERS)}")
            continue
        if "display" not in f and "value" not in f:
            errors.append(f"figure {fid}: needs value or display")
        src = f.get("source")
        if tier == "V" and not src:
            errors.append(f"figure {fid}: tier V needs a source ref")
        if tier == "P" and not (src or f.get("method")):
            errors.append(f"figure {fid}: tier P needs a method or a source")
        if src and src not in refs:
            errors.append(f"figure {fid}: source {src!r} is not in refs")
    if deck is None:
        return errors, warnings

    used = set()
    for s in deck.get("slides", []):
        for text in _texts(s):
            for kind, key in PLACEHOLDER.findall(text):
                used.add((kind, key))
                pool = figs if kind == "fig" else refs
                if key not in pool:
                    errors.append(f"{s.get('id')}: {{{{{kind}:{key}}}}} is not in the ledger")
            bare = PLACEHOLDER.sub("", text)
            for m in TYPED_NUMBER.finditer(bare):
                token = m.group(0).strip()
                if re.fullmatch(r"(19|20)\d\d", token) or len(token) == 1:
                    continue  # years and single digits (step numbers) are fine
                warnings.append(f"{s.get('id')}: typed number {token!r}; "
                                "compute it in the ledger and use {{fig:...}}")
    for fid in figs:
        if ("fig", fid) not in used:
            warnings.append(f"figure {fid} is never shown")
    return errors, warnings


def resolve(deck: dict, ledger: dict) -> dict:
    """Replace placeholders, number refs by first use, attach per-slide sources."""
    figs, refs = ledger["figures"], ledger["refs"]
    order: list[str] = []

    def num(key):
        if key not in order:
            order.append(key)
        return order.index(key) + 1

    def sub(text, slide_refs, slide_tiers):
        def rep(m):
            kind, key = m.groups()
            if kind == "ref":
                slide_refs.add(key)
                return f"[{num(key)}]"
            f = figs[key]
            slide_tiers.add(f["tier"])
            if f.get("source"):
                slide_refs.add(f["source"])
                num(f["source"])
            return str(f.get("display", f.get("value")))
        return PLACEHOLDER.sub(rep, text)

    def walk(node, slide_refs, slide_tiers):
        if isinstance(node, str):
            return sub(node, slide_refs, slide_tiers)
        if isinstance(node, dict):
            return {k: walk(v, slide_refs, slide_tiers) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, slide_refs, slide_tiers) for v in node]
        return node

    out = {**deck, "slides": []}
    for s in deck.get("slides", []):
        r, t = set(), set()
        new = walk(s, r, t)
        new["_sources"] = sorted((num(k), refs[k]["text"]) for k in r)
        new["_tiers"] = sorted(t)
        out["slides"].append(new)
    out["_references"] = [{"n": i + 1, "key": k, "text": refs[k]["text"]}
                          for i, k in enumerate(order)]
    return out
