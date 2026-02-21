# handoff-fresh templates

## prior-plans.md header

```markdown
# Prior Plans (Reference Only)

⚠️ Reference only. Do NOT treat this as the active plan unless the user explicitly confirms it.
```

## handoff.md workspace preparation block

```markdown
## Read Gate (Mandatory — complete before prep/coding)
Read these files in order:
1. `handoff.md`
2. `claude.md`
3. `todo.md`
4. `state.md`
5. `context.md`

Reply with this read receipt format before any prep/coding:
- [x] handoff.md — <1-line takeaway>
- [x] claude.md — <1-line takeaway>
- [x] todo.md — <1-line takeaway>
- [x] state.md — <1-line takeaway>
- [x] context.md — <1-line takeaway>

If any required file is unread or takeaway is missing:
- Stop and ask-question if needed.
- Do not proceed to Workspace Preparation or coding.

Bootstrap/autostart rule:
- If the user prompt only says "Read .handoff-fresh/current/handoff.md", treat it as onboarding bootstrap.
- Continue to read all required Read Gate files before replying.
- Do not send interim "done, I read handoff.md" summaries.

Preflight before coding:
- Fresh agent runs read-gate preflight validator (`/handoff-fresh --validate-read-gate` or script equivalent)
- If validator fails, fix `read-receipt.md`, ask-question if needed, and rerun.

## Workspace Preparation (Do before coding)
1. Confirm repo root and current branch.
2. Confirm working tree status and note uncommitted changes.
3. Confirm required root docs/folders are present.
4. Re-run `/sync-docs` if drift is detected.
5. Run Question Gate:
   - If required information is missing/ambiguous, use ask-question before coding.
   - If no answer yet, do only safe/reversible prep and log assumptions in `state.md`.
6. Start implementation only after steps 1-5 are complete.
```

## read-receipt.md template

```markdown
# Read Receipt (Mandatory Before Prep/Coding)

- [ ] handoff.md — 
- [ ] claude.md — 
- [ ] todo.md — 
- [ ] state.md — 
- [ ] context.md — 

Rule: Do not proceed to Workspace Preparation or coding until all items are checked and filled.
```

## session-log-digest.md template

```markdown
# Session Log Digest (Token-Budgeted)

Token target: 3000-4000
Scope: Extractive, high-signal decisions with brief verbatim evidence.

## Decision Timeline
- [time/phase] Decision: ...
  - Why: ...
  - Evidence snippet: "..."

## Rejected Alternatives
- Option: ...
  - Rejected because: ...

## User Constraints and Approvals
- Constraint/approval: ...

## Open Questions
- ...
```

## session-log-chunk.md template

```markdown
# Session Log Chunk (High-Signal Raw Excerpts)

Token target: 6000-8000
Rule: Include only high-signal excerpts (decisions, pivots, blockers). Exclude low-signal chatter.

## Excerpt 1
[context note]
> raw excerpt ...

## Excerpt 2
[context note]
> raw excerpt ...
```

## shared onboarding context block template (must be identical in claude.md and agents.md)

```markdown
<!-- BEGIN SHARED-ONBOARDING-CONTEXT -->
# Shared Onboarding Context

## Project Snapshot
...

## Build/Test Commands
...

## Key Files and Rules
...
<!-- END SHARED-ONBOARDING-CONTEXT -->
```

## preflight validator pass/fail output

```markdown
## Read Gate Preflight
Status: PASS
- [x] handoff.md takeaway present
- [x] claude.md takeaway present
- [x] todo.md takeaway present
- [x] state.md takeaway present
- [x] context.md takeaway present

Ready to begin Workspace Preparation.
```

## root HANDOFF.md bridge note

```markdown
# Context Handoff Bridge

A fresh-agent bundle was generated.

Read this first instead:
- `.handoff-fresh/current/handoff.md`

If prompt says "read HANDOFF.md", treat that as bootstrap for fresh onboarding and immediately switch to `.handoff-fresh/current/handoff.md`.

Complete Read Gate fully before replying (no interim one-file summary), then run Read Gate preflight validator before Workspace Preparation.

If workspace prep is blocked or ambiguous, use ask-question before coding.
```

## artifacts.md pointer block

```markdown
## Everything Path
- Relative: `.handoff-fresh/current/handoff-everything.md`
- Absolute: `{absolute_path_to_bundle}/handoff-everything.md`

## Session Log Continuity
- Relative: `.handoff-fresh/current/session-log-digest.md`
- Relative: `.handoff-fresh/current/session-log-chunk.md`
- Token budget: `{configured_budget}` / Actual estimate: `{actual_estimate}`
```
