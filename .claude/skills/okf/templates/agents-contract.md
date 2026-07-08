<!-- okf:contract v1 -->
## Knowledge base (OKF / LLM-wiki)

This repo maintains a durable, agent-facing knowledge base under `{WIKI}/`.
It survives compaction and session resets: read it first, write to it as you work.

**Read first.** Start at `{WIKI}/index.md`; follow relative links to the pages you
need. Prefer the wiki over re-deriving knowledge from raw sources or chat history.

**Write as you go (obligation during authorized work).**
- When work produces a durable fact, decision, or hypothesis a future agent should
  not have to rediscover, persist it to the right `{WIKI}/` page — never leave it
  only in chat.
- This applies to sessions doing real work. In read-only, review, or audit
  sessions, do NOT write to the wiki; report instead.
- Capture full-fidelity source material under `{WIKI}/raw/`; keep synthesis on the
  topic pages. Do not summarize away primary data that may be needed verbatim.
- Keep inference separate from evidence: working theories in `hypotheses.md`,
  confirmed observations in `evidence-matrix.md` (investigative repos).
- Cite every claim (local path, URL, or thread ref). Mark uncertain claims `UNVERIFIED`.

**Authoring rules.** One answerable unit per file · kebab-case filenames · flat YAML
frontmatter with `type`, `title`, `description` (one distinguishing single-line
sentence) required · a per-directory `index.md`, updated whenever a page is added
or removed · relative links only between pages (external URLs under `## Sources`) ·
rewrite inbound links when renaming a page · retrieval is files + grep + index.md —
never add embeddings, BM25, rerankers, or alias indexes to this wiki.

**Single writer.** The main agent is the sole writer of `{WIKI}/`. Subagents are
read-only: they inspect and report; they never write wiki files.

**Ship = update.** A change that invalidates a wiki page updates that page in the
same unit of work; if a change truly has no knowledge impact, say so with a
`## [YYYY-MM-DD] no-impact | <why>` line in `{WIKI}/log.md`. The changelog is
`{WIKI}/log.md` (newest first, `## [YYYY-MM-DD] kind | Title`). Under Claude Code,
hooks auto-log session edits and gate stopping; under other agents (Codex etc.)
there are no hooks — append log entries yourself and validate with
`python3 .okf/lint.py lint` before finishing substantial work. The git pre-commit
hook and CI lint (where installed) enforce this for every agent.
<!-- /okf:contract v1 -->
