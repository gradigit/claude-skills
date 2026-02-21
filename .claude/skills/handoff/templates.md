# Handoff Templates

Templates used by the handoff skill. Referenced from SKILL.md.

## HANDOFF.md Template

```markdown
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

## Reference Files

| File | Purpose |
|------|---------|
| {path} | {description} |
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
2. Say: "Read HANDOFF.md and continue"

Last commit: {hash} — {message}
```

## Emergency Handoff Template

Abbreviated version for interrupted sessions:

```markdown
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

## Resume From
{Exact instruction for where to pick up}
```

## Quick Handoff Template

Lightweight version for small tasks (bug fix, config change, single-file edit):

```markdown
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

## Last Commit
{hash} — {message}

## Bootstrap Read Rule
If prompt says "read HANDOFF.md", read all First Steps files before replying; no interim one-file summary.
```
