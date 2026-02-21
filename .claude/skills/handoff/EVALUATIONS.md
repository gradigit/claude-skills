# Evaluations for handoff

## Scenario 1: Happy path — project with changes (should-trigger, functional)

**Given** a git project with 3 modified files and existing CLAUDE.md, AGENTS.md, and TODO.md
**When** user says "handoff" or "/handoff"
**Then**
- [ ] Skill activates
- [ ] Runs git status to assess current state
- [ ] Commits uncommitted work (specific files, not `git add -A`)
- [ ] Creates or overwrites HANDOFF.md in project root
- [ ] HANDOFF.md includes First Steps, Session Summary, What's Next sections
- [ ] HANDOFF.md First Steps includes both CLAUDE.md and AGENTS.md when both exist
- [ ] HANDOFF.md includes bootstrap read rule and first-response read-receipt contract
- [ ] All file paths in HANDOFF.md point to files that actually exist
- [ ] `.git/info/exclude` contains `HANDOFF.md` and `.handoff-fresh/` by default (`--ignore-mode local`)
- [ ] Outputs confirmation with commit hash and instructions

## Scenario 2: Edge case — no git repo (should-trigger, functional)

**Given** a project directory without git initialized
**When** user says "save context"
**Then**
- [ ] Skill activates
- [ ] Skips commit step (no git)
- [ ] Notes "No git — changes not committed" in HANDOFF.md
- [ ] Still creates HANDOFF.md with session context

## Scenario 3: Should-NOT-trigger — sync docs request

**Given** user wants to update documentation to match code
**When** user says "sync my docs with the code changes"
**Then**
- [ ] handoff does NOT activate
- [ ] syncing-docs activates instead

## Scenario 4: Should-NOT-trigger — fresh agent onboarding bundle request

**Given** user wants a fork-safe package for a brand-new agent
**When** user says "/handoff-fresh"
**Then**
- [ ] handoff does NOT activate
- [ ] handoff-fresh activates instead

## Scenario 5: Edge case — AGENTS.md missing (should-trigger, functional)

**Given** CLAUDE.md exists but AGENTS.md is missing
**When** user says "/handoff"
**Then**
- [ ] Skill activates
- [ ] Creates or notes minimal AGENTS.md parity handling per contract
- [ ] HANDOFF.md clearly reports instruction-doc parity status

## Scenario 6: Edge case — user prompt only says read HANDOFF.md (should-trigger, functional)

**Given** a generated HANDOFF.md with First Steps list
**When** the next-session agent is prompted "read handoff.md"
**Then**
- [ ] Agent treats request as bootstrap and continues to read all First Steps files before replying
- [ ] Agent does not send one-file interim summary
- [ ] Agent's first substantive reply includes per-file read receipt with one-line takeaways

## Scenario 7: Edge case — shared ignore mode (should-trigger, functional)

**Given** a git project where user requests `/handoff --ignore-mode shared`
**When** handoff runs
**Then**
- [ ] `.gitignore` contains `HANDOFF.md` and `.handoff-fresh/`
- [ ] `.git/info/exclude` is not required for correctness in this mode
