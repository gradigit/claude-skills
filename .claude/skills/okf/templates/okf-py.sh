#!/bin/sh
# okf runner — copied to .okf/okf-py.sh at bootstrap and TRACKED. Every hook (Claude, Codex, git)
# goes through here so the interpreter policy lives in one place:
#  * the repo root is the directory that CONTAINS this script (…/.okf/..), never the caller's current
#    directory: Claude Code runs hooks in the current directory, which follows the agent's `cd`, so a
#    cwd-derived root could run a nested repo's .okf/ code (2026-11 review); git hooks call it as
#    `sh .okf/okf-py.sh` from the repo root, which resolves the same way;
#  * prefers uv only when it can find a system Python 3 WITHOUT reading the repo's .python-version
#    or uv.toml and WITHOUT downloading (a repo-shipped .python-version made `uv run` exit 2, which
#    a Stop hook reads as BLOCK) — otherwise bare python3;
#  * a Stop hook that cannot run must still print '{}' (Codex requires JSON on allow).
# Trust note: .okf/ is repo-controlled code that runs on every edit, stop and commit — review it
# like husky/ or CI config.
R="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd -P)"
if [ -z "$R" ] || [ ! -f "$R/.okf/lint.py" ]; then [ "$1" = stop-gate ] && echo '{}'; exit 0; fi
cd "$R" || exit 0
if command -v uv >/dev/null 2>&1 && UV_PYTHON_DOWNLOADS=never uv python find 3 >/dev/null 2>&1; then
  UV_PYTHON_DOWNLOADS=never exec uv run --no-project --no-config --python 3 python3 .okf/lint.py "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then [ "$1" = stop-gate ] && echo '{}'; exit 0; fi
exec python3 .okf/lint.py "$@"
