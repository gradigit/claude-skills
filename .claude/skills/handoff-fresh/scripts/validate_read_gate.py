#!/usr/bin/env python3
"""
Validate handoff-fresh read gate completion from read-receipt.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = ["handoff.md", "claude.md", "todo.md", "state.md", "context.md"]

LINE_PATTERN = re.compile(
    r"^\s*-\s*\[(?P<check>[xX ])\]\s*(?P<file>[A-Za-z0-9._-]+\.md)\s*(?:—|-)?\s*(?P<takeaway>.*)\s*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate handoff-fresh read-receipt.md completion."
    )
    parser.add_argument(
        "--bundle-dir",
        default=".handoff-fresh/current",
        help="Bundle directory containing read-receipt.md (default: .handoff-fresh/current)",
    )
    parser.add_argument(
        "--receipt",
        default=None,
        help="Explicit path to read-receipt.md (overrides --bundle-dir)",
    )
    return parser.parse_args()


def normalized_takeaway(text: str) -> str:
    return text.strip()


def takeaway_is_valid(text: str) -> bool:
    t = normalized_takeaway(text)
    if not t:
        return False
    if t in {"-", "—"}:
        return False
    if t.startswith("<") and t.endswith(">"):
        return False
    return True


def main() -> int:
    args = parse_args()

    receipt_path = (
        Path(args.receipt).expanduser().resolve()
        if args.receipt
        else (Path(args.bundle_dir).expanduser().resolve() / "read-receipt.md")
    )

    print("## Read Gate Preflight")
    print(f"Receipt: {receipt_path}")

    if not receipt_path.exists():
        print("Status: FAIL")
        print("- read-receipt.md not found.")
        print("- Use ask-question if required context is missing/ambiguous before coding.")
        return 1

    lines = receipt_path.read_text(encoding="utf-8").splitlines()
    found: dict[str, tuple[bool, str]] = {}

    for line in lines:
        match = LINE_PATTERN.match(line)
        if not match:
            continue
        filename = match.group("file").strip().lower()
        checked = match.group("check").lower() == "x"
        takeaway = match.group("takeaway")
        if filename in REQUIRED_FILES and filename not in found:
            found[filename] = (checked, takeaway)

    failures: list[str] = []

    for filename in REQUIRED_FILES:
        if filename not in found:
            failures.append(f"- [ ] {filename} entry is missing")
            continue

        checked, takeaway = found[filename]
        if not checked:
            failures.append(f"- [ ] {filename} is not checked")
        if not takeaway_is_valid(takeaway):
            failures.append(f"- [ ] {filename} takeaway is empty or placeholder")

    if failures:
        print("Status: FAIL")
        for item in failures:
            print(item)
        print("- Do not proceed to coding.")
        print("- Use ask-question if required context is missing/ambiguous.")
        return 1

    print("Status: PASS")
    for filename in REQUIRED_FILES:
        print(f"- [x] {filename} takeaway present")
    print("Ready to begin Workspace Preparation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
