#!/usr/bin/env python3
"""
Validate a read gate from a read-receipt file.

Two consumers share this validator:
  * handoff-fresh — the fixed 5-file bundle Read Gate (default behavior).
  * pickup        — an arbitrary required-read list derived from a canonical
                    HANDOFF.md "First Steps" section, or passed explicitly.

Back-compat: with no new flags the behavior is identical to the original
handoff-fresh validator (REQUIRED_FILES bundle default, .md LINE_PATTERN,
takeaway_is_valid rules, exit 0 PASS / 1 FAIL).

NOTE: this file is mirrored at pickup/scripts/validate_read_gate.py. The two
copies must stay byte-identical on REQUIRED_FILES, LINE_PATTERN, LINE_PATTERN_ANY,
and takeaway_is_valid (see EVALUATIONS.md "validator parity" scenario).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = ["handoff.md", "claude.md", "todo.md", "state.md", "context.md"]

# Original (unchanged) pattern — .md receipts. Matched first for back-compat.
LINE_PATTERN = re.compile(
    r"^\s*-\s*\[(?P<check>[xX ])\]\s*(?P<file>[A-Za-z0-9._-]+\.md)\s*(?:—|-)?\s*(?P<takeaway>.*)\s*$"
)

# Common extensionless files that legitimately appear in a read list.
_EXTLESS = r"Dockerfile|Makefile|LICENSE|CHANGELOG|README|Procfile|Gemfile|Rakefile|Justfile|Caddyfile"

# Broader fallback — receipts for non-.md First Steps files (e.g. src/x.ts) and
# the known extensionless files above. Captures a path-like token; basename is compared.
LINE_PATTERN_ANY = re.compile(
    r"^\s*-\s*\[(?P<check>[xX ])\]\s*[`'\"]?(?P<file>(?:[A-Za-z0-9._/-]+\.[A-Za-z0-9]+)|(?:"
    + _EXTLESS
    + r"))[`'\"]?\s*(?:—|-)?\s*(?P<takeaway>.*)\s*$",
    re.IGNORECASE,
)

# "First Steps (Read in Order)" / "READ FIRST (in order)" numbered list lines.
FIRSTSTEPS_HEADING = re.compile(r"^#{1,6}\s*(first steps|read first)\b", re.IGNORECASE)
FIRSTSTEPS_ITEM = re.compile(
    r"^\s*\d+\.\s*(?:read\s+)?[`'\"]?(?P<file>(?:[A-Za-z0-9._/-]+\.[A-Za-z0-9]+)|(?:"
    + _EXTLESS
    + r"))",
    re.IGNORECASE,
)
HEADING = re.compile(r"^#{1,6}\s+\S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a read-receipt against a required-read list."
    )
    parser.add_argument(
        "--bundle-dir",
        default=".handoff-fresh/current",
        help="Bundle directory containing read-receipt.md (default: .handoff-fresh/current)",
    )
    parser.add_argument(
        "--receipt",
        default=None,
        help="Explicit path to the read-receipt file (overrides --bundle-dir)",
    )
    parser.add_argument(
        "--required-list",
        default=None,
        help="Comma-separated required filenames (basenames), overriding the bundle default",
    )
    parser.add_argument(
        "--required-from-firststeps",
        default=None,
        help="Path to a HANDOFF.md; derive the required list from its 'First Steps' numbered section",
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


def derive_required_from_firststeps(handoff_path: Path) -> list[str]:
    """Parse the numbered First Steps list and return required basenames (lowercased).

    A long-lived HANDOFF.md can contain multiple First-Steps eras. The NEWEST block
    wins (matches pickup SKILL.md Step 2): each First-Steps heading resets the
    collected list, and any other heading closes the current block, so what remains
    is the items of the last First-Steps block.
    """
    if not handoff_path.exists():
        return []
    required: list[str] = []
    seen: set[str] = set()
    in_section = False
    for line in handoff_path.read_text(encoding="utf-8").splitlines():
        if FIRSTSTEPS_HEADING.match(line):
            in_section = True
            required = []  # reset — newer block supersedes any earlier one
            seen = set()
            continue
        if HEADING.match(line):  # any other heading closes the current block
            in_section = False
            continue
        if in_section:
            m = FIRSTSTEPS_ITEM.match(line)
            if m:
                base = Path(m.group("file")).name.lower()
                if base not in seen:
                    seen.add(base)
                    required.append(base)
    return required


def resolve_required(args: argparse.Namespace) -> list[str]:
    if args.required_list:
        return [p.strip().lower() for p in args.required_list.split(",") if p.strip()]
    if args.required_from_firststeps:
        derived = derive_required_from_firststeps(
            Path(args.required_from_firststeps).expanduser().resolve()
        )
        return derived
    return list(REQUIRED_FILES)


def main() -> int:
    args = parse_args()

    receipt_path = (
        Path(args.receipt).expanduser().resolve()
        if args.receipt
        else (Path(args.bundle_dir).expanduser().resolve() / "read-receipt.md")
    )

    required = resolve_required(args)

    print("## Read Gate Preflight")
    print(f"Receipt: {receipt_path}")
    print(f"Required ({len(required)}): {', '.join(required) if required else '(none)'}")

    if args.required_from_firststeps and not required:
        print("Status: FAIL")
        print("- Could not derive a First Steps list from the handoff file.")
        print("- Confirm the handoff has a 'First Steps (Read in Order)' numbered section.")
        return 1

    if not receipt_path.exists():
        print("Status: FAIL")
        print("- read-receipt file not found.")
        print("- Use ask-question if required context is missing/ambiguous before proceeding.")
        return 1

    lines = receipt_path.read_text(encoding="utf-8").splitlines()
    found: dict[str, tuple[bool, str]] = {}

    for line in lines:
        match = LINE_PATTERN.match(line) or LINE_PATTERN_ANY.match(line)
        if not match:
            continue
        filename = Path(match.group("file").strip()).name.lower()
        checked = match.group("check").lower() == "x"
        takeaway = match.group("takeaway")
        if filename in required and filename not in found:
            found[filename] = (checked, takeaway)

    failures: list[str] = []

    for filename in required:
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
        print("- Do not proceed.")
        print("- Use ask-question if required context is missing/ambiguous.")
        return 1

    print("Status: PASS")
    for filename in required:
        print(f"- [x] {filename} takeaway present")
    print("Read gate complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
