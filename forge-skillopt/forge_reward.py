#!/usr/bin/env python3
"""
forge_reward — deterministic reward over a completed forge run's artifacts.

This is the gradable substrate for the SkillOpt pilot (M5). A SkillOpt rollout
replays one forge milestone under the candidate skill, then calls score_run() on
the resulting artifact tree to produce {hard, soft} for the optimizer.

Design (per the forge eval + adversarial review):
- Lean on `hard` (all-or-nothing, hard to game); `soft` is only a gradient shaper.
- Reuse the M2 completion guard's VERIFIED logic for the criteria signal — single
  source of truth, no divergent re-implementation (the guard already excludes the
  forge artifacts from its search, so naming a test isn't enough → anti-Goodhart).
- Every component is a deterministic parse of files the orchestrator already emits
  (FORGE-STATUS.md gates/state, the goal-reconciliation table, scope-guard log).

soft = weighted blend of:
    criteria_coverage   (# criteria with resolvable Code+Test) / (# criteria)
    gate_adherence      (# of GATE A–E reached) / 5
    1 - false_completion   (run claims complete but criteria lack evidence)
    1 - scope_violation    (out-of-scope writes / total writes, from scope log)
hard = 1 iff  every criterion verified  AND  no gate skipped  AND  scope_violations == 0
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

WEIGHTS = {"coverage": 0.40, "gates": 0.25, "not_false_completion": 0.20, "not_scope_violation": 0.15}
GATES = ["A", "B", "C", "D", "E"]


def _load_guard(repo_root: Path):
    """Import forge_completion_guard from the orchestrator hooks (single source)."""
    candidates = [
        repo_root / ".claude/hooks/forge_completion_guard.py",
        repo_root / ".claude/skills/forge-orchestrator/hooks/forge_completion_guard.py",
        Path(__file__).resolve().parents[1] / ".claude/skills/forge-orchestrator/hooks/forge_completion_guard.py",
    ]
    for c in candidates:
        if c.exists():
            spec = importlib.util.spec_from_file_location("forge_completion_guard", c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            return mod
    raise FileNotFoundError("forge_completion_guard.py not found (install guards first)")


def _coverage(guard, recon: Path, repo_root: Path) -> tuple[float, int, int]:
    """Fraction of criteria with resolvable Code + existing Test, via the guard."""
    if not recon.exists():
        return 0.0, 0, 0
    rows = guard.parse_rows(recon.read_text(encoding="utf-8"))
    if not rows:
        return 0.0, 0, 0
    ok = 0
    for r in rows:
        code, test, status = r.get("code", ""), r.get("test", ""), r.get("status", "")
        code_ok = not guard.is_placeholder(code) and guard.code_resolves(repo_root, code)
        test_ok = not guard.is_placeholder(test) and guard.test_exists(repo_root, test)
        status_ok = status.strip().strip("`").lower() in guard.VERIFIED
        if code_ok and test_ok and status_ok:
            ok += 1
    return ok / len(rows), ok, len(rows)


def _gate_adherence(run: Path, status_text: str) -> float:
    """Artifact-grounded gate proxy. The orchestrator does NOT serialize per-gate
    markers, so regexing 'GATE X reached' always returned 0. Instead, score the
    fraction of the pipeline's actual outputs that exist: research produced
    (RESEARCH/A), review-findings produced (REVIEW/C), a reconciliation table (GATE E),
    and a FINALIZED ledger (FINALIZATION). These are the durable artifacts a real run
    leaves behind."""
    def has_files(rel: str) -> bool:
        d = run / rel
        return d.is_dir() and any(p.suffix == ".md" for p in d.glob("*.md"))
    signals = [
        has_files("architect/research"),
        has_files("architect/review-findings"),
        any((run / "architect" / "review-findings").glob("*-goal-reconciliation.md")) if (run / "architect" / "review-findings").is_dir() else False,
        bool(re.search(r"state\s*:\s*finalized", status_text, re.IGNORECASE)),
    ]
    return sum(1 for s in signals if s) / len(signals)


def _claims_complete(status_text: str) -> bool:
    return bool(re.search(r"state\s*:\s*finalized|status\s*:\s*completed", status_text, re.IGNORECASE))


def _scope_violation_rate(run: Path) -> float:
    """From a scope-guard log if present (out-of-scope warnings / total writes)."""
    log = run / "architect" / "scope-guard.log"
    if not log.exists():
        return 0.0
    text = log.read_text(encoding="utf-8", errors="ignore")
    warns = len(re.findall(r"WARNING: Agent .* outside declared scope", text))
    writes = len(re.findall(r"\b(Edit|Write|apply_patch)\b", text)) or warns
    return (warns / writes) if writes else 0.0


def score_run(run_dir: str, milestone: str, repo_root: str | None = None) -> dict:
    run = Path(run_dir).expanduser().resolve()
    root = Path(repo_root).expanduser().resolve() if repo_root else run
    guard = _load_guard(root)

    recon = run / "architect" / "review-findings" / f"{milestone}-goal-reconciliation.md"
    status_file = run / "FORGE-STATUS.md"
    status_text = status_file.read_text(encoding="utf-8") if status_file.exists() else ""

    coverage, ok, total = _coverage(guard, recon, root)
    gates = _gate_adherence(run, status_text)
    scope_viol = _scope_violation_rate(run)
    claims = _claims_complete(status_text)

    # false completion = claims complete while not every criterion is verified
    false_completion = 1.0 if (claims and (total == 0 or ok < total)) else 0.0

    soft = (
        WEIGHTS["coverage"] * coverage
        + WEIGHTS["gates"] * gates
        + WEIGHTS["not_false_completion"] * (1.0 - false_completion)
        + WEIGHTS["not_scope_violation"] * (1.0 - scope_viol)
    )
    # hard = every criterion evidence-backed, no false completion, no scope violation.
    # (gate_adherence is a soft proxy only — it is NOT required for hard, because the
    # criteria-coverage check via the M2 guard is the real all-or-nothing signal.)
    hard = int(total > 0 and ok == total and false_completion == 0.0 and scope_viol == 0.0)

    return {
        "id": milestone,
        "hard": hard,
        "soft": round(soft, 4),
        "components": {
            "criteria_coverage": round(coverage, 4),
            "criteria_ok": ok,
            "criteria_total": total,
            "gate_adherence": round(gates, 4),
            "false_completion": false_completion,
            "scope_violation_rate": round(scope_viol, 4),
            "claims_complete": claims,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic forge run reward.")
    ap.add_argument("run_dir", help="completed forge run directory")
    ap.add_argument("milestone", help="milestone id (matches {milestone}-goal-reconciliation.md)")
    ap.add_argument("--repo-root", default=None, help="repo root for guard + evidence (default: run_dir)")
    args = ap.parse_args()
    print(json.dumps(score_run(args.run_dir, args.milestone, args.repo_root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
