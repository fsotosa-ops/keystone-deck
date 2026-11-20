"""Structural and editorial checks on deck.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

# The shared layout vocabulary. Each engine declares which ones it renders.
LAYOUTS = {
    "cover":           "title slide: the promise in one sentence",
    "thesis":          "one claim, large, with an optional supporting line",
    "figures":         "up to three big numbers, each with a one-line label",
    "cards":           "two to four parallel items; one may be highlighted",
    "flow":            "phases left to right",
    "cycle":           "something that repeats",
    "funnel":          "something that filters, from many to few",
    "comparison":      "two things side by side",
    "matrix":          "a 2x2 positioning",
    "device":          "the product in a phone or laptop frame, in context",
    "quote":           "a person's own words, attributed",
    "appendix-thread": "backup slides chained as questions",
    "code":            "a terminal or code block showing real output",
    "dots":            "a population of N where some share a trait (the marked ones regroup on click)",
    "bars":            "grouped bars that grow on entry, with an optional labelled gap",
    # stage scenes (keystone-html build_stage): high-impact pitch and keynote pieces
    "persona":         "a named person in a concrete moment, with the product in their phone",
    "journey":         "a population that sets out and only part arrives",
    "mirror":          "problem and solution in mirror, one pair per click",
    "product":         "the live product in a laptop and a phone, driven click by click",
    "why-now":         "two or three reasons side by side",
    "model":           "free side vs paid side, with the product next to it",
    "timeline":        "traction as 'how we did it', milestone by milestone",
    "projection":      "cost vs income per period, with the gap labelled",
    "team":            "the people and why them",
    "ask":             "the ask with use of funds, slice by slice",
    "closing":         "the last line, with the product",
    "html":            "a slide Claude composes for its argument",
}
NO_HEADLINE = {"cover", "quote", "ask", "closing", "html"}
NO_WORD_LIMIT = {"appendix-thread", "code", "html", "matrix", "mirror"}
MAX_VISIBLE_WORDS = 25
MAX_FIGURES = 3
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _visible_words(slide: dict) -> int:
    skip = {"id", "layout", "src", "image", "notes", "steps", "highlight", "appendix", "code", "theme", "reveal", "alt"}

    def walk(node):
        if isinstance(node, str):
            return len(re.findall(r"\w+", re.sub(r"\{\{[^}]+\}\}", "N", node)))
        if isinstance(node, dict):
            return sum(walk(v) for k, v in node.items() if k not in skip)
        if isinstance(node, list):
            return sum(walk(v) for v in node)
        return 0
    return walk(slide)


def check(deck: dict, rules: dict | None = None) -> tuple[list[str], list[str]]:
    rules = rules or {}
    errors, warnings = [], []
    meta = deck.get("meta", {})
    for key in ("title", "brand"):
        if not meta.get(key):
            errors.append(f"meta.{key} is required")
    slides = deck.get("slides", [])
    if not slides:
        errors.append("deck has no slides")
    seen = set()
    for s in slides:
        sid = s.get("id", "?")
        if not SLUG.match(str(sid)):
            errors.append(f"{sid}: id must be a lowercase slug")
        if sid in seen:
            errors.append(f"{sid}: duplicate id")
        seen.add(sid)
        layout = s.get("layout")
        if layout not in LAYOUTS:
            errors.append(f"{sid}: unknown layout {layout!r}; use one of {', '.join(LAYOUTS)}")
            continue
        if layout not in NO_HEADLINE:
            if not s.get("kicker"):
                errors.append(f"{sid}: needs a kicker (the section)")
            title = s.get("title", "")
            if not title:
                errors.append(f"{sid}: needs a title that states the thesis")
            elif len(re.findall(r"\w+", title)) < 4:
                warnings.append(f"{sid}: title {title!r} reads like a label; state the claim")
            if re.search(r"\d|\{\{fig:", title):
                warnings.append(f"{sid}: number in the title; the title claims, the number lives in the body")
        if layout == "figures" and len(s.get("figures", [])) > MAX_FIGURES:
            errors.append(f"{sid}: {len(s['figures'])} figures; three at most or none is read")
        hl = s.get("highlight")
        n_hl = len(hl) if isinstance(hl, list) else (0 if hl is None else 1)
        if n_hl > rules.get("highlightPieces", 1):
            errors.append(f"{sid}: {n_hl} highlighted pieces; if everything stands out nothing does")
        words = _visible_words(s)
        if not s.get("appendix") and layout not in NO_WORD_LIMIT and words > MAX_VISIBLE_WORDS:
            warnings.append(f"{sid}: ~{words} visible words (aim for {MAX_VISIBLE_WORDS} or fewer); "
                            "move the rest to the spoken text")
    return errors, warnings
