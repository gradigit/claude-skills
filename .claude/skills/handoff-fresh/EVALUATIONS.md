# Evaluations for handoff-fresh

## Scenario 1: Happy path — foldered bundle in project directory (should-trigger, functional)

**Given** a git project with CLAUDE.md, TODO.md, and existing HANDOFF.md
**When** user says "/handoff-fresh"
**Then**
- [ ] Skill activates
- [ ] Runs `/sync-docs` first (unless skipped)
- [ ] Generates required files in `.handoff-fresh/current/`
- [ ] Generates `.handoff-fresh/current/handoff-everything.md`
- [ ] Includes project context, history, prior plans, and current status across output files

## Scenario 2: Edge case — no git repo (should-trigger, functional)

**Given** a new folder without git initialized
**When** user says "/handoff-fresh"
**Then**
- [ ] Skill activates
- [ ] Records `no-git` state in `.handoff-fresh/current/state.md`
- [ ] Generates all required files from filesystem context
- [ ] Includes explicit no-git note in `.handoff-fresh/current/handoff-everything.md`

## Scenario 3: Edge case — root handoff bridge pointer (should-trigger, functional)

**Given** fresh bundle generation completed
**When** user opens root `HANDOFF.md`
**Then**
- [ ] `HANDOFF.md` clearly states fresh bundle was generated
- [ ] `HANDOFF.md` points to `.handoff-fresh/current/handoff.md`
- [ ] File instructs fresh agent to follow workspace preparation in bundle handoff before coding

## Scenario 4: Edge case — read gate hard-stop + read receipt (should-trigger, functional)

**Given** a fresh agent starts from `.handoff-fresh/current/handoff.md`
**When** the handoff is consumed
**Then**
- [ ] `handoff.md` contains mandatory Read Gate section before Workspace Preparation
- [ ] Read Gate requires receipts for `handoff.md`, `claude.md`, `todo.md`, `state.md`, `context.md`
- [ ] `read-receipt.md` exists in bundle with required checklist entries
- [ ] Handoff explicitly says not to proceed if any required file is unread

## Scenario 5: Edge case — prior plans safety labeling (should-trigger, functional)

**Given** old plan files exist in architect/ and docs/
**When** user says "/handoff-fresh"
**Then**
- [ ] `.handoff-fresh/current/prior-plans.md` is generated
- [ ] Top warning states plans are reference-only unless user explicitly confirms active use
- [ ] Fresh agent is not instructed to treat prior plans as active by default

## Scenario 6: Edge case — mandatory question gate in workspace prep (should-trigger, functional)

**Given** bundle handoff has missing branch target and ambiguous task priority
**When** a fresh agent follows `.handoff-fresh/current/handoff.md`
**Then**
- [ ] Workspace Preparation explicitly instructs use of ask-question before coding
- [ ] Fresh agent is instructed to do only safe/reversible prep while waiting
- [ ] Fresh agent is instructed to log assumptions in `state.md`

## Scenario 7: Edge case — read gate preflight validator (should-trigger, functional)

**Given** `.handoff-fresh/current/read-receipt.md` exists
**When** user runs `/handoff-fresh --validate-read-gate`
**Then**
- [ ] Skill validates required checklist entries for all five required files
- [ ] Skill fails if any checklist item is unchecked (`[ ]`)
- [ ] Skill fails if any checklist item has an empty takeaway
- [ ] `scripts/validate_read_gate.py` exits non-zero on failure and zero on success
- [ ] Failure output instructs ask-question before coding if information is missing/ambiguous
- [ ] Success output indicates Read Gate passed and coding may proceed

## Scenario 8: Should-NOT-trigger — standard handoff request

**Given** user wants normal end-of-session handoff only
**When** user says "/handoff"
**Then**
- [ ] handoff-fresh does NOT activate
- [ ] handoff activates instead

## Scenario 9: Edge case — user prompt only says read handoff.md (should-trigger, functional)

**Given** a fresh agent receives prompt "Read .handoff-fresh/current/handoff.md"
**When** agent opens the bundle handoff
**Then**
- [ ] Agent treats prompt as onboarding bootstrap and continues full Read Gate automatically
- [ ] Agent reads `claude.md`, `todo.md`, `state.md`, and `context.md` before replying
- [ ] Agent does not send one-file interim summary
- [ ] Agent's first substantive response is full Read Gate receipt with one-line takeaways

## Scenario 10: Edge case — claude/agents context parity (should-trigger, functional)

**Given** `/handoff-fresh` generates both `.handoff-fresh/current/claude.md` and `.handoff-fresh/current/agents.md`
**When** bundle validation runs
**Then**
- [ ] Both files include `BEGIN/END SHARED-ONBOARDING-CONTEXT` marker block
- [ ] Shared onboarding block content is byte-identical in both files
- [ ] Any platform-specific appendix appears only after the shared block
- [ ] Fresh agent using only one file still receives the same shared project context

## Scenario 11: Edge case — token-budgeted session-log continuity (should-trigger, functional)

**Given** session logs are available during `/handoff-fresh`
**When** bundle generation runs
**Then**
- [ ] `session-log-digest.md` and `session-log-chunk.md` are generated
- [ ] Digest is extractive/high-signal (decisions, pivots, constraints), not generic prose
- [ ] Raw chunk excludes low-signal chatter and includes context notes
- [ ] Combined log payload stays within configured token budget
- [ ] `handoff-everything.md` records budget targets and actual estimate

## Scenario 12: Edge case — user prompt says read root HANDOFF.md (should-trigger, functional)

**Given** root `HANDOFF.md` is a bridge to fresh bundle
**When** a fresh agent is prompted "read handoff.md"
**Then**
- [ ] Agent treats request as bootstrap and immediately switches to `.handoff-fresh/current/handoff.md`
- [ ] Agent completes bundle Read Gate before substantive reply
- [ ] Agent does not stop after summarizing root bridge file only
