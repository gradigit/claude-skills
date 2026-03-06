# Milestone Template

Each milestone has explicit per-step success criteria. Without them, agents frequently skip steps or declare premature completion.

---

## Template

```markdown
## Milestone: {name}
- **Goal**: {what this milestone achieves — one sentence}
- **Dependencies**: {which milestones must complete first, or "none"}
- **Files in scope**: own: [{glob patterns}], read: [{glob patterns}], deny: [{glob patterns}]
- **Quality criteria**: {specific pass conditions for the quality gate}
- **Acceptance criteria** (reconciliation targets for GATE E):
  1. {criterion — specific, verifiable behavior}
     - Code: {file:line — filled after implementation}
     - Test: {test name — filled after implementation}
  2. {criterion}
     - Code: {file:line}
     - Test: {test name}
- **Research needed**: {unknowns to resolve before building, or "none"}
- **Steps**:
  1. {step name}
     - Success criteria: {concrete, verifiable condition proving this step is done}
     - Artifacts: {files/data this step produces for later steps}
  2. {step name}
     - Success criteria: {verifiable condition}
     - Artifacts: {files produced}
```

---

## Example

```markdown
## Milestone: Authentication Module
- **Goal**: Build JWT-based auth middleware with RS256 signing and refresh token rotation
- **Dependencies**: none
- **Files in scope**: own: [src/auth/*, src/middleware/auth.ts, tests/auth/*], read: [src/config/auth.ts, src/models/user.ts], deny: [src/routes/*]
- **Quality criteria**: All auth tests pass, tokens validate correctly, refresh rotation works end-to-end
- **Acceptance criteria**:
  1. JWT middleware validates RS256 tokens and returns 401 on invalid
     - Code: {filled by builder}
     - Test: {filled by builder}
  2. Refresh token rotation returns new access+refresh pair
     - Code: {filled by builder}
     - Test: {filled by builder}
  3. Old refresh tokens are invalidated after rotation
     - Code: {filled by builder}
     - Test: {filled by builder}
- **Research needed**: Best practices for refresh token rotation with Redis session store
- **Steps**:
  1. Research token rotation patterns
     - Success criteria: Research doc exists at architect/research/token-rotation.md with >=2 approaches compared
     - Artifacts: architect/research/token-rotation.md
  2. Implement JWT validation middleware
     - Success criteria: src/middleware/auth.ts exists, verifies RS256 tokens, returns 401 on invalid tokens
     - Artifacts: src/middleware/auth.ts
  3. Implement refresh token rotation
     - Success criteria: POST /auth/refresh returns new access+refresh pair, old refresh is invalidated
     - Artifacts: src/auth/refresh.ts, src/auth/token-store.ts
  4. Write tests
     - Success criteria: tests/auth/ has >=10 test cases covering valid, expired, malformed, and rotated tokens
     - Artifacts: tests/auth/auth.test.ts, tests/auth/refresh.test.ts
```

---

## Rules

- Every step MUST have a success criteria field — steps without criteria will be skipped or prematurely declared done
- Success criteria must be **verifiable** — the agent (or a reviewer) can check it without subjective judgment
- Artifacts must name specific files or directories, not vague descriptions
- Dependencies between milestones must be explicit — implicit ordering causes race conditions in parallel threads
- File scope ownership prevents two milestones from modifying the same files concurrently
- Every milestone MUST have acceptance criteria — they are the reconciliation targets for GATE E
- Acceptance criteria evidence (Code/Test fields) are filled by the builder and verified at goal reconciliation
- If a todo is merged into another item, status stays `in_progress` until the merged item's implementation covers the original criteria
