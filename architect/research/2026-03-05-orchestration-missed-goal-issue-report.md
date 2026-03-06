---
title: "Orchestration Gap Report: Missed Hybrid Typora Mode Goal"
date: 2026-03-05
severity: high
owner: forge-orchestrator
status: resolved
---

# Orchestration Gap Report: Missed Hybrid Typora Mode Goal

## Summary
A user-requested goal (caret-proximate hybrid Typora-like markdown syntax expansion mode) was treated as complete in todo tracking, but was not actually implemented in code.

## User Impact
- Repeated user frustration and trust erosion.
- False confidence from green tests despite missing expected behavior.
- Manual QA burden shifted to the user.

## Confirmed Evidence

### 1) Missing mode in implementation
`NativeEditorSyntaxVisibilityMode` contains only:
- `wysiwyg`
- `markdown`

No hybrid/caret-proximate mode exists.

### 2) Todo status drift (false completion)
Todo item for caret-proximate mode was marked complete/merged into related work even though acceptance criteria were unchecked and behavior absent.

### 3) Tests do not cover hybrid behavior
Current syntax visibility tests validate only WYSIWYG vs full markdown syntax visible mode.
No tests exist for:
- inline syntax expansion near caret,
- collapse when leaving span,
- no-style-leak transitions,
- matrix/stateful permutations with hybrid enabled.

## Root Cause Analysis
1. **Merged scope interpreted as completed scope**
   - “Merged into another todo” was operationally treated as “done” without implementation verification.

2. **No requirement-to-evidence completion gate**
   - Milestone close lacked strict checks tying user goals to code + tests + runtime proof.

3. **Firefighting priority drift**
   - Crash/perf work consumed loop budget; pinned feature goals were not re-validated before closure.

4. **Coverage blind spot**
   - Test suite had no failing guardrail for missing hybrid feature.

## Process/Skillset Fixes Required

### A. Done Definition Hard Gate (mandatory)
A goal cannot be closed unless each acceptance criterion has:
- code evidence (file:line),
- automated test evidence (named test),
- runtime/manual verification evidence.

### B. “Merged != Complete” policy
If a todo is merged into another item, status must remain `pending` or `in_progress` until behavior ships.

### C. Goal Reconciliation Gate at milestone close
Before marking complete, orchestrator must compare:
- explicit user goals,
- implemented behavior,
- evidence map.
Any mismatch blocks closure.

### D. Feature Presence Audit step
Add a required adversarial pass that checks:
- enums/settings/UI/control paths exist,
- behavior-specific tests exist and pass,
- claimed features are discoverable in code.

### E. Acceptance Criteria ↔ Test Mapping Table
Every criterion must map to one or more tests.
Missing mapping fails the quality gate.

### F. Pinned Request Escalation
If user repeats a request twice, mark as pinned critical and prevent closure until delivered.

## Suggested Skill Changes (forge-orchestrator)
1. Add explicit gate after QUALITY GATE and before COMPOUND:
   - `GOAL_RECONCILIATION_GATE`.
2. Enforce artifact:
   - `architect/review-findings/<milestone>-goal-reconciliation.md`.
3. Add hard failure condition:
   - no "complete" status if any pinned acceptance criterion lacks evidence.
4. Add a required “feature-presence reviewer” fan-out task in REVIEW phase.

## Immediate Follow-up Tasks
- Reopen hybrid Typora/caret-proximate mode as active milestone.
- Add failing tests first for caret-proximate behavior.
- Implement mode + preference + transitions.
- Re-run typing matrix/stateful sequences with hybrid permutations enabled.

## Verification Checklist
- [ ] Hybrid mode enum + persisted preference exists
- [ ] Caret-enter reveals span syntax (links/emphasis/code)
- [ ] Caret-leave collapses revealed syntax
- [ ] No link/style leakage after transition
- [ ] Typing behavior tests include hybrid permutations
- [ ] Todo status updated only after evidence is attached

