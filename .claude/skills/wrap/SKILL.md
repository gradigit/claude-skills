---
name: wrap
description: Coordinates the end of a session by chaining sync-docs, an instruction-doc quality pass (CLAUDE.md + AGENTS.md), and handoff into one /wrap command; optionally adds a handoff-fresh bundle. Captures the verbatim last exchange first so nothing is lost. Do NOT use for a bare handoff (use /handoff) or to resume/ingest a prior session (use /pickup).
license: MIT
metadata:
  version: "1.5.0"
  author: gradigit
  updated: "2026-06-20"
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

`/wrap` **closes** a session. Its consumer counterpart is **`/pickup`**, which
**opens** the next one — it reads whatever `/wrap` (via `/handoff` /
`/handoff-fresh`) wrote. Together they form a producer→consumer contract pair.

## Command Contract (Explicit, Manual)

- Primary entry point: `/wrap`
- Execute only when user asks explicitly (`/wrap` or direct equivalent wording)
- Do **not** run via automatic hooks unless user explicitly configures and documents that behavior
- Optional fresh bundle generation must be explicit (`--with-fresh`)

## Workflow

```
- [ ] 0. Capture the verbatim last exchange FIRST (before sync/compaction can lose it)
- [ ] 1. Run syncing-docs (full mode — drift fix + session learnings + cross-file checks)
- [ ] 2. Run instruction-doc quality pass (CLAUDE.md improver + AGENTS parity mirror)
- [ ] 3. Run handoff (commit, update docs, generate HANDOFF.md)
- [ ] 4. Run handoff-fresh (optional, only if --with-fresh)
```

## Step 0: Capture the Verbatim Last Exchange First

Before running sync (which can be long enough for a context compaction to occur),
capture the **last user prompt** and **last assistant response** verbatim into
working notes, per the `/handoff` Step 0 contract. This guarantees the verbatim
resume anchor survives into the handoff regardless of what happens during the
later steps. Capture is manual — `/wrap` installs no auto-hooks.

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

Invoke the **handoff** skill (v3.0.0):
- Commit current work
- Generate/update HANDOFF.md with session snapshot, including the mandatory
  `## Last Exchange (Verbatim)` and machine-runnable `## Verify Block` sections
  (and the line-1 schema marker) — these are what make the handoff consumable by
  `/pickup`
- Ready for /clear or session end

To resume in the next session, the user runs **`/pickup`** (or "read HANDOFF.md",
which routes to `/pickup`).

## Step 4: Fresh Bundle (Optional)

Only when user explicitly passes `--with-fresh`:

- Invoke **handoff-fresh** with `--no-sync`
- Generate fresh-agent onboarding files in `.handoff-fresh/current/`
- Report bundle output paths in final summary

### Choosing the artifact shape (avoid silent inconsistency)

The output shape must be a deliberate choice, not an accident of which flag was
typed. Default `/wrap` writes the single canonical `HANDOFF.md` — correct for
same-repo continuity. Recommend `--with-fresh` (the multi-file bundle) when the next
agent is **fork/clone/fresh-onboarding** (new worktree, handed to a teammate, or a
cold start with no prior context).

- **Always state the shape** in the final summary: which artifact was written
  (`HANDOFF.md` vs `.handoff-fresh/` bundle) and that `/pickup` consumes it.
- If a `.handoff-fresh/` bundle already exists but you wrote only the canonical
  `HANDOFF.md` this run, say so — the now-older bundle is historical (handoff's
  precedence header + `/pickup`'s freshness check keep the next resume from following
  the stale bundle).
- Never leave both a fresh single-file handoff and an older bundle with no note of
  which is authoritative.

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
  Artifact shape: single canonical HANDOFF.md (no bundle) — /pickup will consume it
  Fresh: (omitted unless --with-fresh)
```

## Self-Evolution

Update this skill when:
1. **New end-of-session skill added**: Add to the chain
2. **Ordering issue**: If a step should run before/after another, adjust sequence
3. **Fresh-agent flow changes**: Update `--with-fresh` step and output contract
4. **Instruction-doc drift**: If CLAUDE.md and AGENTS.md drift repeatedly, tighten parity pass in Step 2

**Applied Learnings:**

- v1.5.0: **Artifact-shape discipline** (gap NEW-B from the A/B eval). Made the
  single-file-vs-bundle choice deliberate and self-described: guidance on when to add
  `--with-fresh`, the final summary always states which artifact was written and that
  `/pickup` consumes it, and a coexisting older bundle is explicitly marked historical
  (backed by handoff's new precedence header). Fixes the silent "shape depends on which
  flag was typed" inconsistency.
- v1.4.0: Added Step 0 (capture the verbatim last exchange first, before sync, so a compaction during later steps cannot lose it) and documented the wrap↔pickup producer→consumer contract pair. Step 3 now relies on handoff v3.0.0's mandatory Last Exchange + Verify Block sections that make the handoff consumable by `/pickup`.
- v1.3.0: Step 2 expanded from a CLAUDE-only quality pass to an instruction-doc quality flow (CLAUDE.md improvements + AGENTS.md parity mirror).
- v1.2.0: Updated `--with-fresh` to target the foldered handoff-fresh bundle path `.handoff-fresh/current/`.
- v1.0.0: Initial end-of-session coordinator chaining sync-docs → claude-md-improver → handoff.

Current version: 1.5.0. See [CHANGELOG.md](CHANGELOG.md) for history.
