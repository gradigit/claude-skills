---
name: okf
description: Bootstraps and maintains OKF/LLM-wiki agent knowledge bases (Karpathy LLM-wiki + Google Open Knowledge Format) in any repo. Auto-detects state — fresh repos get a value-gated bootstrap (full or lite: wiki skeleton, AGENTS.md contract with CLAUDE.md symlinked to it, agent-agnostic git hooks + Claude hooks, git-tracking guard, shipped lint); already-bootstrapped repos get incremental update/lint/audit/repair; legacy or foreign wikis get confirmation-gated migration. Activates on /okf, "bootstrap the wiki", "set up OKF", "llm wiki", "knowledge base for agents", or when a repo's agent wiki needs maintenance/repair. Do NOT use for ordinary documentation work (READMEs, docstrings, API docs) that does not involve the agent-maintained knowledge base.
argument-hint: "[bootstrap|update|lint|audit|migrate|repair]"
version: "1.2.3"
---

# OKF — bootstrap & maintain an agent knowledge base

Sets up and maintains a durable, agent-facing markdown wiki in the current repo — Karpathy's LLM-wiki pattern in Google's Open Knowledge Format (OKF v0.1). Works from Claude Code and Codex with the same files and contract; the hook layers are Claude-only (this file is self-contained; see §Codex parity for what differs).

Canonical concepts (on bootstrap, confirm you understand these before building; fetch only if unfamiliar):
- Karpathy LLM-wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- OKF spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
- House authoring rules (evidence-backed, REQUIRED before writing pages): [reference.md](reference.md)

## Workflow

- [ ] 1. Detect repo state (§Detection) → route to a mode
- [ ] 2. Run that mode's flow (§Bootstrap / §Update / §Lint / §Audit / §Migrate / §Repair)
- [ ] 3. Verify: lint passes, wiki git-tracked, contract + symlink + hooks intact
- [ ] 4. Report visibly: show lint output, list pages touched, state what was skipped

An explicit argument overrides detection: `/okf bootstrap|update|lint|audit|migrate|repair`.

## Enforcement model — three honest layers

The skill does not pretend a linter can judge knowledge. Each layer is named for what it actually does:
1. **Structure guard** (`.okf/lint.py`): well-formedness and rot signals only — frontmatter, links, orphans, git-tracking, citation *presence*. It cannot measure insight; don't claim it does.
2. **Write-forcing & nudges**: the only mechanism that BLOCKS on "code changed, wiki untouched" is the **Claude Code Stop gate** (session end is blocked while uncommitted code changes have no wiki/log counterpart; a `## [date] no-impact | why` log line is the deliberate escape). The agent-agnostic layers are weaker, and say so: the **git pre-commit hook** blocks malformed STAGED wiki pages and WARNS — never blocks — on code-without-wiki commits; **CI lint** re-runs the structure guard at merge and cannot detect a skipped write. Honesty about reach: git hooks are LOCAL config — they fire for every agent and human *in a clone that ran /okf once*; fresh clones get only CI + contract until then. Under Codex there is no blocking write-forcing at all — there, the write obligation rests entirely on the contract. These layers force or nudge *that* you write, never *what*.
3. **Guidance** (AGENTS.md contract + [reference.md](reference.md)): where quality lives — model judgment by design.

## Core invariants (non-negotiable)

1. **AGENTS.md is the real file; CLAUDE.md is a relative symlink to it.** Never duplicate content (drift is the failure mode this kills). Fallback where symlinks are impossible: a 3-line delegating stub — never a copy.
2. **Pointer, not inline.** AGENTS.md carries a short contract pointing into the wiki; never inline wiki content.
3. **Single writer.** The main agent is the sole writer of the wiki; subagents inspect and report only.
4. **Generate minimally; pages accrete.** LLM-generated verbose context files measurably reduce agent success (ETH, arXiv:2602.11988). First pass ≤8 pages; no architecture dumps.
5. **The wiki must be git-tracked.** The #1 observed rot cause. CAUTION — a bare `!/docs/llm-wiki/**` negation does NOT work under a blanket `docs/` ignore (git never descends into excluded parents). Re-include parents instead: `docs/*` then `!docs/llm-wiki/`. Verify with `git check-ignore -v <wiki>/index.md` after editing.
6. **Copy-first migration.** Never move/delete/overwrite existing docs or agent files without a shown plan and explicit confirmation.
7. **Retrieval is files + grep + index.md.** No embeddings/BM25/rerankers/alias indexes by default (see reference.md §Retrieval for the one sanctioned opt-in and the honest token-cost note).
8. **Mechanize what can be mechanized; be honest about the rest.** Log appends, lint, commit and stop gates fire from hooks/scripts. Knowledge quality cannot be mechanized — the contract and playbook carry it.

## Detection (run first, always)

Check in priority order; first match wins. Auto-detect the wiki dir among: `wiki/`, `docs/llm-wiki/`, `docs/wiki/`, `llm-wiki/`, `openwiki/` (a dir with an `index.md`). Default for NEW bootstraps: `wiki/`. An existing healthy wiki dir always beats the default — never relocate a working wiki.

| # | State | Signals | Route |
|---|-------|---------|-------|
| 1 | Fully bootstrapped | AGENTS.md contains `<!-- okf:contract` AND CLAUDE.md is a symlink/stub to it AND `<wiki>/index.md` + `.okf/config.json` exist (config.json is the deliberate bootstrap-completed marker) | `update` (or `audit` if the user asked for status) |
| 2 | Partial / drifted | Wiki exists but contract, symlink, `.okf/`, or hooks missing; or CLAUDE.md and AGENTS.md are diverged regular files | `repair` |
| 3 | Legacy/foreign wiki | `docs/llm-wiki/` without frontmatter, `openwiki/`, `droid-wiki/`, flat dated `research-*.md` — or ANY substantial pre-OKF knowledge dir even if differently named (`architect/`, `research/`, `notes/`, dated reports) | `migrate` |
| 4 | Nothing | none of the above | `bootstrap` |

Always also check: `git rev-parse --show-toplevel` succeeds (no git → bootstrap must `git init` first; the persistence promise requires git) and the wiki path is tracked (`git check-ignore`, `git status --porcelain --ignored`).

## Bootstrap

1. **Value gate first.** Ask: does this repo clear the wiki's cost bar? Knowledge-dense, investigative, or long-lived multi-session repos do. A small script repo may not — offer the **lite profile** (step L below) or decline with reasons. Also ask (≤3 questions total) about capture depth and wiki dir if ambiguous. Push back; don't follow blindly. **Unattended runs:** self-arbitrate each question with the most reasonable assumption and record it in DECISIONS.md at the repo root (git-track it or delete it when done — an untracked root file pins noop-check to STALE) instead of blocking.
2. **Concept gate.** Confirm the two canonical concepts are understood (offline: [reference.md](reference.md) summarizes both and is sufficient; fetch the primary sources only if genuinely unfamiliar).
3. **Survey** (read-only subagents allowed; single writer enforced): structural pass (README, manifests, entrypoints, CI), then semantic pass (domain, key flows, sources to ingest).
4. **Plan-then-delete.** Write `<wiki>/_plan.md` (page list → evidence → open questions); delete it before finishing. Mandatory for bootstraps and multi-file migrations; skippable for trivial (≤3-file) migrations — log the skip in DECISIONS.md.
5. **Generate minimally** per invariant 4: root `index.md` (navigational, ≤200 lines; entries reuse each page's `description` — that is what makes progressive disclosure real), `log.md` (an event log of what happened, not a page catalog), and only the pages the survey justifies (≤8). Frontmatter per [reference.md](reference.md); no inline comments inside YAML. **Evidence durability:** newly fetched source material goes verbatim under `<wiki>/raw/`; pre-existing repo files that pages CITE stay in place if tracked, but if a cited file is UNTRACKED (and not ignored by policy), copy — never move — it into `<wiki>/raw/` or get it tracked: cited evidence must survive `git clean`.
6. **Wire the contract.** Create or append to AGENTS.md from [templates/agents-contract.md](templates/agents-contract.md) (replace `{WIKI}`; preserve every non-OKF section, deduping prose that the contract now covers). CLAUDE.md, four cases: absent → `ln -s AGENTS.md CLAUDE.md`; regular file → show its content and SPLIT it: instruction-shaped parts (how to work here) are absorbed into AGENTS.md; **knowledge-shaped parts (domain facts, architecture, findings) are routed into wiki pages — never inlined into AGENTS.md (invariant 2 outranks this step)**; then replace with the symlink (confirm first); **already a symlink** → if it targets AGENTS.md, done; if it targets anything else (dotfiles/shared config), show the target and do NOT retarget without explicit confirmation; symlinks impossible → stub: `Read AGENTS.md — it is the single source of truth for this repo.`
7. **Install enforcement.**
   - Copy this skill's `scripts/okf_lint.py` → `.okf/lint.py`; write `.okf/config.json` (`{"wikiDir": "<wiki>", "typeVocab": [...]}`).
   - **Git hooks (agent-agnostic anchor — local to this clone):** copy [templates/githooks/pre-commit](templates/githooks/pre-commit) → `.okf/githooks/pre-commit` (chmod +x). Route by what exists, checked IN THIS ORDER:
     0. `git config --global core.hooksPath` or `--system core.hooksPath` is set → **NEVER set a local core.hooksPath** (it would shadow the user's global hooks — secret scanners, git-lfs). Chain instead: if the global hook framework documents a per-repo chain point (e.g. `.git/hooks-local/`), install a pre-commit there calling `.okf/githooks/pre-commit` and VERIFY it fires (`git commit` a trivial change or read the global hook source); no chain point → skip git hooks with a loud note and lean on CI.
     1. `.git/hooks/` has ANY native non-sample hook (pre-push, commit-msg, ...) → install into `.git/hooks/pre-commit` directly (chaining into an existing pre-commit with confirmation); do NOT set core.hooksPath (it would orphan the other native hooks).
     2. husky/lefthook config present → chain into that framework or skip with a visible note.
     3. Clean → `git config core.hooksPath .okf/githooks`.
     Record the routing choice in DECISIONS.md. Note to user: hooks are per-clone; fresh clones need one `/okf` run (CI is the clone-surviving backstop).
   - **Claude hooks (scripted merge — never hand-edit settings.json):** render [templates/hooks-settings.json](templates/hooks-settings.json) with `{WIKI}` substituted to `.okf/hooks-fragment.json`, then run `python3 .okf/lint.py install-hooks .okf/hooks-fragment.json` — it deep-merges only `hooks.*` entries, is idempotent, backs up an existing settings.json, and refuses to touch invalid JSON. SessionStart + PostToolUse + the Stop gate are all default; to disable the Stop gate later, remove its Stop block.
   - **CI backstop:** copy [templates/ci-okf-lint.yml](templates/ci-okf-lint.yml) → `.github/workflows/okf-lint.yml` (or adapt for GitLab). A backstop matters MOST where git hooks couldn't be installed (routing case 0/2 above) — install it there even if the repo had no CI; where hooks are live it's optional.
   - Git-tracking guard per invariant 5.
8. **Commit + stamp (order matters).** Append the bootstrap entry to `log.md` BEFORE the bootstrap commit (so the log ships in it); add `.okf/last-update.json`, `.okf/hooks-fragment.json`, and `.okf/log.lock` to `.gitignore` (**state is per-clone machine state, deliberately untracked** — it records THIS clone's review anchor; tracking it causes worktree/collaborator churn, and fresh clones simply re-anchor with one full pass); `git init` if needed; `git add` wiki, AGENTS.md, CLAUDE.md, `.okf/`, settings; make the bootstrap commit; THEN `python3 .okf/lint.py state-update` (needs the commit to anchor to; leaves nothing uncommitted because state is ignored); run `python3 .okf/lint.py lint` and show the output.

**L. Lite profile** (repos below the value bar): contract + symlink + git-tracking guard + `.okf/` (lint + config **with `"profile": "lite"`** — the marker detection and noop-check use to distinguish lite from full) + a bare `<wiki>/index.md` + `log.md`. No generated pages, no state machine use, no CI — and **no hooks**: lite is guidance-layer only (the Stop-gate-default decision applies to FULL installs; say so to the user when choosing lite). `/okf` upgrades lite→full later on request (generate pages if warranted, install hooks, set `"profile": "full"`).

## Update (the maintenance loop)

1. **No-op short-circuit:** `python3 .okf/lint.py noop-check`. `CURRENT` → report "wiki already current," stop. It fails toward STALE on any git uncertainty (rebases, renames, no commits) — trust it.
2. **Diff:** it prints changed paths; use `git log <lastHead>..HEAD --name-status` and `git diff --name-status HEAD` for detail.
3. **Docs-impact plan:** changed source path → affected wiki page → edit → why. No impact → no edit.
4. **Soft diff budget:** <5 source files changed → edit ≤1–2 pages; >3 pages needing edits demands re-justification. No-op updates are valid.
5. **Surgical edits:** replace the stale sentence, don't append paragraphs; no formatting-only edits; bump the page `timestamp` when meaning changes.
6. **Rename safety:** renaming/moving a page rewrites ALL inbound relative links in the same change.
7. **Contradictions:** newest verified evidence wins; note supersessions in the page and `log.md`; keep the root index ≤200 lines.
8. **Close out:** update per-dir `index.md` if navigation changed; `python3 .okf/lint.py lint` (show output); commit the wiki changes; then `python3 .okf/lint.py state-update` — or `state-update --mark-reviewed` when you reviewed the diff and it truly had no doc impact (this advances the anchor so the same diff isn't re-reviewed forever). State is per-clone and gitignored, so stamping after the commit leaves the worktree clean.

**Ingest variant** (new source material rather than code drift): capture raw → synthesize into affected pages → cross-link → index if nav changed → log. Same budget discipline.

## Lint

`python3 .okf/lint.py lint` — deterministic, repo-local, stdlib-only. The script resolves the repo root internally, but the *path to the script* is relative — from a subdirectory invoke it as `python3 "$(git rev-parse --show-toplevel)/.okf/lint.py" lint`. Errors (exit 1): missing/malformed/placeholder frontmatter, multi-line scalars in required fields, absolute internal links, gitignored wiki or wiki files, non-git repo, missing root index. Warnings: unknown `type`, forward/broken links, orphans (log.md links don't count), missing per-dir index, thin pages, missing citations (`## Sources` or `source:`), untracked files, >200-line root index, duplicate descriptions, symlinked pages. Fix errors now; triage warnings visibly.

## Audit (read-only)

Report, change nothing — no writes in audit sessions: detection state, lint summary, `noop-check` freshness, page/dir counts, log.md recency, hook presence (`.claude/settings.json`, `git config core.hooksPath`, CI workflow), git-tracking status. End with a prioritized repair list.

## Repair (partial / drifted repos — confirmation-gated)

The messiest path: it touches existing user files. Ordered:
1. Run `audit` first and show the gap list. Confirm scope before changing anything.
2. **Reconcile AGENTS.md/CLAUDE.md drift:** show a diff of both; merge the union of non-duplicate content into AGENTS.md (contract block included/refreshed); only then, with confirmation, replace CLAUDE.md with the symlink (or stub).
3. Add missing pieces in dependency order: `.okf/` (lint + config) → git-tracking fix (invariant 5 pattern) → git hooks → Claude hooks merge → missing `index.md`/`log.md` (generate thin, from existing pages only — no new content).
4. Frontmatter backfill for existing pages: propose `type`/`title`/`description` per page as a shown plan; apply on confirmation.
5. Commit, `state-update`, lint, show output.

## Migrate (absorb existing docs — copy-first, confirmation-gated)

1. Inventory existing knowledge artifacts (legacy `docs/llm-wiki/`, `openwiki/`/`droid-wiki/` output, flat dated research files, ADRs).
2. Present a mapping plan: source file → target wiki page + `type` → synthesized or verbatim. **Nothing moves, is deleted, or overwritten until the user confirms.**
3. Copy content in with frontmatter; park full-fidelity originals under `<wiki>/raw/` when they are external/dated material; keep an existing healthy wiki dir as the wiki dir.
4. Then run Bootstrap steps 6–8. Originals are archived/removed only on explicit confirmation.

## Codex parity (honest version)

- **What is deterministic under Codex:** the git pre-commit hook and CI lint — they fire on commits regardless of agent, but they gate *well-formedness* and warn; there is no *blocking* write-forcing under Codex, so the write obligation there rests entirely on the AGENTS.md contract (Codex-native guidance — real file, not symlink, precisely so Codex reads it first-class).
- **What is Claude-only:** SessionStart pointer, PostToolUse auto-log/quick-lint, Stop gate. The contract says so explicitly and tells non-Claude agents to append log entries themselves and run lint before finishing.
- **Invocation from Codex:** read this SKILL.md (installed at `~/.codex/skills/okf`, a symlink to the Claude copy — content parity is automatic) and follow it directly.
- Everything installed into a repo is plain files + python3 stdlib + git — agent-agnostic by construction, degraded honestly where a runtime lacks hooks.

## Example

**Input:** `/okf` in a repo with `docs/llm-wiki/` (no frontmatter), a content-bearing CLAUDE.md, no AGENTS.md.
**Output:** Detection → state 3 (legacy). Mapping plan shown (5 pages → frontmattered, originals kept; CLAUDE.md absorbed into new AGENTS.md then symlinked — both confirmed). `.okf/` + git hooks + Claude hooks installed; `.gitignore` had a blanket `docs/` rule — fixed with `docs/*` + `!docs/llm-wiki/` (bare `!…/**` would have been a no-op) and verified with `git check-ignore`. Bootstrap commit made, state stamped, lint shown: 0 errors, 3 warnings triaged.

## Self-Evolution

Update when: (1) the user corrects a flow; (2) OKF spec moves past v0.1 or renames reserved files (config layer makes this a default change); (3) lint changes — keep `scripts/okf_lint.py` and repo copies in sync (`lintVersion` is stamped in state files; re-copy on the next `/okf` run per repo).

Current version: 1.2.3 — see [CHANGELOG.md](CHANGELOG.md) for the adversarial-review-driven changes and declared cuts.
