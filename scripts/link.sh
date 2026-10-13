#!/usr/bin/env bash
# Link every skill in this repo into the Codex and Claude Code personal skill folders.
# Safe to re-run. Real folders it would replace are moved to ~/skills-link-backup/<timestamp>-<pid>/.
# Usage: scripts/link.sh [--dry-run]
set -euo pipefail

DRY=0
if [ "$#" -gt 0 ]; then
  if [ "$#" -eq 1 ] && [ "$1" = --dry-run ]; then
    DRY=1
  else
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
  fi
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_DIR="$HOME/.agents/skills"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LEGACY_CODEX_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
BACKUP="$HOME/skills-link-backup/$(date +%Y%m%d-%H%M%S)-$$"

run() {  # print and run a command, or only print it in dry-run mode
  echo "+ $*"
  [ "$DRY" = 1 ] || "$@"
}

# List skill folders (folders with SKILL.md) in one repo folder. Missing or empty folders are fine.
skills_in() {
  local d
  [ -d "$REPO/$1" ] || return 0
  for d in "$REPO/$1"/*/; do
    [ -f "$d/SKILL.md" ] && basename "$d"
  done
  return 0
}

# Real paths, so folders reached through symlinks (or CODEX_HOME / CLAUDE_CONFIG_DIR) compare equal.
resolved() { (cd -P "$1" 2>/dev/null && pwd -P) || true; }
REPO_REAL="$(resolved "$REPO")"
SKILLS_REAL="$(resolved "$REPO/skills")"

# Check everything before changing anything.
problems=""
# An agent folder that is this repo's skills/ already reads the skills: linking into it would move
# the repo's own skill folders aside. Skip it. Any other folder inside the repo is a mistake.
LINK_CODEX=1 LINK_CLAUDE=1
for agent in CODEX CLAUDE; do
  eval "root=\"\$${agent}_DIR\""
  real="$(resolved "$root")"
  [ -n "$real" ] || continue
  if [ "$real" = "$SKILLS_REAL" ]; then
    echo "$root is this repo's skills/ folder; nothing to link there."
    eval "LINK_$agent=0"
  else
    case "$real/" in
      "$REPO_REAL"/*) problems="$problems\n  $root points into this repo ($real); point it to its own folder or to skills/" ;;
    esac
  fi
done
for n in $(skills_in skills); do
  # Claude Code reserves 'synced' (any capitalization) for skills synced from claude.ai.
  [ "$(echo "$n" | tr '[:upper:]' '[:lower:]')" = "synced" ] &&
    problems="$problems\n  '$n' is reserved by Claude Code; rename it"
done
if [ -n "$problems" ]; then
  printf "Nothing changed. Fix these first:$problems\n" >&2
  exit 1
fi

# Desired links: one "<agent folder>/<name> <TAB> <repo skill folder>" per line.
PLAN=""
plan() { PLAN="$PLAN$2/$1	$REPO/$3/$1
"; }
for n in $(skills_in skills); do
  [ "$LINK_CODEX" = 0 ]  || plan "$n" "$CODEX_DIR" skills
  [ "$LINK_CLAUDE" = 0 ] || plan "$n" "$CLAUDE_DIR" skills
done

move_aside() {  # $1 = path, $2 = label
  [ "$DRY" = 1 ] || mkdir -p "$BACKUP/$2"
  run mv "$1" "$BACKUP/$2/"
}

# Remove links into this repo that are not in the plan (deleted or moved skills).
for root in "$CODEX_DIR" "$CLAUDE_DIR"; do
  [ -d "$root" ] || continue
  [ "$(resolved "$root")" != "$SKILLS_REAL" ] || continue
  for l in "$root"/*; do
    [ -L "$l" ] || continue
    case "$(readlink "$l")" in
      "$REPO"/*) printf '%s' "$PLAN" | cut -f1 | grep -qxF "$l" || run rm "$l" ;;
    esac
  done
done

# Create or fix planned links.
while IFS="$(printf '\t')" read -r dest src; do
  [ -n "$dest" ] || continue
  if [ -L "$dest" ]; then
    [ "$(readlink "$dest")" = "$src" ] && continue
    echo "replacing link $dest (was -> $(readlink "$dest"))"
  elif [ -e "$dest" ]; then
    case "$dest" in "$CODEX_DIR"/*) move_aside "$dest" codex ;; *) move_aside "$dest" claude ;; esac
  fi
  [ -d "$(dirname "$dest")" ] || run mkdir -p "$(dirname "$dest")"
  run ln -sfn "$src" "$dest"
done <<EOF
$PLAN
EOF

# Codex still reads the deprecated ~/.codex/skills and would list these skills twice.
# Skip it when it is the same folder as an agent folder or skills/ (a symlink, or CODEX_HOME=~/.agents):
# its entries are the links just made, or the skills themselves.
legacy_real="$(resolved "$LEGACY_CODEX_DIR")"
for other in "$CODEX_DIR" "$CLAUDE_DIR" "$REPO/skills"; do
  if [ -n "$legacy_real" ] && [ "$legacy_real" = "$(resolved "$other")" ]; then
    LEGACY_CODEX_DIR=""
  fi
done
for n in $(skills_in skills); do
  [ -n "$LEGACY_CODEX_DIR" ] || break
  if [ -e "$LEGACY_CODEX_DIR/$n" ] || [ -L "$LEGACY_CODEX_DIR/$n" ]; then
    move_aside "$LEGACY_CODEX_DIR/$n" codex-legacy
  fi
done

[ "$DRY" = 1 ] && echo "Dry run: nothing changed." || echo "Linked skills from $REPO"
