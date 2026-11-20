#!/usr/bin/env bash
# Fails if any term from a private denylist appears in the tree or the git history.
# The denylist lives outside the repo so the terms themselves are never published:
#   ${KEYSTONE_DENYLIST:-$HOME/.config/keystone-deck/denylist.txt}   one term per line
set -euo pipefail
LIST="${KEYSTONE_DENYLIST:-$HOME/.config/keystone-deck/denylist.txt}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
hits=0
# Generic leaks that need no denylist: absolute home paths.
if git grep --cached -nIE '/(Users|home)/[a-z]' -- . ':!scripts/scrub_check.sh' ':!.github/workflows/ci.yml' >/dev/null 2>&1; then
  git grep --cached -nIE '/(Users|home)/[a-z]' -- . ':!scripts/scrub_check.sh' ':!.github/workflows/ci.yml'; hits=1
fi
if [[ -f "$LIST" ]]; then
  while IFS= read -r term || [[ -n "$term" ]]; do
    [[ -z "$term" || "$term" == \#* ]] && continue
    # Tracked and staged files only: ignored output (build/, eval results) never ships.
    if git grep -IniwF --cached -e "$term" >/dev/null 2>&1; then
      echo "tree: '$term'"; git grep -IniwF --cached -e "$term" | head -5; hits=1
    fi
    if git rev-parse HEAD >/dev/null 2>&1 && git log --all -i -G"\\b$term\\b" --oneline | grep -q .; then
      echo "history: '$term'"; hits=1
    fi
    if git rev-parse HEAD >/dev/null 2>&1 && git log --all --format='%an %ae %cn %ce %s %b' | grep -qiw -e "$term"; then
      echo "commit metadata: '$term'"; hits=1
    fi
  done < "$LIST"
else
  echo "note: no denylist at $LIST; only generic checks ran"
fi
if [[ $hits -eq 0 ]]; then echo "scrub: clean"; else echo "scrub: FOUND LEAKS"; exit 1; fi
