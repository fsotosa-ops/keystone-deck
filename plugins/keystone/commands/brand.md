---
description: Create, import, check or switch the brand (colours, fonts, logos) of a deck
argument-hint: "[preset:NAME | path/to/guide.pdf | https://site | path/to/brand.json]"
---

Set up the brand from `$ARGUMENTS` using the **brand-kit** skill.

- With no argument, list the presets (`keystone.py brand list`) and offer the four ways in.
- `preset:NAME`: point deck.json at it.
- A PDF or image guide: read it as images and build `brand/brand.json`.
- A URL: read the site's computed styles with Playwright.
- An existing `brand.json`: check it and compile it.

Always finish with `brand check`, then `brand compile`, then render `build/brand/brand-sheet.html` and look at it. Show it to the user for approval before any deck uses the brand.
