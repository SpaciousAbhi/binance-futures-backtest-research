"""
tests/test_project_memory_protocol.py

Tests for the Project Memory Operating System (Phase 30).
Verifies that all required memory files exist and contain mandatory content.

These tests enforce the AI Work Protocol and ensure that any AI
working on this project has access to correct, non-contradictory guidance.
"""
import os
import csv
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def path(*parts):
    return os.path.join(ROOT, *parts)


def read_file(rel_path):
    fpath = path(rel_path)
    if not os.path.exists(fpath):
        return ""
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: Required Memory Files Exist
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_MEMORY_FILES = [
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


@pytest.mark.parametrize("rel_path", REQUIRED_MEMORY_FILES)
def test_required_memory_file_exists(rel_path):
    """All required project_memory/ files must exist."""
    assert os.path.exists(path(rel_path)), \
        f"Required memory file missing: {rel_path}"


def test_agents_md_exists():
    """AGENTS.md must exist at repo root."""
    assert os.path.exists(path("AGENTS.md")), \
        "AGENTS.md missing at repo root — AI agents won't find project instructions."


def test_readme_md_exists():
    """README.md must exist at repo root."""
    assert os.path.exists(path("README.md")), \
        "README.md missing at repo root."


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: AGENTS.md Content
# ─────────────────────────────────────────────────────────────────────────────

def test_agents_md_references_current_handoff():
    """AGENTS.md must tell AI to read CURRENT_HANDOFF.md first."""
    content = read_file("AGENTS.md")
    assert "CURRENT_HANDOFF.md" in content, \
        "AGENTS.md must reference project_memory/CURRENT_HANDOFF.md"


def test_agents_md_references_master_state():
    """AGENTS.md must reference MASTER_PROJECT_STATE.md."""
    content = read_file("AGENTS.md")
    assert "MASTER_PROJECT_STATE.md" in content, \
        "AGENTS.md must reference project_memory/MASTER_PROJECT_STATE.md"


def test_agents_md_references_project_rulebook():
    """AGENTS.md must reference PROJECT_RULEBOOK.md."""
    content = read_file("AGENTS.md")
    assert "PROJECT_RULEBOOK.md" in content, \
        "AGENTS.md must reference project_memory/PROJECT_RULEBOOK.md"


def test_agents_md_mentions_live_status():
    """AGENTS.md must state NOT_REAL_CAPITAL_READY."""
    content = read_file("AGENTS.md")
    assert "NOT_REAL_CAPITAL_READY" in content, \
        "AGENTS.md must mention NOT_REAL_CAPITAL_READY live trading status."


def test_agents_md_mentions_invalid_benchmarks():
    """AGENTS.md must warn about INVALID benchmarks."""
    content = read_file("AGENTS.md")
    assert "INVALID" in content, \
        "AGENTS.md must mention that PF7/8/8.1 are INVALID."


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: PROJECT_RULEBOOK.md Content
# ─────────────────────────────────────────────────────────────────────────────

def test_rulebook_has_no_lookahead_section():
    """PROJECT_RULEBOOK.md must have a No-Lookahead section."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "No-Lookahead" in content or "lookahead" in content.lower(), \
        "Rulebook must contain No-Lookahead rules."


def test_rulebook_has_no_hardcoding_section():
    """PROJECT_RULEBOOK.md must have a No-Hardcoding section."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "No-Hardcoding" in content or "hardcod" in content.lower(), \
        "Rulebook must contain No-Hardcoding rules."


def test_rulebook_prohibits_trade_sampling():
    """PROJECT_RULEBOOK.md must explicitly prohibit trade sampling."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "sample" in content.lower() and "replace=True" in content, \
        "Rulebook must explicitly prohibit trades.sample(replace=True)."


def test_rulebook_has_no_fake_expansion_section():
    """PROJECT_RULEBOOK.md must have a No-Fake-Expansion section."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "Fake-Expansion" in content or "fake expansion" in content.lower() \
           or "synthetic trade" in content.lower(), \
        "Rulebook must contain No-Fake-Expansion rules."


def test_rulebook_has_metric_calculation_rules():
    """PROJECT_RULEBOOK.md must define metric calculation rules."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "Metric Calculation" in content, \
        "Rulebook must define Metric Calculation Rules."


def test_rulebook_mentions_live_safety():
    """PROJECT_RULEBOOK.md must mention live trading safety and NOT_REAL_CAPITAL_READY."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "NOT_REAL_CAPITAL_READY" in content, \
        "Rulebook must mention NOT_REAL_CAPITAL_READY in Live Trading Safety section."


def test_rulebook_has_stress_testing_rules():
    """PROJECT_RULEBOOK.md must define stress testing rules."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "Stress Testing" in content or "stress" in content.lower(), \
        "Rulebook must contain Stress Testing rules."


def test_rulebook_has_mtf_rules():
    """PROJECT_RULEBOOK.md must define MTF rules."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "MTF" in content or "Multi-Timeframe" in content, \
        "Rulebook must contain MTF rules."


def test_rulebook_references_invalid_forced_metric():
    """PROJECT_RULEBOOK.md must reference INVALID_FORCED_METRIC classification."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "INVALID_FORCED_METRIC" in content, \
        "Rulebook must reference INVALID_FORCED_METRIC classification."


def test_rulebook_references_teacher_reference():
    """PROJECT_RULEBOOK.md must reference TEACHER_REFERENCE classification."""
    content = read_file("project_memory/PROJECT_RULEBOOK.md")
    assert "TEACHER_REFERENCE" in content, \
        "Rulebook must reference TEACHER_REFERENCE classification."


# ─────────────────────────────────────────────────────────────────────────────
# Section 4: README.md Content
# ─────────────────────────────────────────────────────────────────────────────

def test_readme_references_project_memory():
    """README.md must reference project_memory/."""
    content = read_file("README.md")
    assert "project_memory" in content, \
        "README.md must reference project_memory/ directory."


def test_readme_references_agents_md():
    """README.md must reference AGENTS.md."""
    content = read_file("README.md")
    assert "AGENTS.md" in content, \
        "README.md must reference AGENTS.md."


def test_readme_mentions_live_status():
    """README.md must mention NOT_REAL_CAPITAL_READY."""
    content = read_file("README.md")
    assert "NOT_REAL_CAPITAL_READY" in content, \
        "README.md must state NOT_REAL_CAPITAL_READY live trading status."


# ─────────────────────────────────────────────────────────────────────────────
# Section 5: CURRENT_HANDOFF.md Content
# ─────────────────────────────────────────────────────────────────────────────

def test_handoff_references_phase_29_6():
    """CURRENT_HANDOFF.md must reference Phase 29.6."""
    content = read_file("project_memory/CURRENT_HANDOFF.md")
    assert "29.6" in content or "Phase 29.6" in content, \
        "CURRENT_HANDOFF.md must reference Phase 29.6 as latest completed phase."


def test_handoff_contains_phase29_6_pnl():
    """CURRENT_HANDOFF.md must contain the Phase 29.6 PnL result."""
    content = read_file("project_memory/CURRENT_HANDOFF.md")
    assert "-9940.72" in content or "9940.72" in content or "9,940" in content, \
        "CURRENT_HANDOFF.md must contain Phase 29.6 result PnL (-9940.72 or $9,940.72)."


def test_handoff_contains_next_phase_reference():
    """CURRENT_HANDOFF.md must reference next phase."""
    content = read_file("project_memory/CURRENT_HANDOFF.md")
    assert "29.7" in content or "Teacher Trade Replay" in content or "31" in content, \
        "CURRENT_HANDOFF.md must reference the next phase (29.7 or Teacher Trade Replay)."


def test_handoff_mentions_live_status():
    """CURRENT_HANDOFF.md must mention NOT_REAL_CAPITAL_READY."""
    content = read_file("project_memory/CURRENT_HANDOFF.md")
    assert "NOT_REAL_CAPITAL_READY" in content, \
        "CURRENT_HANDOFF.md must state NOT_REAL_CAPITAL_READY."


# ─────────────────────────────────────────────────────────────────────────────
# Section 6: BENCHMARK_REGISTRY.csv Content
# ─────────────────────────────────────────────────────────────────────────────

def test_benchmark_registry_has_required_columns():
    """BENCHMARK_REGISTRY.csv must have required columns."""
    fpath = path("project_memory/BENCHMARK_REGISTRY.csv")
    assert os.path.exists(fpath), "BENCHMARK_REGISTRY.csv must exist."
    with open(fpath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
    required_cols = ["benchmark_name", "status", "pnl", "trades", "profit_factor",
                     "max_dd", "validation_status"]
    for col in required_cols:
        assert col in cols, f"BENCHMARK_REGISTRY.csv missing column: {col}"


def test_benchmark_registry_has_pf12():
    """BENCHMARK_REGISTRY.csv must include PF 1.2 entry."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "PF 1.2" in content or "21684.99" in content, \
        "BENCHMARK_REGISTRY.csv must include PF 1.2 teacher reference entry."


def test_benchmark_registry_has_dirty_pf8():
    """BENCHMARK_REGISTRY.csv must include Dirty PF8 diagnostic entry."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "Dirty PF8" in content or "23216.75" in content, \
        "BENCHMARK_REGISTRY.csv must include Dirty PF8 diagnostic entry."


def test_benchmark_registry_has_phase29_6_engine():
    """BENCHMARK_REGISTRY.csv must include Phase 29.6 engine result."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "29.6" in content or "-9940.72" in content, \
        "BENCHMARK_REGISTRY.csv must include Phase 29.6 engine result."


def test_benchmark_registry_has_invalid_pf81():
    """BENCHMARK_REGISTRY.csv must include PF 8.1 as INVALID."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "PF 8.1" in content or "31250.80" in content, \
        "BENCHMARK_REGISTRY.csv must include PF 8.1 INVALID entry."


def test_benchmark_registry_has_invalid_forced_metric_entries():
    """BENCHMARK_REGISTRY.csv must have at least one INVALID_FORCED_METRIC entry."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "INVALID_FORCED_METRIC" in content, \
        "BENCHMARK_REGISTRY.csv must have INVALID_FORCED_METRIC entries."


def test_benchmark_registry_has_variant_b():
    """BENCHMARK_REGISTRY.csv must include Variant B teacher entry."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "Variant B" in content or "19589.91" in content, \
        "BENCHMARK_REGISTRY.csv must include Variant B teacher entry."


def test_benchmark_registry_has_variant_c():
    """BENCHMARK_REGISTRY.csv must include Variant C teacher entry."""
    content = read_file("project_memory/BENCHMARK_REGISTRY.csv")
    assert "Variant C" in content or "20455.48" in content, \
        "BENCHMARK_REGISTRY.csv must include Variant C teacher entry."


# ─────────────────────────────────────────────────────────────────────────────
# Section 7: AI_WORK_PROTOCOL.md Content
# ─────────────────────────────────────────────────────────────────────────────

def test_protocol_says_update_project_memory():
    """AI_WORK_PROTOCOL.md must instruct AI to update project_memory after every phase."""
    content = read_file("project_memory/AI_WORK_PROTOCOL.md")
    assert "project_memory" in content and \
           ("update" in content.lower() or "after" in content.lower()), \
        "AI_WORK_PROTOCOL.md must instruct AI to update project_memory after every phase."


def test_protocol_mentions_pytest():
    """AI_WORK_PROTOCOL.md must mention running pytest."""
    content = read_file("project_memory/AI_WORK_PROTOCOL.md")
    assert "pytest" in content, \
        "AI_WORK_PROTOCOL.md must mention running pytest before/after work."


def test_protocol_mentions_git_push():
    """AI_WORK_PROTOCOL.md must mention pushing to GitHub."""
    content = read_file("project_memory/AI_WORK_PROTOCOL.md")
    assert "push" in content.lower() or "git push" in content, \
        "AI_WORK_PROTOCOL.md must mention pushing to GitHub after completion."


# ─────────────────────────────────────────────────────────────────────────────
# Section 8: Key Script and Source Files
# ─────────────────────────────────────────────────────────────────────────────

def test_check_script_exists():
    """scripts/check_project_memory.py must exist."""
    assert os.path.exists(path("scripts/check_project_memory.py")), \
        "scripts/check_project_memory.py must exist."


def test_phase12_runner_exists():
    """src/research/phase12_runner.py must exist (PF1.2 constructor)."""
    assert os.path.exists(path("src/research/phase12_runner.py")), \
        "src/research/phase12_runner.py missing — this is the PF1.2 teacher constructor."


def test_engine_exists():
    """src/backtest/engine.py must exist."""
    assert os.path.exists(path("src/backtest/engine.py")), \
        "src/backtest/engine.py missing — this is the core backtest engine."


def test_phase29_6_engine_script_exists():
    """scripts/phase29_6_event_driven_mtf_engine.py must exist (Phase 29.6 MTF engine)."""
    assert os.path.exists(path("scripts/phase29_6_event_driven_mtf_engine.py")), \
        "Phase 29.6 MTF engine script missing."


# ─────────────────────────────────────────────────────────────────────────────
# Section 9: Phase 30 Files
# ─────────────────────────────────────────────────────────────────────────────

def test_phase30_report_exists():
    """Phase 30 main report must exist."""
    assert os.path.exists(
        path("reports/phase30_project_memory_operating_system_report.md")), \
        "Phase 30 report missing: reports/phase30_project_memory_operating_system_report.md"


def test_memory_index_exists():
    """project_memory/MEMORY_INDEX.md must exist."""
    assert os.path.exists(path("project_memory/MEMORY_INDEX.md")), \
        "project_memory/MEMORY_INDEX.md missing."


def test_open_problems_exists():
    """project_memory/OPEN_PROBLEMS.md must exist."""
    assert os.path.exists(path("project_memory/OPEN_PROBLEMS.md")), \
        "project_memory/OPEN_PROBLEMS.md missing."


def test_next_phase_plan_exists():
    """project_memory/NEXT_PHASE_PLAN.md must exist."""
    assert os.path.exists(path("project_memory/NEXT_PHASE_PLAN.md")), \
        "project_memory/NEXT_PHASE_PLAN.md missing."
