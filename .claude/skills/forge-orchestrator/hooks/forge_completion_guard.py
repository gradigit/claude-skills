#!/usr/bin/env python3
"""
forge-completion-guard — deterministic GATE E enforcement (anti-false-completion).

The forge eval found GATE E (goal reconciliation) bypassed in ~88% of completed
runs because it lived only as prose. This checker makes it mechanical and
PLATFORM-AGNOSTIC: both Claude Code and Codex run it as a tool call before
writing a FINALIZED status or making a milestone-completion commit. On Codex
(no PreToolUse hooks) this is the primary enforcement; on Claude the
forge-completion-guard.sh PreToolUse hook also calls it as defense-in-depth.

It validates the reconciliation artifact
  architect/review-findings/{milestone}-goal-reconciliation.md
which must list every acceptance criterion with Code evidence (file:line that
exists) and Test evidence (a named test that exists in the repo), status verified.

Exit 0 = every criterion has real, resolvable evidence  -> completion allowed.
Exit 1 = missing artifact / unmet criteria / unresolvable evidence -> BLOCK.

Escape hatch (verifier-required, to avoid deadlocking a legitimately-complete run
on a parser edge case): pass --override "<reason>" or set FORGE_GATE_OVERRIDE=1.
The override is logged loudly and recorded; it never happens silently.

Reconciliation artifact format (see state-templates.md):

  | Criterion | Code | Test | Status |
  |-----------|------|------|--------|
  | refresh rotates token | src/auth/refresh.ts:40 | test_refresh_rotation | verified |
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

CODE_RE = re.compile(r"^(?P<path>[A-Za-z0-9._/\-]+?)(?::(?P<line>\d+))?$")
PLACEHOLDER = {"", "-", "—", "n/a", "na", "tbd", "todo", "pending", "{code}", "{test}", "..."}
VERIFIED = {"verified", "pass", "passed", "done", "complete", "✓", "x"}


def is_placeholder(s: str) -> bool:
    t = s.strip().strip("`").lower()
    return t in PLACEHOLDER or (t.startswith("{") and t.endswith("}")) or (t.startswith("<") and t.endswith(">"))


def parse_rows(text: str) -> list[dict]:
    """Parse the markdown table rows under a header containing Criterion|Code|Test."""
    rows: list[dict] = []
    header_idx = None
    cols: list[str] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if header_idx is None:
            if "criterion" in low and "code" in low and "test" in low:
                header_idx = low
                cols = low
            continue
        if set(line.replace("|", "").replace("-", "").replace(":", "").split()) == set():
            continue  # separator row ---|---
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = {cols[i]: cells[i] for i in range(min(len(cols), len(cells)))}
        if row.get("criterion"):
            rows.append(row)
    return rows


def _excluded(rel: str) -> bool:
    # Don't let a test name "exist" just because it's written in the forge
    # artifacts themselves (that would make the guard trivially Goodhart-able).
    rel = rel.replace("\\", "/")
    return (
        rel.startswith("architect/")
        or "/architect/" in rel
        or rel.endswith("-goal-reconciliation.md")
        or "review-findings/" in rel
        or rel.startswith("FORGE-")
    )


# A real test reference, not just any substring. The token must look like a test
# identifier AND appear either in a test-ish file or as an actual test definition —
# otherwise "export"/"return" trivially "exist" and defeat the anti-Goodhart intent.
_TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|[._-](test|spec)s?\.", re.IGNORECASE)
_TEST_DEF = re.compile(r"(\bdef\s+test|\bfunc\s+Test|\bit\(|\btest\(|\bdescribe\(|@Test|\bclass\s+\w*Test|\bTEST(_F|_P)?\()")
_COMMON_TOKENS = {
    "export", "return", "import", "const", "let", "var", "function", "func", "class",
    "def", "test", "tests", "it", "the", "true", "false", "public", "static", "void",
    "async", "await", "type", "value", "data", "main", "run", "name", "todo", "pass",
}


def _is_test_token(token: str) -> bool:
    t = token.strip("`\"'")
    return len(t) >= 4 and t.lower() not in _COMMON_TOKENS


def test_exists(repo_root: Path, test_name: str) -> bool:
    """Confirm the named test genuinely exists: the token is a plausible test
    identifier AND is found in a test-ish file OR as a test definition — NOT a bare
    substring in any source file, and NEVER in the forge artifacts (circular)."""
    name = test_name.strip().strip("`")
    if not name:
        return False
    token = re.split(r"[ (\[]", name)[0]  # strip args/desc
    if not _is_test_token(token):
        return False

    def _accept(path: str, content: str) -> bool:
        return not _excluded(path) and (_TEST_PATH.search(path) or bool(_TEST_DEF.search(content)))

    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "grep", "-n", "-F", token, "--", ":!architect/", ":!FORGE-*.md"],
            capture_output=True, text=True, timeout=20,
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                parts = line.split(":", 2)  # path:lineno:content
                if len(parts) == 3 and _accept(parts[0].strip(), parts[2]):
                    return True
            return False  # git grep ran and found no test-quality hit — trust it
    except Exception:
        pass
    # fallback only when git grep is unavailable: restrict to test-path files
    try:
        for p in repo_root.rglob("*"):
            if not p.is_file() or p.stat().st_size >= 2_000_000:
                continue
            rel = str(p.relative_to(repo_root))
            if _excluded(rel):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if token in content and (_TEST_PATH.search(rel) or _TEST_DEF.search(content)):
                return True
    except Exception:
        pass
    return False


def code_resolves(repo_root: Path, code: str) -> bool:
    m = CODE_RE.match(code.strip().strip("`"))
    if not m:
        return False
    path = repo_root / m.group("path")
    if not path.is_file():
        return False
    if m.group("line"):
        try:
            n = sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
            return 1 <= int(m.group("line")) <= n
        except Exception:
            return True
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic GATE E completion guard.")
    ap.add_argument("artifact", help="path to {milestone}-goal-reconciliation.md")
    ap.add_argument("--repo-root", default=".", help="repo root for evidence existence checks")
    ap.add_argument("--no-existence", action="store_true", help="skip file/test existence checks (structure only)")
    ap.add_argument("--override", default=None, help="escape hatch: proceed despite failure, with a logged reason")
    args = ap.parse_args()

    _env_override = os.environ.get("FORGE_GATE_OVERRIDE", "").strip().lower() in {"1", "true", "yes", "on"}
    override = args.override or ("FORGE_GATE_OVERRIDE" if _env_override else None)
    repo_root = Path(args.repo_root).expanduser().resolve()
    artifact = Path(args.artifact).expanduser()

    print("## Forge Completion Guard (GATE E)")
    print(f"Artifact: {artifact}")

    failures: list[str] = []
    if not artifact.exists():
        failures.append("- reconciliation artifact MISSING — GATE E was skipped (the #1 false-completion cause)")
    else:
        rows = parse_rows(artifact.read_text(encoding="utf-8"))
        if not rows:
            failures.append("- no acceptance-criterion rows found (expected a | Criterion | Code | Test | Status | table)")
        for r in rows:
            crit = r.get("criterion", "?")[:60]
            code, test, status = r.get("code", ""), r.get("test", ""), r.get("status", "")
            if is_placeholder(code):
                failures.append(f"- '{crit}': no Code evidence")
            elif not args.no_existence and not code_resolves(repo_root, code):
                failures.append(f"- '{crit}': Code '{code}' does not resolve to an existing file:line")
            if is_placeholder(test):
                failures.append(f"- '{crit}': no Test evidence")
            elif not args.no_existence and not test_exists(repo_root, test):
                failures.append(f"- '{crit}': Test '{test}' not found in repo (named but does not exist)")
            if status.strip().strip("`").lower() not in VERIFIED:
                failures.append(f"- '{crit}': status '{status}' is not verified")

    if failures:
        print("Status: FAIL")
        for f in failures:
            print(f)
        if override:
            print(f"\n!! OVERRIDE ENGAGED ({override}) — proceeding despite {len(failures)} unmet checks.")
            print("!! This is recorded. Completion is NOT evidence-backed; justify in FORGE-MEMORY.md.")
            return 0
        print("\nDo NOT mark the run/milestone complete. Build the unmet criteria, or re-run with")
        print('--override "<reason>" only if this is a genuine parser edge case.')
        return 1

    print("Status: PASS — every acceptance criterion has resolvable Code + Test evidence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
