---
name: wrap
description: End-of-session coordinator that chains sync-docs, claude-md-improver, and handoff into one command. Activates when user asks to "wrap up", "wrap", "end session", "session wrap", or types /wrap.
license: MIT
metadata:
  version: "1.0.0"
  author: gradigit
  tags:
    - session
    - workflow
    - automation
  triggers:
    - "wrap up"
    - "wrap"
    - "end session"
    - "session wrap"
---

# Wrap

Chains end-of-session skills into one command: sync docs, audit CLAUDE.md quality, and hand off.

## Workflow

```
- [ ] 1. Run syncing-docs (full mode — drift fix + session learnings + cross-file checks)
- [ ] 2. Run claude-md-improver (quality audit + targeted improvements)
- [ ] 3. Run handoff (commit, update docs, generate HANDOFF.md)
```

## Arguments

- No args: Run all three steps in sequence
- `--no-handoff`: Skip step 3 (useful mid-session when you want to sync but keep working)
- `--quick`: Pass `--quick` to syncing-docs (drift fix only, skip learnings/cross-file)

## Step 1: Sync Docs

Invoke the **syncing-docs** skill (full mode unless `--quick`):
- Fix drift between code and owned docs
- Capture session learnings into CLAUDE.md
- Check cross-file consistency across all state files

## Step 2: Audit CLAUDE.md Quality

Invoke the **claude-md-improver** skill:
- Score CLAUDE.md against quality rubric
- Fill gaps (missing commands, architecture, gotchas)
- Apply improvements with user approval

## Step 3: Handoff

Invoke the **handoff** skill:
- Commit current work
- Generate/update HANDOFF.md with session snapshot
- Ready for /clear or session end

## Example

```
/wrap
```

Runs sync-docs → claude-md-improver → handoff sequentially. Each step shows its own output. Final output:

```
=== Wrap Complete ===
  Sync: 3 drift fixes, 1 learning captured, 2 cross-file issues flagged
  Quality: CLAUDE.md scored B (78/100), 2 improvements applied
  Handoff: Committed (abc1234), HANDOFF.md updated
```

## Self-Evolution

Update this skill when:
1. **New end-of-session skill added**: Add to the chain
2. **Ordering issue**: If a step should run before/after another, adjust sequence
