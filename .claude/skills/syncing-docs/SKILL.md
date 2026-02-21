---
name: syncing-docs
description: Detects drift between code and all project state files. Fixes docs it owns (CLAUDE.md, AGENTS.md, README.md, ARCHITECTURE.md). Flags inconsistencies in files owned by other skills (TODO.md, HANDOFF.md, architect/, handoff-fresh bundle files). Captures session learnings into CLAUDE.md and AGENTS.md. Activates when user asks to "sync docs", "update docs", "refresh docs", or uses /sync-docs. Supports --dry-run, --quick, and --refresh-fresh-bundle.
license: MIT
metadata:
  version: "2.6.0"
  author: gradigit
  tags:
    - documentation
    - sync
    - drift-detection
  triggers:
    - "/sync-docs"
    - "sync docs"
    - "update docs"
    - "refresh docs"
---

# Syncing Docs

Detects drift between code and project state files. Fixes docs it owns, flags inconsistencies in files it doesn't, and captures session learnings.

## Workflow

```
- [ ] 1. Detect project context (git? manifest? state files?)
- [ ] 2. Identify what changed since last sync
- [ ] 3. Map changes to affected files
- [ ] 4. Fix drift in owned docs (or preview if --dry-run)
- [ ] 5. Capture session learnings into CLAUDE.md + AGENTS.md (skip if --quick)
- [ ] 6. Cross-file consistency check (skip if --quick)
- [ ] 7. Update .doc-manifest.yaml
- [ ] 8. Refresh handoff-fresh bundle (optional)
- [ ] 9. Show summary
```

## Arguments

- `--dry-run`: Preview all changes without applying edits
- `--quick`: Drift fix only — skip session learnings (step 5) and cross-file checks (step 6)
- `--refresh-fresh-bundle`: After sync, run `/handoff-fresh --no-sync` so fresh-agent onboarding files are regenerated from latest docs/state
- No args: Full sync — drift fix + session learnings + cross-file consistency

## File Ownership

This skill has two relationships with files: **owned** (can edit) and **watched** (read-only, flag only).

| File | Relationship | Owner Skill |
|------|-------------|-------------|
| CLAUDE.md (key files, commands, architecture, code style) | **Owned** | syncing-docs |
| AGENTS.md (agent policies, command behavior, shared project context) | **Owned** | syncing-docs |
| README.md | **Owned** | syncing-docs |
| ARCHITECTURE.md, docs/ARCHITECTURE.md | **Owned** | syncing-docs |
| docs/**/*.md | **Owned** | syncing-docs |
| .doc-manifest.yaml | **Owned** | managing-doc-manifest (invoked) |
| TODO.md | Watched | forging-plans / execution |
| HANDOFF.md | Watched | handoff |
| .handoff-fresh/current/claude.md | Watched | handoff-fresh |
| .handoff-fresh/current/agents.md | Watched | handoff-fresh |
| .handoff-fresh/current/todo.md | Watched | handoff-fresh |
| .handoff-fresh/current/handoff.md | Watched | handoff-fresh |
| .handoff-fresh/current/context.md | Watched | handoff-fresh |
| .handoff-fresh/current/reports.md | Watched | handoff-fresh |
| .handoff-fresh/current/artifacts.md | Watched | handoff-fresh |
| .handoff-fresh/current/state.md | Watched | handoff-fresh |
| .handoff-fresh/current/prior-plans.md | Watched | handoff-fresh |
| .handoff-fresh/current/read-receipt.md | Watched | handoff-fresh |
| .handoff-fresh/current/session-log-digest.md | Watched | handoff-fresh |
| .handoff-fresh/current/session-log-chunk.md | Watched | handoff-fresh |
| .handoff-fresh/current/handoff-everything.md | Watched | handoff-fresh |
| architect/plan.md | Watched | forging-plans |
| architect/prompt.md | Watched | forging-plans |

**Rule: Never edit watched files.** Only report issues.

## Step 1: Detect Project Context

```bash
# Check for git
git rev-parse --git-dir 2>/dev/null

# Check for existing manifest
cat .doc-manifest.yaml 2>/dev/null
```

### Auto-Discovery

Scan for all project state files:

**Owned docs:**
- `CLAUDE.md` (project root + nested directories)
- `AGENTS.md` (project root + nested directories)
- `README.md`
- `ARCHITECTURE.md`, `docs/ARCHITECTURE.md`
- `docs/**/*.md`
- `CHECKLIST.md`, `CHANGELOG.md`
- Any `.md` files in project root (except watched files)

**Watched state files:**
- `TODO.md`
- `HANDOFF.md`
- `architect/*.md` (plan.md, prompt.md, transcript.md)

### With Manifest

Read `.doc-manifest.yaml` for explicit file list and code references.

## Step 2: Identify Changes

### Git Projects

```bash
# Changes since last sync (use manifest last_synced if available)
git log --since="<last_synced>" --name-only --pretty=format: | sort -u

# Fallback: unstaged + staged changes
git diff --name-only HEAD

# Fallback: compare with last commit
git diff --name-only HEAD~1
```

**Key improvement over v1:** Use manifest `last_synced` timestamp to capture all cumulative changes, not just the latest commit.

### Non-Git Projects (Timestamp Fallback)

Compare file modification times:
- For each doc, check timestamps of code files it references
- If any referenced code file is newer than the doc → stale
- If no manifest, scan `src/`, `lib/`, `config/`, `main.*` for recent changes

## Step 3: Map Changes to Docs

| Changed File Pattern | Affected Doc Sections |
|---------------------|----------------------|
| `src/**/*.py`, `lib/**/*.js`, `src/**/*.ts` | CLAUDE.md + AGENTS.md (key files, architecture), ARCHITECTURE.md |
| `tests/**/*`, `test/**/*` | CLAUDE.md + AGENTS.md (commands/testing) |
| `*.yaml`, `*.json`, `*.toml` (config) | CLAUDE.md + AGENTS.md (configuration/policies) |
| `main.py`, `cli.py`, `index.*`, `app.*` | CLAUDE.md + AGENTS.md (commands), README.md (usage) |
| `requirements.txt`, `package.json`, `Cargo.toml`, `go.mod` | README.md (setup/installation) |
| `Makefile`, `Taskfile.*`, `justfile`, `scripts/**` | CLAUDE.md + AGENTS.md (commands) |
| `Dockerfile`, `docker-compose.*`, `*.dockerfile` | README.md (setup), ARCHITECTURE.md |
| `__init__.py`, `index.ts` (barrel files) | CLAUDE.md + AGENTS.md (architecture/exports) |
| `docs/**/*.md` | Cross-reference consistency between docs |

### Code Element Reference Tracking

For all discovered files (owned + watched), extract code references:
- File paths in backticks or plain text (e.g., `src/validators/preflight.py`)
- Function/class names in backticks (e.g., `PreflightValidator`)
- CLI commands and flags (e.g., `--strict`)

Cross-reference against the codebase:
- **Renamed**: Symbol exists under a new name in git history → auto-fix in owned files, flag in watched
- **Deleted**: Symbol no longer exists anywhere → flag for review
- **New**: Significant new symbol not referenced in any doc → suggest adding

## Step 4: Fix Drift in Owned Docs

### Auto-Fix (apply directly)

- **Broken file paths**: File renamed/moved → update path
- **Stale commands**: CLI flag renamed, test directory changed → update command
- **Missing new files**: New significant module in src/ → add to Key Files
- **Outdated counts**: Doc says "12 modules" but now 14 → update number
- **Renamed symbols**: Function/class renamed → update references

### Flag for Review (report only)

- **Deleted code**: File referenced in doc was deleted → "REVIEW: Remove section or update?"
- **Major refactor**: Module structure changed significantly → "REVIEW: Architecture may need rewrite"
- **Semantic changes**: Function signature changed but name didn't → "REVIEW: Description may be outdated"

### Execution Model

1. **Scan in main context** — session-aware, knows what was just worked on
2. **Spawn Task agent** with explicit per-file edit instructions
3. Task agent uses Edit tool for each modification

If `--dry-run`: Skip Task agent. Output planned changes as preview.

## Step 5: Capture Session Learnings

**Skip if `--quick`.**

Reflect on the current session and add useful context to instruction docs:

### What to capture
- Bash commands that were used or discovered
- Code style patterns followed
- Testing approaches that worked
- Environment/configuration quirks
- Warnings or gotchas encountered

### Guidelines
- **One line per concept** — CLAUDE.md is part of the prompt, brevity matters
- Format: `<command or pattern>` - `<brief description>`
- Avoid verbose explanations, obvious information, one-off fixes unlikely to recur

### Placement
- `CLAUDE.md` — team-shared context and architecture learnings (checked into git)
- `AGENTS.md` — agent-execution policy and workflow learnings (checked into git)
- `.claude.local.md` — personal/local preferences (gitignored)

If both CLAUDE.md and AGENTS.md exist:
- Keep shared project context synchronized.
- Allow platform-specific appendices only where explicitly needed.

### Approval
Show proposed additions as diffs. Ask user before applying:

```
### Session Learnings → CLAUDE.md + AGENTS.md

**Why:** Discovered during this session

+ `python -m pytest test/ -x --tb=short` - fast test with short traceback
+ Chain normalization uses 3-tier lookup: alias → canonical → fallback
```

Apply only what user approves.

## Step 6: Cross-File Consistency Check

**Skip if `--quick`.**

Scan watched files for issues without editing them.

### Broken References in Watched Files
- File paths in TODO.md, HANDOFF.md, architect/*.md that no longer exist
- Function/class names that were renamed or deleted
- Commands that no longer work
- Validate handoff-fresh bundle file set under `.handoff-fresh/current/`

### Cross-File Contradictions
- TODO.md says "Phase 3 in progress" but CLAUDE.md says "Current Phase: 2"
- TODO.md says "Phase 3 in progress" but AGENTS.md says "Current Phase: 2"
- HANDOFF.md references files that were deleted since it was written
- architect/plan.md step marked as next but TODO.md shows it completed
- CLAUDE.md key files table missing files that TODO.md references as created
- CLAUDE.md and AGENTS.md shared project context disagree on current phase/commands
- `.handoff-fresh/current/claude.md` and `.handoff-fresh/current/agents.md` shared onboarding context block differs (fresh-agent context parity drift)

### Staleness Alerts
- HANDOFF.md last modified > 10 commits ago → "Consider running /handoff"
- TODO.md has items marked "in progress" for tasks that appear complete in code → flag
- architect/plan.md references phase N but code appears to be past that → flag
- handoff-fresh bundle under `.handoff-fresh/current/` present but older than source docs/state files → "Consider running /handoff-fresh"

### Output Format
```
Cross-File Issues:
  TODO.md:
    - References src/old_module.py (deleted in commit abc1234)
    - "Phase 2 in progress" but CLAUDE.md says Phase 3
  HANDOFF.md:
    - 23 commits old — consider running /handoff
    - References src/utils/helpers.py (renamed to src/utils/common.py)
```

## Step 7: Update Manifest

Invoke the managing-doc-manifest skill (or update `.doc-manifest.yaml` directly):
- Set `last_synced` to current timestamp
- Update `last_updated` for each modified doc
- Add any newly discovered doc files
- Update `references` based on code files actually checked

## Step 8: Refresh handoff-fresh bundle (optional)

Only if user explicitly requested `--refresh-fresh-bundle`:

1. Run `/handoff-fresh --no-sync` in the same project root
2. Confirm required bundle files were re-generated
3. Include generated bundle output path in summary

If not requested, do nothing.

## Step 9: Show Summary

```
=== Docs Sync Summary ===

Drift Fixed:
  CLAUDE.md:
    - Commands: added --strict flag documentation
    - Key Files: added src/validators/preflight.py
    - Fixed: tests/ → test/ path correction
  AGENTS.md:
    - Commands: mirrored --strict flag documentation
    - Policies: synced shared project context with CLAUDE.md

Session Learnings:
  CLAUDE.md + AGENTS.md:
    + Added 2 synchronized entries (commands, gotcha)

Cross-File Issues:
  TODO.md: 1 broken reference, 1 phase mismatch
  HANDOFF.md: 23 commits stale — run /handoff

Flagged for Review:
  ARCHITECTURE.md:
    - src/old_module.py deleted but still referenced (line 78)

Manifest: .doc-manifest.yaml updated (5 files tracked)

Fresh Bundle:
  regenerated via /handoff-fresh --no-sync
  output: ./.handoff-fresh/current/
```

## CLAUDE.md Sections to Maintain

| Section | Synced From |
|---------|------------|
| Commands | CLI entry points, test runners, build scripts, Makefile targets |
| Key Files | Most-imported or most-changed files in src/ |
| Architecture | Directory structure, module relationships, data flow |
| Code Style | Language version, formatter config, conventions |
| Domain Edge Cases | Special handling in code comments/logic |

## AGENTS.md Sections to Maintain

| Section | Synced From |
|---------|------------|
| Command Behavior | CLI entry points, workflow gates, execution constraints |
| Shared Project Context | Aligned with CLAUDE.md shared context |
| Agent Policies | Safety constraints, sequencing requirements, handoff protocol |

## Example

**Input:** `/sync-docs`

**Context:** User just added `src/validators/preflight.py`, updated `main.py` with `--strict` flag, and discovered a useful pytest invocation.

**Output:**
```
=== Docs Sync Summary ===

Drift Fixed:
  CLAUDE.md:
    - Commands: added --strict flag
    - Key Files: added src/validators/preflight.py
    - Architecture: added preflight step to data flow
  AGENTS.md:
    - Commands: added --strict flag
    - Shared context: synced with CLAUDE.md updates

Session Learnings:
  CLAUDE.md + AGENTS.md:
    + `pytest test/ -x --tb=short` - fast test with short traceback

Cross-File Issues:
  HANDOFF.md: 15 commits stale — consider /handoff

Flagged for Review:
  (none)

Manifest: .doc-manifest.yaml updated (2 files tracked)
```

**Quick mode:** `/sync-docs --quick`

Runs steps 1-4, 7, 9. Step 8 runs only when `--refresh-fresh-bundle` is explicitly provided. No session learnings, no cross-file checks.

## Self-Evolution

Update this skill when:
1. **On missed staleness**: Doc was stale but skill didn't detect it → add detection rule to Step 3
2. **On false positive**: Skill flagged something that wasn't stale → refine mapping
3. **On new state file**: Project uses a new state file pattern → add to auto-discovery
4. **On cross-file miss**: Inconsistency between files went undetected → add check to Step 6

**Applied Learnings:**
- v2.6.0: Added AGENTS.md as owned instruction doc and synchronized shared-context + session-learning maintenance across CLAUDE.md/AGENTS.md.
- v2.5.0: Added watched-file coverage for handoff-fresh `session-log-digest.md` and `session-log-chunk.md` continuity artifacts.
- v2.4.0: Added cross-file contradiction check for handoff-fresh `claude.md`/`agents.md` shared-context parity drift.
- v2.3.0: Added `.handoff-fresh/current/read-receipt.md` to watched-file drift checks so sync-docs can flag incomplete fresh-agent Read Gate artifacts.
- v2.2.0: Updated handoff-fresh bundle expectations to foldered model (`.handoff-fresh/current/`). Updated watched-file checks and summary output paths accordingly.
- v2.1.0: Added explicit `/sync-docs` command trigger. Added `--refresh-fresh-bundle` to regenerate handoff-fresh onboarding files after sync. Added watched-file staleness checks for handoff-fresh bundle and `handoff-everything.md`.
- v2.0.0: Merged session learnings capture from revise-claude-md. Added cross-file consistency checking for watched files (TODO.md, HANDOFF.md, architect/). Added code element reference tracking. Added --quick mode. Dropped template creation (scaffolding ≠ syncing). Added cumulative git history via manifest last_synced.
- v1.0.0: Initial version
