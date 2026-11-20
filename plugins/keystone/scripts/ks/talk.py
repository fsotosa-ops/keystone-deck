"""Parse talk.md: the single source for speaker notes and timing.

Format (English or Spanish labels are both accepted):

    # Title
    **Audience:** who is in the room and what they need to decide.
    **Thread:** the whole talk in one sentence.

    ## slide-id · Speaker · 0:45
    **On slide:** what to point at, what each click reveals.
    The spoken text: what the slide does not say.
    **Click:** a step reveal, inline.
    **Leads to:** the question the next slide answers.

    # Appendix
    ## backup-slide · Speaker
    ...

Slides after an H1 named Appendix/Anexo are backup: they are not timed and
do not need a "Leads to".
"""

from __future__ import annotations

import re
from pathlib import Path

LABELS = {
    "on_slide": ["on slide", "en la lámina", "en la lamina"],
    "leads_to": ["leads to", "pasa a"],
    "audience": ["audience", "audiencia"],
    "thread": ["thread", "hilo en una oración", "hilo en una oracion", "hilo"],
}
CLICK = re.compile(r"\*\*(click|clic):\*\*", re.I)
HEADING = re.compile(r"^##\s+(?P<id>[A-Za-z0-9_-]+)(?P<rest>.*)$")
APPENDIX = re.compile(r"^#\s+(appendix|anexo)\b", re.I)
TIME = re.compile(r"^(\d+):(\d{2})$")
WORDS_PER_SECOND = 2.6  # measured on recorded talks; used to sanity-check timing


def _label(line: str):
    m = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line.strip())
    if not m:
        return None, None
    name = m.group(1).strip().lower()
    for key, names in LABELS.items():
        if name in names:
            return key, m.group(2).strip()
    return None, None


def parse(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    doc = {"title": "", "audience": "", "thread": "", "slides": []}
    appendix = False
    cur = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# ") and not doc["title"] and not APPENDIX.match(line):
            doc["title"] = line[2:].strip()
            continue
        if APPENDIX.match(line):
            appendix = True
            continue
        h = HEADING.match(line)
        if h:
            parts = [p.strip() for p in re.split(r"[·|]", h.group("rest")) if p.strip()]
            speaker, seconds = "", None
            for p in parts:
                t = TIME.match(p)
                if t:
                    seconds = int(t.group(1)) * 60 + int(t.group(2))
                else:
                    speaker = p
            cur = {"id": h.group("id"), "speaker": speaker, "seconds": seconds,
                   "appendix": appendix, "on_slide": "", "spoken": [],
                   "leads_to": "", "clicks": 0}
            doc["slides"].append(cur)
            continue
        key, value = _label(line)
        if cur is None:
            if key in ("audience", "thread"):
                doc[key] = value
            continue
        if key in ("on_slide", "leads_to"):
            cur[key] = value
            continue
        if line.strip() in ("", "---"):
            continue
        cur["clicks"] += len(CLICK.findall(line))
        cur["spoken"].append(CLICK.sub("", line).strip())

    for s in doc["slides"]:
        s["spoken"] = " ".join(x for x in s["spoken"] if x)
        s["words"] = len(re.findall(r"\w+", s["spoken"]))
    return doc


def check(doc: dict, deck_ids: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors, warnings = [], []
    if not doc["audience"]:
        errors.append("missing **Audience:** line at the top")
    if not doc["thread"]:
        errors.append("missing **Thread:** line (the talk in one sentence)")
    ids = [s["id"] for s in doc["slides"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errors.append(f"duplicate slide ids: {', '.join(dup)}")
    main = [s for s in doc["slides"] if not s["appendix"]]
    for i, s in enumerate(doc["slides"]):
        if not s["spoken"]:
            errors.append(f"{s['id']}: no spoken text (say what the slide does not)")
        if not s["on_slide"]:
            warnings.append(f"{s['id']}: no **On slide:** line")
        last_main = s is (main[-1] if main else None)
        if not s["appendix"] and not last_main and not s["leads_to"]:
            errors.append(f"{s['id']}: no **Leads to:** (the question the next slide answers)")
        if s["seconds"] and s["words"]:
            need = s["words"] / WORDS_PER_SECOND
            if need > s["seconds"] * 1.25:
                warnings.append(f"{s['id']}: {s['words']} words need ~{need:.0f}s, "
                                f"budget is {s['seconds']}s")
    if deck_ids is not None:
        missing = [i for i in deck_ids if i not in ids]
        orphan = [i for i in ids if i not in deck_ids]
        if missing:
            errors.append(f"slides in deck.json without notes: {', '.join(missing)}")
        if orphan:
            warnings.append(f"notes without a slide in deck.json: {', '.join(orphan)}")
    return errors, warnings


def summary(doc: dict) -> dict:
    main = [s for s in doc["slides"] if not s["appendix"]]
    secs = sum(s["seconds"] or 0 for s in main)
    by = {}
    for s in main:
        by.setdefault(s["speaker"] or "-", 0)
        by[s["speaker"] or "-"] += s["seconds"] or 0
    return {"slides": len(main), "appendix": len(doc["slides"]) - len(main),
            "seconds": secs, "by_speaker": by}
