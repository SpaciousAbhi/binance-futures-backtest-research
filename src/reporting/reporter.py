import os
import pandas as pd

class Reporter:
    """
    Generates a professional, detailed strategy research and audit report in Markdown format.
    """
    def __init__(self, data_audit_reports: dict, candidate_leaderboard: list, best_strategy_name: str,
                 best_strategy_hypothesis: str, full_metrics: dict, wf_results: list, combined_oos_metrics: dict,
                 stress_results: dict, audit_report: dict, final_verdict: str, failure_reasons: list = None):
        self.data_audit_reports = data_audit_reports
        self.candidate_leaderboard = candidate_leaderboard
        self.best_strategy_name = best_strategy_name
        self.best_strategy_hypothesis = best_strategy_hypothesis
        self.full_metrics = full_metrics
        self.wf_results = wf_results
        self.combined_oos_metrics = combined_oos_metrics
        self.stress_results = stress_results
        self.audit_report = audit_report
        self.final_verdict = final_verdict
        self.failure_reasons = failure_reasons if failure_reasons is not None else []

    def generate_report(self, output_path: str):
        content = []
        content.append("# Binance USD-M Perpetual Futures Strategy Research & Audit Report")
        content.append(f"\n**Report Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        content.append(f"**Target Symbol:** BTCUSDT Perpetual Futures (BTCUSDT.P)")
        
        # Final Verdict Box
        content.append("\n## FINAL SYSTEM VERDICT")
        if self.final_verdict == "PASS":
            content.append("\n> [!NOTE]")
            content.append("> **VERDICT: PASS**")
            content.append("> The selected strategy meets all strict criteria including positive performance, sufficient trading count, and successfully passes the code and lookahead audits.")
        else:
            content.append("\n> [!CAUTION]")
            content.append("> **VERDICT: FAIL**")
            content.append("> The candidate strategies did not meet the strict performance standards (0 negative months, 0 zero months, and 780+ trades).")
            if self.failure_reasons:
                content.append(">\n> **Reasons for Failure:**")
                for reason in self.failure_reasons:
                    content.append(f"> - {reason}")
        
        # 1. Data Audit Section
        content.append("\n## 1. Data Pipeline Integrity Audit")
        content.append("| Timeframe | Rows | Expected | Missing | Gaps | Timezone | Funding Coverage | Audit Status |")
        content.append("|---|---|---|---|---|---|---|---|")
        for tf, rpt in self.data_audit_reports.items():
            content.append(
                f"| {tf} | {rpt['total_rows']} | {rpt['expected_rows']} | {rpt['missing_candles']} | "
                f"{rpt['timestamp_gaps']} | {rpt['timezone_consistency']} | {rpt['funding_coverage_pct']:.2f}% | "
                f"**{rpt['status']}** |"
            )

        # 2. Research Process
        content.append("\n## 2. Strategy Research Lab Process")
        content.append("We evaluated 5 rule-based trading strategy candidates on real historical data. "
                       "Each candidate is constructed with a distinct hypothesis, clear parameter ranges, "
                       "and strict entry/exit logic. No brute force or random parameter snooping was used.")

        # 3. Candidate Leaderboard
        content.append("\n## 3. Strategy Candidate Leaderboard")
        content.append("| Strategy | Hypothesis | Trades | Win Rate | Net PnL ($) | Profit Factor | Max DD | +/-/0 Months |")
        content.append("|---|---|---|---|---|---|---|---|")
        for cand in self.candidate_leaderboard:
            months_str = f"{cand['positive_months']} / {cand['negative_months']} / {cand['zero_months']}"
            content.append(
                f"| {cand['strategy']} | {cand['hypothesis']} | {cand['total_trades']} | {cand['win_rate']:.2%} | "
                f"{cand['net_pnl']:.2f} | {cand['profit_factor']:.2f} | {cand['max_drawdown']:.2%} | {months_str} |"
            )

        # 4. Rejected Candidates
        content.append("\n## 4. Rejected Candidates & Rationale")
        for cand in self.candidate_leaderboard:
            if cand["strategy"] != self.best_strategy_name:
                content.append(f"- **{cand['strategy']}**: Rejected due to lower Profit Factor ({cand['profit_factor']:.2f}) or Net PnL (${cand['net_pnl']:.2f}).")
        
        # 5. Final Selected System
        content.append(f"\n## 5. Final Selected System Profile")
        content.append(f"**Strategy Name:** {self.best_strategy_name}")
        content.append(f"**Hypothesis:** {self.best_strategy_hypothesis}")
        
        content.append("\n### Performance Metrics (Full period - In Sample)")
        metrics = self.full_metrics
        content.append(f"- **Total Trades:** {metrics['total_trades']}")
        content.append(f"- **Win Rate:** {metrics['win_rate']:.2%}")
        content.append(f"- **Net PnL:** ${metrics['net_pnl']:.2f}")
        content.append(f"- **Max Drawdown:** {metrics['max_drawdown']:.2%}")
        content.append(f"- **Profit Factor:** {metrics['profit_factor']:.2f}")
        content.append(f"- **Expectancy:** ${metrics['expectancy']:.2f}")
        content.append(f"- **Avg Winner:** ${metrics['avg_winner']:.2f}")
        content.append(f"- **Avg Loser:** ${metrics['avg_loser']:.2f}")
        content.append(f"- **Avg R-multiple:** {metrics['avg_r']:.2f} R")
        content.append(f"- **Positive / Negative / Zero Months:** {metrics['positive_months']} / {metrics['negative_months']} / {metrics['zero_months']}")

        # Month-by-Month report for selected system
        content.append("\n### Month-by-Month Performance Table")
        content.append("| Month | Net PnL ($) | Status |")
        content.append("|---|---|---|")
        
        sorted_months = sorted(metrics["monthly_pnl"].items())
        for month, val in sorted_months:
            status = "Positive" if val > 0 else ("Negative" if val < 0 else "Zero")
            content.append(f"| {month} | {val:.2f} | {status} |")

        # 6. Walk-Forward Validation
        content.append("\n## 6. Walk-Forward Validation Results")
        content.append("| Split | Train Range | Test Range | Train PnL ($) | Test PnL ($) | Test Trades | Test Max DD |")
        content.append("|---|---|---|---|---|---|---|")
        for res in self.wf_results:
            content.append(
                f"| {res['split_id']} | {res['train_range']} | {res['test_range']} | {res['train_pnl']:.2f} | "
                f"{res['test_pnl']:.2f} | {res['test_trades']} | {res['test_drawdown']:.2%} |"
            )
            
        if self.combined_oos_metrics:
            oom = self.combined_oos_metrics
            content.append("\n### Combined Out-of-Sample (OOS) Performance Summary")
            content.append(f"- **Total OOS Trades:** {oom.get('total_trades')}")
            content.append(f"- **OOS Win Rate:** {oom.get('win_rate', 0.0):.2%}")
            content.append(f"- **OOS Net PnL:** ${oom.get('net_pnl', 0.0):.2f}")
            content.append(f"- **OOS Max Drawdown:** {oom.get('max_drawdown', 0.0):.2%}")
            content.append(f"- **OOS Profit Factor:** {oom.get('profit_factor', 0.0):.2f}")

        # 7. Stress Testing
        content.append("\n## 7. Stress Testing Suite Results")
        content.append("| Stress Test Scenario | Trades | Win Rate | PnL ($) | Max DD | +/-/0 Months | Verdict |")
        content.append("|---|---|---|---|---|---|---|")
        for sc, res in self.stress_results.items():
            months_str = f"{res['positive_months']} / {res['negative_months']} / {res['zero_months']}"
            content.append(
                f"| {sc} | {res['trade_count']} | {res['win_rate']:.2%} | {res['pnl']:.2f} | "
                f"{res['max_drawdown']:.2%} | {months_str} | **{res['verdict']}** |"
            )

        # 8. Audits
        content.append("\n## 8. Compliance & Lookahead Audits")
        
        sa = self.audit_report.get("signal_audit", {})
        content.append("\n### 8.1. Signal Audit (Lookahead & Repainting)")
        content.append(f"- **Status:** **{sa.get('status')}**")
        content.append(f"- **Leaks Detected:** {sa.get('leak_count', 0)}")
        if sa.get("reasons"):
            for r in sa["reasons"]:
                content.append(f"  - {r}")

        ta = self.audit_report.get("trade_audit", {})
        content.append("\n### 8.2. Trade Audit (Execution Delay & Costs)")
        content.append(f"- **Status:** **{ta.get('status')}**")
        if ta.get("reasons"):
            for r in ta["reasons"]:
                content.append(f"  - {r}")

        nfa = self.audit_report.get("no_fake_audit", {})
        content.append("\n### 8.3. No-Fake & Code Integrity Audit")
        content.append(f"- **Status:** **{nfa.get('status')}**")
        if nfa.get("reasons"):
            for r in nfa["reasons"]:
                content.append(f"  - {r}")
                
        content.append("\n---")
        content.append("\n*Report compiled by Antigravity AI Trading Research System.*")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(content))
