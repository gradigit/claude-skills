#!/usr/bin/env python3
"""
OKF-lite emitter/validator for handoff-fresh bundles.

Adopts a lightweight subset of Google's Open Knowledge Format (OKF) — per-file
YAML frontmatter with a required `type` key, plus a bundle-root `index.md` that
carries `okf_version`. Deliberately does NOT depend on the upstream `okf` package
and does NOT enforce its stricter 4-key requirement (the OKF spec requires only
`type`; consumers must tolerate unknown keys).

Usage:
  okf_bundle.py stamp <file.md> --type handoff --role state [--timestamp <iso>]
  okf_bundle.py validate <bundle-dir>

Uses PyYAML if available; falls back to a minimal flat-key parser otherwise.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore

    def _loads(s: str) -> dict:
        data = yaml.safe_load(s) or {}
        return data if isinstance(data, dict) else {}

    def _dumps(d: dict) -> str:
        return yaml.safe_dump(d, sort_keys=False, default_flow_style=False).strip()

except ModuleNotFoundError:  # minimal flat key: value fallback

    def _loads(s: str) -> dict:
        out: dict = {}
        for line in s.splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition(":")
                out[k.strip()] = v.strip().strip("'\"")
        return out

    def _dumps(d: dict) -> str:
        return "\n".join(f"{k}: {v}" for k, v in d.items())


def split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            return _loads(fm), body
    return {}, text


def stamp(args: argparse.Namespace) -> int:
    path = Path(args.file)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    meta, body = split_frontmatter(text)
    meta["type"] = args.type
    if args.role:
        meta["handoff_role"] = args.role
    meta["timestamp"] = args.timestamp or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    if args.okf_version:
        meta["okf_version"] = args.okf_version
    path.write_text(f"---\n{_dumps(meta)}\n---\n\n{body}".rstrip() + "\n", encoding="utf-8")
    print(f"stamped {path} (type={meta['type']}, role={meta.get('handoff_role','-')})")
    return 0


def validate(args: argparse.Namespace) -> int:
    bundle = Path(args.bundle_dir)
    if not bundle.is_dir():
        print(f"Status: FAIL\n- bundle dir not found: {bundle}")
        return 1
    failures: list[str] = []
    md_files = sorted(bundle.glob("*.md"))
    if not md_files:
        print(f"Status: FAIL\n- no .md files in {bundle}")
        return 1
    for f in md_files:
        meta, _ = split_frontmatter(f.read_text(encoding="utf-8"))
        if not meta.get("type"):
            failures.append(f"- {f.name}: missing required `type` frontmatter key")
        if not meta.get("timestamp"):
            failures.append(f"- {f.name}: missing `timestamp`")
    index = bundle / "index.md"
    if not index.exists():
        failures.append("- index.md missing (OKF bundle index)")
    else:
        meta, _ = split_frontmatter(index.read_text(encoding="utf-8"))
        if not meta.get("okf_version"):
            failures.append("- index.md missing `okf_version` (pin OKF draft version)")

    if failures:
        print("Status: FAIL")
        print("\n".join(failures))
        return 1
    print(f"Status: PASS\n- {len(md_files)} files carry OKF `type`+`timestamp`; index.md has okf_version")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OKF-lite emitter/validator for handoff bundles.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stamp", help="Add/update OKF frontmatter on a file")
    s.add_argument("file")
    s.add_argument("--type", default="handoff")
    s.add_argument("--role", default=None)
    s.add_argument("--timestamp", default=None)
    s.add_argument("--okf-version", dest="okf_version", default=None)
    s.set_defaults(func=stamp)

    v = sub.add_parser("validate", help="Validate OKF-lite conformance of a bundle dir")
    v.add_argument("bundle_dir")
    v.set_defaults(func=validate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
