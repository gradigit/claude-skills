---
name: handoff
description: Creates context handoff files that preserve session state for seamless continuation after /clear. Manual command entry point is /handoff. Commits work, updates docs, and generates HANDOFF.md with branching instructions for new sessions. Defaults to local git-ignore for handoff artifacts so they do not pollute working tree status. Use handoff-fresh for brand-new/forked-repo onboarding bundles.
license: MIT
metadata:
  version: "3.1.2"
  author: gradigit
  updated: "2026-06-20"
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

## Command Contract (Explicit, Manual)

- Primary entry point: `/handoff`
- Secondary natural-language triggers are allowed when user intent is explicit
- Do **not** rely on auto hooks or side-channel invocation
- Scope: standard session continuity (`HANDOFF.md`)
- If user requests fork-safe onboarding for a brand-new agent, run `/handoff-fresh` instead

## Workflow

```
- [ ] 0. Capture the verbatim last exchange FIRST (before anything can compact it away)
- [ ] 1. Assess current state
- [ ] 2. Handle prerequisites (git, docs)
- [ ] 3. Commit uncommitted work
- [ ] 4. Update documentation
- [ ] 5. Generate HANDOFF.md (incl. Last Exchange + Verify Block)
- [ ] 6. Validate and confirm
```

## Step 0: Capture the Verbatim Last Exchange First

Before any other step, capture — into your working notes — the **last user
prompt** and **last assistant response** *verbatim* (character-for-character),
plus any **load-bearing earlier directives** still governing the work. Do this
first because a context compaction can discard the raw turns at any time; once
captured you can safely run the rest of the flow.

This is the standardized replacement for the recurring manual workaround of
typing "save my last prompt and your last response so nothing is lost" into the
command. It is now part of the contract.

- **Redact** secrets/credentials that appeared in the turn (replace with «redacted»).
- **Budget** the verbatim block to ~1500 tokens; if the last response was long,
  quote the decision-bearing portion verbatim and summarize the rest in [brackets].
- **If the session is already compacted** (you see a compaction summary / boundary
  rather than the raw turns), capture what the summary preserves, then note in the
  handoff that pre-compaction verbatim detail is recoverable only from the raw
  transcript path. Do not fabricate a verbatim quote you no longer have.

> Capture is **manual** (part of `/handoff` and `/wrap`). This skill does not
> install auto-hooks; the family's contract is explicit-manual, and SessionStart/
> PreCompact hook injection is unreliable.

## Quick Mode

When the session was short or the task was small (bug fix, config change, single-file edit), use the quick path:

1. `git status` — commit if needed
2. Apply handoff artifact ignore policy (`--ignore-mode`, default local)
3. Generate HANDOFF.md using the quick template from [templates.md](templates.md)
4. Output confirmation

**Use quick mode when**: user says "quick handoff", session touched fewer than 3 files, or the task was a single focused change. Skip the full Step 2-4 deep pass (except apply ignore policy).

## Arguments

- `--quick`: Use quick mode template/flow
- `--ignore-mode <local|shared|off>`: How to ignore handoff artifacts
  - `local` (default): update `.git/info/exclude`
  - `shared`: update `.gitignore`
  - `off`: skip ignore updates

## Step 1: Assess Current State

Run these checks in parallel:

| Check | Command | What to look for |
|-------|---------|-----------------|
| Uncommitted changes | `git status` | Modified/untracked files |
| Change scope | `git diff --stat` | Which files changed |
| Existing docs | Check filesystem | CLAUDE.md, AGENTS.md, TODO.md, HANDOFF.md |
| Planning artifacts | Check filesystem | architect/ directory |
| Project root | `pwd` | Current working directory |

## Step 2: Handle Prerequisites

Handle edge cases before proceeding:

| Situation | Action |
|-----------|--------|
| **No git repo** | Skip Step 3. Note "No git — changes not committed" in handoff. |
| **No CLAUDE.md** | Create a minimal one with project name, key files, and current phase. |
| **No AGENTS.md** | If CLAUDE.md exists, create minimal AGENTS.md mirror for agent parity; otherwise note missing instruction-doc parity in HANDOFF.md blockers. |
| **No TODO.md** | Skip TODO updates. List next steps directly in HANDOFF.md. |
| **Git repo + ignore mode `local` (default)** | Ensure `.git/info/exclude` contains `HANDOFF.md` and `.handoff-fresh/`. |
| **Git repo + ignore mode `shared`** | Ensure `.gitignore` contains `HANDOFF.md` and `.handoff-fresh/`. |
| **Ignore mode `off`** | Do not edit ignore files. Note handoff artifacts may appear as untracked. |
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

### Instruction docs (CLAUDE.md + AGENTS.md)

Update only if these sections exist:

- **Current Phase** — what phase/step we're on
- **Next step** — what to do next
- Add any new conventions or patterns discovered this session

Parity rules:
- If both files exist, keep shared project context synchronized across both.
- If one has richer shared context, propagate the shared parts to the other.
- Platform-specific notes may differ, but shared execution context must match.

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

`/handoff` stays focused on one canonical file (`HANDOFF.md`).  
Do not generate the multi-file fresh-agent bundle here; that is `/handoff-fresh`.

### Mandatory sections (schema v3.0.0)

Every generated `HANDOFF.md` must include, and they must be non-empty (or marked
`N/A` with a reason):

- **Line 1 schema marker**: `<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->` —
  lets `/pickup` detect the schema/producer and tell skill-generated from
  hand-written handoffs.
- **Checkout binding** (in Current State): record the absolute checkout/worktree path
  + branch this handoff was written from (`git rev-parse --show-toplevel` + branch).
  In a repo with parallel worktrees this lets `/pickup` confirm a handoff belongs to
  the checkout being resumed and flag a cross-worktree mismatch instead of silently
  resuming from a sibling session's handoff.
- **`## Last Exchange (Verbatim)`** (after Session Summary): the verbatim last
  user prompt, last assistant response, and load-bearing earlier directives
  captured in Step 0. This is the resume anchor `/pickup` reads first.
- **`## Verify Block`** (after Reference Files): the load-bearing claims a
  resuming agent must not trust blindly, each as `claim | check-command |
  expected`. `/pickup` runs these on resume. Always include branch/HEAD; add
  test/health/build checks when the work depends on them. **Each command must
  actually validate its full claim** — use `git branch --show-current` for a
  branch-name claim (not `git rev-parse --short HEAD`, which returns only the hash);
  if a check can't run in this directory, mark its expected cell `unverifiable here`.

**Mark unverified results at the point of claim.** A result you did not run *this
session* (test counts, build/health status) must be labeled `(per session notes —
unverified)` wherever it appears in prose — "What Was Done", "Current State" — not
only inside the Verify Block. Never write "Verified: 42 passing" for a figure you are
merely carrying forward; that is the producer-side form of the fabricated-PASS failure
`/pickup` guards against. State what you actually ran, and mark the rest unverified.

### Branching Instructions Pattern

The "First Steps" section is critical — it tells the next session exactly what to read and in what order. The user only needs to say:

> "Read HANDOFF.md and continue"

The handoff branches out to all relevant files, eliminating the need for the user to list them.

### Bootstrap Read Rule (mandatory in generated HANDOFF.md)

Generated `HANDOFF.md` must explicitly say:
- If prompt says "read HANDOFF.md", treat it as a `/pickup` bootstrap (preferred:
  run `/pickup` for the full read-all + verify behavior).
- Continue reading all files listed in First Steps before replying.
- Do not send one-file interim acknowledgements.
- First substantive reply must include a read receipt with one-line takeaway per First Steps file.

> The embedded rule is a **hint**, not the enforcement mechanism. The guarantee
> lives in the `/pickup` consumer skill, which enforces read-all + receipts +
> verify even when the artifact is old/hand-written and lacks this clause.

### Existing Handoff Detection

If HANDOFF.md already exists:

1. Read it to understand previous state
2. Incorporate relevant context into the new handoff
3. Overwrite with updated state

Each handoff is a **complete snapshot** — never append.

### Resume-artifact precedence & cleanup

Repos accumulate competing resume artifacts — old dated `FORGE-HANDOFF.*`,
`FORGE-STATUS.*`, `MERGE-READINESS-*`, a stale `.handoff-fresh/`, prior dated
`HANDOFF-*.md` stubs. With no precedence rule the next agent (or `/pickup`) can
resume from the wrong one. Make this handoff unambiguously authoritative:

1. **Detect coexisting artifacts.** Scan the repo root (and worktrees) for
   `*HANDOFF*`, `FORGE-*`, and `.handoff-fresh/`.
2. **Emit a precedence header.** Immediately under the schema marker, when other
   resume artifacts exist, add:
   `> AUTHORITATIVE handoff — supersedes: FORGE-HANDOFF.2026-04-28.md, FORGE-STATUS.md, .handoff-fresh/ (stale).`
   naming the specific stale artifacts this file replaces. If none coexist, omit.
3. **Write to the one canonical path.** Overwrite `HANDOFF.md` — never create a new
   dated stub (`HANDOFF-2026-06-20.md`), which is exactly what creates the sprawl.
4. **Recommend cleanup (do not auto-delete).** In the confirmation output, list the
   dead artifacts and suggest archiving/removing them. Deletion needs explicit user
   confirmation — surface it, don't perform it.

## Step 6: Validate and Confirm

Before confirming, verify:

- [ ] Line 1 is the schema marker `<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->`
- [ ] Every file listed in "First Steps" actually exists
- [ ] Every file in "Reference Files" table has a valid path
- [ ] Commit hash matches actual last commit (if applicable)
- [ ] No placeholder text left unfilled (no `{...}` remaining)
- [ ] If both CLAUDE.md and AGENTS.md exist, shared project context is not contradictory
- [ ] HANDOFF.md includes bootstrap read rule and no-interim-summary first-response contract
- [ ] If in git repo and `--ignore-mode` is not `off`, selected ignore file contains `HANDOFF.md` and `.handoff-fresh/`
- [ ] If competing resume artifacts exist (`FORGE-*`, dated stubs, stale `.handoff-fresh/`), a precedence header naming the superseded ones is present, and the confirmation lists them for cleanup

**Content completeness** (each present and non-empty, or explicitly `N/A — <reason>`):

- [ ] `## Last Exchange (Verbatim)` — last user prompt + last assistant response captured verbatim, secrets redacted, within the ~1500-token budget
- [ ] `## Verify Block` — at least a branch/HEAD claim with a check command and expected value
- [ ] What's Next, Open Questions / Blockers, Current State (with last commit), Failed Approaches

**Final write is a full overwrite.** The last write of `HANDOFF.md` must rewrite
the whole file from the template — never finalize with a tiny trailing Edit patch.
Each handoff is a complete, self-validated snapshot.

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
<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->
# Context Handoff — 2026-02-07

## First Steps (Read in Order)
1. Read CLAUDE.md — project context, auth architecture decisions
2. Read AGENTS.md — agent operating constraints + command policy
3. Read TODO.md — 2 of 4 auth tasks complete
4. Read src/middleware/auth.ts — JWT validation + refresh token rotation

## Session Summary

### What Was Done
- Implemented JWT validation middleware with RS256 signing
- Added refresh token rotation (old token invalidated on use)
- Updated login route to issue token pairs
- Started unit tests (3 of 8 passing)

### Current State
- Checkout: /Users/you/project/.worktrees/feature-auth (branch: feature-auth)
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

## Last Exchange (Verbatim)
**Last user prompt:**
\`\`\`
fix the token expiry edge cases next, the 5 failing tests
\`\`\`
**Last assistant response:**
\`\`\`
The 5 failures are all in tests/auth.test.ts around clock-skew on exp. Plan: add a
30s leeway to verifyToken() and assert refresh issues a new exp. Starting there next.
\`\`\`
**Load-bearing earlier directives:**
1. "use RS256, not HS256 — we rotate keys without redeploy"
2. "refresh tokens go in Redis so we can revoke"

## Reference Files
| File | Purpose |
|------|---------|
| src/middleware/auth.ts | JWT validation middleware |
| src/routes/login.ts | Login endpoint, token issuance |
| tests/auth.test.ts | Auth unit tests (3/8 passing) |
| config/keys/private.pem | RS256 signing key |

## Verify Block
| Claim | Check command | Expected |
|-------|---------------|----------|
| On branch main, HEAD abc1234 | `git rev-parse --short HEAD` | abc1234 |
| 3 of 8 auth tests passing | `npm test -- tests/auth.test.ts` | 3 passing, 5 failing |
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
| New dated stub (`HANDOFF-<date>.md`) alongside the old one | Write the one canonical `HANDOFF.md`; that sprawl is what confuses the next resume |
| Stale `FORGE-*`/old artifacts left unmarked | Emit a precedence header naming them superseded; recommend cleanup |

## Self-Evolution

Update this skill when:

1. **On missed context**: User reports context not preserved → add to handoff template
2. **On branching failure**: New session didn't find files → improve First Steps section
3. **On workflow friction**: Handoff takes too long → streamline steps
4. **On edge case miss**: Unhandled situation encountered → add to Step 2 table

**Applied Learnings:**

- v3.1.2: **Checkout binding** for parallel-worktree safety. The generated handoff now
  records the absolute checkout/worktree path + branch in Current State, so `/pickup` can
  confirm a handoff belongs to the checkout being resumed and flag a cross-worktree
  mismatch instead of silently resuming from a sibling parallel session's handoff. Pairs
  with pickup 1.2.0's current-checkout-first rule.
- v3.1.1: **Verify-honesty at the point of claim** (after-eval regression). Note-sourced
  results (test counts, build/health) must be labeled `(per session notes — unverified)`
  in prose, not only in the Verify Block — the producer-side form of `/pickup`'s
  anti-fabrication rule. Each Verify Block command must validate its *full* claim
  (`git branch --show-current` for branch names; mark in-dir-unrunnable checks).
- v3.1.0: **Resume-artifact precedence & cleanup** (gap NEW-A/#6 from the A/B eval).
  When competing artifacts coexist (`FORGE-*`, dated stubs, stale `.handoff-fresh/`),
  the generated handoff now emits an `> AUTHORITATIVE — supersedes: …` header naming
  them, writes only the one canonical `HANDOFF.md` (never a new dated stub), and the
  confirmation recommends archiving the dead ones (no auto-delete). Closes the
  divergent-artifact-with-no-precedence-rule failure observed in real logs and the
  fixture eval (P3).
- v3.0.0: Schema v3 — mandatory line-1 `<!-- HANDOFF-SCHEMA -->` marker, a verbatim `## Last Exchange` section (last user prompt + last assistant response + load-bearing directives, captured first in Step 0 so compaction can't strip them), and a machine-runnable `## Verify Block` (claim | check | expected) consumed by the new `/pickup` skill. Added content-completeness assertions and a full-overwrite finalize rule (fixes the 47B-vs-12KB stub inconsistency). Standardizes the verbatim-capture workaround users were forcing manually. **Breaking**: old/hand-written HANDOFF.md files lack the marker — `/pickup` still handles them but flags a weak contract.
- v2.5.0: Added handoff-artifact ignore policy (`--ignore-mode local|shared|off`, default local) so `HANDOFF.md` and `.handoff-fresh/` do not show up as noisy untracked files.
- v2.4.0: Added mandatory bootstrap read rule in HANDOFF.md so "read handoff.md" prompts automatically trigger full First Steps reading before reply.
- v2.2.0: Added explicit manual command contract for `/handoff`; clarified separation of responsibilities between `/handoff` (standard continuity) and `/handoff-fresh` (fork-safe fresh onboarding bundle).
- v2.3.0: Added AGENTS.md-aware behavior for prerequisite checks, instruction-doc parity updates, and HANDOFF validation so Codex/Claude continuity remains aligned.
- v2.1.0: Added Failed Approaches section to template (prevents next session repeating dead ends). Added Quick Mode for lightweight handoffs. Research-backed by cross-referencing Amp, Mother CLAUDE, and willseltzer/claude-handoff approaches.
- v2.0.0: Renamed from handing-off. Fixed frontmatter. Added edge case handling, pitfalls table, git ops table, validation step, concrete example. Extracted templates to templates.md.
- v1.0.0: Initial version based on forging-plans handoff pattern and external best practices

Current version: 3.1.2. See [CHANGELOG.md](CHANGELOG.md) for history.
