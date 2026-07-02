# Phase 30.1 — Project Memory Auto-Updater Design

The `update_project_memory.py` script serves as a safety gate for modifications made to the `project_memory/` metadata directory.

## 1. Safety Principles
1. **No Blind Overwrites**: The updater never replaces `CURRENT_HANDOFF.md` or `MASTER_PROJECT_STATE.md` without presenting a diff preview.
2. **Deterministic Hashing**: File references added to `ARTIFACT_REGISTRY.csv` are automatically validated for SHA-256 integrity.
3. **Structured Verification**: The updater reads output artifacts (such as manifest JSONs) to extract verified metrics rather than accepting raw CLI inputs.

## 2. Command Line Interface (Planned)
- `python scripts/update_project_memory.py preview-handoff --phase <id>`: Reads `reports/phase{id}_audit_manifest.json` and prints the proposed markdown block.
- `python scripts/update_project_memory.py sync-registry`: Scans `reports/` for newly created CSV and MD reports and adds them to `ARTIFACT_REGISTRY.csv` with their calculated SHA-256 hashes.
- `python scripts/update_project_memory.py open-problem --add <desc>`: Appends a structured open problem entry to `OPEN_PROBLEMS.md`.
