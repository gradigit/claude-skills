# Pickup Templates

Templates used by the pickup skill. Referenced from SKILL.md.

## Read Receipt (first substantive reply)

One line per required file. This is the agent's **first** substantive reply after
reading — not an interim one-file summary.

```
## Read Receipt
- [x] <file> — <one-line takeaway>
- [x] <file> — <one-line takeaway>
- [x] <file> — <one-line takeaway>
```

Rules:
- Every required file from the chosen artifact's First Steps / bundle Read Gate.
- Takeaway must be specific (not empty, not `-`, not a `<placeholder>`).
- Validated by `scripts/validate_read_gate.py` (exit 0 PASS / 1 FAIL).

## Verify-Gate Report

```
## Verify Gate (<advisory | blocking>)
Stakes: <low | high> — <reason, e.g. "next action writes code" / "live monitor referenced">

| Claim | Check | Expected | Actual | Result |
|-------|-------|----------|--------|--------|
| {claim} | {command} | {expected} | {actual} | PASS / DRIFT |

Verdict: <all checks pass | N drift items — blocking | advisory only>
```

If the producer supplied no Verify Block, derive the rows from the advisory
checklist (First-Steps files exist, tree clean, HEAD matches "Last commit",
bundle-vs-source freshness, basis-diff).

## Resume Contract (final output)

```
## Pickup — Resume Contract

1. RESUME TARGET — {artifact chosen} (date {YYYY-MM-DD}, commit {hash}).
   Historical (not used): {list of older/divergent artifacts, or "none"}

2. FRESHNESS — {current | stale | unknown}
   {basis-diff / drift evidence: HEAD stored vs now, branch, changed-file set, tests}

3. NEXT ACTIONS
   1. {single prioritized next action}
   2. {optional}
   Resume commands:
   ```bash
   {runnable commands to continue}
   ```

4. FALLBACK PATH — {none — handoff found | bundle | canonical | FORGE/CLAUDE pointer | era N}

5. BLOCKERS / DRIFT FLAGS
   - {failed verify check / missing file / timestamp divergence / no-verbatim-captured}
   OPEN DECISIONS (surfaced from handoff):
   - {decision the handoff left for the user, if any}
```

## Drift / Staleness Flag (inline)

Use when an artifact is stale or self-inconsistent:

```
⚠ DRIFT: {artifact} claims {X} but current state is {Y}.
Treating {artifact} as historical context; rebuilding {X} from {live source}.
```

## No-Handoff Fallback

When no handoff artifact exists at all:

```
No handoff artifact found (.handoff-fresh/current/, HANDOFF.md, FORGE-*, CLAUDE.md pointers all absent/empty).
Reconstructing from live sources instead:
- git log / git status (recent work)
- TODO.md (open tasks)
- CLAUDE.md / AGENTS.md (project context)
Then proposing the most likely resume point for confirmation.
```
