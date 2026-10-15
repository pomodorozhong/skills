#!/usr/bin/env bash
# Copy selected existing Codex and Claude Code skills into this repo's skills/.
# A skill is imported only when all its installed copies (~/.agents/skills,
# ~/.codex/skills, ~/.claude/skills) are identical.
set -euo pipefail

usage() {
  cat <<EOF
Usage:
  $0 --skill NAME [NAME ...] [--skill NAME ...]
  $0 --all

Import one or more named skills, or use --all to import every eligible skill.
The script skips tool-managed folders (.system and synced), differing copies,
and any skill that already exists in this repository.
EOF
}

usage_error() {
  echo "Error: $1" >&2
  echo >&2
  usage >&2
  exit 2
}

MODE=""
SELECTED=()
if [ "$#" -eq 0 ]; then
  usage_error "No arguments provided. Choose --skill NAME [NAME ...] or --all."
fi

add_selected() {
  local item
  for item in "${SELECTED[@]-}"; do
    [ "$item" = "$1" ] && return 0
  done
  SELECTED+=("$1")
}

valid_skill_name() {
  [[ "$1" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || return 1
  [ "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" != "synced" ]
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help|-h)
      [ "$#" -eq 1 ] || usage_error "--help must be used by itself."
      usage
      exit 0
      ;;
    --all)
      [ -z "$MODE" ] && [ "$#" -eq 1 ] || usage_error "--all cannot be combined with other arguments."
      MODE="all"
      shift
      ;;
    --skill)
      [ "$MODE" != "all" ] || usage_error "--skill cannot be combined with --all."
      MODE="selected"
      shift
      count=0
      while [ "$#" -gt 0 ] && [[ "$1" != --* ]]; do
        valid_skill_name "$1" || usage_error "Invalid or reserved skill name: $1"
        add_selected "$1"
        count=$((count + 1))
        shift
      done
      [ "$count" -gt 0 ] || usage_error "--skill requires at least one skill name."
      ;;
    *)
      usage_error "Unknown argument: $1"
      ;;
  esac
done

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_SRC="$HOME/.agents/skills"
LEGACY_CODEX_SRC="${CODEX_HOME:-$HOME/.codex}/skills"
CLAUDE_SRC="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
STAGE="$REPO/.import"
SOURCES=(agents legacy claude)
EXCLUDES=(--exclude='/.system/' --exclude='/synced/' --exclude='.git/'
          --exclude='.DS_Store' --exclude='__pycache__/')

source_dir() {
  case "$1" in
    agents) echo "$CODEX_SRC" ;;
    legacy) echo "$LEGACY_CODEX_SRC" ;;
    claude) echo "$CLAUDE_SRC" ;;
  esac
}

rm -rf "$STAGE"
mkdir -p "$STAGE/agents" "$STAGE/legacy" "$STAGE/claude"
for source in "${SOURCES[@]}"; do
  root="$(source_dir "$source")"
  [ -d "$root" ] || continue
  if [ "$MODE" = "all" ]; then
    rsync -aL "${EXCLUDES[@]}" "$root/" "$STAGE/$source/"
  else
    for name in "${SELECTED[@]}"; do
      installed="$root/$name"
      [ -d "$installed" ] || continue
      mkdir -p "$STAGE/$source/$name"
      rsync -aL "${EXCLUDES[@]}" "$installed/" "$STAGE/$source/$name/"
    done
  fi
done

# Same files, contents, and executable bits. diff -rq alone ignores permissions.
same() {
  diff -rq "$1" "$2" >/dev/null &&
    [ "$(cd "$1" && find . -type f -perm -100 | sort)" = "$(cd "$2" && find . -type f -perm -100 | sort)" ]
}

add_name() {
  local item
  for item in "${NAMES[@]-}"; do
    [ "$item" = "$1" ] && return 0
  done
  NAMES+=("$1")
}

NAMES=()
if [ "$MODE" = "all" ]; then
  for source in "${SOURCES[@]}"; do
    for dir in "$STAGE/$source"/* "$STAGE/$source"/.[!.]* "$STAGE/$source"/..?*; do
      [ -d "$dir" ] || continue
      add_name "${dir##*/}"
    done
  done
  if [ -n "${NAMES[*]-}" ]; then
    SORTED_NAMES=()
    while IFS= read -r sorted_name; do
      SORTED_NAMES+=("$sorted_name")
    done < <(printf '%s\n' "${NAMES[@]}" | sort)
    NAMES=("${SORTED_NAMES[@]}")
  fi
else
  NAMES=("${SELECTED[@]}")
fi

mkdir -p "$REPO/skills"
differ=""
missing=""
for name in "${NAMES[@]-}"; do
  if [ -e "$REPO/skills/$name" ] || [ -L "$REPO/skills/$name" ]; then
    echo "already in repo, not overwritten: skills/$name" >&2
    continue
  fi
  first=""
  ok=1
  for source in "${SOURCES[@]}"; do
    dir="$STAGE/$source/$name"
    [ -f "$dir/SKILL.md" ] || continue
    if [ -z "$first" ]; then
      first="$dir"
    elif ! same "$first" "$dir"; then
      ok=0
    fi
  done
  if [ -z "$first" ]; then
    echo "not found in installed skill folders: $name" >&2
    missing="$missing $name"
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
  echo "Keep one version of each (move the others out of $CODEX_SRC, $LEGACY_CODEX_SRC, and $CLAUDE_SRC), then run import.sh again." >&2
fi
if [ -n "$missing" ]; then
  echo "Requested skills not imported:$missing" >&2
  exit 1
fi
echo "Done. Review imported skills before committing; remove any third-party skills you do not want in this public repo."
