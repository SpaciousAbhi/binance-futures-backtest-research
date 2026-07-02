# MEMORY INDEX
## Guide to All Project Memory Files
## Last Updated: 2026-07-02 (Phase 30)

---

## Which File to Read First

```
AGENTS.md               <- Root of repo. Read this first. Always.
    |
    v
project_memory/CURRENT_HANDOFF.md      <- What happened last? What's next?
    |
    v
project_memory/MASTER_PROJECT_STATE.md <- Full truth, benchmarks, rules summary
    |
    v
project_memory/PROJECT_RULEBOOK.md     <- All detailed rules (read before coding)
    |
    v
project_memory/AI_WORK_PROTOCOL.md     <- Step-by-step before/during/after protocol
```

---

## File Descriptions

| File | Contents | Read When | Update When |
|---|---|---|---|
| `AGENTS.md` (root) | AI entry point — benchmarks, rules summary, workflow | **Every session, before anything** | When major project state changes |
| `CURRENT_HANDOFF.md` | Latest phase result, exact metrics, next action | **Every session, first read** | **After every phase completion** |
| `MASTER_PROJECT_STATE.md` | Benchmark truth, engine status, infrastructure, all rules | When context is needed | When benchmarks change |
| `PROJECT_RULEBOOK.md` | Full 16-section rule system (lookahead, hardcoding, etc.) | Before any coding | When new rule categories are added |
| `AI_WORK_PROTOCOL.md` | Checklist before/during/after phase | Before starting a phase | When workflow is refined |
| `PHASE_HISTORY_TIMELINE.md` | Every phase from 1–29.6+ with verdict and classification | When historical context needed | After each new phase |
| `BENCHMARK_REGISTRY.csv` | Machine-readable table of all benchmarks | When benchmark comparison needed | After each new benchmark result |
| `DATA_REGISTRY.md` | All data files, rows, hashes, date ranges | When data questions arise | When new data is downloaded |
| `ARTIFACT_REGISTRY.csv` | Key proof files and their hashes | When file integrity matters | After each phase generates artifacts |
| `OPEN_PROBLEMS.md` | Current unsolved research problems | Before starting a new phase | After each phase, update open problems |
| `NEXT_PHASE_PLAN.md` | Specification for next research phase | Before starting next phase | After each phase completion |
| `README_FOR_NEXT_AI.md` | Short intro for a brand-new AI or developer | When bringing in a new agent | Rarely; only if project pivots |

---

## Who Should Update Each File

| File | Who Updates | When |
|---|---|---|
| `AGENTS.md` | Any AI completing major phase | When major project direction changes |
| `CURRENT_HANDOFF.md` | **Every AI, every phase** | **Mandatory after every phase** |
| `MASTER_PROJECT_STATE.md` | AI completing major benchmark changes | When benchmarks are added or invalidated |
| `PROJECT_RULEBOOK.md` | Project owner or senior AI | When new rule violations are discovered |
| `BENCHMARK_REGISTRY.csv` | AI running any benchmark evaluation | After computing new benchmark metrics |
| `PHASE_HISTORY_TIMELINE.md` | AI completing a phase | After each phase is complete |
| `DATA_REGISTRY.md` | AI downloading or processing new data | After any data update |
| `OPEN_PROBLEMS.md` | Any AI | After any phase that discovers or closes a problem |
| `NEXT_PHASE_PLAN.md` | AI completing previous phase | When preparing for next phase |

---

## How Antigravity and Codex Use This

### Starting a Session (Either AI)
1. Pull latest from GitHub: `git pull origin master`
2. Read `AGENTS.md`
3. Read `project_memory/CURRENT_HANDOFF.md`
4. Run `pytest -q` to confirm tests pass
5. Run `python scripts/check_project_memory.py` to verify memory integrity

### Ending a Session (Either AI)
1. Update `project_memory/CURRENT_HANDOFF.md`
2. Update any other memory files that changed
3. Run `pytest -q`
4. Commit: `git commit -am "Phase N — [description]; update project memory"`
5. Push: `git push origin master`

### When AI Switches (Antigravity -> Codex or reverse)
- The finishing AI MUST push changes to GitHub before switching.
- The new AI MUST pull from GitHub before starting.
- The new AI reads `CURRENT_HANDOFF.md` to know exact state.
- No assumptions from chat history.

---

## Memory File Quick Health Check

Run this script to verify memory integrity:
```bash
python scripts/check_project_memory.py
```

Or run the test:
```bash
pytest tests/test_project_memory_protocol.py -v
```
