#!/usr/bin/env python3
"""
check_no_skillopt_sleep — hard security precondition for the SkillOpt pilot.

SkillOpt's pyproject.toml packages BOTH `skillopt` (clean) and `skillopt_sleep`,
whose backend.py hardcodes internal Azure OpenAI endpoints + a managed-identity
client-id GUID. A plain `pip install -e .` of the SkillOpt repo therefore pulls
the leaky module into the environment. A grep over our own source CANNOT catch a
transitively-installed dependency, so the PRIMARY control is install-time:

  the pilot must vendor/install ONLY the `skillopt` subtree, such that
  `import skillopt_sleep` raises ImportError.

This script enforces that (primary) and keeps a secret grep as a secondary
tripwire. Run it in CI / pre-commit and before any optimization run. Exit 1 on
any failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

# Real secrets that must NEVER appear in our tree. (The `skillopt_sleep` module
# itself is handled by the PRIMARY import check — its name legitimately appears in
# docs that explain avoiding it, so it is not a grep marker.)
LEAK_MARKERS = [
    "8cafa2b1-a2a7-4ad9-814a-ffe4aed7e800",  # managed-identity client-id GUID
    "cognitiveservices.azure.com",
    "openai.azure.com",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert skillopt_sleep is absent from env + tree.")
    ap.add_argument("--tree", default=".", help="source tree to grep as a secondary tripwire")
    args = ap.parse_args()

    failures: list[str] = []

    # PRIMARY (hard) control: the leaky module must not be importable.
    if importlib.util.find_spec("skillopt_sleep") is not None:
        failures.append(
            "- PRIMARY: `import skillopt_sleep` resolves — it is on sys.path / installed. "
            "Install ONLY the `skillopt` subtree (do NOT `pip install -e .` the whole SkillOpt repo)."
        )

    # SECONDARY tripwire: no leaked secrets/endpoints checked into our tree.
    tree = Path(args.tree).resolve()
    for marker in LEAK_MARKERS:
        try:
            r = subprocess.run(
                ["git", "-C", str(tree), "grep", "-l", "-F", marker],
                capture_output=True, text=True, timeout=20,
            )
            hits = [h for h in r.stdout.splitlines() if h.strip() and "check_no_skillopt_sleep" not in h]
            if hits:
                failures.append(f"- SECONDARY: marker '{marker}' found in: {', '.join(hits)}")
        except Exception:
            # fall back to filesystem scan
            for p in tree.rglob("*"):
                if p.is_file() and p.name != "check_no_skillopt_sleep.py" and p.stat().st_size < 2_000_000:
                    try:
                        if marker in p.read_text(encoding="utf-8", errors="ignore"):
                            failures.append(f"- SECONDARY: marker '{marker}' found in {p}")
                            break
                    except Exception:
                        continue

    print("## SkillOpt secret-isolation check")
    if failures:
        print("Status: FAIL")
        print("\n".join(failures))
        print("\nDo NOT run the SkillOpt pilot until skillopt_sleep is absent from the environment.")
        return 1
    print("Status: PASS — skillopt_sleep not importable; no leaked endpoints/GUID in tree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
