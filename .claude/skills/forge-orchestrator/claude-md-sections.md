# CLAUDE.md Forge Sections

The orchestrator adds these two sections to CLAUDE.md during intake (Step 1i). They serve distinct purposes — one guides the compaction summarizer, the other guides the agent after compaction.

---

## Section 1: Compact Instructions

Read by the compaction summarizer itself. Guides WHAT to preserve.

```markdown
## Compact Instructions
When compacting, preserve:
- The current forge pipeline stage and substep
- All file paths from the last 10 tool calls
- All test results and their pass/fail status
- Any error messages being actively debugged
- The exact milestone name and number from FORGE-STATUS.md
```

---

## Section 2: Forge Pipeline State

Read by the agent after compaction. Guides WHAT TO DO next.

```markdown
## Forge Pipeline State
After any context compaction, re-read these files immediately:
1. FORGE-HANDOFF.md — what you were doing when compaction occurred
2. FORGE-STATUS.md — current milestone and phase
3. TODO.md — task checklist with completion status
4. FORGE-MEMORY.md — cross-session learnings

Then continue from the point described in FORGE-HANDOFF.md "What's In Progress".
```

---

## Placement

- Add both sections near the end of CLAUDE.md, after existing project-specific content
- Do not overwrite existing CLAUDE.md content — append these sections
- If these sections already exist (resumption), verify they are current and leave them
