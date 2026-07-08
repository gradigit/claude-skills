# OKF authoring playbook — house rules, evidence-backed

Read this before writing wiki pages. Every rule is grounded in benchmarks or verified
adopter evidence; rules marked ⚖ were revised after adversarial review (2026-07-08,
two rounds: priors challenge + 6-reviewer panel). The full evidence trail lives in the
user's okf research project (see CHANGELOG.md for pointers).

## 1. Frontmatter (leaf pages)

```yaml
type: reference
title: OKX Withdrawal Rate Limits
description: Per-endpoint withdrawal rate caps and the 429 backoff contract for OKX v5.
tags: [okx, rate-limits]
source: https://www.okx.com/docs-v5/
timestamp: 2026-07-08
status: verified
```

Field rules (`type`, `title`, `description` REQUIRED; the rest optional):
- **`description` is the single highest-leverage field** — the only one with a measured
  retrieval lift (+5.4pp hit@1 at 515 docs). ONE single-line sentence, distinguishing
  terms front-loaded. Never a truncated first paragraph. ⚖ No folded/literal scalars
  (`>` / `|`) — the lint rejects them rather than silently corrupting.
- ⚖ **No inline `#` comments inside the YAML block** — they pollute parsed values
  (found by the review panel in this skill's own v1.0 template); lint warns when it
  strips one. If a value legitimately contains ` #` (e.g. "see issue #157"), QUOTE
  the whole value. Guidance lives in prose or HTML comments *below* the frontmatter.
- **Flat keys only. Never `name:`, never `metadata:` nesting** — the file *path* is the
  concept ID; that is what makes relative links work.
- ⚖ **`type` is free-text with a suggested vocabulary** (fixed enums were overfit):
  `reference`, `concept`, `decision`, `method`, `case-study`, `asset`, `idea`,
  `hypothesis`, `evidence`, `index`. Lint warns (never errors) on unknown types; a repo
  may customize the suggested vocab in `.okf/config.json` (still warn-only by design).
- `status: verified | unverified | draft` — flip from `draft` once sourced.
- Reserved files (`index.md`, `README.md`, `log.md`, `hypotheses.md`,
  `evidence-matrix.md`, `_plan.md`) are exempt from leaf-page frontmatter requirements.

## 2. Granularity — one answerable unit per file

A page fully answers ONE question. Litmus test: can you write one distinguishing
`description` sentence for it? Needs two → split. Can't write one → too thin, merge.
Mega-pages lost the benchmarks; per-concept files won; stub sprawl is the opposite
failure (thin-page lint warning).

## 3. Naming & layout

- Filenames: kebab-case slug of the title. Descriptive names are load-bearing
  (opaque names measurably lost). No dates/versions in filenames.
- Directories group by domain; subdirectory only past ~7–10 pages; every topic
  directory gets an `index.md`.
- Default tree (dir name configurable in `.okf/config.json`; upstream naming is
  churning, so reserved names are parameters, not constants ⚖):

```
wiki/
  index.md          # root catalog — thin, navigational, ≤200 lines
  log.md            # append-only, newest-first: ## [YYYY-MM-DD] kind | Title
  raw/              # full-fidelity captured sources, verbatim (capture-then-synthesize)
  <topic>/index.md  # per-directory catalog: [Title](file.md) — description
  <topic>/<answerable-unit>.md
.okf/               # machine layer: config.json + lint.py + githooks/ are TRACKED;
                    # last-update.json is per-clone state, deliberately GITIGNORED
                    # (fresh clones/worktrees re-anchor with one full pass)
```

## 4. index.md — progressive disclosure

Read-first catalog; the reason agents navigate without retrieval infra. One line per
entry: `[Title](file.md) — description` (reuse the page's own description). Dirs of
dirs list `## Sections`; dirs of leaves list `## Pages`. Update the index in the same
change as any page add/remove. Root index stays ≤200 lines; push detail down.

## 5. Linking — relative paths build the graph

- Internal links are ALWAYS relative markdown paths. Never absolute paths (broken
  rendering — OKF issues #48/#157), never external URLs for internal concepts, never
  `[[wikilinks]]`.
- Forward links to not-yet-written pages are sanctioned (they mark gaps); lint warns
  so they eventually get written.
- No orphans: every page gets an inbound link from its `index.md` at minimum
  (⚖ log.md mentions don't count — the lint checks the real navigation graph).
- **Rename = rewrite all inbound links in the same change** (path-as-identity breaks
  silently under reorganization — OKF #120).

## 6. Citations & evidence discipline

- Every claim cites a source: `[S1]` inline markers → `## Sources` block
  (`[S1] Title — URL (accessed YYYY-MM-DD)` / `[S2] Local: path`). Unverified claims
  tagged `UNVERIFIED`. ⚖ Lint now checks citation *presence* (a `## Sources` section
  or `source:` field on every non-draft leaf page) — presence is checkable; quality
  remains your job.
- Separate inference from evidence: `hypotheses.md` vs `evidence-matrix.md`
  (investigative repos). Delete or fill abandoned placeholder files — lint flags them.
- Capture-then-synthesize: full-fidelity raw material into `raw/` verbatim BEFORE
  synthesis ("did you actually save every piece?" is the recurring failure).
- Contradictions resolve recency-wins: newest verified evidence supersedes; note the
  supersession on the page and in `log.md`.

## 7. Retrieval — files + grep + index.md ⚖

Default: NO retrieval infrastructure. No embeddings, BM25/FTS5, rerankers, or
pre-generated alias/keyword indexes — benchmarked net-neutral-to-negative on
keyword-rich corpora (the alias layer cost 6.4M tokens for negative value). The free
lever for fuzzy queries is query-time: *extract the distinctive identifiers from the
question and grep the tree for them*.

Honesty notes (from the adversarial review):
- Those benchmarks used keyword-rich API docs and frontier models. For very large
  (1000s of pages) or low-keyword prose corpora, grep degrades — the one sanctioned
  escape hatch is an external search layer (e.g. qmd, BM25+vector+rerank MCP) as a
  **manual, documented opt-in**. Never installed by default.
- Agentic wiki navigation measured ~28k tokens / ~10s per deep query on a 515-doc
  corpus. That is the cost of quality. If a repo won't earn that back, use the lite
  profile (contract + bare index, no generated pages) — see SKILL.md §Bootstrap.

## 8. Generation & maintenance discipline

- **Do not auto-generate verbose wikis.** LLM-generated context files reduced agent
  success ~3% at +20% cost; "stale structural references actively mislead" (ETH,
  arXiv:2602.11988). Bootstrap small (≤8 pages); pages accrete from real ingests.
- **Never agentically re-write body prose you already have** (~20× token cost
  measured). Convert deterministically; spend tokens on `description` + `type` only.
- **Soft diff budget** (from openwiki): <5 source files changed → edit ≤1–2 pages.
  Surgical edits; no formatting-only churn; no-op updates are valid.
- **No-op short-circuit**: `python3 .okf/lint.py noop-check` before any update pass.
  ⚖ It fails toward STALE on every git uncertainty (rebased anchors, renames,
  zero-commit repos) — a false "CURRENT" was the worst defect the panel found in v1.0.
- **State stamps are churn-guarded**: `state-update` refuses to rewrite when the wiki
  hash is unchanged; ⚖ `state-update --mark-reviewed` advances the anchor after a
  reviewed no-doc-impact diff (otherwise the same diff re-reviews forever).
- **log.md**: auto-entries (`auto |`) come from the Claude PostToolUse hook — leaf
  wiki pages only, lock-guarded, one dated block per day. Hand entries are for
  meaningful events (`ingest | decision | migration | no-impact`), newest first,
  greppable. Under hookless agents (Codex), append hand entries yourself.
- **Single writer**: orchestrator writes the wiki; subagents inspect and report only.
- **Plan-then-delete**: `_plan.md` during bootstrap/big ingests; deleted before done.

## 9. Enforcement — three layers, named honestly ⚖

| Layer | What it actually does | Fires | Platform |
|---|---|---|---|
| **Structure guard** — `.okf/lint.py` | well-formedness + rot signals (never knowledge quality) | on demand, hooks, pre-commit, CI | any |
| **Structure guard at commit** — git pre-commit (`.okf/githooks/`) | blocks malformed STAGED wiki pages; WARNS (never blocks) on code-without-wiki commits — a nudge, not forcing | every commit, any agent or human | any (git) |
| **Structure guard at merge** — CI lint (`ci-okf-lint.yml`) | the same `lint` at PR time; catches malformed pages on fresh clones — it cannot detect a skipped write | PR/push | any (CI) |
| **Write-forcing** — Stop gate (`lint.py stop-gate`, default) | the ONLY layer that blocks on code-changed-without-wiki-update; `no-impact` log line is the deliberate escape; honors `stop_hook_active` (8-block cap is platform behavior) | deterministic, zero tokens | Claude Code |
| **Accelerators** — SessionStart pointer, PostToolUse quick-lint + auto-log | re-inject context; catch frontmatter slips at write time | deterministic | Claude Code |
| **Guidance** — AGENTS.md contract + this playbook | the only layer that carries *quality* | every session (agents read natively) | any |

Evidence: instructions alone reliably fail (Cline memory-bank: "claims to update but
never writes files"); deterministic firing works; and the v1.0 review showed the
opposite overclaim — calling shape-checks "enforcement of knowledge" — is Goodhart
bait. Front-loading the contract is necessary but not sufficient; the write-forcing
layers are the pressure substitute. Declared v1 cut ⚖: no PreCompact transcript
snapshot (conflicts with minimal-generation; the SessionStart `compact` matcher
already re-injects the pointer after compaction).

## 10. Anti-patterns (lint enforces most)

- Untracked/gitignored wiki. ⚖ Bare `!/dir/**` negation under an excluded parent is
  itself the anti-pattern — it does nothing; re-include parents (`docs/*` +
  `!docs/llm-wiki/`) and verify with `git check-ignore -v`.
- Duplicated AGENTS.md/CLAUDE.md content — symlink or stub, never copy.
- Inlining wiki content into AGENTS.md; architecture-dump indexes; speculative pages.
- Mega-pages; stub sprawl; weak descriptions; `name:`/`metadata:` nesting; inline
  YAML comments; template placeholders left in frontmatter.
- Absolute internal links; external URLs as internal links; `[[wikilinks]]`.
- Orphans; stale per-dir indexes; frozen placeholder files; uncited claims.
- Retrieval infra by default; confidently stale pages (mark `UNVERIFIED`,
  timestamp meaning-changes, resolve contradictions recency-wins).
- Writing to the wiki during read-only/review/audit sessions.

## Sources (abbreviated)

Karpathy LLM-wiki gist · OKF SPEC.md v0.1 (GoogleCloudPlatform/knowledge-catalog) ·
langchain-ai/openwiki source (no-op/state-guard/diff-budget mechanics) · Factory
AutoWiki docs · ETH "Evaluating AGENTS.md" arXiv:2602.11988 · format study
arXiv:2602.05447 · Claude Code hooks docs (Stop/prompt hooks, 8-block cap verified) ·
Cline memory-bank issue #1911 · the user's own June 2026 benchmarks (fs-vs-embeddings
parity; description lift; alias-layer negative; agentic-nav token cost) · local repo
rot survey + 6-reviewer adversarial panel (2026-07-08, 18 reproduced lint defects
fixed in 1.1.0).
