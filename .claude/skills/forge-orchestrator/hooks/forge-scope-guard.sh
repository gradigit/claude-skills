#!/usr/bin/env bash
# forge-scope-guard.sh — PreToolUse hook for Edit/Write scope validation
# Reads .claude/forge-scopes.json and warns (stderr, exit 0) when a build
# agent edits files outside its declared FILE SCOPE own patterns.
# Ships with forge-orchestrator; installed to .claude/hooks/ during intake.
set -euo pipefail

INPUT=$(cat)

# Only check Edit and Write tools
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL" in
  Edit|Write) ;;
  *) exit 0 ;;
esac

# Extract file path being edited
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[[ -z "$FILE_PATH" ]] && exit 0

# Extract cwd (agent identity for worktree-isolated agents)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
[[ -z "$CWD" ]] && exit 0

# Walk up from cwd to find .claude/forge-scopes.json
SEARCH_DIR="$CWD"
SCOPES_FILE=""
while [[ "$SEARCH_DIR" != "/" ]]; do
  if [[ -f "$SEARCH_DIR/.claude/forge-scopes.json" ]]; then
    SCOPES_FILE="$SEARCH_DIR/.claude/forge-scopes.json"
    break
  fi
  SEARCH_DIR=$(dirname "$SEARCH_DIR")
done

# No scopes file = no enforcement
[[ -z "$SCOPES_FILE" ]] && exit 0

# Look up agent by cwd key
AGENT_JSON=$(jq -r --arg cwd "$CWD" '.agents[$cwd] // empty' "$SCOPES_FILE" 2>/dev/null)
[[ -z "$AGENT_JSON" || "$AGENT_JSON" == "null" ]] && exit 0

AGENT_NAME=$(echo "$AGENT_JSON" | jq -r '.name // "unknown"')

# Derive project root from scopes file (one dir up from .claude/)
PROJECT_ROOT=$(dirname "$(dirname "$SCOPES_FILE")")

# Make file_path relative to project root
REL_PATH="${FILE_PATH#"$PROJECT_ROOT"/}"

# Check if relative path matches any "owns" pattern
MATCHED=false
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  # shellcheck disable=SC2053
  if [[ "$REL_PATH" == $pattern ]]; then
    MATCHED=true
    break
  fi
done < <(echo "$AGENT_JSON" | jq -r '.owns[]? // empty')

if [[ "$MATCHED" == "false" ]]; then
  OWNS=$(echo "$AGENT_JSON" | jq -c '.owns // []')
  echo "[forge-scope-guard] WARNING: Agent '$AGENT_NAME' editing '$REL_PATH' — outside declared scope $OWNS" >&2
fi

# Always exit 0 — warn only, never block
exit 0
