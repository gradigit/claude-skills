# Quality Gate Criteria

> "Validation is the only path to finality."

Never assume success or settle for unverified changes. A phase passes its quality gate when ALL applicable criteria are satisfied.

## Gate Criteria

### 1. Tests Pass

Run the project's test suite for the affected code paths.

| Condition | Action |
|-----------|--------|
| Test infrastructure exists and tests are relevant | Run tests — all must pass |
| Test infrastructure exists but no tests cover changes | Note gap in self-review, optionally write tests (this is an "improvement") |
| No test infrastructure at all | Skip this gate — do NOT fabricate test infrastructure unless the directive asks for it |

### 2. Lint/Format Clean

Run the project's configured linter and formatter.

| Condition | Action |
|-----------|--------|
| Linter/formatter configured (eslint, ruff, rustfmt, etc.) | Run it — output must be clean |
| No linter configured | Skip this gate |

### 3. Self-Review: No Critical Issues

Review own changes for critical issues. Critical means:

- **Broken functionality**: code that will not work as intended at runtime
- **Security vulnerabilities**: injection, auth bypass, secrets in code, unsafe deserialization
- **Data loss risks**: destructive operations without confirmation, missing backups, silent overwrites

Non-critical findings (style, naming, minor performance) are noted but do not block the gate.

### 4. Requirements Match

Verify that the changes satisfy the stated requirements for this phase:

- Every goal from the build directive is addressed
- No goal is partially implemented without documentation of what remains
- The implementation matches the agreed approach (no surprise architectural pivots)

### 5. No Regressions

Verify that existing functionality is not broken:

- If tests exist: test suite passes (covered by Gate 1)
- If no tests: manual review of changed files for unintended side effects
- Check imports, exports, and interfaces that other modules depend on

## Gate Failure Protocol

| Attempt | Action |
|---------|--------|
| 1st failure | Identify the failing criterion. Fix the issue. Re-run the gate. |
| 2nd failure | Review whether the approach is fundamentally flawed. Fix and re-gate. |
| 3rd failure | **Escalate to user** with: what failed, what was tried (both attempts), and suggested next steps. The task decomposition or requirements may need revision. |

## Gate Failure Report Format

When escalating after 3 failures:

```markdown
## Quality Gate Failure — {phase name}

### What Failed
- Gate: {which criterion}
- Details: {specific error or finding}

### Attempts
1. {what was tried first, why it didn't resolve}
2. {what was tried second, why it didn't resolve}

### Suggested Next Steps
- {option A}
- {option B}

### Context
- Files modified: {list}
- Tests affected: {list or "none"}
```

## Gate Pass Confirmation

When a gate passes, record it:

```markdown
- [x] Phase {N}: {name} — gate passed
  - Tests: {passed | N/A}
  - Lint: {clean | N/A}
  - Self-review: clear
  - Requirements: satisfied
  - Regressions: none detected
```

Update TODO.md with this confirmation after each passed gate.
