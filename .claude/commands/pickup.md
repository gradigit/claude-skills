# /pickup

Run the `pickup` skill as an explicit manual command — the consumer counterpart
to `/handoff`, `/handoff-fresh`, and `/wrap`.

## Contract
- Trigger from explicit user invocation (`/pickup`) or the bare "read HANDOFF.md" path
- Producer-agnostic: detect whichever artifact exists, in precedence order:
  1. fresh bundle `.handoff-fresh/current/handoff.md`
  2. canonical root `HANDOFF.md` (bridge → bundle, else canonical via First Steps)
  3. `FORGE-*` set / CLAUDE.md resume pointers (fallback)
  Pick the freshest by embedded date then mtime; flag the rest historical.
- Read ALL required files before the first substantive reply; first reply is the
  per-file read receipt (`- [x] <file> — <takeaway>`). No interim one-file summary.
- Validate the receipt deterministically with `scripts/validate_read_gate.py`
  (`--bundle-dir` for the bundle, `--required-from-firststeps` for the canonical path)
- Read the verbatim `## Last Exchange` FIRST and use it as the exact resume anchor
- Run the stakes-tiered verify-still-true gate: advisory by default; BLOCKING when
  the artifact declares a `## Verify Block` or when high-stakes is detected
  (live/production system signals, or next action is a write/destructive op)
- Surface the handoff's open decisions; use ask-question only if genuinely blocked
- Output the 5-item resume contract (resume target, freshness, next actions,
  fallback path, blockers/drift)
- Non-mutating by default; `--write-receipt` opt-in writes only `.pickup-receipt.md`

## Arguments
- `--write-receipt`: persist the read receipt to `.pickup-receipt.md`
- `--stakes <auto|low|high>`: override verify-gate stakes detection (default auto)
- `--artifact <path>`: skip detection and pick up from an explicit artifact
