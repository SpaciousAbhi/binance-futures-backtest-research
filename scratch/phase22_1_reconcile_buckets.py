"""
scratch/phase22_1_reconcile_buckets.py

Regenerates the phase22_loss_bucket_report.csv with all 12 taxonomy rows,
re-calculates hashes, and updates the manifest.
"""
import os
import csv
import json
import shutil
import hashlib
import pandas as pd

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS_DIR = os.path.join(_ROOT, "reports")
BRAIN_REPORTS = "C:/Users/HP/.gemini/antigravity/brain/92120e2d-8d79-4bf9-991f-c62be6fedb3c/reports"

TAXONOMY = [
    "false_breakout",
    "range_chop",
    "trend_whipsaw",
    "funding_drag",
    "late_fill_adverse_selection",
    "weak_continuation",
    "volatility_compression",
    "overextended_entry",
    "stop_loss_too_tight",
    "take_profit_too_far",
    "time_decay",
    "session_liquidity_issue"
]

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def main():
    mechanism_path = os.path.join(REPORTS_DIR, "phase22_mechanism_dataset.csv")
    mechanism_df = pd.read_csv(mechanism_path)
    
    losers = mechanism_df[mechanism_df["net_pnl"] <= 0].copy()
    
    # Recalculate buckets
    def get_bucket(r):
        if r["funding_drag"] < -2.0:
            return "funding_drag"
        elif r["immediate_failure"] == 1:
            return "trend_whipsaw"
        elif r["reached_0_5R"] == 0:
            return "false_breakout"
        elif r["chop_state"] == "chop":
            return "range_chop"
        elif r["decayed_after_profit"] == 1:
            return "weak_continuation"
        elif r["failed_continuation"] == 1:
            return "weak_continuation"
        elif r["MAE_1"] > 0.02:
            return "overextended_entry"
        else:
            return "time_decay"

    losers["bucket"] = losers.apply(get_bucket, axis=1)
    
    bucket_rows = []
    for bucket in TAXONOMY:
        grp = losers[losers["bucket"] == bucket]
        if not grp.empty:
            avg_r = grp["R"].mean() if "R" in grp.columns else 0.0
            grp_m = grp.copy()
            grp_m["month"] = pd.to_datetime(grp_m["entry_time"]).dt.to_period("M")
            months = "|".join(grp_m["month"].unique().astype(str).tolist()[:3])
            
            bucket_rows.append({
                "bucket_name": bucket,
                "num_trades": len(grp),
                "total_pnl_damage": round(grp["net_pnl"].sum(), 2),
                "avg_R": round(avg_r, 4),
                "month_contribution": months,
                "repairable_live": "YES" if bucket in ["funding_drag", "false_breakout", "range_chop"] else "PARTIAL",
                "live_known_feature_fix": "funding_extreme_skip" if bucket == "funding_drag" else (
                    "adx_compression_filter" if bucket == "range_chop" else "volume_confirm"
                )
            })
        else:
            bucket_rows.append({
                "bucket_name": bucket,
                "num_trades": 0,
                "total_pnl_damage": 0.0,
                "avg_R": 0.0,
                "month_contribution": "None",
                "repairable_live": "YES" if bucket in ["funding_drag", "false_breakout", "range_chop"] else "PARTIAL",
                "live_known_feature_fix": "none"
            })
            
    bucket_df = pd.DataFrame(bucket_rows)
    bucket_path = os.path.join(REPORTS_DIR, "phase22_loss_bucket_report.csv")
    bucket_df.to_csv(bucket_path, index=False)
    print("Regenerated bucket report with 12 rows.")
    
    # Update manifest
    manifest_path = os.path.join(REPORTS_DIR, "phase22_audit_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    manifest["loss_bucket_report_hash"] = file_hash(bucket_path)
    
    # Make sure top_100 hash is updated as well
    top100_path = os.path.join(REPORTS_DIR, "phase22_top_100_candidates.md")
    if os.path.exists(top100_path):
        manifest["top_100_candidates_hash"] = file_hash(top100_path)
        
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Updated audit manifest with new hashes.")
    
    # Copy to brain reports
    os.makedirs(BRAIN_REPORTS, exist_ok=True)
    shutil.copy(bucket_path, os.path.join(BRAIN_REPORTS, "phase22_loss_bucket_report.csv"))
    shutil.copy(manifest_path, os.path.join(BRAIN_REPORTS, "phase22_audit_manifest.json"))
    print("Copied files to brain directory.")

if __name__ == "__main__":
    main()
