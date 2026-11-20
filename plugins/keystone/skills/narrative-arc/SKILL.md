---
name: narrative-arc
description: Use when planning, writing or reviewing a presentation, pitch, keynote or deck before any slide is drawn, or when a deck "doesn't flow", reads as a list of topics, or the speaker notes repeat the slides. Produces talk.md, the single source for slide order, speaker notes and timing. Also triggers on "guion", "hilo", "armar la presentación", "storyline".
---

# Narrative arc

The talk is written before the deck. `talk.md` decides the order, what each slide must prove, what is said out loud and how long it takes. Slides are drawn from it, never the other way round.

## Start with three lines

At the top of `talk.md`:

1. **Audience:** who is in the room and what they need to know to decide. Name the decision ("whether to fund a pilot"), not the demographic.
2. **Thread:** the whole talk in one sentence. If it does not fit in one sentence, the argument is not settled yet; stop and settle it with the user.
3. A table of blocks (speaker, slides, time) when more than one person presents.

## One heading per slide

```markdown
## slide-id · Speaker · 0:45
**On slide:** what to point at, and what each click reveals.
The spoken text: what the slide does not say.
**Click:** inline, where a step reveals the next element.
**Leads to:** the question the next slide answers.
```

The parser (`keystone.py talk check`) accepts English or Spanish labels (`En la lámina`, `Pasa a`, `Clic`) and fails when a slide has no spoken text or no **Leads to**.

## Rules

- **Each slide answers the question the previous one left open.** Write every **Leads to** as a real question in the audience's words. If two consecutive slides do not connect through a question, one of them is in the wrong place or should not exist.
- **The spoken text says what the slide does not.** Reading the slide aloud wastes the slide and the voice. The slide holds the claim and the evidence; the voice holds the reason, the example and the transition.
- **Start from a person in a moment, not from an idea.** "At 7 a.m. the night nurse hands over twelve patients on one paper sheet" lands; "Healthcare faces challenges" does not. Use invented people with plain names and say that they are illustrative.
- **Problem and solution in mirror.** Each limitation named in the problem gets its answer on a later slide, in the same order, so the audience can tick them off.
- **Show the product in someone's hands, in context**, not as a feature list.
- **Market as the payer's budget**, not users times price.
- **Traction before revenue is usage evidence**: pilots, deployments, signed interest. Say plainly what has not been tested yet.
- **Appendix for the defence.** Backup slides go after `# Appendix`; they are not timed and need no **Leads to**. Chain them as questions so the presenter can find the right one under pressure.

## Pick the type first

Set `meta.type` in deck.json and read its reference before writing the sequence:

| Type | Reference |
|---|---|
| `pitch` | `references/pitch.md` — investor deck, 12-15 slides, scene per slide |
| `keynote` | `references/keynote.md` — talk with a hook, three ideas and one line to repeat |
| `class` | `references/clase.md` — intuition, worked example, check question |
| `report` | `references/informe.md` — decision first, options, recommendation |

## A default order for pitches

Person → problem with your own evidence → solution in mirror → product in context → why now → competition as a matrix → business model next to the product → numbers (unit economics, funding) → usage traction → team → ask with use of funds. Then the appendix.

Adapt it for other talks. A status review runs from the decision needed, to what changed, to the evidence, to the options, and ends on the recommendation. A teaching deck runs from intuition, to a worked example with numbers, to a check question.

## Timing

Budget about 2.6 spoken words per second. `talk check` warns when a slide's text needs more than 125% of its time. It prints the total and the time per speaker, excluding the appendix.

## Then

- Every number the talk mentions goes through **evidence-ledger** before it reaches a slide.
- The visible slide is designed with **visual-grammar**.
- Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" talk check talk.md --deck deck.json`.
