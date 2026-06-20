#!/usr/bin/env python3
"""
forge-spawn-breaker — make the circuit breakers behavioral, not just documented.

The forge eval found the 50-spawn / 10-milestone limits were never enforced or
narrated (5/98 runs exceeded 50 spawns, max 118). This checker reads the live
counters the orchestrator persists in FORGE-STATUS.md frontmatter and decides
whether another spawn / milestone is allowed. The orchestrator runs it before
each spawn batch and before starting a new milestone.

FORGE-STATUS.md frontmatter must carry:
    spawns: <int>        # cumulative spawn_agent / sub-agent count this run
    milestones: <int>    # milestones started this run

Exit 0 = under limits (allowed). Exit 1 = at/over a limit -> STOP: save state,
summarize, ask the user to continue or stop (do not silently blow past).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEF_MAX_SPAWNS = 50
DEF_MAX_MILESTONES = 10


def read_counter(text: str, key: str) -> int:
    m = re.search(rf"^{key}\s*:\s*(\d+)\s*$", text, re.MULTILINE)
    return int(m.group(1)) if m else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Forge spawn/milestone circuit breaker.")
    ap.add_argument("status_file", nargs="?", default="FORGE-STATUS.md")
    ap.add_argument("--max-spawns", type=int, default=DEF_MAX_SPAWNS)
    ap.add_argument("--max-milestones", type=int, default=DEF_MAX_MILESTONES)
    ap.add_argument("--check", choices=["spawn", "milestone", "both"], default="both")
    args = ap.parse_args()

    path = Path(args.status_file).expanduser()
    print("## Forge Spawn Breaker")
    if not path.exists():
        print(f"Status: PASS (no {path} yet — counters start at 0)")
        return 0

    text = path.read_text(encoding="utf-8")
    spawns = read_counter(text, "spawns")
    milestones = read_counter(text, "milestones")
    print(f"spawns={spawns}/{args.max_spawns}  milestones={milestones}/{args.max_milestones}")

    tripped = []
    if args.check in ("spawn", "both") and spawns >= args.max_spawns:
        tripped.append(f"spawn limit reached ({spawns} >= {args.max_spawns})")
    if args.check in ("milestone", "both") and milestones >= args.max_milestones:
        tripped.append(f"milestone limit reached ({milestones} >= {args.max_milestones})")

    if tripped:
        print("Status: STOP")
        for t in tripped:
            print(f"- {t}")
        print("- Save state (FORGE-STATUS/HANDOFF), write a summary, and ask the user to continue or stop.")
        print("- Do NOT keep spawning past the breaker.")
        return 1

    print("Status: PASS (under limits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
