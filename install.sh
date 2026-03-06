#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/gradigit/claude-skills.git"
CLONE_DIR=""

cleanup() { [[ -n "$CLONE_DIR" ]] && find "$CLONE_DIR" -depth -delete 2>/dev/null; }
trap cleanup EXIT

echo "claude-skills installer"
echo ""

CLONE_DIR=$(mktemp -d)
echo "Fetching latest..."
git clone --depth 1 --quiet "$REPO" "$CLONE_DIR"

# Collect skill names
skills=()
while IFS= read -r dir; do
  skills+=("$(basename "$dir")")
done < <(find "$CLONE_DIR/.claude/skills" -mindepth 1 -maxdepth 1 -type d | sort)

echo ""
echo "Available skills (${#skills[@]}):"
echo ""
echo "  Meta/Tooling:      creating-skills, updating-skills, auditing-skills, testing-skills"
echo "  Session:           handoff, handoff-fresh, syncing-docs, managing-doc-manifest, wrap"
echo "  Research:          study"
echo "  Forge (autonomous): forge-claude-teams, forge-codex-multiagent, forge-research,"
echo "                      forge-builder, forge-orchestrator"
echo ""

# Defaults
loc="1"
selected=()

if [[ "${1:-}" == "--all" ]]; then
  selected=("${skills[@]}")
else
  printf "Install all? [Y/n] "
  read -r ans < /dev/tty
  if [[ "${ans:-Y}" =~ ^[Nn] ]]; then
    echo ""
    echo "Enter skill names separated by spaces:"
    printf "> "
    read -ra selected < /dev/tty
  else
    selected=("${skills[@]}")
  fi

  echo ""
  echo "Install to:"
  echo "  1) ~/.claude/  — global, all projects [default]"
  echo "  2) .claude/    — current project only"
  printf "Choice [1]: "
  read -r loc < /dev/tty
fi

dest="$HOME/.claude"
[[ "${loc:-1}" == "2" ]] && dest=".claude"

mkdir -p "$dest/skills" "$dest/commands"
count=0
has_forge=false

for skill in "${selected[@]}"; do
  if [[ -d "$CLONE_DIR/.claude/skills/$skill" ]]; then
    cp -r "$CLONE_DIR/.claude/skills/$skill" "$dest/skills/"
    count=$((count + 1))
    [[ "$skill" == forge-* ]] && has_forge=true
  else
    echo "  skip: '$skill' not found"
  fi
done

# Copy all commands
for cmd in "$CLONE_DIR/.claude/commands/"*.md; do
  [[ -f "$cmd" ]] && cp "$cmd" "$dest/commands/"
done

# Copy forge agents if any forge skill was selected
if $has_forge && [[ -d "$CLONE_DIR/.claude/agents" ]]; then
  mkdir -p "$dest/agents"
  cp "$CLONE_DIR/.claude/agents/"*.md "$dest/agents/"
  echo "  + forge custom agents"
fi

echo ""
echo "Installed $count skills to $dest/skills/"
echo ""
echo "Commands:"
for cmd in "$dest/commands/"*.md; do
  [[ -f "$cmd" ]] && echo "  /$(basename "${cmd%.md}")"
done
echo ""
echo "Update anytime by re-running this command."
