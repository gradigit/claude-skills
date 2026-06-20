# Handoff Templates

Templates used by the handoff skill. Referenced from SKILL.md.

The `<!-- HANDOFF-SCHEMA ... -->` marker on line 1 is **mandatory** — it lets the
`/pickup` consumer detect the schema version and producer and distinguish
skill-generated handoffs from hand-written ones.

## HANDOFF.md Template

```markdown
<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->
# Context Handoff — {YYYY-MM-DD}

Session summary for context continuity after clearing.

## First Steps (Read in Order)

1. Read CLAUDE.md — project context, conventions, current phase
2. Read AGENTS.md — agent operating policy and command behavior
3. Read TODO.md — task status, blockers, what's next
4. {Additional files specific to current task}

After reading these files, you'll have full context to continue.

## Bootstrap Read Rule (Mandatory)

If the user prompt only says "read HANDOFF.md", treat that as a bootstrap command for this list.

- This is a `/pickup` bootstrap — prefer running `/pickup` to get the full
  read-all + verify behavior.
- Continue by reading every file in **First Steps** before replying.
- Do not send interim "done/read handoff" summaries.
- First substantive reply must include a read receipt:
  - `- [x] <file> — <1-line takeaway>`
  - one line per First Steps file

## Session Summary

### What Was Done
{Bullet points of completed work this session}

### Current State
{Brief description of where things stand}
- Files modified: {list}
- Files created: {list}
- Last commit: {hash} — {message}

### What's Next
{Specific next steps, in priority order}
1. {First thing to do}
2. {Second thing}

### Failed Approaches
{Approaches tried that didn't work — prevents next session from repeating them}
- Tried {X} — didn't work because {Y}

### Open Questions / Blockers
{Any unresolved issues or decisions needed}

### Key Context
{Critical information that might not be in CLAUDE.md}
- {Pattern or convention discovered}
- {Gotcha or warning}

## Last Exchange (Verbatim)

> Quoted character-for-character so the next session resumes exactly where this
> one stopped. Do NOT paraphrase — this is the resume anchor `/pickup` reads first.
> Budget: keep this section under ~1500 tokens; if the last response was very long,
> quote the decision-bearing portion verbatim and summarize the rest in [brackets].
> Redact secrets/credentials that appeared in the turn (replace with «redacted»).

**Last user prompt:**
```
{verbatim last user message}
```

**Last assistant response:**
```
{verbatim last assistant message — or its decision-bearing excerpt if long}
```

**Load-bearing earlier directives** (verbatim, in order — standing instructions that still govern the work):
1. "{quoted directive}"
2. "{quoted directive}"

## Reference Files

| File | Purpose |
|------|---------|
| {path} | {description} |

## Verify Block

> Claims to re-check. `/pickup` runs these on resume before trusting the handoff's claims.
> Format: `claim | check-command | expected`. List the load-bearing claims a
> resuming agent must NOT trust blindly (build/test/health/branch state). Use N/A
> with a reason only if there is genuinely nothing to verify.

| Claim | Check command | Expected |
|-------|---------------|----------|
| On branch {branch}, HEAD {hash} | `git rev-parse --short HEAD` | {hash} |
| {N tests passing} | `{test command}` | {expected result} |
| {service/system healthy} | `{health-check command}` | {expected} |
```

## Confirmation Output Template

```
Handoff complete.

Files updated:
- HANDOFF.md (created/updated)
- {other files updated}
- Ignore policy: {local|shared|off} ({.git/info/exclude|.gitignore|none})

To continue:
1. /clear to reset context
2. Say: "/pickup" (or "Read HANDOFF.md and continue")

Last commit: {hash} — {message}
```

## Emergency Handoff Template

Abbreviated version for interrupted sessions. The verbatim Last Exchange matters
*most* here — it captures the exact mid-task intent.

```markdown
<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->
# Context Handoff — {YYYY-MM-DD} (Emergency)

Session interrupted mid-{task}. Resume from {exact point}.

## First Steps (Read in Order)

1. Read CLAUDE.md
2. Read AGENTS.md
3. Read TODO.md
4. {File being actively edited}

## State at Interruption
- Working on: {task description}
- Progress: {what was done vs what remains}
- Last commit: {hash} — WIP: Interrupted — {brief context}

## Last Exchange (Verbatim)
**Last user prompt:**
```
{verbatim last user message}
```
**Last assistant response:**
```
{verbatim last assistant message or decision-bearing excerpt}
```

## Resume From
{Exact instruction for where to pick up}
```

## Quick Handoff Template

Lightweight version for small tasks (bug fix, config change, single-file edit):

```markdown
<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->
# Context Handoff — {YYYY-MM-DD}

## First Steps (Read in Order)
1. Read CLAUDE.md
2. Read AGENTS.md
3. {Primary file being worked on}

## What Was Done
{1-3 bullet points}

## What's Next
{1-2 bullet points}

## Failed Approaches
{Omit if nothing failed}

## Last Exchange (Verbatim)
**Last user prompt:**
```
{verbatim last user message}
```
**Last assistant response:**
```
{verbatim last assistant message or decision-bearing excerpt}
```

## Last Commit
{hash} — {message}

## Bootstrap Read Rule
If prompt says "read HANDOFF.md", run `/pickup` (or read all First Steps files before replying; no interim one-file summary).
```
```
