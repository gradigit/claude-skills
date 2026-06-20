# Evaluations for pickup

## Scenario 1: Canonical HANDOFF.md resume (should-trigger, functional)

**Given** a repo with a root `HANDOFF.md` (canonical, `producer=handoff`) whose First Steps list names CLAUDE.md, AGENTS.md, TODO.md, and one source file
**When** user says "/pickup" or "pick up where we left off"
**Then**
- [ ] Skill activates
- [ ] Detects the canonical artifact (schema marker first, heading fallback)
- [ ] Reads ALL First Steps files before the first substantive reply
- [ ] First reply is a per-file read receipt with non-empty takeaways (no interim one-file summary)
- [ ] Reads the `## Last Exchange (Verbatim)` section before proposing next steps
- [ ] Runs the verify gate (advisory or blocking per stakes)
- [ ] Outputs the 5-item resume contract

## Scenario 2: Fresh bundle resume (should-trigger, functional)

**Given** `.handoff-fresh/current/handoff.md` exists and root `HANDOFF.md` is a bridge pointer
**When** user says "/pickup"
**Then**
- [ ] Detects the bundle path (precedence rung 1); follows the bridge rather than stopping at root HANDOFF.md
- [ ] Uses the 5-file bundle Read Gate (handoff.md, claude.md, todo.md, state.md, context.md)
- [ ] Reads the verbatim last-turn block in session-log-chunk.md
- [ ] Validates the receipt via `scripts/validate_read_gate.py --bundle-dir .handoff-fresh/current`

## Scenario 3: Bare "read HANDOFF.md" routes to pickup (should-trigger, functional)

**Given** a generated `HANDOFF.md`
**When** the next-session agent is prompted only "read handoff.md"
**Then**
- [ ] The request is treated as a `/pickup` bootstrap (the high-traffic weak path gets strong behavior)
- [ ] Agent expands to all First Steps, emits receipts, reads verbatim, runs verify — does NOT read one file and summarize

## Scenario 4: Stale handoff — high-stakes blocking gate (should-trigger, functional)

**Given** a `HANDOFF.md` that references a live monitor/production system and claims "system healthy, 81 tests green", but `git` HEAD has diverged from the claimed last commit
**When** user says "/pickup"
**Then**
- [ ] Stakes detected as high (live-system signal present)
- [ ] Verify gate is BLOCKING: the named checks (HEAD vs claimed commit, tests, health) are re-run before any action
- [ ] Drift is reported (HEAD mismatch); agent does NOT act on the stale "healthy" claim
- [ ] If a `## Verify Block` exists, each claim|check|expected line is executed

## Scenario 5: Old / hand-written artifact, no contract (should-trigger, functional)

**Given** a hand-written `HANDOFF.md` with no schema marker, no bootstrap rule, and no verbatim section
**When** user says "/pickup"
**Then**
- [ ] Agent enforces read-all + receipts + verify ANYWAY (guarantee lives in the skill, not the artifact)
- [ ] Flags "weak contract: no schema marker" and "no verbatim exchange captured" as drift
- [ ] Falls back to synthesis + freshness rebuild rather than assuming continuity

## Scenario 6: Divergent pointers — pick freshest, flag historical (should-trigger, functional)

**Given** CLAUDE.md points at a `FORGE-*` set dated months ago while `HANDOFF.md` is recent
**When** user says "/pickup"
**Then**
- [ ] Picks the freshest artifact by embedded date (then mtime)
- [ ] Explicitly flags the stale `FORGE-*` set as historical in the drift flags
- [ ] Does NOT silently merge contradictory eras

## Scenario 7: No handoff exists — fallback (should-trigger, functional)

**Given** no bundle, no HANDOFF.md, no FORGE-*, no CLAUDE.md resume pointer
**When** user says "/pickup"
**Then**
- [ ] Reports no handoff found
- [ ] Reconstructs from live sources (git log/status, TODO.md, CLAUDE.md)
- [ ] Proposes the most likely resume point for confirmation (uses ask-question only if genuinely blocked)

## Scenario 8: Should-NOT-trigger — user wants to WRITE a handoff

**Given** user is ending a session and wants to save state
**When** user says "/handoff" or "/wrap" or "save context"
**Then**
- [ ] pickup does NOT activate
- [ ] handoff / wrap activates instead (pickup is read-only consumer)

## Scenario 9: Should-NOT-trigger — generic file read

**Given** user wants a specific unrelated file read
**When** user says "read src/app.ts"
**Then**
- [ ] pickup does NOT activate (only the handoff-bootstrap phrasing "read HANDOFF.md" routes here)

## Scenario 10: Non-mutating by default (functional)

**Given** any successful pickup
**When** `/pickup` runs without `--write-receipt`
**Then**
- [ ] No files are written (receipt is printed inline only)
- [ ] With `--write-receipt`, only `.pickup-receipt.md` is written; no exported handoff artifact is modified

## Scenario 11: Validator parity (maintenance, deterministic)

**Given** the validator exists at both `handoff-fresh/scripts/validate_read_gate.py` and `pickup/scripts/validate_read_gate.py`
**When** comparing the two files
**Then**
- [ ] The shared functions/constants (`REQUIRED_FILES`, `LINE_PATTERN`, `LINE_PATTERN_ANY`, `takeaway_is_valid`) are byte-identical
- [ ] `diff` of the two files reports no differences (the copies are kept in sync)
