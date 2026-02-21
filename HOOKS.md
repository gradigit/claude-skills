# Hooks and Command Wiring

This repo uses an explicit, command-driven model for handoff flows.

## Manual-Only Policy

- `/handoff` and `/wrap` are manual slash-command entry points
- `/handoff-fresh` is a separate manual slash-command entry point for fresh-agent onboarding bundles
- No implicit or side-channel hook behavior is required for these flows

## Recommended Hook Registration Mode

Use hooks only for notifications/telemetry, not to auto-run handoff logic.

Example intent:

```json
{
  "hooks": {
    "PreCompact": [],
    "SessionStart": [],
    "SessionEnd": []
  }
}
```

Then invoke commands explicitly:
- `/handoff`
- `/handoff-fresh`
- `/wrap`

If old auto-handoff hooks exist in a project:

1. Archive first (recommended)
2. Remove active registrations
3. Keep command paths explicit (`/handoff`, `/wrap`, `/handoff-fresh`)

## Archive-First Cleanup Policy

Before removing deprecated hook scripts:

- Move files to an archive path such as:
  - `.claude/hooks/archive/<YYYY-MM-DD>/`
- Preserve a short `README` note explaining why they were archived
- Only then remove references from settings/hook registration files

This preserves rollback ability and avoids destructive migration surprises.
