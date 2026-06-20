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
  okf_bundle.py validate <bundle-dir> [--recursive]
  okf_bundle.py freshness <bundle-dir> [--recursive] [--strict]
  okf_bundle.py index <bundle-dir> [--okf-version 0.1]

Uses PyYAML if available; falls back to a minimal flat-key parser otherwise.

Shared by handoff-fresh and forge-orchestrator. All extensions are ADDITIVE: the
default `validate <dir>` behavior (non-recursive, type+timestamp on each file,
index.md needs okf_version) is unchanged so handoff-fresh keeps passing.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reserved structural files: index.md carries okf_version (not type/timestamp);
# log.md is the append-only history. Both are exempt from the type+timestamp rule
# (OKF spec §3.1/§7 — they are bundle structure, not knowledge documents).
RESERVED = {"index.md", "log.md"}

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


def _md_files(bundle: Path, recursive: bool) -> list[Path]:
    files = bundle.rglob("*.md") if recursive else bundle.glob("*.md")
    return sorted(p for p in files if "__pycache__" not in p.parts)


def validate(args: argparse.Namespace) -> int:
    bundle = Path(args.bundle_dir)
    if not bundle.is_dir():
        print(f"Status: FAIL\n- bundle dir not found: {bundle}")
        return 1
    failures: list[str] = []
    md_files = _md_files(bundle, getattr(args, "recursive", False))
    if not md_files:
        print(f"Status: FAIL\n- no .md files in {bundle}")
        return 1
    for f in md_files:
        if f.name in RESERVED:
            continue  # reserved structural files exempt from type+timestamp
        meta, _ = split_frontmatter(f.read_text(encoding="utf-8"))
        rel = f.relative_to(bundle)
        if not meta.get("type"):
            failures.append(f"- {rel}: missing required `type` frontmatter key")
        if not meta.get("timestamp"):
            failures.append(f"- {rel}: missing `timestamp`")
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
    scope = "recursively" if getattr(args, "recursive", False) else ""
    print(f"Status: PASS\n- {len(md_files)} files {scope} carry OKF `type`+`timestamp` (reserved exempt); index.md has okf_version")
    return 0


def _head_commit_iso(bundle: Path) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(bundle), "log", "-1", "--format=%cI"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def freshness(args: argparse.Namespace) -> int:
    """Flag artifacts whose stamped timestamp predates the repo's current state.

    Deterministic staleness signal that replaces the vague 'bundle older than
    source' mtime heuristic. Uses git HEAD commit time when available; degrades
    gracefully (file mtime) outside a git repo. Advisory (exit 0) unless --strict.
    """
    bundle = Path(args.bundle_dir)
    if not bundle.is_dir():
        print(f"Status: FAIL\n- dir not found: {bundle}")
        return 1
    head_iso = _head_commit_iso(bundle)
    ref = head_iso
    basis = "git HEAD commit time"
    if not head_iso:
        basis = "git unavailable — using directory mtime"
        ref = datetime.fromtimestamp(bundle.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"## OKF Freshness\nReference ({basis}): {ref}")
    stale: list[str] = []
    for f in _md_files(bundle, getattr(args, "recursive", False)):
        if f.name in RESERVED:
            continue
        meta, _ = split_frontmatter(f.read_text(encoding="utf-8"))
        ts = str(meta.get("timestamp", "")).strip()
        if not ts:
            continue
        if ref and ts < ref:
            stale.append(f"- {f.relative_to(bundle)}: stamped {ts} < reference {ref}")
    if stale:
        print(f"Status: STALE ({len(stale)})")
        print("\n".join(stale))
        print("- Re-stamp / regenerate these or treat them as historical.")
        return 1 if getattr(args, "strict", False) else 0
    print("Status: FRESH — all stamped artifacts at or after the reference.")
    return 0


def index(args: argparse.Namespace) -> int:
    """Generate/refresh a skeleton index.md (read-order + typed file listing).

    The orchestrator may overwrite the body with richer navigation; this provides
    a conformant base carrying okf_version.
    """
    bundle = Path(args.bundle_dir)
    if not bundle.is_dir():
        print(f"Status: FAIL\n- dir not found: {bundle}")
        return 1
    lines = ["# Bundle Index", "", "Files (type — path):"]
    for f in _md_files(bundle, getattr(args, "recursive", True)):
        if f.name == "index.md":
            continue
        meta, _ = split_frontmatter(f.read_text(encoding="utf-8"))
        lines.append(f"- {meta.get('type', '?')} — {f.relative_to(bundle)}")
    meta = {
        "type": "index",
        "okf_version": args.okf_version,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "handoff_role": "index",
    }
    (bundle / "index.md").write_text(f"---\n{_dumps(meta)}\n---\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {bundle / 'index.md'} (okf_version={args.okf_version})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OKF-lite emitter/validator for handoff + forge bundles.")
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
    v.add_argument("--recursive", action="store_true", help="validate nested dirs too (e.g. architect/**)")
    v.set_defaults(func=validate)

    fr = sub.add_parser("freshness", help="Flag artifacts stamped before the repo's current state")
    fr.add_argument("bundle_dir")
    fr.add_argument("--recursive", action="store_true")
    fr.add_argument("--strict", action="store_true", help="exit 1 on stale (default advisory exit 0)")
    fr.set_defaults(func=freshness)

    ix = sub.add_parser("index", help="Generate/refresh a skeleton index.md")
    ix.add_argument("bundle_dir")
    ix.add_argument("--okf-version", dest="okf_version", default="0.1")
    ix.add_argument("--recursive", action="store_true", default=True)
    ix.set_defaults(func=index)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
