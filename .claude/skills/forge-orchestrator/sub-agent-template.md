# Sub-Agent Prompt Template

All sub-agent prompts in the forge pipeline use this 7-tag XML template. It implements 5 conceptual concerns (task, context, scope/boundaries, output contract, quality assurance) as 7 XML tags for optimal information ordering.

---

## Template

```xml
<agent-prompt>

<objective>
{1-3 sentences describing the end state. End-state, not procedure.
"Build X that passes Y" beats "First do A, then B, then C."}
</objective>

<context>
{Minimal, task-specific. Maximum 2000 tokens. Only what this agent needs.
Fresh, minimal context — not the orchestrator's full history.}
</context>

<output-format>
---
status: complete | blocked | partial
confidence: high | medium | low
evidence: [{file paths, line numbers, URLs}]
---

## Result
{Structured content per role-specific contract}

## Verification
{How the agent verified its own output}
</output-format>

<tools>
{Explicit but neutral tool guidance. List only relevant tools.
"Use Read to examine files before modifying them."
NOT "You MUST use tools" or "ALWAYS call a tool."}
</tools>

<boundaries>
FILE SCOPE:
  own: [{glob patterns this agent may create/modify}]
  read: [{glob patterns for read-only reference}]
  deny: [{glob patterns that must never be touched}]

ALWAYS:
- {mandatory behavior 1}
- {mandatory behavior 2}
NEVER:
- Modify files outside the FILE SCOPE own list
- {hard prohibition}
ASK FIRST:
- {action requiring orchestrator approval}
</boundaries>

<quality-bar>
Before returning output, verify:
- [ ] Output matches the schema in output-format exactly
- [ ] All file references use absolute paths and exist
- [ ] Confidence level is justified by evidence
- [ ] No placeholder text remains
</quality-bar>

<task>
{Concrete action instruction — goes LAST per information ordering.
Specific: "Analyze src/auth/ for SQL injection vulnerabilities"
NOT "Review the code."}
</task>

</agent-prompt>
```

---

## Tag Rationale

| Tag | Position | Purpose |
|-----|----------|---------|
| `<objective>` | First | Critical content at start (lost-in-the-middle mitigation) |
| `<context>` | Second | Reference material for the task |
| `<output-format>` | Middle | Schema for structured return |
| `<tools>` | Middle | Neutral tool guidance (prevents overtriggering) |
| `<boundaries>` | Middle | Structured FILE SCOPE (own/read/deny) + three-tier constraints |
| `<quality-bar>` | Near end | Pre-flight verification checklist |
| `<task>` | Last | Critical content at end (30% improvement from end placement) |

---

## Role-Specific Contracts

**Research worker**: hypothesis-driven, source citations per-claim, counter-evidence included. Output: findings table with confidence + evidence columns.

**Build worker**: end-state objective from spec, run tests after each change, self-review checklist, temperature 0.0, step limit 60 tool calls.

**Adversarial reviewer**: confidence >80% threshold, file:line evidence + code snippet per finding, severity-confidence matrix (S3C3=critical, S2C2=warning, S1C1=info). Include >=1 positive observation.

**Performance auditor**: every finding backed by profiling data, before/after metrics, exact commands to reproduce. Never "feels slow" without measurements.

**Brainstorm agent**: scope budget (max N proposals), effort + impact + trade-offs per proposal, ranked by impact/effort ratio.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|-------------|--------------|
| "You are an expert {role}" without behavioral instructions | Role prompting alone has no measurable accuracy effect |
| "Think step by step" on all tasks | CoT degrades performance up to 36.3% on pattern recognition |
| Dumping full project context | Context rot: 20-50% accuracy drop at large sizes |
| "You MUST use tools", "ALWAYS call a tool" | Overtriggering — unnecessary tool calls |
| Burying the task in the middle | Lost-in-the-middle: 30%+ degradation |
| Vague constraints ("be efficient") | Explicit constraints produce 9x less output variance |
| "Don't do X" as primary instruction | Positive framing outperforms negative |
| Loading all steering files at spawn | Wastes context budget, violates progressive disclosure |
| More than 3 few-shot examples | Diminishing returns after 2 |
| Complex conditional guardrails | Compound rules are partially followed or ignored |
| Review prompts without confidence thresholds | Overcorrection bias: excessive false positives |

---

## Budget Rules

| Surface | Budget |
|---------|--------|
| Sub-agent spawn prompt | Under 4K tokens |
| Steering files total | Under 8K tokens |
| Context at spawn | Under 40% utilization |

---

## Guardrail Simplicity

- Maximum 5 items per boundary tier
- Each boundary item is one sentence
- No conditional boundaries ("If X then never Y")
- If you need more than 5 rules, decompose into multiple agents
