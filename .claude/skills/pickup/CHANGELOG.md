# Changelog

All notable changes to the pickup skill.

## [1.1.1] - 2026-06-20

### Fixed
- Over-ceremony residual (after-eval C1): Step 5 and the Step 8 blockers contract no
  longer instruct flagging a hand-written file's missing v3 scaffolding (marker / Last
  Exchange / Verify Block) as drift items — it is a single weak-contract line, never a
  per-section findings list. The repair offer is reserved for handoffs whose claims are
  false/stale, not merely unmarked.

## [1.1.0] - 2026-06-20

### Added
- **Anti-fabrication rule (critical):** a check may be reported `PASS`/`current`/clean
  only if actually run this turn with quotable output; otherwise it must be labeled
  `assumed (unverified)`. Fixes agents asserting environment facts ("not a git repo",
  "tree clean", "tests green") as verified with no command run.
- **Worktree-aware detection:** Step 1 now enumerates `HANDOFF.md` / `.handoff-fresh/`
  across sibling worktrees (`git worktree list` / bounded `find`), so a stale root
  handoff no longer hides the live one in `worktrees/<feature>/`.
- **Direction-of-drift evidence** required before a `stale` verdict (date headers,
  mtimes, `git log -1`, date-bounding); freshness is `unknown` when no timestamps.
- **Artifact-anchored read-all:** the receipt quotes the chosen artifact's own
  bootstrap / First-Steps directive as the authority for what to read and in what order.

### Changed
- Step 7 reconciliation now explicitly covers **factual content claims** (counts,
  config values, test results) — open the file and compare, don't pass through.
- Resume now **commits to the handoff's designated next action** instead of a
  redundant "proceed?" round-trip; offers (non-mutating) to **repair a chosen-but-stale
  handoff** whose own claims are false.
- Stops **over-reporting on minimal/hand-written artifacts** (weak-contract flag is a
  one-line note, not a graded critique) and never routes the next session to a
  non-First-Steps oracle file.

### Context
Hardening driven by a 3-arm A/B fixture eval (pre-v3 / HEAD / fixed) that reproduced a
critical hallucinated-verify-PASS failure and several HEAD-introduced over-reporting
regressions, then verified each fix closed.

## [1.0.0] - 2026-06-20

### Added
- Initial release — the consumer counterpart to handoff / handoff-fresh / wrap.
- Producer-agnostic detection with fixed precedence: fresh bundle → canonical root `HANDOFF.md` (bridge vs canonical via schema marker, heading fallback) → `FORGE-*` / CLAUDE.md resume pointers. Picks the freshest by embedded date then mtime; flags the rest historical.
- Skill-owned read-all + per-file read-receipt guarantee (the guarantee lives in the skill, not in the artifact text), so old/hand-written/trimmed handoffs still get strong behavior.
- Routes the high-traffic bare "read HANDOFF.md" path to `/pickup`.
- Verbatim-first resume: reads the `## Last Exchange (Verbatim)` section (canonical) or the verbatim last-turn block in `session-log-chunk.md` (bundle) before acting.
- Stakes-tiered verify-still-true gate: advisory by default; blocking when the artifact declares a `## Verify Block` or when high-stakes is detected deterministically (live/production system signals, or next action is a write/destructive op).
- 5-item resume contract output (resume target, freshness judgment, next actions, fallback path, blockers/drift + surfaced open decisions).
- Non-mutating by default; `--write-receipt` opt-in writes only `.pickup-receipt.md`.

### Reused
- Generalized `handoff-fresh/scripts/validate_read_gate.py` with `--required-list` and `--required-from-firststeps` so the deterministic receipt validator works on the canonical HANDOFF.md path, not just the bundle. A byte-identical copy lives at `pickup/scripts/validate_read_gate.py` (parity enforced by EVALUATIONS Scenario 11).

### Context
Built from a multi-agent evidence campaign: a session-log eval of real resumes (shallow-ingest and act-on-stale-state failures reproduced in production logs), the swarm-research-droid feedback report (producer/consumer asymmetry), the narrative-engine `narrative-handoff-resume` prior art (freshness-as-data), and the OKF / LLM-wiki ingestion patterns (index-first, progressive disclosure, freshness, backlinks).
