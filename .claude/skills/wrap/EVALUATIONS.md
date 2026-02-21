# Evaluations for wrap

## Scenario 1: Happy path — full wrap (should-trigger, functional)

**Given** a project with code changes, existing CLAUDE.md + AGENTS.md, and syncing-docs + handoff skills installed
**When** user says "/wrap"
**Then**
- [ ] Skill activates
- [ ] Runs syncing-docs (step 1)
- [ ] Runs claude-md-improver (step 2)
- [ ] Mirrors shared-context quality-critical updates into AGENTS.md (step 2 parity pass)
- [ ] Runs handoff (step 3)
- [ ] Shows combined summary with results from each step
- [ ] Steps execute sequentially (sync → improve → handoff)

## Scenario 2: Edge case — wrap with --no-handoff (should-trigger, functional)

**Given** user wants to sync docs mid-session without ending
**When** user says "wrap --no-handoff"
**Then**
- [ ] Skill activates
- [ ] Runs syncing-docs (step 1) and claude-md-improver (step 2)
- [ ] Performs AGENTS.md parity mirror in step 2 when AGENTS.md exists
- [ ] Skips handoff (step 3)
- [ ] User can continue working after wrap completes

## Scenario 3: Should-NOT-trigger — just handoff

**Given** user only wants to save context, not sync docs
**When** user says "just do a handoff"
**Then**
- [ ] wrap does NOT activate
- [ ] handoff activates instead (direct handoff, no sync/improve chain)

## Scenario 4: Edge case — explicit fresh bundle in wrap (should-trigger, functional)

**Given** user wants standard wrap plus fork-safe onboarding bundle
**When** user says "/wrap --with-fresh"
**Then**
- [ ] wrap activates
- [ ] Runs syncing-docs, claude-md-improver, and handoff in order
- [ ] Explicitly runs `/handoff-fresh --no-sync` as step 4
- [ ] Reports generated `.handoff-fresh/current/handoff-everything.md` path in summary
