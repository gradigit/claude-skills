# Steering File Templates

Templates for the two human-to-agent communication channels. Created by the orchestrator at startup if missing.

---

## HUMAN-INPUT.md

Human writes brainstorming ideas, feature suggestions, and new work items. Orchestrator checks at every milestone boundary and phase transition.

New entries are integrated as:
- New milestones (if significant enough)
- Additions to the current milestone scope
- New entries in SUGGESTIONS.md (if ideas, not directives)

```markdown
# Human Input

## New
<!-- Write new items here. Agent will process and move to Processed. -->


## Processed
<!-- Agent moves items here after integrating them. -->
```

**Example with entries**:
```markdown
# Human Input

## New
- Consider adding a caching layer to the API — I've seen performance issues in production
- Bug: the login flow breaks when email has a + character

## Processed
- [2026-03-03 14:22] Added caching investigation to Milestone 3 research phase
- [2026-03-03 14:22] Added login bug fix to Milestone 2 as urgent task
```

---

## MISSION-CONTROL.md

Human writes steering directives, priority changes, stop/start orders. This is the "steering wheel" for long-running autonomous sessions. Orchestrator checks at every phase transition.

```markdown
# Mission Control

## Active Directives
<!-- Human writes steering directives here. Agent acknowledges and follows. -->


## Acknowledged
<!-- Agent moves processed directives here with timestamp and action taken. -->
```

**Example with entries**:
```markdown
# Mission Control

## Active Directives
- PRIORITY: Focus on the auth module first, defer the dashboard work
- STOP: Don't refactor the payment service — it's being replaced next sprint
- NOTE: The CI pipeline is flaky right now, don't block on test failures for integration tests

## Acknowledged
- [2026-03-03 14:30] PRIORITY acknowledged — reordered milestones, auth is now Milestone 1
- [2026-03-03 14:35] STOP acknowledged — payment service excluded from scope
```

**Directive types**: PRIORITY (reorder work), STOP (exclude from scope), NOTE (adjust behavior), FOCUS (narrow scope), EXPAND (widen scope).

---

## Write Ownership

- `## New` / `## Active Directives`: human-written exclusively
- `## Processed` / `## Acknowledged`: orchestrator-written exclusively
- The orchestrator never modifies the human-written sections — it only reads them and moves items to the processed section

---

## SUGGESTIONS.md

SUGGESTIONS.md is a **bidirectional async communication channel** between agent and human. The agent writes suggestions; the human writes feedback (approved/rejected/needs-revision). Created by forge-builder when suggestions arise during building.

For the full SUGGESTIONS.md template and lifecycle, see [suggestions-template.md](../forge-builder/suggestions-template.md).

The orchestrator checks SUGGESTIONS.md at every phase transition and during the COMPOUND step.
