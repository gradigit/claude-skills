# /wrap

Run the `wrap` skill as an explicit manual command.

## Contract
- Trigger only from explicit user invocation (`/wrap`)
- Do not auto-run from hooks unless user explicitly configures and documents that behavior
- Default flow: syncing-docs → claude-md-improver (+ AGENTS parity mirror) → handoff
- Optional: `--with-fresh` to append `/handoff-fresh --no-sync`
