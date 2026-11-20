# Authoring a deck

1. `/keystone:new my-deck`. Answer: who is in the room, what they decide, and how long you have.
2. Agree on the **thread** (the talk in one sentence) and the slide sequence. Each slide line ends with the question the next slide answers.
3. Fill `talk.md` slide by slide. Write what you will *say*, which is what the slide will not show.
4. Put every number through `data/` and `evidence.json`, with a tier and a source.
5. Write `deck.json`: pick the layout from the relation, write the title as a claim, and keep about 25 words per slide.
6. `/keystone:review my-deck`, fix, render, look.

## talk.md

```markdown
# Title
**Audience:** who decides what.
**Thread:** one sentence.

## problem · Ana · 0:45
**On slide:** one figure; click reveals the second.
What you say, which the slide does not show. **Click:** the second figure appears.
**Leads to:** why hasn't anyone fixed it?

# Appendix
## costs-detail · Ana
Backup for questions.
```

Spanish labels also work (`En la lámina`, `Pasa a`, `Clic`, `Audiencia`, `Hilo`, `# Anexo`).

## deck.json layouts

| Layout | Fields |
|---|---|
| `cover` | `title`, `subtitle` |
| `thesis` | `kicker`, `title`, `text` |
| `figures` | `kicker`, `title`, `figures[{value, label}]` (up to 3) |
| `cards` | `kicker`, `title`, `items[{label, title, text}]`, `highlight` |
| `flow`, `cycle` | `kicker`, `title`, `items[{title, text}]` |
| `funnel` | `kicker`, `title`, `items[{label, value}]` |
| `comparison` | `kicker`, `title`, `left{title, items}`, `right{title, items}` |
| `matrix` | `kicker`, `title`, `axes{x, y}`, `items[{label, x, y}]` |
| `device` | `kicker`, `title`, `device` (phone or laptop), `src`, `caption` |
| `quote` | `text`, `who` |
| `appendix-thread` | `kicker`, `title`, `questions[]` |

Engines may add optional fields; the schema allows them.
