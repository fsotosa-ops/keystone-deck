# Contributing

Thanks for helping. A few rules keep the project coherent.

## Ground rules

- **The three contracts are stable.** These are content (`talk.md`, `deck.json`), evidence (`evidence.json`) and brand (`brand.json`). Changes to them need an issue first, and must stay backward compatible within a minor version.
- **Engines read only `build/`.** They read the resolved deck and the compiled brand, never the sources directly.
- **No hard-coded colours, fonts, paths or binaries.** Use brand tokens, paths relative to `${CLAUDE_PLUGIN_ROOT}` or the deck folder, and detect binaries at run time.
- **The core stays dependency-free** (Python 3.10+ stdlib).
- **Examples are fictional.** Do not add real organisations, people, client data or trade dress.

## Development

```bash
python3 -m unittest discover tests/unit
claude plugin validate .
./scripts/scrub_check.sh   # optional private denylist; see the script header
```

To try your local copy in Claude Code:

```text
/plugin marketplace add ./
/plugin install keystone@keystone-deck
```

## Skills

- Keep frontmatter to `name` and `description`. The description starts with "Use when…", states the trigger situations, and lists Spanish trigger phrases at the end.
- Write rules with their reason. Rules without a reason get misapplied.
- Keep a SKILL.md under about 120 lines, and move reference material into `references/`.

## Pull requests

One topic per PR, with a CHANGELOG entry under *Unreleased*. Include a rendered PNG when the change affects anything visual.
