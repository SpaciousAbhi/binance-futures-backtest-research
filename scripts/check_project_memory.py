"""
scripts/check_project_memory.py

Project Memory Integrity Check Script
======================================
Verifies that all required project memory files exist and contain
mandatory content. Run this before starting any phase.

Usage:
    python scripts/check_project_memory.py

Returns:
    Exit code 0 if all checks pass.
    Exit code 1 if any check fails.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASS_SYMBOL = "[PASS]"
FAIL_SYMBOL = "[FAIL]"
WARN_SYMBOL = "[WARN]"

failures = []
warnings = []
passes   = []

def check(condition, label, severity="FAIL"):
    if condition:
        passes.append(label)
        print(f"  {PASS_SYMBOL} {label}")
    else:
        if severity == "WARN":
            warnings.append(label)
            print(f"  {WARN_SYMBOL} {label}")
        else:
            failures.append(label)
            print(f"  {FAIL_SYMBOL} {label}")

def file_exists(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))

def file_contains(rel_path, *substrings):
    fpath = os.path.join(ROOT, rel_path)
    if not os.path.exists(fpath):
        return False
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return all(s in content for s in substrings)

print("=" * 60)
print("PROJECT MEMORY INTEGRITY CHECK")
print(f"Root: {ROOT}")
print("=" * 60)

# ─── Section 1: Required Memory Files ────────────────────────
print("\n[1] Required project_memory/ files:")
required_memory_files = [
    "project_memory/CURRENT_HANDOFF.md",
    "project_memory/MASTER_PROJECT_STATE.md",
    "project_memory/PROJECT_RULEBOOK.md",
    "project_memory/AI_WORK_PROTOCOL.md",
    "project_memory/PHASE_HISTORY_TIMELINE.md",
    "project_memory/BENCHMARK_REGISTRY.csv",
    "project_memory/README_FOR_NEXT_AI.md",
    "project_memory/DATA_REGISTRY.md",
    "project_memory/ARTIFACT_REGISTRY.csv",
    "project_memory/OPEN_PROBLEMS.md",
    "project_memory/NEXT_PHASE_PLAN.md",
    "project_memory/MEMORY_INDEX.md",
]
for f in required_memory_files:
    check(file_exists(f), f"Exists: {f}")

# ─── Section 2: Root Files ────────────────────────────────────
print("\n[2] Required root files:")
check(file_exists("AGENTS.md"),  "Exists: AGENTS.md")
check(file_exists("README.md"),  "Exists: README.md")

# ─── Section 3: AGENTS.md Content ────────────────────────────
print("\n[3] AGENTS.md content checks:")
check(file_contains("AGENTS.md", "project_memory/CURRENT_HANDOFF.md"),
      "AGENTS.md references CURRENT_HANDOFF.md")
check(file_contains("AGENTS.md", "project_memory/MASTER_PROJECT_STATE.md"),
      "AGENTS.md references MASTER_PROJECT_STATE.md")
check(file_contains("AGENTS.md", "project_memory/PROJECT_RULEBOOK.md"),
      "AGENTS.md references PROJECT_RULEBOOK.md")
check(file_contains("AGENTS.md", "NOT_REAL_CAPITAL_READY"),
      "AGENTS.md mentions NOT_REAL_CAPITAL_READY")

# ─── Section 4: README.md Content ────────────────────────────
print("\n[4] README.md content checks:")
check(file_contains("README.md", "project_memory"),
      "README.md references project_memory/")
check(file_contains("README.md", "NOT_REAL_CAPITAL_READY"),
      "README.md mentions NOT_REAL_CAPITAL_READY")
check(file_contains("README.md", "AGENTS.md"),
      "README.md references AGENTS.md")

# ─── Section 5: PROJECT_RULEBOOK.md Content ──────────────────
print("\n[5] PROJECT_RULEBOOK.md rule sections:")
rulebook = "project_memory/PROJECT_RULEBOOK.md"
check(file_contains(rulebook, "No-Lookahead"),
      "Rulebook: No-Lookahead section exists")
check(file_contains(rulebook, "No-Hardcoding"),
      "Rulebook: No-Hardcoding section exists")
check(file_contains(rulebook, "No-Fake-Expansion"),
      "Rulebook: No-Fake-Expansion section exists")
check(file_contains(rulebook, "Metric Calculation Rules"),
      "Rulebook: Metric Calculation section exists")
check(file_contains(rulebook, "NOT_REAL_CAPITAL_READY"),
      "Rulebook: Live Trading Safety section mentions NOT_REAL_CAPITAL_READY")
check(file_contains(rulebook, "sample", "replace=True"),
      "Rulebook: Prohibits trade sampling (replace=True)")
check(file_contains(rulebook, "INVALID_FORCED_METRIC"),
      "Rulebook: References INVALID_FORCED_METRIC classification")
check(file_contains(rulebook, "TEACHER_REFERENCE"),
      "Rulebook: References TEACHER_REFERENCE classification")
check(file_contains(rulebook, "Stress Testing"),
      "Rulebook: Stress Testing rules section exists")
check(file_contains(rulebook, "MTF", "Multi-Timeframe"),
      "Rulebook: MTF rules section exists")

# ─── Section 6: CURRENT_HANDOFF.md Content ───────────────────
print("\n[6] CURRENT_HANDOFF.md content checks:")
handoff = "project_memory/CURRENT_HANDOFF.md"
check(file_contains(handoff, "Phase 29.6"),
      "Handoff: References Phase 29.6")
check(file_contains(handoff, "-9940.72") or file_contains(handoff, "9940.72") or file_contains(handoff, "9,940"),
      "Handoff: Contains Phase 29.6 PnL result (-9940.72)")
check(file_contains(handoff, "3111") or file_contains(handoff, "3,111"),
      "Handoff: Contains Phase 29.6 trade count (3111)")
check(file_contains(handoff, "NOT_REAL_CAPITAL_READY"),
      "Handoff: Mentions NOT_REAL_CAPITAL_READY")
check(file_contains(handoff, "Phase 29.7") or file_contains(handoff, "Teacher Trade Replay") or file_contains(handoff, "Phase 33"),
      "Handoff: References next phase (29.7 or subsequent)")

# ─── Section 7: BENCHMARK_REGISTRY.csv Content ───────────────
print("\n[7] BENCHMARK_REGISTRY.csv content checks:")
registry = "project_memory/BENCHMARK_REGISTRY.csv"
check(file_contains(registry, "PF 1.2"),
      "Registry: Contains PF 1.2 entry")
check(file_contains(registry, "Dirty PF8"),
      "Registry: Contains Dirty PF8 entry")
check(file_contains(registry, "INVALID_FORCED_METRIC"),
      "Registry: Contains INVALID_FORCED_METRIC entries")
check(file_contains(registry, "PF 8.1"),
      "Registry: Contains PF 8.1 invalid entry")
check(file_contains(registry, "Variant B"),
      "Registry: Contains Variant B teacher entry")
check(file_contains(registry, "Variant C"),
      "Registry: Contains Variant C teacher entry")
check(file_contains(registry, "-9940.72") or file_contains(registry, "Phase 29.6"),
      "Registry: Contains Phase 29.6 engine result")

# ─── Section 8: AI_WORK_PROTOCOL.md Content ──────────────────
print("\n[8] AI_WORK_PROTOCOL.md content checks:")
protocol = "project_memory/AI_WORK_PROTOCOL.md"
check(file_contains(protocol, "project_memory"),
      "Protocol: References project_memory after every phase")
check(file_contains(protocol, "pytest"),
      "Protocol: Mentions running pytest")
check(file_contains(protocol, "git push") or file_contains(protocol, "push"),
      "Protocol: Mentions pushing to GitHub")

# ─── Section 9: Key Script/Test Existence ────────────────────
print("\n[9] Key scripts and tests:")
check(file_exists("scripts/check_project_memory.py"),
      "Exists: scripts/check_project_memory.py")
check(file_exists("tests/test_project_memory_protocol.py"),
      "Exists: tests/test_project_memory_protocol.py")
check(file_exists("scripts/phase29_6_event_driven_mtf_engine.py"),
      "Exists: scripts/phase29_6_event_driven_mtf_engine.py")

# ─── Section 10: Phase 30 Report ─────────────────────────────
print("\n[10] Phase 30 report:")
check(file_exists("reports/phase30_project_memory_operating_system_report.md"),
      "Exists: reports/phase30_project_memory_operating_system_report.md",
      severity="WARN")

# ─── Summary ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  PASS : {len(passes)}")
print(f"  WARN : {len(warnings)}")
print(f"  FAIL : {len(failures)}")

if failures:
    print("\nFailed checks:")
    for f in failures:
        print(f"  - {f}")
    print("\nResult: MEMORY_INTEGRITY_FAIL")
    sys.exit(1)
elif warnings:
    print("\nWarnings (non-blocking):")
    for w in warnings:
        print(f"  - {w}")
    print("\nResult: MEMORY_INTEGRITY_PASS_WITH_WARNINGS")
    sys.exit(0)
else:
    print("\nResult: MEMORY_INTEGRITY_PASS")
    sys.exit(0)
