# Evaluations for managing-doc-manifest

## Scenario 1: Happy path — first-time manifest creation (should-trigger, functional)

**Given** a project with CLAUDE.md, README.md, and docs/ARCHITECTURE.md but no .doc-manifest.yaml
**When** user says "create doc manifest"
**Then**
- [ ] Skill activates
- [ ] Scans project for all documentation files
- [ ] Creates .doc-manifest.yaml with correct schema (version, last_synced, files array)
- [ ] Each file entry has path, type, last_updated, and references
- [ ] Shows summary with file count and reference counts

## Scenario 2: Edge case — update existing manifest (should-trigger, functional)

**Given** a project with existing .doc-manifest.yaml and a newly added docs/API.md
**When** user says "update manifest"
**Then**
- [ ] Skill activates
- [ ] Reads existing manifest
- [ ] Adds the new docs/API.md entry
- [ ] Preserves manually added entries
- [ ] Updates last_synced timestamp

## Scenario 3: Should-NOT-trigger — sync docs request

**Given** user wants to fix stale documentation
**When** user says "update my docs to match the code"
**Then**
- [ ] managing-doc-manifest does NOT activate
- [ ] syncing-docs activates instead (docs syncing, not manifest management)
