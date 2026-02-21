---
name: handoff-fresh
description: Generates a fork-safe onboarding bundle for a brand-new agent in forked/new-folder repositories. Manual command entry point is /handoff-fresh. Produces structured context/history/status files plus full handoff-everything output in .handoff-fresh/current. Defaults to local git-ignore for handoff artifacts (`HANDOFF.md`, `.handoff-fresh/`) to avoid untracked noise. Do NOT use when only standard HANDOFF.md continuity is needed.
license: MIT
metadata:
  version: "1.9.0"
  author: gradigit
  updated: "2026-02-22"
  tags:
    - handoff
    - onboarding
    - fork-safe
    - continuity
  triggers:
    - "/handoff-fresh"
    - "fresh handoff"
    - "fork-safe handoff"
    - "new-folder handoff"
    - "onboard fresh agent"
---

# Handoff Fresh

Creates a complete, fork-safe onboarding bundle so a brand-new agent can continue work reliably in a forked/new-folder repo.

## Command Contract (Explicit, Manual)

- Primary entry point: `/handoff-fresh`
- Run only when explicitly requested by user
- No implicit hook/side-channel execution
- Output target default: `.handoff-fresh/current` under project root
- Keep `/handoff` separate: `/handoff` = standard continuity, `/handoff-fresh` = fresh-agent onboarding bundle

## Workflow

```
- [ ] 1. Detect project root and bundle path
- [ ] 2. Apply handoff artifact ignore policy (default local) and archive previous bundle snapshot (optional)
- [ ] 3. Run prerequisite sync (unless --no-sync)
- [ ] 4. Collect source context, history, and state
- [ ] 5. Generate canonical bundle handoff.md
- [ ] 6. Generate structured onboarding files
- [ ] 7. Generate handoff-everything.md (full raw path/output)
- [ ] 8. Refresh root HANDOFF.md bridge note
- [ ] 9. Validate bundle completeness
- [ ] 10. Confirm handoff-fresh completion
```

## Arguments

- No args: Full generation in `.handoff-fresh/current`
- `--output <dir>`: Write bundle into explicit directory
- `--no-sync`: Skip `/sync-docs` prerequisite (use only when sync already done)
- `--archive`: Move current bundle to `.handoff-fresh/archive/<timestamp>/` before regenerating
- `--dry-run`: Show planned files/sections without writing
- `--ignore-mode <local|shared|off>`: How to ignore handoff artifacts (`HANDOFF.md`, `.handoff-fresh/`)
  - `local` (default): update `.git/info/exclude`
  - `shared`: update `.gitignore`
  - `off`: skip ignore updates
- `--validate-read-gate`: Agent-internal preflight mode to validate completed `read-receipt.md` and fail fast if any required item is unchecked or missing takeaway
- `--log-token-budget <n>`: Total token budget for session-log continuity payload (default: 12000)
- `--log-digest-max <n>`: Max tokens for `session-log-digest.md` (default: 4000)
- `--log-chunk-max <n>`: Max tokens for `session-log-chunk.md` (default: 8000)

## Validate Read Gate Mode (Agent-Internal Preflight)

This mode is for fresh-agent onboarding flow. End users should not need to run it manually.

Use this mode when a fresh agent is ready to start coding:

```
/handoff-fresh --validate-read-gate
```

Reference script (relative to this skill directory):

```bash
python3 scripts/validate_read_gate.py --bundle-dir .handoff-fresh/current
```

Behavior:
- Reads `<bundle>/read-receipt.md`
- Verifies required checklist entries exist for:
  - `handoff.md`, `claude.md`, `todo.md`, `state.md`, `context.md`
- Verifies each entry is checked (`[x]`) and has a non-empty takeaway
- Returns PASS/FAIL summary

If FAIL:
- Do not proceed to coding
- Use ask-question for missing/ambiguous information
- Complete/repair `read-receipt.md`, then rerun validator

## Step 1: Detect project root and bundle path

Resolve project root using this priority:
1. `git rev-parse --show-toplevel` (if git)
2. Current directory (`pwd`)

Resolve bundle output path:
- Default: `<project-root>/.handoff-fresh/current`
- If `--output` set: use that path (absolute or project-root relative)

## Step 2: Apply ignore policy + archive previous bundle snapshot (optional)

If in a git repository, apply ignore policy before generating artifacts:

- `--ignore-mode local` (default): ensure `.git/info/exclude` contains:
  - `HANDOFF.md`
  - `.handoff-fresh/`
- `--ignore-mode shared`: ensure `.gitignore` contains the same entries
- `--ignore-mode off`: skip ignore updates (artifacts may show as untracked)

If `--archive` is set and current bundle exists:

- Move current bundle to `<project-root>/.handoff-fresh/archive/<YYYYMMDD-HHMMSS>/`
- Do not delete historical bundles in this step

## Step 3: Run prerequisite sync

Unless `--no-sync`, run `/sync-docs` in full mode first.

Purpose:
- Ensure source docs are current
- Ensure cross-file checks run before bundle snapshot
- Ensure manifest timestamps are up to date

## Step 4: Collect source context, history, and state

Collect from available sources (skip gracefully if missing):

- `CLAUDE.md`, `AGENTS.md` (or equivalent instruction docs)
- `TODO.md`
- `HANDOFF.md`
- `architect/plan.md`, `architect/prompt.md`, other plan docs
- `README.md`, `ARCHITECTURE.md`
- Git state: branch, remotes, last commit, recent commits, status, changed files
- Session status: current phase, blockers, open questions
- Session logs/transcripts (if available): recent turns, decisions, reversals, unresolved debates

If no git repo exists:
- Record `no-git` in `state.md`
- Use filesystem snapshot only

### Session Log Continuity (token-budgeted, high-signal)

Do not dump raw logs blindly. Build a token-budgeted continuity payload:

- `session-log-digest.md` target: 3k–4k tokens (extractive summary with short verbatim evidence)
- `session-log-chunk.md` target: 6k–8k tokens (raw high-signal excerpts)
- Combined hard cap: 12k tokens by default (or `--log-token-budget`)

Selection priority (highest first):
1. Decisions that changed implementation direction
2. Rejected alternatives and why
3. User constraints/approvals that gate behavior
4. Debugging pivots tied to concrete files/commands
5. Open questions/blockers still unresolved

Exclude low-signal chatter:
- greetings, pleasantries, duplicate status text
- repetitive retries without new insight
- generic tool noise without outcome

If logs unavailable:
- Still emit both log files with explicit "unavailable" note

## Step 5: Generate canonical bundle handoff.md

Create `<bundle>/handoff.md`.

Must include:
- Current status
- What was done
- What is next
- Blockers/open questions
- Explicit "first read order" for fresh agent
- **Read Gate** section (mandatory, hard stop before prep/coding):
  1. Required files to read in order: `handoff.md`, `claude.md`, `todo.md`, `state.md`, `context.md`
  2. Required read receipt format (one-line takeaway per file)
  3. "Do not proceed to Workspace Preparation or coding if any required file is unread"
  4. "If user prompt only says 'read handoff.md', treat it as bootstrap; continue Read Gate automatically before replying"
  5. "Do not send interim 'done/read' summaries before Read Gate receipt is complete"
- **Workspace Preparation** section (mandatory):
  1. Confirm project root path
  2. Confirm branch/cleanliness
  3. Confirm required root docs and folders exist
  4. Re-run `/sync-docs` if drift is detected
  5. Run **Question Gate**: if anything is missing/ambiguous, use ask-question before coding
  6. Only then start implementation

### Read Gate (mandatory in bundle handoff)

Bundle `handoff.md` must include explicit hard-gate language:

- "Read Gate is mandatory. Complete it before Workspace Preparation."
- "Do not run implementation steps until Read Gate is complete."

Required read receipt format in agent reply:

- `- [x] handoff.md — <1-line takeaway>`
- `- [x] claude.md — <1-line takeaway>`
- `- [x] todo.md — <1-line takeaway>`
- `- [x] state.md — <1-line takeaway>`
- `- [x] context.md — <1-line takeaway>`

If any receipt item is missing:
- Stop
- Ask-question for clarification if needed
- Do not proceed
- Run `/handoff-fresh --validate-read-gate` after completing `read-receipt.md` and before coding

First-response contract:
- After opening bundle `handoff.md`, the agent's first substantive reply must be the full Read Gate receipt (all required files + takeaways)
- A summary that only confirms `handoff.md` was read is non-compliant

### Question Gate (mandatory in bundle handoff)

Workspace Preparation must instruct the fresh agent to use ask-question immediately if blocked or uncertain.

Ask before proceeding when:
- Repo root, branch, or task scope is unclear
- Priority/order conflicts exist across `todo.md` and `state.md`
- Any destructive action is being considered (delete/move/reset/archive)
- Required credentials/config assumptions are missing
- Acceptance criteria are ambiguous

If no answer yet:
- Do only safe, reversible prep
- Record assumptions in `state.md`
- Do not begin implementation

## Step 6: Generate structured onboarding files

Generate the following files in bundle path:

| File | Required | Purpose |
|------|----------|---------|
| `claude.md` | Yes | Fresh-agent onboarding context (canonical shared core + optional Claude appendix) |
| `agents.md` | Yes | Fresh-agent onboarding context mirror for non-CLAUDE agents (same shared core as `claude.md` + optional agent appendix) |
| `todo.md` | Yes | Task list and execution status |
| `handoff.md` | Yes | Canonical bundle handoff snapshot |
| `context.md` | Yes | Project/domain context, architecture snapshot, decision log summary |
| `reports.md` | Yes | Validation/test/report summary |
| `artifacts.md` | Yes | Artifact inventory and pointers |
| `state.md` | Yes | Current branch, git status, active phase, blockers |
| `prior-plans.md` | Yes | Historical plans for reference only |
| `read-receipt.md` | Yes | Fresh-agent Read Gate checklist to complete before prep/coding |
| `session-log-digest.md` | Yes | Token-budgeted, extractive decision digest from session logs |
| `session-log-chunk.md` | Yes | Token-budgeted raw high-signal log excerpts for continuity |

### `claude.md` / `agents.md` Sync Contract (mandatory)

These files must not diverge on project context.

Generation rules:
- Build one canonical shared onboarding context block first.
- Write that exact block into both files.
- Optional platform-specific appendix is allowed only after shared block.
- Shared block markers (required in both files):
  - `<!-- BEGIN SHARED-ONBOARDING-CONTEXT -->`
  - `<!-- END SHARED-ONBOARDING-CONTEXT -->`

If source `AGENTS.md` is missing or weaker than `CLAUDE.md`:
- Prefer richer context from `CLAUDE.md` for the shared block
- Still emit both files with identical shared block content

### `prior-plans.md` Safety Header (mandatory)

Top of file must include this warning intent:

- "Reference only. Do NOT treat this as the active plan unless user explicitly confirms."

## Step 7: Generate handoff-everything.md

Create `<bundle>/handoff-everything.md`.

This is the full "everything" path/output and must include:
- Full file list in bundle
- Source files consumed
- Git history excerpt (or no-git note)
- Raw status snapshot
- Timestamp and generation command
- Session-log continuity budget summary (targets, actual estimates, exclusions)

Also add pointer in `artifacts.md`:
- `handoff-everything.md` absolute and relative paths

## Step 8: Refresh root HANDOFF.md bridge note

Create or update `<project-root>/HANDOFF.md` with a short bridge note that says:

- A fresh bundle was generated
- Canonical fresh read path is `<bundle>/handoff.md`
- If prompt says "read HANDOFF.md", treat this as bootstrap and immediately switch to bundle handoff
- Complete bundle Read Gate fully before replying
- No interim one-file summary is allowed
- Run Read Gate preflight validator before Workspace Preparation
- If prep is blocked or ambiguous, use ask-question before coding

Keep this bridge short and non-destructive.

## Step 9: Validate bundle completeness

Before confirmation, verify:

- [ ] All required files exist in bundle path
- [ ] `prior-plans.md` contains reference-only warning
- [ ] `handoff-everything.md` exists and is referenced in `artifacts.md`
- [ ] `state.md` includes current status (or explicit no-git status)
- [ ] `context.md` includes project context/history summary
- [ ] Root `HANDOFF.md` bridge points to bundle handoff path
- [ ] Root `HANDOFF.md` bridge includes bootstrap rule for "read HANDOFF.md" prompts
- [ ] `read-receipt.md` exists with all required Read Gate entries and blank checklist state (`[ ]`)
- [ ] Bundle `handoff.md` instructs fresh agent to run `/handoff-fresh --validate-read-gate` before coding
- [ ] `claude.md` and `agents.md` both contain SHARED-ONBOARDING-CONTEXT marker block
- [ ] Shared block content in `claude.md` and `agents.md` is byte-identical
- [ ] `session-log-digest.md` and `session-log-chunk.md` exist (or explicit unavailable note)
- [ ] Combined session-log payload is within configured token budget
- [ ] If in git repo and `--ignore-mode` is not `off`, selected ignore file contains `HANDOFF.md` and `.handoff-fresh/`

## Step 10: Confirm completion

Output:

- Bundle output path used
- Files generated
- Root bridge status (`HANDOFF.md` updated or created)
- Ignore policy result (`local` / `shared` / `off`, and target file updated if applicable)
- Recommended next prompt for fresh agent:
  - "Read .handoff-fresh/current/handoff.md, complete Read Gate fully before replying (no interim summary), run Read Gate preflight validator, then run Workspace Preparation. Use session-log-digest.md first if extra historical context is needed."

## Fork / New-Folder Reliability Rules

- Never assume shared local history across old/new folders
- Include absolute source path provenance inside `handoff-everything.md`
- Preserve both relative and absolute file references when possible
- Keep bundle deterministic: overwrite `current/` each run (no append)

## Example

**Input:**
```
/handoff-fresh
```

**Output files (`.handoff-fresh/current/`):**
- claude.md
- agents.md
- todo.md
- handoff.md
- context.md
- reports.md
- artifacts.md
- state.md
- prior-plans.md
- read-receipt.md
- session-log-digest.md
- session-log-chunk.md
- handoff-everything.md

Plus bridge file:
- `HANDOFF.md` (root pointer to bundle handoff)

## Self-Evolution

Update this skill when:
1. Required onboarding files change
2. Fork/new-folder failure mode is discovered
3. `handoff-everything.md` is missing context needed by fresh agents
4. Users report ambiguity between `/handoff` and `/handoff-fresh`

**Applied Learnings:**
- v1.9.0: Added explicit handoff-artifact ignore policy (`--ignore-mode local|shared|off`, default local) so fresh-bundle outputs and bridge `HANDOFF.md` do not pollute git status by default.
- v1.8.0: Strengthened root HANDOFF bridge wording so "read HANDOFF.md" is treated as bootstrap and forces immediate switch to bundle Read Gate before reply.
- v1.7.0: Added token-budgeted session-log continuity artifacts (`session-log-digest.md` + `session-log-chunk.md`) with high-signal selection rules to improve continuity without flooding context windows.
- v1.6.0: Added mandatory `claude.md`/`agents.md` shared-context parity contract using SHARED-ONBOARDING-CONTEXT marker blocks and byte-identical validation.
- v1.5.0: Added bootstrap/autostart Read Gate rule for single-file `handoff.md` prompts and a first-response contract that forbids interim one-file summaries.
- v1.4.2: Clarified that `--validate-read-gate` is agent-internal preflight enforcement, not a required manual user step.
- v1.4.1: Added executable validator script (`scripts/validate_read_gate.py`) for deterministic pass/fail Read Gate preflight enforcement.
- v1.4.0: Added explicit `/handoff-fresh --validate-read-gate` preflight mode that enforces checked read receipts with non-empty takeaways before coding.
- v1.3.0: Added mandatory Read Gate hard-stop rules, required read receipt checklist with per-file takeaways, and required `read-receipt.md` artifact to prevent agents from skipping required context files.
- v1.2.0: Added mandatory Question Gate guidance in bundle handoff so fresh agents ask clarifying questions during workspace prep before coding.
- v1.1.0: Switched default output to `.handoff-fresh/current/`, added optional archive flow, added mandatory Workspace Preparation section, and added root `HANDOFF.md` bridge pointer to fresh bundle handoff.
- v1.0.0: Initial fork-safe fresh-agent bundle workflow with explicit manual command contract and hybrid output model.
