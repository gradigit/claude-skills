#!/usr/bin/env python3
"""
measure_noise — the M5 numeric gate that MUST pass before any optimization (M6).

A reward parsed from multi-agent orchestration artifacts is structurally noisier
than an in-process cell comparison. Optimizing against a noisy reward is worse than
not optimizing (the optimizer chases noise / reward-hacks). So before M6 we replay
the SAME milestone N times under the SAME skill and require the reward to be
low-variance: per-milestone soft-score std-dev below a threshold AND consistent
`hard`. If this gate fails, fix the parseable-state emission (M2/M4) — do not
optimize.

Input: a replay root containing subdirs named "<milestone>__run<k>/" (each a
completed forge run). Or a JSON manifest: {"<milestone>": ["run_dir1", ...]}.

Exit 0 = low-noise (safe to proceed to M6).  Exit 1 = too noisy (do NOT optimize).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import forge_reward


def discover(replay_root: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for d in sorted(replay_root.iterdir()):
        if not d.is_dir():
            continue
        m = re.match(r"(?P<ms>.+?)__run\d+$", d.name)
        if m:
            groups.setdefault(m.group("ms"), []).append(d)
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description="Reward noise gate (run before optimizing).")
    ap.add_argument("replay_root", help="dir of <milestone>__run<k>/ run dirs (or use --manifest)")
    ap.add_argument("--manifest", default=None, help="JSON {milestone: [run_dir,...]} (overrides discovery)")
    ap.add_argument("--max-std", type=float, default=0.10, help="max allowed per-milestone soft std-dev")
    ap.add_argument("--min-replays", type=int, default=3, help="min replays per milestone to judge")
    args = ap.parse_args()

    root = Path(args.replay_root).expanduser().resolve()
    if args.manifest:
        groups = {k: [Path(p) for p in v] for k, v in json.loads(Path(args.manifest).read_text()).items()}
    else:
        groups = discover(root)

    if not groups:
        print(f"Status: FAIL\n- no '<milestone>__run<k>/' replay dirs found in {root}")
        return 1

    print("## Reward Noise Gate")
    worst = 0.0
    failures: list[str] = []
    any_hard = False
    for ms, runs in sorted(groups.items()):
        softs, hards = [], []
        for run in runs:
            try:
                r = forge_reward.score_run(str(run), ms, repo_root=str(run))
                softs.append(r["soft"])
                hards.append(r["hard"])
                any_hard = any_hard or r["hard"] == 1
            except Exception as e:
                failures.append(f"- {ms}: scoring {run.name} failed: {e}")
        if len(softs) < args.min_replays:
            failures.append(f"- {ms}: only {len(softs)} replays (< {args.min_replays})")
            continue
        std = statistics.pstdev(softs)
        worst = max(worst, std)
        hard_consistent = len(set(hards)) == 1
        flag = "" if (std <= args.max_std and hard_consistent) else "  <-- TOO NOISY"
        print(f"- {ms}: n={len(softs)} soft_mean={statistics.mean(softs):.3f} soft_std={std:.3f} hard={set(hards)}{flag}")
        if std > args.max_std:
            failures.append(f"- {ms}: soft std {std:.3f} > max {args.max_std}")
        if not hard_consistent:
            failures.append(f"- {ms}: hard inconsistent across replays {hards}")

    print(f"\nworst soft_std = {worst:.3f} (threshold {args.max_std})")
    if not any_hard:
        failures.append("- no replay EVER achieved hard==1 — the reward never rewards success "
                        "(mis-specified or no genuinely-complete milestone in the set); optimizing against it is meaningless")
    if failures:
        print("Status: FAIL — reward not safe to optimize against.")
        print("\n".join(failures))
        print("Fix the parseable-state emission (M2 reconciliation / M4 validate) before M6.")
        return 1
    print("Status: PASS — reward is low-variance and rewards success; safe to proceed to the M6 optimization run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
