# Suggestions Template

Use this format when writing entries to SUGGESTIONS.md. The file is a bidirectional async communication channel — the agent writes suggestions, the human writes feedback.

## Template

```markdown
# Suggestions

## {Feature Title}
- **Confidence**: {1-5} — {rationale for score}
- **Type**: new-feature | enhancement | optimization
- **Impact**: {what it improves and for whom}
- **Effort**: small | medium | large
- **Research**: {summary of research done, sources if any}
- **Plan**: {implementation approach — 2-5 sentences}
- **Files affected**: {list of files that would be created or modified}
- **Dependencies**: {what must exist first — other features, infrastructure, etc.}
- **Status**: proposed | researched | planned | ready-for-review | approved | rejected | implemented

### Human Feedback
<!-- Human: write comments, approve, or reject below. Agent reads this on each pass. -->
- Decision: {approved | rejected | needs-revision}
- Comments: {any notes, constraints, or direction from human}
```

## Status Lifecycle

| Status | Who Sets It | Meaning |
|--------|------------|---------|
| `proposed` | Agent | Initial suggestion created |
| `researched` | Agent | Agent has investigated feasibility |
| `planned` | Agent | Agent has drafted implementation plan |
| `ready-for-review` | Agent | Agent has self-reviewed the plan, ready for human decision |
| `approved` | Human (via Human Feedback) | Human approves — agent implements in next cycle |
| `rejected` | Human (via Human Feedback) | Human rejects — agent skips, leaves for reference |
| `needs-revision` | Human (via Human Feedback) | Human wants changes — agent refines and cycles to `planned` |
| `implemented` | Agent | Approved suggestion has been built |

## Example Entry

```markdown
## Rate Limiting Middleware
- **Confidence**: 4 — the API has no rate limiting and is publicly exposed; standard practice
- **Type**: new-feature
- **Impact**: prevents abuse and protects backend resources; benefits all API consumers
- **Effort**: small
- **Research**: Express rate-limit package is mature (15M weekly downloads). Redis-backed store needed for multi-instance deployments. Current project uses Express 4 + single instance.
- **Plan**: Install express-rate-limit. Create src/middleware/rate-limit.ts with configurable windows (default: 100 req/15min). Apply globally via app.use(). Add per-route overrides for auth endpoints (stricter) and health checks (exempt).
- **Files affected**: src/middleware/rate-limit.ts (new), src/app.ts (modified), package.json (modified)
- **Dependencies**: none — can be implemented independently
- **Status**: ready-for-review

### Human Feedback
<!-- Human: write comments, approve, or reject below. Agent reads this on each pass. -->
- Decision: approved
- Comments: Good call. Use 50 req/15min for auth endpoints. Skip Redis for now — single instance is fine.
```

## Write Ownership Rules

- **Agent-authored sections** (everything except Human Feedback): only the main builder thread or orchestrator writes these. Sub-agents return suggestions inline; the orchestrator collects and appends.
- **Human Feedback section**: exclusively human-written. The agent reads it but NEVER modifies it.
- **Deduplication**: the orchestrator merges suggestions from different agents that describe the same feature. If two agents suggest conflicting approaches, note both with rationale.
- **Sorting**: keep suggestions sorted by confidence score (highest first).
