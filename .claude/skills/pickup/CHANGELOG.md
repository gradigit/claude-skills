# Changelog

All notable changes to the pickup skill.

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
