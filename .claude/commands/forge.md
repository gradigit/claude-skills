Launch the forge orchestrator pipeline. Read `.claude/skills/forge-orchestrator/SKILL.md` and follow its workflow.

If arguments are provided, use them as the goal:
- `/forge build the auth module` → orchestrate a full build
- `/forge research caching strategies` → orchestrate focused research

If no arguments, check for existing state files (FORGE-STATUS.md, FORGE-HANDOFF.md) and resume or prompt for a goal.

$ARGUMENTS
