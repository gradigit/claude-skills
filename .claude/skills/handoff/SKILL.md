---
name: handoff
description: Creates context handoff files that preserve session state for seamless continuation after /clear. Activates when user says "handoff", "save context", "context handoff", "save progress", or types /handoff. Commits work, updates docs, and generates HANDOFF.md with branching instructions for new sessions.
license: MIT
metadata:
  version: "2.1.0"
  author: gradigit
  updated: "2026-02-07"
  tags:
    - context
    - handoff
    - continuity
    - session
  triggers:
    - "/handoff"
    - "handoff"
    - "save context"
    - "context handoff"
    - "save progress"
    - "quick handoff"
---

# Handoff

Creates context handoff files for seamless session continuation after `/clear`.

## Workflow

```
- [ ] 1. Assess current state
- [ ] 2. Handle prerequisites (git, docs)
- [ ] 3. Commit uncommitted work
- [ ] 4. Update documentation
- [ ] 5. Generate HANDOFF.md
- [ ] 6. Validate and confirm
```

## Quick Mode

When the session was short or the task was small (bug fix, config change, single-file edit), use the quick path:

1. `git status` — commit if needed
2. Generate HANDOFF.md using the quick template from [templates.md](templates.md)
3. Output confirmation

**Use quick mode when**: user says "quick handoff", session touched fewer than 3 files, or the task was a single focused change. Skip Steps 2-4 of the full workflow.

## Step 1: Assess Current State

Run these checks in parallel:

| Check | Command | What to look for |
|-------|---------|-----------------|
| Uncommitted changes | `git status` | Modified/untracked files |
| Change scope | `git diff --stat` | Which files changed |
| Existing docs | Check filesystem | CLAUDE.md, TODO.md, HANDOFF.md |
| Planning artifacts | Check filesystem | architect/ directory |
| Project root | `pwd` | Current working directory |

## Step 2: Handle Prerequisites

Handle edge cases before proceeding:

| Situation | Action |
|-----------|--------|
| **No git repo** | Skip Step 3. Note "No git — changes not committed" in handoff. |
| **No CLAUDE.md** | Create a minimal one with project name, key files, and current phase. |
| **No TODO.md** | Skip TODO updates. List next steps directly in HANDOFF.md. |
| **Merge conflicts** | Note conflicts in handoff under "Blockers". Do NOT attempt to resolve. |
| **User says no commit** | Skip Step 3. Note "Uncommitted changes exist" in handoff with file list. |
| **Dirty submodules** | Ignore submodule changes. Note in handoff if relevant. |

## Step 3: Commit Uncommitted Work

**Skip if**: no git repo, no changes, or user declines.

| Rule | Detail |
|------|--------|
| Stage files | `git add <specific files>` — never use `-A` or `.` |
| Exclude | `.env`, credentials, large binaries, `node_modules` |
| Commit message | `WIP: {brief description of current state}` |
| Never amend | Always create a new commit |
| Never push | Unless user explicitly requests it |

If no changes or user declines, note in handoff and continue.

## Step 4: Update Documentation

### CLAUDE.md

Update only if these sections exist:

- **Current Phase** — what phase/step we're on
- **Next step** — what to do next
- Add any new conventions or patterns discovered this session

### TODO.md

Update only if it exists:

- Mark completed items as `[x]`
- Add newly discovered tasks
- Note blockers in "Blocked / Issues" section

### Other docs

Only touch if changes were made this session:

| Doc | When to update |
|-----|---------------|
| README.md | Project structure changed |
| architect/STATE.md | In forging-plans workflow |

## Step 5: Generate HANDOFF.md

Create or overwrite `HANDOFF.md` in project root.

Use the standard template from [templates.md](templates.md). For emergency handoffs, use the emergency template.

### Branching Instructions Pattern

The "First Steps" section is critical — it tells the next session exactly what to read and in what order. The user only needs to say:

> "Read HANDOFF.md and continue"

The handoff branches out to all relevant files, eliminating the need for the user to list them.

### Existing Handoff Detection

If HANDOFF.md already exists:

1. Read it to understand previous state
2. Incorporate relevant context into the new handoff
3. Overwrite with updated state

Each handoff is a **complete snapshot** — never append.

## Step 6: Validate and Confirm

Before confirming, verify:

- [ ] Every file listed in "First Steps" actually exists
- [ ] Every file in "Reference Files" table has a valid path
- [ ] Commit hash matches actual last commit (if applicable)
- [ ] No placeholder text left unfilled (no `{...}` remaining)

Then output the confirmation using the template from [templates.md](templates.md).

## Emergency Handoff

When user interrupts mid-task (Esc + `/handoff`):

- Prioritize **speed over completeness**
- Commit partial work: `WIP: Interrupted — {brief context}`
- Use the emergency template from [templates.md](templates.md)
- Note exact resumption point: "Session interrupted mid-{task}. Resume from {exact point}."

## Example

**User:** `/handoff`

**Step 1 — Assess:**
```
git status → 3 files modified:
  src/middleware/auth.ts
  src/routes/login.ts
  tests/auth.test.ts
git diff --stat → 187 insertions, 23 deletions
CLAUDE.md → exists (has Current Phase section)
TODO.md → exists (4 items, 2 completed)
architect/ → not present
```

**Step 2 — Prerequisites:** All clear, git initialized, docs exist.

**Step 3 — Commit:**
```
git add src/middleware/auth.ts src/routes/login.ts tests/auth.test.ts
git commit -m "WIP: JWT auth middleware with refresh token rotation"
→ abc1234
```

**Step 4 — Update docs:**
- TODO.md: marks "Implement JWT validation" and "Add refresh token logic" as `[x]`
- CLAUDE.md: updates Current Phase to "Testing auth flow"

**Step 5 — Generate HANDOFF.md:**
```markdown
# Context Handoff — 2026-02-07

## First Steps (Read in Order)
1. Read CLAUDE.md — project context, auth architecture decisions
2. Read TODO.md — 2 of 4 auth tasks complete
3. Read src/middleware/auth.ts — JWT validation + refresh token rotation

## Session Summary

### What Was Done
- Implemented JWT validation middleware with RS256 signing
- Added refresh token rotation (old token invalidated on use)
- Updated login route to issue token pairs
- Started unit tests (3 of 8 passing)

### Current State
- Files modified: src/middleware/auth.ts, src/routes/login.ts, tests/auth.test.ts
- Last commit: abc1234 — WIP: JWT auth middleware with refresh token rotation

### What's Next
1. Fix remaining 5 failing auth tests (token expiry edge cases)
2. Add rate limiting to login endpoint
3. Integration test with frontend auth flow

### Failed Approaches
- Tried HS256 signing — switched to RS256 for key rotation without redeploying
- Tried storing refresh tokens in JWT — too large, moved to Redis for revocation support

### Key Context
- Using RS256 not HS256 — private key in config/keys/
- Refresh tokens stored in Redis, not JWT (design decision from CLAUDE.md)

## Reference Files
| File | Purpose |
|------|---------|
| src/middleware/auth.ts | JWT validation middleware |
| src/routes/login.ts | Login endpoint, token issuance |
| tests/auth.test.ts | Auth unit tests (3/8 passing) |
| config/keys/private.pem | RS256 signing key |
```

**Step 6 — Validate and confirm:**
```
Handoff complete.

Files updated:
- HANDOFF.md (created)
- TODO.md (2 items marked complete)
- CLAUDE.md (Current Phase updated)

To continue:
1. /clear to reset context
2. Say: "Read HANDOFF.md and continue"

Last commit: abc1234 — WIP: JWT auth middleware with refresh token rotation
```

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| `git add -A` stages secrets or binaries | Always stage specific files by name |
| `--amend` overwrites previous commit | Always create a new commit |
| Pushing without permission | Never push unless user explicitly asks |
| Stale file paths in HANDOFF.md | Validate all paths exist before confirming (Step 6) |
| Placeholder text left in template | Check for unfilled `{...}` tokens |
| Appending to old HANDOFF.md | Always overwrite — each handoff is a complete snapshot |
| Handoff without noting uncommitted work | If skipping commit, list uncommitted files in handoff |

## Self-Evolution

Update this skill when:

1. **On missed context**: User reports context not preserved → add to handoff template
2. **On branching failure**: New session didn't find files → improve First Steps section
3. **On workflow friction**: Handoff takes too long → streamline steps
4. **On edge case miss**: Unhandled situation encountered → add to Step 2 table

**Applied Learnings:**

- v2.1.0: Added Failed Approaches section to template (prevents next session repeating dead ends). Added Quick Mode for lightweight handoffs. Research-backed by cross-referencing Amp, Mother CLAUDE, and willseltzer/claude-handoff approaches.
- v2.0.0: Renamed from handing-off. Fixed frontmatter. Added edge case handling, pitfalls table, git ops table, validation step, concrete example. Extracted templates to templates.md.
- v1.0.0: Initial version based on forging-plans handoff pattern and external best practices

Current version: 2.1.0. See [CHANGELOG.md](CHANGELOG.md) for history.
