---
description: Run every check on a deck folder and review the rendered result
argument-hint: "[folder]"
---

Review the deck in `$ARGUMENTS` (default: current folder).

1. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/keystone.py" check <folder>` and list the errors and warnings.
2. If a build exists (`build/`), render it and look at it with the **render-review** skill.
3. Dispatch the `deck-critic` agent on the folder for an independent read of the argument.
4. Report in three groups: errors to fix, judgement calls for the user, and what already works. Do not edit files unless the user asks.
