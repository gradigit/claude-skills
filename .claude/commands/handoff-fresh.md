# /handoff-fresh

Run the `handoff-fresh` skill as an explicit manual command.

## Contract
- Trigger only from explicit user invocation (`/handoff-fresh`)
- Produce fork-safe fresh-agent onboarding bundle under `.handoff-fresh/current/` (default)
- Default ignore policy should keep `HANDOFF.md` + `.handoff-fresh/` out of untracked noise via `--ignore-mode local` unless user requests `shared` or `off`
- Required outputs in bundle: `claude.md`, `agents.md`, `todo.md`, `handoff.md`, `context.md`, `reports.md`, `artifacts.md`, `state.md`, `prior-plans.md`, `read-receipt.md`, `session-log-digest.md`, `session-log-chunk.md`, `handoff-everything.md`
- Root `HANDOFF.md` should be updated with a bridge pointer to `.handoff-fresh/current/handoff.md`
- Root `HANDOFF.md` bridge should treat "read HANDOFF.md" as bootstrap and force immediate switch to bundle handoff
- Bundle `handoff.md` must include Question Gate guidance: use ask-question before coding when prep info is missing/ambiguous
- Fresh-agent preflight gate should be enforceable via agent-internal `/handoff-fresh --validate-read-gate` before coding
- Deterministic preflight validator script is available at `scripts/validate_read_gate.py` (relative to skill directory)
- Bundle `handoff.md` should enforce bootstrap/autostart Read Gate behavior when prompt only says "read handoff.md" (no one-file interim summary)
- `claude.md` and `agents.md` must share an identical `SHARED-ONBOARDING-CONTEXT` block so either file provides the same core project context
- Session-log continuity should be token-budgeted and high-signal (extractive digest + raw chunk), not full unfiltered transcript dumps
- `prior-plans.md` must be marked reference-only unless user explicitly says it is the active plan
