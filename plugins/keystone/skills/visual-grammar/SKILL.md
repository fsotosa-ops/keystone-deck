---
name: visual-grammar
description: Use when designing or critiquing what a slide, figure or diagram looks like, choosing a layout for content, deciding what to highlight, or when slides feel crowded, decorative or all the same. Maps each relation (repeat, filter, compare, sequence, position) to a layout and enforces one accent, one highlighted piece and about 25 visible words per slide. Also triggers on "diseño de láminas", "se ve recargado", "qué diagrama uso".
---

# Visual grammar

A slide has one job: make the claim in its title believable at a glance. Everything on it either supports that claim or goes to the spoken text.

## Anatomy of a slide

- **Kicker**: the section, small and uppercase, in the accent colour (`accent-inverse` on dark).
- **Title**: the thesis as a full sentence. Never a label like "Market" or "Team".
- **Body**: the evidence, using the layout that matches the relation.
- **Source line**: at the foot, small, in the muted colour. It is required when there are figures.
- **Signature**: the brand mark in a corner, the same on every slide.

## The form says the relation

Choose the layout from what the content *is*, not from what looks varied:

| The content… | Layout | Not |
|---|---|---|
| repeats (a weekly routine, a loop) | `cycle` | a bullet list |
| filters (100 applicants → 20 admitted) | `funnel`, or dots that fade | a pie chart |
| compares two options | `comparison`, side by side | two separate slides |
| happens in phases | `flow`, left to right | a vertical list |
| positions players on two criteria | `matrix` (2×2) | a feature checklist table |
| is two to four parallel ideas | `cards` | a paragraph |
| is a few hard numbers | `figures` (up to three) | a chart with one bar |
| is the product in use | `device`: phone or laptop frame, a named person, a concrete moment | a bare screenshot |
| is someone's own words | `quote` with attribution | a paraphrase |

A grid of identical cards communicates nothing about how the items relate. If the items are steps, draw a flow; if they compete, draw a matrix.

## Restraint rules

- **One accent per piece.** One brand colour carries emphasis. Do not set two accents as text in the same sentence.
- **One highlighted piece per slide**, a solid accent fill with `on-accent` text. If everything stands out, nothing does.
- **The highlight colour is the single exception**: the target, the warning, the one number that matters. It appears on few slides.
- **The `ai` colour marks only content an AI proposed** that a person has not approved yet.
- **About 25 visible words per slide.** `keystone.py check` warns above that. Move the rest to the spoken text.
- **Status colours always come with text** ("on track", "late"), never colour alone.
- **The mascot or illustration appears at most once per slide**, and only at transitions (opening the demo, the close).
- **Alternate dark and light slides** for rhythm, not at random. For example, dark for argument and light for evidence.
- **Contrast is checked, not eyeballed.** A colour may be used as text only in the pairs the brand declares, and `brand check` verifies them against WCAG 2.2.

## Figures outside slides

Report and document figures follow the same grammar. In an academic report, the title, conclusion and source go in the caption and not inside the image. A figure that does not fit stays whole: give it its own page rather than cropping it.

## Then

Render and look at the result with **render-review**. The brand roles referenced here (`accent`, `on-accent`, `highlight`, `muted`) are defined by **brand-kit**.
