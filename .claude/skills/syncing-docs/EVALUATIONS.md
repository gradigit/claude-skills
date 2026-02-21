# Evaluations for syncing-docs

## Scenario 1: Happy path — stale docs after code change (should-trigger, functional)

**Given** a git project where src/main.py was renamed to src/app.py but CLAUDE.md still references src/main.py
**When** user says "/sync-docs"
**Then**
- [ ] Skill activates
- [ ] Detects the renamed file via git history
- [ ] Updates the path reference in CLAUDE.md and AGENTS.md (owned docs)
- [ ] Does NOT edit TODO.md or HANDOFF.md directly (watched files — flags only)
- [ ] Updates .doc-manifest.yaml last_synced timestamp
- [ ] Shows summary of drift fixes applied

## Scenario 2: Edge case — quick mode (should-trigger, functional)

**Given** a project with recent code changes
**When** user says "sync docs --quick"
**Then**
- [ ] Skill activates
- [ ] Runs drift fix (steps 1-4) and manifest update (step 7)
- [ ] Skips session learnings (step 5) and cross-file checks (step 6)
- [ ] Completes faster than full mode

## Scenario 3: Edge case — refresh fresh-agent bundle (should-trigger, functional)

**Given** `.handoff-fresh/current/` bundle files exist but are older than current CLAUDE.md and git status
**When** user says "/sync-docs --refresh-fresh-bundle"
**Then**
- [ ] Skill activates
- [ ] Completes normal sync flow
- [ ] Runs `/handoff-fresh --no-sync` explicitly (step 8)
- [ ] Verifies required bundle files are regenerated in `.handoff-fresh/current/`
- [ ] Includes `read-receipt.md` in required bundle-file checks
- [ ] Includes `session-log-digest.md` and `session-log-chunk.md` in required bundle-file checks
- [ ] Flags contradiction if bundle `claude.md` and `agents.md` shared onboarding context is out of sync
- [ ] Reports bundle directory and `handoff-everything.md` output path in summary

## Scenario 4: Should-NOT-trigger — handoff request

**Given** user wants to save session state for continuation
**When** user says "save my progress and create a handoff"
**Then**
- [ ] syncing-docs does NOT activate
- [ ] handoff activates instead
