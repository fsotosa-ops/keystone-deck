---
name: render-review
description: Use after building or changing any slide, deck, figure, brand sheet or video, before telling the user it is done. Renders the output to images, looks at them, and checks overflow, legibility, contrast, scale and timing. Also use when the user says something "looks off", text is cut, or asks to review a deck visually. Also triggers on "revisa cómo se ve", "captura", "hoja de contactos".
---

# Render and review

Code that builds a slide says nothing about how the slide looks. Every visual deliverable is rendered to pixels and looked at before it is reported as done. Iterating blind costs more rounds than looking once.

## Render

- **HTML** (deck, brand sheet, figures): use headless Chrome. It needs no extra dependencies:
  ```bash
  CHROME="$(command -v google-chrome || command -v chromium || echo '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')"
  "$CHROME" --headless=new --hide-scrollbars --window-size=1920,1080 \
    --virtual-time-budget=3000 --screenshot="$PWD/build/review/01.png" "file://$PWD/build/index.html"
  ```
  Use Playwright when steps must be opened or the page must be driven. HTML decks from keystone-html expose `window.__deck.go(n, {allSteps: true})`.
- **Figures for documents:** render at 2× or 3× device scale so they stay sharp in Docs and PDFs.
- **Google Slides:** export the PDF and convert the pages to PNG.
- **Video:** extract a strip of frames (about six, evenly spaced, plus any timestamps the user mentions) and measure the audio levels before listening.

## Look

Open the PNGs with the Read tool. For decks, look at a contact sheet first: all slides as thumbnails on one image, to judge rhythm, then the full-size slides that need it. Check:

1. **Nothing overflows or is clipped**: text against the edges, cards spilling, the source line covered.
2. **Readable at presentation size**: nothing under about 14 px at 1920×1080, and no figure scaled below 75%.
3. **One accent and one highlighted piece**: count them.
4. **Contrast in context**: text over images or gradients is not covered by `brand check`.
5. **The title is a claim** and the layout matches the relation (see visual-grammar).
6. **Figures carry their source line.**
7. **Video**: there are no blank or white frames at cuts, the voice is not clipped, the music sits under the voice, and nothing changes faster than it can be read.

Report what you saw, with the slide id, and fix it before reporting done. If something cannot be fixed, say so plainly.

## Independent review

For a second opinion that is not anchored on how the deck was built, dispatch the `deck-critic` agent with the folder path. It reads talk.md, deck.json and the rendered PNGs, and reports gaps without editing anything.
