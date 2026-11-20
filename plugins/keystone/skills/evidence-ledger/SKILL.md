---
name: evidence-ledger
description: Use when a deck, report or pitch shows numbers, market sizes, projections, costs, impact figures or citations, or when the user asks where a figure comes from or how to cite it. Every figure is computed in data/, recorded in evidence.json with a tier (verified, project, assumption, decision) and a source, and pulled into slides as {{fig:id}}. Also triggers on "cifras", "fuentes", "de dónde sale este número", "modelo financiero".
---

# Evidence ledger

A number on a slide is a promise that someone can check it. The ledger makes that promise explicit: each figure is computed once, carries how sure we are, and travels to every slide, report and video with its source attached.

## The file

`evidence.json` holds two maps:

```json
{
  "figures": {
    "enrolment-rate": {"value": 47.9, "display": "47.9%", "tier": "V",
                       "source": "stats-2025", "asOf": "2025"},
    "cost-per-user":  {"value": 3.1, "display": "USD 3.10", "tier": "P",
                       "method": "data/costs.py: infra + AI tokens / active users, 2027 plan"}
  },
  "refs": {
    "stats-2025": {"text": "National Statistics Office. (2025). Higher education report. https://example.org"}
  }
}
```

| Tier | Meaning | Required | On the slide |
|---|---|---|---|
| **V** verified | published by a primary source | `source` | the reference number at the foot |
| **P** project | measured or computed by the team | `method` or `source` | the source line names the method |
| **S** assumption | an estimate | nothing more | say "estimate" or "assumption" |
| **D** decision | a target the team chose | nothing more | say "target" or "goal" |

## Rules

- **Compute, do not type.** Figures come from a script or spreadsheet in `data/` that writes or updates `evidence.json`. When a spreadsheet is the deliverable, keep live formulas and tag each input cell with its tier and source.
- **Slides reference, never copy.** Write `{{fig:enrolment-rate}}` in deck.json. `keystone.py check` warns about every number typed by hand, except years and single digits.
- **Every slide with figures closes with a source line.** The engines add it from the ledger, and references are numbered by first appearance in the deck.
- **The title claims; the number lives in the body.** "Most graduates never reach university" is a title; "47.9% enrolment" is not.
- **Three figures per slide at most**, each a big number with a one-line label. With more, none gets read.
- **Prefer primary sources.** When only a secondary source exists, tier it V and name the secondary source honestly. Never upgrade an inference to V.
- **Say what is not known.** A slide that admits "not yet tested with users" survives questions; one that implies it was tested does not.
- **Names stay inside.** Only show aggregates for groups of ten or more people. Strip names from figures, quotes and screenshots that leave the team.

## Check

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" evidence check evidence.json --deck deck.json
```

The check reports errors for V without a source, P without a method, unknown sources and placeholders not in the ledger. It warns about typed numbers and figures never shown. `keystone.py resolve` fills the placeholders and writes `build/deck.resolved.json` with per-slide `_sources` and `_tiers` for the engines.
