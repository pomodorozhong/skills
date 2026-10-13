#!/usr/bin/env bash
# One-time import: copy existing Codex and Claude Code skills into this repo's skills/.
# Every skill here is shared by both agents, so a name is imported only when all its installed
# copies (~/.agents/skills, ~/.codex/skills, ~/.claude/skills) are identical. Names whose copies
# differ are skipped and listed; keep one version and run this again.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_SRC="$HOME/.agents/skills"
LEGACY_CODEX_SRC="${CODEX_HOME:-$HOME/.codex}/skills"
CLAUDE_SRC="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
STAGE="$REPO/.import"
SOURCES=(agents legacy claude)
EXCLUDES=(--exclude='/.system/' --exclude='/synced/' --exclude='.git/'
          --exclude='.DS_Store' --exclude='__pycache__/')

rm -rf "$STAGE"
mkdir -p "$STAGE/agents" "$STAGE/legacy" "$STAGE/claude"
[ -d "$CODEX_SRC" ]        && rsync -aL "${EXCLUDES[@]}" "$CODEX_SRC/" "$STAGE/agents/"
[ -d "$LEGACY_CODEX_SRC" ] && rsync -aL "${EXCLUDES[@]}" "$LEGACY_CODEX_SRC/" "$STAGE/legacy/"
[ -d "$CLAUDE_SRC" ]       && rsync -aL "${EXCLUDES[@]}" "$CLAUDE_SRC/" "$STAGE/claude/"

# Same files, contents, and executable bits. diff -rq alone ignores permissions.
same() {
  diff -rq "$1" "$2" >/dev/null &&
    [ "$(cd "$1" && find . -type f -perm -100 | sort)" = "$(cd "$2" && find . -type f -perm -100 | sort)" ]
}

mkdir -p "$REPO/skills"
differ=""
for name in $(for s in "${SOURCES[@]}"; do ls "$STAGE/$s"; done | sort -u); do
  first=""
  ok=1
  for s in "${SOURCES[@]}"; do
    d="$STAGE/$s/$name"
    [ -d "$d" ] || continue
    if [ -z "$first" ]; then first="$d"; elif ! same "$first" "$d"; then ok=0; fi
  done
  [ -n "$first" ] && [ -f "$first/SKILL.md" ] || continue
  if [ -e "$REPO/skills/$name" ]; then
    echo "already in repo, not overwritten: skills/$name" >&2
  elif [ "$ok" = 0 ]; then
    differ="$differ $name"
  else
    mv "$first" "$REPO/skills/"
    echo "imported: skills/$name"
  fi
done

rm -rf "$STAGE"
if [ -n "$differ" ]; then
  echo "Not imported, installed copies differ:$differ" >&2
  echo "Keep one version of each (move the others out of $CODEX_SRC, $LEGACY_CODEX_SRC, and $CLAUDE_SRC), then run this again." >&2
fi
echo "Done. Remove any third-party skills from the repo before running link.sh."
