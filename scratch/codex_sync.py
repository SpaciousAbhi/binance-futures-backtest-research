"""
Codex -> Antigravity Sync Script
Phase 29 through Phase 29.6 file import
"""
import os
import hashlib
import shutil
import csv
from datetime import datetime

# Paths
CODEX_OUT   = r"C:\Users\HP\Documents\Codex\2026-07-01\spaciousabhi-binance-futures-backtest-research-https\outputs"
CODEX_WORK  = r"C:\Users\HP\Documents\Codex\2026-07-01\spaciousabhi-binance-futures-backtest-research-https\work\binance-futures-backtest-research"
AG_ROOT     = r"C:\Users\HP\.gemini\antigravity\scratch\binance_futures_backtest"

DEST_REPORTS = os.path.join(AG_ROOT, "reports")
DEST_OUTPUTS = os.path.join(AG_ROOT, "outputs")
DEST_SCRIPTS = os.path.join(AG_ROOT, "scripts")
DEST_TESTS   = os.path.join(AG_ROOT, "tests")
DEST_SRC     = os.path.join(AG_ROOT, "src")

os.makedirs(DEST_REPORTS, exist_ok=True)
os.makedirs(DEST_OUTPUTS, exist_ok=True)
os.makedirs(DEST_SCRIPTS, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def copy_file(src, dst, log_rows):
    action = "SKIP"
    notes  = ""
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        action = "COPIED_NEW"
    else:
        h_src = sha256(src)
        h_dst = sha256(dst)
        if h_src != h_dst:
            # Backup then overwrite only for phase29+ files
            bak = dst + ".before_phase29_sync.bak"
            if not os.path.exists(bak):
                shutil.copy2(dst, bak)
            shutil.copy2(src, dst)
            action = "UPDATED_WITH_BACKUP"
            notes  = f"prev_hash={h_dst}"
        else:
            action = "IDENTICAL_SKIP"

    rel_dst = dst.replace(AG_ROOT + os.sep, "")
    rel_src = src.replace(CODEX_OUT + os.sep, "").replace(CODEX_WORK + os.sep, "")
    sz_kb = round(os.path.getsize(src) / 1024, 1)
    log_rows.append({
        "codex_rel_path": rel_src,
        "antigravity_rel_path": rel_dst,
        "size_kb": sz_kb,
        "action": action,
        "notes": notes,
    })
    return action

log_rows = []

# ── 1. Import all phase29_* from Codex outputs/ -> Antigravity reports/ ──
print("=== Importing Codex outputs/ -> reports/ ===")
for fname in sorted(os.listdir(CODEX_OUT)):
    if not fname.startswith("phase29"):
        continue
    src = os.path.join(CODEX_OUT, fname)
    dst = os.path.join(DEST_REPORTS, fname)
    action = copy_file(src, dst, log_rows)
    print(f"  [{action}] {fname}")

# ── 2. Import Codex scripts/ phase29_* -> Antigravity scripts/ ──
print("\n=== Importing Codex scripts/ phase29_* -> scripts/ ===")
codex_scripts = os.path.join(CODEX_WORK, "scripts")
if os.path.isdir(codex_scripts):
    for fname in sorted(os.listdir(codex_scripts)):
        if "phase29" not in fname and fname != "reproduce_champions.py":
            continue
        src = os.path.join(codex_scripts, fname)
        dst = os.path.join(DEST_SCRIPTS, fname)
        action = copy_file(src, dst, log_rows)
        print(f"  [{action}] scripts/{fname}")

# ── 3. Import Codex tests/ phase29_* -> Antigravity tests/ ──
print("\n=== Importing Codex tests/ phase29_* -> tests/ ===")
codex_tests = os.path.join(CODEX_WORK, "tests")
if os.path.isdir(codex_tests):
    for fname in sorted(os.listdir(codex_tests)):
        if "phase29" not in fname:
            continue
        src = os.path.join(codex_tests, fname)
        dst = os.path.join(DEST_TESTS, fname)
        action = copy_file(src, dst, log_rows)
        print(f"  [{action}] tests/{fname}")

# ── 4. Check Codex src/ for phase29-related files ──
print("\n=== Checking Codex src/ for new phase29 research files ===")
codex_src_research = os.path.join(CODEX_WORK, "src", "research")
ag_src_research    = os.path.join(AG_ROOT,   "src", "research")
if os.path.isdir(codex_src_research):
    for fname in sorted(os.listdir(codex_src_research)):
        if "phase29" not in fname and "__pycache__" not in fname:
            pass  # Only import phase29 research runners
        if "phase29" not in fname:
            continue
        src = os.path.join(codex_src_research, fname)
        dst = os.path.join(ag_src_research, fname)
        action = copy_file(src, dst, log_rows)
        print(f"  [{action}] src/research/{fname}")

# ── 5. Check for updated candidates.py and engine.py ──
print("\n=== Checking Codex src/ core files vs Antigravity ===")
core_files = [
    ("src/backtest/engine.py",      os.path.join(CODEX_WORK,"src","backtest","engine.py"),      os.path.join(AG_ROOT,"src","backtest","engine.py")),
    ("src/strategies/candidates.py",os.path.join(CODEX_WORK,"src","strategies","candidates.py"),os.path.join(AG_ROOT,"src","strategies","candidates.py")),
    ("src/features/indicators.py",  os.path.join(CODEX_WORK,"src","features","indicators.py"),  os.path.join(AG_ROOT,"src","features","indicators.py")),
]
for label, codex_f, ag_f in core_files:
    if os.path.exists(codex_f) and os.path.exists(ag_f):
        h1 = sha256(codex_f)
        h2 = sha256(ag_f)
        sz_codex = round(os.path.getsize(codex_f)/1024,1)
        sz_ag    = round(os.path.getsize(ag_f)/1024,1)
        match = "SAME" if h1==h2 else f"DIFF (codex={sz_codex}KB ag={sz_ag}KB)"
        print(f"  {label}: {match}")
        log_rows.append({
            "codex_rel_path": label,
            "antigravity_rel_path": label,
            "size_kb": sz_codex,
            "action": "HASH_CHECK_ONLY",
            "notes": match,
        })

# ── 6. Write import log ──
log_path = os.path.join(DEST_REPORTS, "phase29_codex_to_antigravity_import_log.csv")
with open(log_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["codex_rel_path","antigravity_rel_path","size_kb","action","notes"])
    w.writeheader()
    w.writerows(log_rows)

copied  = sum(1 for r in log_rows if r["action"] in ("COPIED_NEW","UPDATED_WITH_BACKUP"))
skipped = sum(1 for r in log_rows if r["action"] == "IDENTICAL_SKIP")
print(f"\n=== IMPORT COMPLETE ===")
print(f"  Files copied/updated : {copied}")
print(f"  Files identical skip : {skipped}")
print(f"  Import log written   : {log_path}")
