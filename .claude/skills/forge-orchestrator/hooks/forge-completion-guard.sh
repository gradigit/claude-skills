#!/usr/bin/env bash
# forge-completion-guard.sh — PreToolUse hook (Claude Code) for anti-false-completion.
#
# Defense-in-depth on top of forge_completion_guard.py. Fires on Write/Edit; when
# the write marks a run/milestone COMPLETE (state: FINALIZED, or a milestone set to
# completed in FORGE-STATUS.md), it requires a passing goal-reconciliation artifact
# before allowing the write. Blocks with exit 2 if GATE E evidence is missing.
#
# Cross-platform note: Codex has no PreToolUse hooks, so on Codex the orchestrator
# runs forge_completion_guard.py directly as a GATE E tool call. This hook only
# hardens the Claude path. Escape hatch: FORGE_GATE_OVERRIDE=1 (logged).
#
# Install to .claude/hooks/ and register on PreToolUse matcher "Write|Edit".
set -euo pipefail

INPUT=$(cat)

TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
case "$TOOL" in
  Write|Edit) ;;
  *) exit 0 ;;
esac

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
[[ -z "$CWD" ]] && CWD="$(pwd)"

# Only engage when the write signals completion.
is_completion=false
case "$FILE_PATH" in
  *FORGE-STATUS.md|*FORGE-HANDOFF.md) ;;
  *) FILE_PATH="" ;;
esac
if echo "$CONTENT" | grep -qiE 'state:[[:space:]]*finalized|status:[[:space:]]*completed|^- \[x\] Milestone .*completed'; then
  is_completion=true
fi
[[ "$is_completion" == "false" ]] && exit 0

# Escape hatch (loud).
if [[ "${FORGE_GATE_OVERRIDE:-}" == "1" ]]; then
  echo "[forge-completion-guard] OVERRIDE: FORGE_GATE_OVERRIDE=1 — allowing completion write without GATE E verification." >&2
  exit 0
fi

GUARD="$(dirname "$0")/forge_completion_guard.py"
[[ -f "$GUARD" ]] || GUARD="$CWD/.claude/hooks/forge_completion_guard.py"

# Find the current milestone's reconciliation artifact (newest in review-findings).
RECON=$(ls -t "$CWD"/architect/review-findings/*-goal-reconciliation.md 2>/dev/null | head -1 || true)

if [[ -z "$RECON" ]]; then
  echo "[forge-completion-guard] BLOCK: completion write detected but no goal-reconciliation artifact exists (GATE E skipped). Run GATE E first, or set FORGE_GATE_OVERRIDE=1 with justification." >&2
  exit 2
fi

if python3 "$GUARD" "$RECON" --repo-root "$CWD" >/tmp/forge-gate-e.out 2>&1; then
  exit 0
else
  echo "[forge-completion-guard] BLOCK: GATE E checker FAILED for $RECON:" >&2
  sed 's/^/[forge-completion-guard]   /' /tmp/forge-gate-e.out >&2
  echo "[forge-completion-guard] Build the unmet criteria or set FORGE_GATE_OVERRIDE=1 (logged) to override." >&2
  exit 2
fi
