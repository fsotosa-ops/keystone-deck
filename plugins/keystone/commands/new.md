---
description: Start a new deck folder (talk.md, deck.json, evidence.json) with a brand
argument-hint: "<folder> [--brand preset:NAME|path] [--engine html|slides|video]"
---

Start a new keystone deck in `$ARGUMENTS` (default: `./deck`).

1. If the user has not said who the audience is, what they must decide and how long the talk is, ask in one message. Ask also which brand: a preset (`neutral`, `ink`, `ocean`, `warm`), their own guide, or a website. Do not ask anything that the arguments already answer.
2. Scaffold:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" new <folder> --title "<title>" --brand <brand> --engine <engine>
   ```
3. If the brand is not a preset, follow the **brand-kit** skill before anything else.
4. Write `talk.md` with the **narrative-arc** skill: audience, thread in one sentence, one heading per slide. Show the thread and the slide sequence (one line per slide with its **Leads to**) to the user before writing deck.json.
5. Only after the user agrees with the sequence, write deck.json (**visual-grammar**) and evidence.json (**evidence-ledger**).
6. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" check <folder>` and fix every error.
