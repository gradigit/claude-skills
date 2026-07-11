# Changelog — okf skill

## 1.2.3 (2026-07-11)

Day-3 refinements from two production repos:

- **Hooks use `uv run --no-project python3`**: plain `uv run` in a repo with a
  pyproject creates/syncs the project venv on every hook and pre-commit fire
  (observed live in a production repo — the commit hook created a `.venv`). The
  lint is stdlib-only; `--no-project` removes the side effect.
- **`.okf/log.lock` added to the bootstrap gitignore list** (upstreamed from a
  production repo) — per-clone hook lock, same class as `last-update.json`.
- Lint message: "untracked file(s)" → "untracked path(s)" (git porcelain reports
  an untracked directory as one path, so "file" undercounted).

## 1.2.2 (2026-07-09)

First-day-of-real-use fixes (found by the first live production bootstrap —
both issues surfaced within hours of actual work):

- **uv-aware hooks (upstreamed from a production repo's decisions log):** environments that
  PATH-shim bare `python3` to exit 1 inside agent sessions (e.g. the
  trailofbits/modern-python Claude plugin) made stock git hooks BLOCK every
  Claude-side commit and silently neutered the Stop gate (shim exits 1; Stop only
  blocks on 2). `templates/githooks/pre-commit` and the PostToolUse/Stop commands
  in `templates/hooks-settings.json` now prefer `uv run python3` when uv exists
  and fall back to bare `python3`. Command strings match the production repo's adapted
  install verbatim, so `install-hooks` dedup stays idempotent on re-runs.
- **Junk-file false positive:** gitignoring `.DS_Store` made the
  ignored-files-inside-wiki check report a hard ERROR (and the untracked-files
  warning count Finder droppings). OS/tooling junk (`.DS_Store`, `Thumbs.db`,
  `desktop.ini`, `__pycache__`, `*.pyc`) is now excluded from both checks —
  ignoring junk is desirable, not knowledge loss. (Root-level `.DS_Store` also
  tripped the Stop gate as an "uncommitted code change"; gitignoring it — now
  false-positive-free — is the documented remedy.)

Fixes from the LIVE A/B test (3 real repos cloned; Sonnet executor ran SKILL.md
unattended; verdicts: all three detection states executed with zero data damage,
high fidelity, B+/A−/A− wiki quality; blinded probes showed NO navigation speedup —
the one clean comparison was a 6/6 tie with MORE tool calls on the bootstrapped
clone):

- **P0-1: global/system `core.hooksPath` branch added to git-hook routing** (hit in
  2 of 3 real repos — the literal instruction would have silently disabled the
  user's secret-scanner + git-lfs; only executor judgment avoided it). Routing now
  checks global/system first and chains via the framework's documented chain point,
  with verification, or falls back to CI loudly. Pre-commit template header made
  wiring-agnostic.
- **P0-2: evidence durability** — pages citing PRE-EXISTING untracked files must
  copy them (never move) into tracked `wiki/raw/` or get them tracked; "capture-
  then-synthesize" now distinguishes newly-fetched from already-in-repo material.
- P1: detection state 3 covers substantial pre-OKF knowledge dirs under any name
  (`architect/`, `research/`, ...); step 6 explicitly routes knowledge-shaped
  CLAUDE.md content to the wiki (invariant 2 outranks absorption); CI-backstop
  intent clarified (matters MOST where hooks couldn't install); unattended-run
  "self-arbitrate + DECISIONS.md" mode named (and DECISIONS.md must be tracked or
  deleted — untracked root files pin noop-check to STALE).
- P2: log.md = event log, not page catalog; index entries reuse page descriptions
  (progressive disclosure); `_plan.md` skippable only for ≤3-file migrations with a
  logged skip; concept-gate has an offline path (reference.md suffices); step-8
  "FIRST" disambiguated.

## 1.2.0 (2026-07-08)

Consolidated fixes from the FRESH re-review panel (byte-identical cold prompts vs
v1.0). Panel verdicts on v1.1.1: cold Opus review flipped **no-ship → SHIP** (0
CRITICAL); Codex gpt-5.5 xhigh: ship-with-fixes (2 process-level P0s, none of the
v1.0 silent-corruption class); requirements audit: all 3 hard requirements + all 9
locked decisions PASS; framing honesty: MOSTLY-HONEST → fixed. Regression suite: 55
assertions.

- **State is now per-clone, deliberately untracked** (`.okf/last-update.json`
  gitignored at bootstrap): fixes the dirty-repo-after-stamp ordering P0 AND the
  round-1 worktree/collaborator churn concern in one policy. Bootstrap/update flows
  reordered: log entry → commit → stamp.
- **Scripted settings merge**: new `install-hooks <fragment.json>` subcommand
  deep-merges only `hooks.*` into `.claude/settings.json` (idempotent, backs up,
  refuses invalid JSON, preserves sibling keys). SKILL.md no longer narrates a
  hand-edit of a high-blast-radius file.
- **Git-hook install routing**: native `.git/hooks/` entries present → install into
  `.git/hooks/pre-commit` directly (never set core.hooksPath over native pre-push/
  commit-msg hooks); clean repos → core.hooksPath. Clone-locality stated honestly
  everywhere ("fires in clones that ran /okf once; CI is the clone-surviving backstop").
- **noop-check classification parity**: uses the same NON_KNOWLEDGE exclusions as
  stop-gate/pre-commit — plumbing-only diffs (.gitignore, AGENTS.md, .claude/) no
  longer report spurious STALE.
- **Lite profile marker** (`"profile": "lite"` in config.json): detection and
  noop-check now distinguish lite from full instead of demanding update passes on
  deliberately page-less wikis.
- **Configured wikiDir is authoritative**: missing/invalid config errors loudly
  instead of silently falling back to candidate dirs (monorepo wrong-wiki guard).
- **Pre-commit graph pass**: staged wiki deletions/renames trigger a full-graph
  lint — errors block, broken-link/orphan fallout is surfaced loudly (warn).
- CLAUDE.md-is-already-a-symlink branch added (never silently retarget a foreign
  symlink); subdir invocation documented honestly (`git rev-parse --show-toplevel`
  wrapper); hook commands guarded with `[ -f .okf/lint.py ]`; dead NotebookEdit
  matcher dropped; inline-comment stripping now WARNS (parser transparency);
  "works identically" claim softened to match reality.

## 1.1.1 (2026-07-08)

Round-2 fixes from the lint-breaker re-attack on v1.1.0's new surface (its verdict:
round-1 fixes all held, 38/38 independently confirmed, no crashes; 4 new
wrong-results + 1 hash flaw — all fixed, regression suite now 45 assertions):

- **pre-commit now validates STAGED index blobs** (`git show :path`), not the working
  tree — continued edits after `git add` can no longer slip broken content into git
  history while the gate reports success (the classic pre-commit-hook mistake).
- **Gitignore probe de-false-positived**: plain probe filename (was dunder-style,
  which collided with legitimate `__*` private-page conventions) and the error now
  names the exact matching ignore rule via `check-ignore -v`.
- **Unicode paths**: all git calls run with `core.quotepath=false`, so non-ASCII
  filenames appear as real UTF-8 in noop-check/stop-gate output instead of octal
  escape garbage.
- **Case-insensitive filesystems** (macOS APFS default): hook containment falls back
  to case-blind comparison, so `WIKI/page.md` payloads still count as wiki edits.
- **Tree hash hardened**: length-prefixed (path, content) framing removes the
  boundary-shift collision in the state churn guard.
- **Framing honesty pass** (fresh-panel verdict: MOSTLY-HONEST → fixed): CI lint and
  the pre-commit gate are now labeled structure guards (at merge / at commit) with an
  explicit "cannot detect a skipped write"; the Stop gate is named as the ONLY
  blocking write-forcer; Codex parity states plainly that no blocking write-forcing
  exists there and the obligation rests on the contract.
- **Requirements-audit-v2 fixes** (its verdict: all 3 hard requirements + all 9
  locked decisions PASS; findings fixed): the pre-commit git-persistence guard now
  fires on EVERY commit — code-only commits get a loud non-blocking warning when the
  wiki's git persistence is broken (was: silently skipped unless wiki files were
  staged); version metadata unified at 1.1.1; regression suite path made portable
  (was hardcoded to this machine); lite profile explicitly documents "no hooks —
  guidance-layer only"; reserved-file list and "strict vocab" wording corrected.
  Regression suite: 46 assertions.

## 1.1.0 (2026-07-08)

Hardening + architecture release driven by a 6-reviewer adversarial panel (fresh Opus
review, empirical fixture attack, Codex GPT-5.5 xhigh cold review, devil's-advocate,
requirements audit, hooks fact-check vs official docs).

Regression suite: `tests/run_regression.py` (38 assertions, one per reproduced
finding — run with `uv run --no-project python3 tests/run_regression.py` after any
lint change).

### Fixed (all panel P0s reproduced, then regression-tested)
- **NEW, found during regression (no reviewer caught it): symlinked-path containment
  bug** — hook payload paths vs physical cwd (macOS `/var`→`/private/var`, symlinked
  project dirs) made the PostToolUse hook silently skip real wiki edits; fixed with
  `realpath` on both sides. Companion fix: a probe now errors when a TRACKED wiki
  sits under a blanket ignore rule (future files would be silently ignored).
- **Gitignore remediation was wrong in its motivating case**: bare `!/dir/**` cannot
  un-ignore under an excluded parent. All guidance + lint hints now teach parent
  re-inclusion (`docs/*` + `!docs/llm-wiki/`) and lint detects ignored files inside
  the wiki (`--ignored`).
- **`noop-check` false verdicts (4 causes)**: porcelain output no longer corrupted by
  whole-output strip; renames classify both sides; zero-commit repos can't stamp a
  bogus `"HEAD"` anchor; missing/rebased anchors and any git failure now degrade to
  STALE/NO-STATE, never CURRENT.
- **State deadlock**: `state-update --mark-reviewed` advances the git anchor after a
  reviewed no-doc-impact diff (churn guard still blocks pure metadata rewrites).
- **`hook` crash contract**: entire hook path wrapped; type-invalid JSON payloads
  (int/list/bool file_path) exit 0 instead of stack-tracing.
- **Frontmatter parser vs own docs**: BOM handled (utf-8-sig everywhere); inline `#`
  comments stripped (and banned from templates/docs); folded scalars (`>`/`|`) are an
  explicit lint error instead of silent corruption; leftover `<placeholders>` error;
  unterminated frontmatter gets a precise message.
- **cwd fragility**: every subcommand resolves the repo root via
  `git rev-parse --show-toplevel`; explicit not-a-git-repo errors replace silent no-ops.
- **Link lint**: titled links extracted; inline code spans stripped; line-anchored
  fence pairing; wiki-escaping `../` links no longer misvalidated; log.md links no
  longer suppress orphan detection; symlinked pages skipped with a note.
- **Bootstrap ordering**: commit before state stamp; `git add` covers the state file.
- Reserved-file gap: `hypotheses.md`/`evidence-matrix.md` no longer get leaf-page
  frontmatter errors. Undocumented `sources/` alias removed (docs say `raw/`, code
  now agrees). Auto-log restricted to leaf wiki `.md` pages, lock-guarded, and
  handles headerless log files.

### Changed (user-decided architecture)
- **Enforcement reframed as three honest layers** (structure guard / write-forcing /
  guidance) — replaces the overclaimed "deterministic enforcement" banner.
- **New agent-agnostic anchor: git hooks** (`.okf/githooks/pre-commit` via
  `core.hooksPath`, with existing-hook-framework detection): lint errors block
  commits; code-without-wiki commits warn loudly (never block). Fires for Claude,
  Codex, and humans alike.
- **Stop gate is now default-on and command-based** (`lint.py stop-gate`): real git
  checks, zero token cost, `no-impact` log-line escape, `stop_hook_active` honored.
  Replaces the opt-in prompt-type hook (`templates/stop-gate.json` removed; the
  prompt-hook schema was verified correct but the mechanism couldn't see git state).
- **Value-bar gate + lite profile at bootstrap**: repos below the wiki's cost bar get
  contract + symlink + git guard + bare index only; upgradeable to full later.
- **Auto-log kept, narrowed** (leaf wiki .md only) per user decision, against the
  devil's-advocate's delete recommendation.
- PostToolUse matcher widened to `Edit|MultiEdit|Write|NotebookEdit`; `_comment` keys
  stripped from JSON templates; SKILL.md `metadata.version` migrated to top-level
  `version`; CI lint scaffold now actually ships (`templates/ci-okf-lint.yml`);
  contract text is Codex-honest and forbids wiki writes in read-only sessions;
  machine-absolute paths removed from SKILL.md/reference.md.

### Declared cuts (decisions, not drops)
- **No PreCompact transcript snapshot** (user decision: conflicts with
  minimal-generation; SessionStart `compact` matcher already re-injects the pointer).
- **No openwiki binary dependency** (mechanisms folded in; user decision from design
  round). No PR-time staleness CI (lint-only in CI for v1.1).

## 1.0.0 (2026-07-08)

Initial release. Built from a 51-agent deep-research pass (web + hands-on GitHub survey
+ local Claude/Codex session-log mining + adversarial challenge of the June 2026 priors).

- Modes: auto-detect + bootstrap/update/lint/audit/migrate; AGENTS.md real +
  CLAUDE.md symlink; deterministic core hooks; shipped stdlib lint; openwiki
  mechanisms (no-op short-circuit, SHA-256 state guard, soft diff budget,
  plan-then-delete, single-writer, state anchor); copy-first migration.
- Superseded same-day by 1.1.0 after adversarial review (verdict: ship-with-fixes).
