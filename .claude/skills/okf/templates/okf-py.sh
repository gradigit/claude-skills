#!/bin/sh
# okf runner — copied to .okf/okf-py.sh at bootstrap and TRACKED. Every hook (Claude, Codex, git)
# goes through here so the interpreter policy lives in one place:
#  * resolves the repo root itself, so hooks work when the session was launched in a subdirectory
#    or moved with /cd (a cwd-relative guard silently disabled every hook in 1.2.x);
#  * prefers uv only when it can find a system Python 3 WITHOUT reading the repo's .python-version
#    or uv.toml and WITHOUT downloading (a repo-shipped .python-version made `uv run` exit 2, which
#    a Stop hook reads as BLOCK) — otherwise bare python3;
#  * a Stop hook that cannot run must still print '{}' (Codex requires JSON on allow).
# Trust note: .okf/ is repo-controlled code that runs on every edit, stop and commit — review it
# like husky/ or CI config.
R="$(git rev-parse --show-toplevel 2>/dev/null || printf %s "${CLAUDE_PROJECT_DIR:-.}")"
if [ ! -f "$R/.okf/lint.py" ]; then [ "$1" = stop-gate ] && echo '{}'; exit 0; fi
cd "$R" || exit 0
if command -v uv >/dev/null 2>&1 && UV_PYTHON_DOWNLOADS=never uv python find 3 >/dev/null 2>&1; then
  UV_PYTHON_DOWNLOADS=never exec uv run --no-project --no-config --python 3 python3 .okf/lint.py "$@"
fi
if ! command -v python3 >/dev/null 2>&1; then [ "$1" = stop-gate ] && echo '{}'; exit 0; fi
exec python3 .okf/lint.py "$@"
