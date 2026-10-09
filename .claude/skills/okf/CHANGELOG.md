# Changelog — okf skill

## 1.4.1 (2026-10-09)

From an upgrade rehearsal: `/okf` run unattended on copies of the four production repos (still on okf 1.2.3), with
their real uncommitted work overlaid; graded on lint/runner/hooks upgraded, contract refreshed, Codex and git
hooks present, no page lost, lint clean, others' uncommitted files untouched and uncommitted.

- **Upgrade first, every run.** On 1.4.0, plain `/okf` routed two current-looking repos to `update` and left their
  two-versions-old `.okf/` (old Stop gate included) in place (8/14 and 7/14 checks); in one of them the old Stop
  gate then fired on the user's pre-existing uncommitted source files and the agent spent 13 minutes on it. Every
  run now compares the repo's `OKF_LINT_VERSION` with the skill's and upgrades first (Repair steps 2–3, committed
  on its own; audit only reports). Repair keeps a githook that differs from the template (a project gate).
- **Session-start upgrade notice.** From 1.4.1 on, the SessionStart hook says when an installed okf skill
  (Claude or Codex copy) is newer than the repo's `.okf/`, so later upgrades are not left to chance.
- **Others' uncommitted work is off-limits** (invariant 9): never edit, stage or commit a file that already holds
  uncommitted changes the agent did not make; do the rest and list the skipped steps. On 1.4.0 one run edited
  AGENTS.md, `.gitignore` and 11 pages that held a parallel session's uncommitted work.

Rehearsal on 1.4.1: 14/14, 14/14, 14/14 and 13/14 (the one miss is the agent correcting a stale count in AGENTS.md,
"30" to "34" scenes, verified against the code). Where AGENTS.md held others' work the contract refresh was left
open and reported. No-regression pass on 1.4.1: update-stale 9/9, fresh-bootstrap 28/28, repair-drifted 11/11,
migrate-legacy-ignored 13/13, ship-crosspage-hard 9/9, audit-truth with no false alarm. Codex parity (1.4.0,
codex exec): ship-crosspage-hard 9/9 ×3, audit-truth every sampled planted fact reported, no false alarm, read-only.
Regression suite: 130 → 132.

## 1.4.0 (2026-10-03)

**Truth check in `/okf audit`.** Lint can only check a wiki's shape. A production audit (four repos, 600 claims
checked against the code) found 4.3% of checkable claims wrong, almost all exact numbers and status lines, and
the review anchor and `noop-check` cannot see them: an `Okf-Impact: none` commit makes a stale wiki look CURRENT. `/okf audit` now adds a
read-only truth check:

- `lint.py claims [--n 12] [--seed S]` samples sentences from leaf pages, weighted toward status lines, numbers and
  code references (where production went wrong), at most ~2n/pages per page, each with its cited sources (`[S#]`,
  v0.2 `[^id]` footnotes, inline links and paths, or the page's Sources list). Deterministic per seed (default:
  today), read-only, one sentence per output line. A repo whose `.okf/lint.py` predates 1.4.0 runs the skill's copy.
- The agent checks every sampled sentence against code, config, tests, data, `raw/` captures and git history (never
  the wiki) and reports one row per sentence: `supported` · `wrong` (only with the contradicting line quoted) ·
  `unconfirmed` · `outside the repo`. Fixes go through `/okf update`. Rubric: reference.md §11.

How the wording was settled (live runs on Claude Sonnet 5.5, all read-only, none changed a file):
- First wording on real production wikis (clones of two repos): agents checked only the easy half of the sample
  (6 of 12, 8 of 20), skipped the subagent fan-out and the second look. Second wording ("check every sentence",
  default 12, quote the evidence for every flag): 12 of 12 checked in every run, but a "partly" verdict absorbed
  "did not confirm" — the same 12 sentences got 4 partly flags in one run and 1 in the next. Final wording: `wrong`
  needs a quoted contradicting line, otherwise `unconfirmed`. Four real-wiki audits: 46 of 48 sentences checked
  (the 2 others lost to a `| head` on pretty-printed JSON, now one sentence per line), 0 `wrong`, no false alarms,
  $0.28–0.35 per audit. Evidence gaps showed up as `unconfirmed` (5–6 of 12 in one repo cite gitignored scratch
  files).

A/B (eval case `audit-truth`: 19-page wiki, three facts gone stale behind an `Okf-Impact: none` commit so lint and
`noop-check` say CURRENT, two claims wrong when written; prompt `/okf audit`):
- 1.3.5 (structure-only audit): planted facts surfaced 3 of 15 (one run fact-checked on its own initiative).
- 1.4.0, 20-sentence sample: 25 of 25 (5 runs). Final 1.4.0, 12-sentence sample: every sampled planted fact
  reported (9 of 9 over 3 runs, plus one found outside the sample); recall per audit is bounded by the sample
  (3–4 of 5). No true fact reported wrong in any run; cost $0.19–0.22 per audit, the same as 1.3.5's.

The OKF v0.2 migration earlier earmarked for 1.4.0 is not in this release. Regression suite: 121 → 130.

## 1.3.5 (2026-10-03)

From a production audit: 600 claims sampled from the four production wikis were
checked against each repo's code; 4.3% of the checkable ones were wrong or outdated. The wrong ones were almost all
exact numbers (a count that had grown, a schema version that had moved) or status lines left standing after the
work landed ("<feature> stays refused", "open blocker"). Half were wrong when written, half went stale later. One
commit implemented a feature and updated that feature's page but left the old status and count on a design page
nobody reopened. Pages whose cited sources had changed were no more likely to be wrong (3.9%) than the rest (5.2%), so
source churn does not predict these errors.

- **Dead index entries are errors.** An `index.md` entry whose page does not exist now fails lint instead of
  warning; a line that says `planned` downgrades it to a warning. The pre-commit hook checks every index in the
  commit-to-be (the staged tree, not the disk) and blocks wiki commits until it is fixed; code-only commits are
  not blocked. The write-time hook names such entries whenever the session writes a page or index. Production: a
  sub-index listed a page that was never written, for two months under the old warning.
  Behaviour change: deleting a page whose index entry remains is now blocked at commit, not just warned.
- **Sweep the wiki for status lines; give volatile numbers provenance** (reference.md §6, Update step 5, page
  template). These are authoring rules, deliberately NOT in the per-session contract: in the A/B below the executor
  already swept the wiki without them, and wrote new counts without provenance with them.
- **Contract v3** adds only the index rule (about 20 tokens). **Outdated contracts get refreshed:** lint warns
  when AGENTS.md carries an older `okf:contract` version than the template; Repair now treats an older marker as
  outdated (show the diff, refresh with confirmation, keep the repo's own lines) and a same-version difference as a
  customization. Before this there was no upgrade path, and
  all four production repos still carry contract v1.

A/B on Claude Sonnet 5.5 (eval case `ship-crosspage`, 8-page wiki, and `ship-crosspage-hard`, 19 pages with the
status line also on a page not linked from the export page; a normal coding task, no `/okf` in the prompt; 6 runs
per version per case, alternating batches):
- dead index entry fixed: 1.3.4 0/12, 1.3.5 12/12. Every run in both versions ran the lint and saw the entry; as a
  warning it was ignored every time, as an error it was fixed every time (all by marking it `planned`; no page was
  invented).
- status lines and counts on the obvious, the linked and the unlinked page: 12/12 in both versions, so the sweep
  rule showed no lift (ceiling). Counts were rewritten without provenance in both versions.
- the final 1.3.5 (contract without the sweep sentence) re-run on `ship-crosspage-hard`: 3/3 runs, 9/9 each.
- cost per run $0.21 vs $0.22; turns unchanged. No-regression pass on 1.3.5: fresh-bootstrap 28/28, update-stale
  9/9, migrate-legacy-ignored 13/13, repair-drifted 11/11.

Regression suite: 109 → 121.

## 1.3.4 (2026-10-02)

Follow-up from the 1.3.3 live confirmation: update runs edited pages with `sed -i` and committed in the same shell
command, so a `git status`-based change detector saw a clean tree and skipped them. Change detection is now a stat
walk over the wiki's pages (raw/ excluded; untracked raw captures still listed via git), so edits are seen whether or
not they were committed in the same command. With no baseline yet (hooks installed mid-session), the first hook
run records one silently instead of treating the whole wiki as just written. The auto-log now records only edits that are
still uncommitted (they ride along with the agent's next commit); an edit already committed in the same command is
recorded by git and only gets the quality nudges — logging it would leave `log.md` dirty after the agent's last commit,
which the first 1.3.4 live run did. Regression suite: 105 → 109.

## 1.3.3 (2026-10-02)

Hook-coverage fix from the eval. The current default executor (Claude Sonnet 5.5) wrote wiki pages with shell
heredocs instead of the Edit/Write tools in every bootstrap and migration run, so the PostToolUse hook (matcher
`Edit|Write`) never fired while the wiki was being authored: no frontmatter, description or index nudges, no
auto-log. The hook is now tool-agnostic: it also matches `Bash` (Codex: all tools) and processes every wiki file
whose state changed since its previous run (one `git status` scoped to the wiki, state in the gitignored
`.okf/hook-seen.json`, baselined at SessionStart so pre-existing dirt is not re-nudged). Regression suite: 101 → 105.

## 1.3.2 (2026-10-02)

Wiki-quality release, from the eval's rubric judge (8 items over every wiki the eval produced). Two defects
recurred in every version and are deterministic, so they are now mechanized rather than left to prose:

- **Generic description openers** ("How…", "Why…", "When…", "This page…"): 23–44% of pages in every version.
  Lint warns, and the PostToolUse hook nudges the model (`additionalContext`) the moment such a page is written.
- **Index entries that paraphrase instead of reusing the page description**: 12–40% of pages. Lint warns per page;
  writing an `index.md` that paraphrases triggers a nudge naming the pages.
- **Premature subdirectories** (house rule: flat until ~7 pages): a newer executor split 4-page wikis into
  subdirectories in both runs. Lint warns.

Bootstrap step 5 states all three rules inline. Regression suite: 94 → 101.

## 1.3.1 (2026-09-15)

Trigger-tier fix from the eval (20 probes, Haiku executor, skill 1.2.3): should-not-trigger prompts stayed
quiet 10/10, but only 3/10 should-trigger prompts invoked the skill — "create a knowledge base for agents"
produced a hand-rolled 1,192-line knowledge base and "is the wiki up to date?" was handled without the
no-op check. The description now front-loads the maintenance verbs (bootstrap, set up, create, migrate,
repair, lint, audit, update, up to date) and states that hand-rolling a knowledge base is wrong; the contract
routes maintenance requests to `/okf`.

Evidence-durability fix from the eval (both 1.2.3 and 1.3.0 left cited ADRs gitignored after fixing a blanket
`docs/` ignore in the migration case): lint now ERRORS on every cited local file (`[S1] Local: path`, `source:`,
`resource:`) that is untracked or gitignored (a warning was ignored 3/3 times in the eval), and the migrate flow re-checks cited files with `git check-ignore`
after any ignore fix. `DECISIONS.md` now counts as agent plumbing (like AGENTS.md and `.okf/`), so a
decisions-only commit never needs an `Okf-Impact` trailer.

## 1.3.0 (2026-09-09)

Production-evidence release. Driven by transcript mining of every real session (1 Claude, 148 Codex
threads, 4 repos), an 8-lens adversarial review with reproductions, and a new eval harness with
planted-fact fixtures. The knowledge model is unchanged; the enforcement
mechanics were the weak part and are rebuilt.

- **Stop gate closes the commit bypass.** `session-start` records the session base HEAD
  (`.okf/session-head`, gitignored); `stop-gate` now inspects commits since that base as well as
  the worktree, so "commit, then stop" no longer passes. Escapes: a wiki page or log entry touched
  this session, a `no-impact` line **dated today**, or an `Okf-Impact: none` commit trailer.
  `raw/` captures never satisfy a gate. Prints `{}` on allow (Codex requires JSON).
- **Anchor advances itself.** New git hooks `post-commit` (stamps when a commit touches the wiki)
  and `post-rewrite` (follows amend/rebase). `noop-check` reports uncertified *commits* (code
  touched, no wiki, no marker) instead of hundreds of flat paths; `state-update
  --from-last-wiki-commit` recovers a clone with no anchor.
- **Codex hooks.** `templates/hooks-codex.json` + `install-hooks --target codex` install the same
  three hooks into `.codex/hooks.json`; the PostToolUse hook parses `apply_patch` payloads. Trust
  them once with `/hooks` in Codex. The "no write-forcing under Codex" claim is gone.
- **The frontmatter nudge reaches the model.** PostToolUse output is now
  `hookSpecificOutput.additionalContext` JSON (plain stdout on exit 0 only ever reached the debug
  log — zero nudges were seen in any production transcript).
- **Hooks survive real sessions.** All hooks go through the tracked `.okf/okf-py.sh`, which resolves
  the repo root (subdirectory launches and `/cd` silently disabled every hook), pins uv to a system
  Python 3 with downloads off (a repo `.python-version` made `uv run` exit 2 = permanent Stop
  block), and falls back to bare `python3`. `git` timeouts fail closed in the Stop gate.
- **Auto-log no longer corrupts `log.md`** (entry lands below preamble prose, above the newest entry
  — the fix a production repo had already made locally); CRLF logs keep CRLF; `msvcrt` lock on
  Windows; case-insensitive filesystems detected by probe, not `sys.platform` (WSL `/mnt/c`).
- **Re-runs never clobber.** `.okf/githooks/pre-commit.local` chain point for project gates;
  `install-hooks` upgrades an older okf entry instead of appending, honors `hooksDisabled` in
  config, writes atomically, backs up under `.okf/`; contract marker bumped to v2.
- **OKF v0.2 tolerance.** Nested `sources:`/`generated:`/`verified:` parse; `status:
  draft|stable|deprecated` accepted alongside the legacy set; a passed `stale_after` warns; `raw/`
  excluded from the wiki hash. Full v0.2 migration (`migrate-v02`, stamping) is 1.4.0.
- Lint lists untracked raw captures by name; pre-commit warns when synthesis is committed while its
  captures are untracked; `wikiDir` validated against shell-safe names; `--help` prints usage and
  unknown subcommands exit 2 instead of silently linting.
- SKILL.md: CLAUDE.md defaults to an `@AGENTS.md` import (symlink opt-in — Windows clones turned the
  symlink into a one-word file); trust boundary stated; fresh-clone and Codex sentences corrected;
  13 contradictions fixed; length held under 18 KB despite the additions. Regression suite: 58 → 90 assertions, green on Linux.

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
