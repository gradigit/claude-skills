---
name: wrap
description: End-of-session coordinator that chains sync-docs, instruction-doc quality pass, and handoff into one command. Manual command entry point is /wrap. Optionally adds handoff-fresh bundle generation when explicitly requested.
license: MIT
metadata:
  version: "1.3.0"
  author: gradigit
  tags:
    - session
    - workflow
    - automation
  triggers:
    - "/wrap"
    - "wrap up"
    - "wrap"
    - "end session"
    - "session wrap"
---

# Wrap

Chains end-of-session skills into one command: sync docs, audit instruction docs quality (CLAUDE.md + AGENTS.md), and hand off.

## Command Contract (Explicit, Manual)

- Primary entry point: `/wrap`
- Execute only when user asks explicitly (`/wrap` or direct equivalent wording)
- Do **not** run via automatic hooks unless user explicitly configures and documents that behavior
- Optional fresh bundle generation must be explicit (`--with-fresh`)

## Workflow

```
- [ ] 1. Run syncing-docs (full mode — drift fix + session learnings + cross-file checks)
- [ ] 2. Run instruction-doc quality pass (CLAUDE.md improver + AGENTS parity mirror)
- [ ] 3. Run handoff (commit, update docs, generate HANDOFF.md)
- [ ] 4. Run handoff-fresh (optional, only if --with-fresh)
```

## Arguments

- No args: Run all three steps in sequence
- `--no-handoff`: Skip step 3 (useful mid-session when you want to sync but keep working)
- `--quick`: Pass `--quick` to syncing-docs (drift fix only, skip learnings/cross-file)
- `--with-fresh`: After step 3, run `/handoff-fresh --no-sync` to generate fork-safe onboarding bundle

## Step 1: Sync Docs

Invoke the **syncing-docs** skill (full mode unless `--quick`):
- Fix drift between code and owned docs
- Capture session learnings into CLAUDE.md + AGENTS.md
- Check cross-file consistency across all state files

## Step 2: Audit Instruction-Doc Quality

Invoke the **claude-md-improver** skill for CLAUDE.md:
- Score CLAUDE.md against quality rubric
- Fill gaps (missing commands, architecture, gotchas)
- Apply improvements with user approval

Then mirror shared-context quality-critical updates into AGENTS.md:
- Keep shared execution context aligned with CLAUDE.md
- Preserve platform-specific sections where needed
- Flag any unresolved CLAUDE/AGENTS contradiction in final summary

## Step 3: Handoff

Invoke the **handoff** skill:
- Commit current work
- Generate/update HANDOFF.md with session snapshot
- Ready for /clear or session end

## Step 4: Fresh Bundle (Optional)

Only when user explicitly passes `--with-fresh`:

- Invoke **handoff-fresh** with `--no-sync`
- Generate fresh-agent onboarding files in `.handoff-fresh/current/`
- Report bundle output paths in final summary

## Example

```
/wrap
```

Runs sync-docs → claude-md-improver → handoff sequentially. Each step shows its own output. Final output:

```
=== Wrap Complete ===
  Sync: 4 drift fixes (CLAUDE.md + AGENTS.md), 1 learning captured, 2 cross-file issues flagged
  Quality: CLAUDE.md scored B (78/100), 2 improvements applied, AGENTS.md parity mirrored
  Handoff: Committed (abc1234), HANDOFF.md updated
  Fresh: (omitted unless --with-fresh)
```

## Self-Evolution

Update this skill when:
1. **New end-of-session skill added**: Add to the chain
2. **Ordering issue**: If a step should run before/after another, adjust sequence
3. **Fresh-agent flow changes**: Update `--with-fresh` step and output contract
4. **Instruction-doc drift**: If CLAUDE.md and AGENTS.md drift repeatedly, tighten parity pass in Step 2
