#!/usr/bin/env bash
# Link every skill in this repo into the Codex and Claude Code personal skill folders.
# Safe to re-run. Each run that changes something records its changes, and moves any real
# folder it replaces, into ~/skills-link-backup/<timestamp>/ so the run can be undone.
#
# Usage: scripts/link.sh                     make the changes
#        scripts/link.sh --dry-run           print what would change, change nothing
#        scripts/link.sh --undo <run folder> undo one run (undo the newest run first)
#        scripts/link.sh --undo <run folder> --dry-run
set -euo pipefail

usage() {
  echo "Usage: $0 [--dry-run] [--undo <run folder>]" >&2
  exit 2
}
DRY=0 UNDO=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) [ "$DRY" = 0 ] || usage; DRY=1 ;;
    --undo) [ -z "$UNDO" ] && [ -n "${2:-}" ] || usage; UNDO="$2"; shift ;;
    *) usage ;;
  esac
  shift
done

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_DIR="$HOME/.agents/skills"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LEGACY_CODEX_DIR="${CODEX_HOME:-$HOME/.codex}/skills"

run() {  # print and run a command, or only print it in dry-run mode
  echo "+ $*"
  [ "$DRY" = 1 ] || "$@"
}

# ---------------------------------------------------------------- undo
if [ -n "$UNDO" ]; then
  LOG="$UNDO/changes.log"
  [ -f "$LOG" ] || { echo "No changes.log in $UNDO (already undone?)" >&2; exit 1; }
  skipped=0
  # Dry run keeps the state produced by its planned actions instead of changing files.
  preview_paths=() preview_types=() preview_targets=()
  state() {
    local i
    state_type=missing state_target=""
    if [ "$DRY" = 1 ]; then
      for ((i=${#preview_paths[@]}-1; i>=0; i--)); do
        if [ "${preview_paths[$i]}" = "$1" ]; then
          state_type="${preview_types[$i]}" state_target="${preview_targets[$i]}"
          return 0
        fi
      done
    fi
    if [ -L "$1" ]; then
      state_type=link state_target="$(readlink "$1")"
    elif [ -e "$1" ]; then
      state_type=other
    fi
  }
  preview() {
    [ "$DRY" = 1 ] || return 0
    preview_paths+=("$1"); preview_types+=("$2"); preview_targets+=("${3:-}")
  }
  occupied() { state "$1"; [ "$state_type" != missing ]; }
  # Undo in reverse order. Each line: action <TAB> path <TAB> value <TAB> previous link target
  while IFS="$(printf '\t')" read -r action path value old; do
    case "$action" in
      link)    # we pointed path at value; old is the previous link target, if any
        state "$path"
        if [ "$state_type" = link ] && [ "$state_target" = "$value" ]; then
          run rm "$path"
          preview "$path" missing
          if [ -n "$old" ]; then
            run ln -s "$old" "$path"
            preview "$path" link "$old"
          fi
        elif { [ "$state_type" = missing ] && [ -z "$old" ]; } ||
             { [ "$state_type" = link ] && [ -n "$old" ] && [ "$state_target" = "$old" ]; }; then
          echo "already unchanged or restored: $path"
        else
          echo "skip: $path changed since this run" >&2; skipped=1
        fi ;;
      move)    # we moved path to value
        if ! occupied "$value"; then
          if occupied "$path"; then
            echo "already restored or move not applied: $path"
          else
            echo "skip: both $path and its backup $value are missing" >&2; skipped=1
          fi
        elif occupied "$path"; then
          echo "skip: $path is occupied; original left at $value" >&2; skipped=1
        else
          state "$value"
          restored_type="$state_type" restored_target="$state_target"
          run mv "$value" "$path"
          preview "$value" missing
          preview "$path" "$restored_type" "$restored_target"
        fi ;;
      unlink)  # we removed a link at path that pointed at value
        state "$path"
        if [ "$state_type" = link ] && [ "$state_target" = "$value" ]; then
          echo "already unchanged or restored: $path"
        elif [ "$state_type" != missing ]; then
          echo "skip: $path is occupied; it pointed to $value" >&2; skipped=1
        else
          run ln -s "$value" "$path"
          preview "$path" link "$value"
        fi ;;
    esac
  done < <(awk '{ l[NR] = $0 } END { for (i = NR; i > 0; i--) print l[i] }' "$LOG")
  if [ "$DRY" = 1 ]; then
    echo "Dry run: nothing changed."
  elif [ "$skipped" = 1 ]; then
    echo "Undone except the skipped items above. $UNDO was kept." >&2
    exit 1
  else
    mv "$LOG" "$LOG.undone"
    echo "Undone. Delete $UNDO when you no longer need it."
  fi
  exit 0
fi

# ---------------------------------------------------------------- plan
# List skill folders (folders with SKILL.md) in one repo folder. Missing or empty folders are fine.
skills_in() {
  local d
  [ -d "$REPO/$1" ] || return 0
  for d in "$REPO/$1"/*/; do
    [ -f "$d/SKILL.md" ] && basename "$d"
  done
  return 0
}

# Check everything before changing anything.
problems=""
for n in $(skills_in skills); do
  [ -d "$REPO/codex-only/$n" ] && problems="$problems\n  '$n' is in skills/ and codex-only/"
  [ -d "$REPO/claude-only/$n" ] && problems="$problems\n  '$n' is in skills/ and claude-only/"
done
for n in $(skills_in skills) $(skills_in claude-only); do
  # Claude Code reserves 'synced' (any capitalization) for skills synced from claude.ai.
  [ "$(echo "$n" | tr '[:upper:]' '[:lower:]')" = "synced" ] &&
    problems="$problems\n  '$n' is reserved by Claude Code; rename it or move it to codex-only/"
done
if [ -n "$problems" ]; then
  printf "Nothing changed. Fix these first:$problems\n" >&2
  exit 1
fi

# Desired links: one "<agent folder>/<name> <TAB> <repo skill folder>" per line.
PLAN=""
plan() { PLAN="$PLAN$2/$1	$REPO/$3/$1
"; }
for n in $(skills_in skills);      do plan "$n" "$CODEX_DIR" skills; plan "$n" "$CLAUDE_DIR" skills; done
for n in $(skills_in codex-only);  do plan "$n" "$CODEX_DIR" codex-only; done
for n in $(skills_in claude-only); do plan "$n" "$CLAUDE_DIR" claude-only; done
planned() { printf '%s' "$PLAN" | cut -f1 | grep -qxF "$1"; }

# ---------------------------------------------------------------- apply
RUN_DIR="$HOME/skills-link-backup/$(date +%Y%m%d-%H%M%S)-$$"
changed=0
record() {  # action path value [old]
  if [ "$DRY" != 1 ]; then
    mkdir -p "$RUN_DIR"
    # Write the previous state before mutating it. A failed write stops the next change.
    printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "${4:-}" >> "$RUN_DIR/changes.log"
  fi
  changed=1
}
move_aside() {  # $1 = path, $2 = label
  local held="$RUN_DIR/$2/$(basename "$1")"
  [ "$DRY" = 1 ] || mkdir -p "$RUN_DIR/$2"
  record move "$1" "$held"
  run mv "$1" "$held"
}

# Remove links into this repo that are not in the plan (deleted or moved skills).
for root in "$CODEX_DIR" "$CLAUDE_DIR"; do
  [ -d "$root" ] || continue
  for l in "$root"/*; do
    [ -L "$l" ] || continue
    target="$(readlink "$l")"
    case "$target" in
      "$REPO"/*) planned "$l" || { record unlink "$l" "$target"; run rm "$l"; } ;;
    esac
  done
done

# Create or fix planned links.
while IFS="$(printf '\t')" read -r dest src; do
  [ -n "$dest" ] || continue
  old=""
  if [ -L "$dest" ]; then
    old="$(readlink "$dest")"
    [ "$old" = "$src" ] && continue
    echo "replacing link $dest (was -> $old)"
  elif [ -e "$dest" ]; then
    case "$dest" in "$CODEX_DIR"/*) label=codex ;; *) label=claude ;; esac
    move_aside "$dest" "$label"
  fi
  record link "$dest" "$src" "$old"
  [ -d "$(dirname "$dest")" ] || run mkdir -p "$(dirname "$dest")"
  run ln -sfn "$src" "$dest"
done <<EOF
$PLAN
EOF

# Codex still reads the deprecated ~/.codex/skills and would list these skills twice.
# Skip it when it is the same folder as ~/.agents/skills (a symlink, or CODEX_HOME=~/.agents):
# its entries are the links just made.
resolved() { (cd -P "$1" 2>/dev/null && pwd -P) || true; }
legacy_real="$(resolved "$LEGACY_CODEX_DIR")"
[ -n "$legacy_real" ] && [ "$legacy_real" = "$(resolved "$CODEX_DIR")" ] && LEGACY_CODEX_DIR=""
for n in $(skills_in skills) $(skills_in codex-only); do
  [ -n "$LEGACY_CODEX_DIR" ] || break
  if [ -e "$LEGACY_CODEX_DIR/$n" ] || [ -L "$LEGACY_CODEX_DIR/$n" ]; then
    move_aside "$LEGACY_CODEX_DIR/$n" codex-legacy
  fi
done

if [ "$DRY" = 1 ]; then
  echo "Dry run: nothing changed."
elif [ "$changed" = 1 ]; then
  echo "Linked skills from $REPO"
  echo "To undo this run: $0 --undo $RUN_DIR"
else
  echo "Already up to date."
fi
