#!/usr/bin/env python3
"""
scripts/update_project_memory.py

Project Memory Auto-Updater - Phase 30.1
Helps automate updates to the project_memory/ directory by generating previews
of proposed updates and preventing destructive blind overwrites.
Outputs:
  - reports/phase30_1_memory_updater_design.md
"""
import os
import json
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEMORY_DIR = os.path.join(ROOT_DIR, "project_memory")
DESIGN_PATH = os.path.join(ROOT_DIR, "reports", "phase30_1_memory_updater_design.md")

class MemoryUpdater:
    def __init__(self):
        pass

    def preview_handoff_update(self, phase_name, verdict, metrics):
        """Generates a proposed handoff preview block without overwriting CURRENT_HANDOFF.md."""
        preview = f"""# PROPOSED CURRENT_HANDOFF.md UPDATE PREVIEW
## Last Updated: {time.strftime('%Y-%m-%d UTC')}

---

## Latest Completed Phase: {phase_name}
**Verdict:** `{verdict}`
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC')}

### Key Performance Summary:
- **Net PnL:** {metrics.get('net_pnl', '—')}
- **Profit Factor:** {metrics.get('profit_factor', '—')}
- **Max Drawdown:** {metrics.get('max_drawdown', '—')}
- **Trade Count:** {metrics.get('trade_count', '—')}
- **Stress Verdict:** {metrics.get('stress_verdict', '—')}

---
"""
        return preview

    def write_design_doc(self):
        md = """# Phase 30.1 — Project Memory Auto-Updater Design

The `update_project_memory.py` script serves as a safety gate for modifications made to the `project_memory/` metadata directory.

## 1. Safety Principles
1. **No Blind Overwrites**: The updater never replaces `CURRENT_HANDOFF.md` or `MASTER_PROJECT_STATE.md` without presenting a diff preview.
2. **Deterministic Hashing**: File references added to `ARTIFACT_REGISTRY.csv` are automatically validated for SHA-256 integrity.
3. **Structured Verification**: The updater reads output artifacts (such as manifest JSONs) to extract verified metrics rather than accepting raw CLI inputs.

## 2. Command Line Interface (Planned)
- `python scripts/update_project_memory.py preview-handoff --phase <id>`: Reads `reports/phase{id}_audit_manifest.json` and prints the proposed markdown block.
- `python scripts/update_project_memory.py sync-registry`: Scans `reports/` for newly created CSV and MD reports and adds them to `ARTIFACT_REGISTRY.csv` with their calculated SHA-256 hashes.
- `python scripts/update_project_memory.py open-problem --add <desc>`: Appends a structured open problem entry to `OPEN_PROBLEMS.md`.
"""
        with open(DESIGN_PATH, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Generated Memory Updater Design Doc: {DESIGN_PATH}")

if __name__ == "__main__":
    u = MemoryUpdater()
    u.write_design_doc()
    # Simple console preview printout for smoke testing
    mock_metrics = {"net_pnl": "$0.00", "profit_factor": "1.0", "max_drawdown": "0.0%", "trade_count": "0", "stress_verdict": "SKIPPED"}
    preview = u.preview_handoff_update("Phase 30.1", "PHASE30_1_PASS_RESEARCH_LAB_OS_BUILT", mock_metrics)
    print("\nProposed Handoff Update Preview:\n" + preview)
