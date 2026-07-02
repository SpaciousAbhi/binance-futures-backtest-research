# Phase 30.1 — Candidate Execution Queue Design

The Candidate Execution Queue is a high-throughput, reproducible scheduling engine designed to execute compiled strategy templates in batches, with crash-recovery checkpointing and hash-locking.

## 1. Core Architecture
- **Batching**: Large sweeps are broken into parameterized chunk sizes to prevent memory leaks and allow incremental progress saves.
- **Checkpointing**: Every completed batch writes the serialized metric logs to `reports/execution_checkpoint.json`. If a run is interrupted, the queue resumes at the next pending parameter set.
- **Hash-Locking**: Parameter configurations are parsed to sorted JSON strings and hashed via SHA-256. If a candidate's parameter hash exists in the checkpoint, execution is skipped.
- **Deterministic Seed**: Sets seed globally (`np.random.seed` / `random.seed`) to ensure identical trade execution.
- **Multiprocessing**: Uses Python's `multiprocessing` Pool pattern to distribute candidate backtests across available CPU cores.

## 2. Queue State Schema
| State | Transition Trigger | Expected Output |
|---|---|---|
| `REGISTERED` | Compilation from idea engine | Empty metrics in registry |
| `STATIC_AUDITED` | Passed `audit_engine.py` scan | Audit manifest record |
| `ENGINE_EXECUTED` | Evaluated by backtest engine | Metrics populated from trade logs |
| `REJECTED` | Fails risk/verdict thresholds | Recorded in checkpoint |
