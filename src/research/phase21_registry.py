"""
src/research/phase21_registry.py

Phase 21 - Real Candidate Registry Builder.
Generates structured candidates with full metadata:
- candidate_id, candidate_hash, family, hypothesis
- primary_1h_setup, lower_tf_confirmation, quality_gates
- exit_module, risk_module, portfolio_role
- parameters_json, complexity_score, overfit_risk_score
- live_known_proof, expected_failure_mode

Generates an initial registry of 1,000+ real candidates across
9 primary setup families x multiple parameter variations.
"""
import hashlib
import itertools
import json
import csv
import os

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# Setup family definitions
SETUP_FAMILIES = [
    "breakout_retest",
    "bb_atr_expansion",
    "volatility_compression_to_expansion",
    "trend_pullback_continuation",
    "failed_breakdown_reclaim",
    "vwap_reclaim",
    "ema50_ema200_pullback",
    "funding_safe_momentum",
    "session_impulse",
]

LTF_CONFIRMATIONS = [
    "5m_retest",
    "15m_retest",
    "5m_pullback_reclaim",
    "15m_reclaim",
    "structure_higher_low",
    "wick_rejection",
    "volume_impulse_confirmation",
]

QUALITY_GATES = [
    "expected_r_gate",
    "adx_slope_gate",
    "atr_percentile_gate",
    "bb_width_gate",
    "funding_safety_gate",
    "volume_impulse_gate",
    "chop_toxicity_filter",
]

EXIT_MODULES = [
    "fixed_atr_tp",
    "dynamic_atr_tp",
    "structure_tp",
    "failed_continuation_exit",
    "breakeven_after_mfe",
    "funding_aware_exit",
]

RISK_MODULES = [
    "fixed_risk_1pct",
    "fixed_risk_0_5pct",
    "dynamic_risk_scaling",
]

TP_ATR_MULTS        = [1.8, 2.0, 2.5, 3.0, 3.5]
SL_ATR_MULTS        = [1.2, 1.5, 1.8, 2.0, 2.5]
BB_WIDTH_THRESH     = [0.04, 0.06, 0.08, 0.10]
ADX_THRESHOLDS      = [15, 20, 25, 30]
EXPECTED_R_THRESHOLDS = [1.20, 1.30, 1.40, 1.50]

TEMPLATE_TYPE_MAP = {
    "breakout_retest":                     "bollinger_expansion_breakout",
    "bb_atr_expansion":                    "bollinger_expansion_breakout",
    "volatility_compression_to_expansion": "atr_volatility_expansion",
    "trend_pullback_continuation":         "bollinger_expansion_breakout",
    "failed_breakdown_reclaim":            "prior_day_sweep_reclaim",
    "vwap_reclaim":                        "vwap_deviation_return",
    "ema50_ema200_pullback":               "bollinger_expansion_breakout",
    "funding_safe_momentum":               "funding_extreme_reversal",
    "session_impulse":                     "bollinger_expansion_breakout",
}

FAMILY_HYPOTHESES = {
    "breakout_retest":                     "Price breaks Bollinger Band, retests, continues in breakout direction.",
    "bb_atr_expansion":                    "ATR+BB width expansion signals start of directional move.",
    "volatility_compression_to_expansion": "BB squeeze then ATR expansion triggers momentum entry.",
    "trend_pullback_continuation":         "Price above EMA200, pulls back to EMA50, continues trend.",
    "failed_breakdown_reclaim":            "Price sweeps prior-day low then immediately reclaims it.",
    "vwap_reclaim":                        "Price rejects below VWAP, reclaims on volume surge.",
    "ema50_ema200_pullback":               "Golden cross with pullback to EMA50 and wick rejection.",
    "funding_safe_momentum":               "Funding extreme with BB expansion; contrarian momentum.",
    "session_impulse":                     "Session open impulse breakout retest in first 2h.",
}

FAMILY_FAILURE_MODES = {
    "breakout_retest":                     "False breakout in range; retest fails, price reverses inside band.",
    "bb_atr_expansion":                    "Volatility spike without follow-through; price mean-reverts.",
    "volatility_compression_to_expansion": "Multiple false expansions in sideways chop.",
    "trend_pullback_continuation":         "Trend reversal: EMA50 pullback becomes new downtrend leg.",
    "failed_breakdown_reclaim":            "True breakdown: price fails to reclaim, continues lower.",
    "vwap_reclaim":                        "Institutional flow overrides VWAP reclaim.",
    "ema50_ema200_pullback":               "EMA death cross during pullback; golden cross invalidated.",
    "funding_safe_momentum":               "Funding normalises without directional follow-through.",
    "session_impulse":                     "Session fake-out reverses within first hour; whipsaw.",
}

def _complexity_score(ltf_conf, quality_gates, exit_mod, risk_mod):
    score = 2
    score += 1
    score += len(quality_gates)
    if "dynamic" in exit_mod:
        score += 1
    if "dynamic" in risk_mod:
        score += 1
    return score

def _overfit_risk_score(family, tp_mult, sl_mult, adx_thresh, expected_r_thresh):
    score = 1
    if tp_mult > 3.0:
        score += 1
    if sl_mult < 1.5:
        score += 1
    if adx_thresh > 25:
        score += 1
    if expected_r_thresh > 1.45:
        score += 1
    return min(score, 5)

def generate_registry(output_path: str) -> list:
    """
    Generate a candidate registry of >= 1,000 entries.
    Returns list of candidate dicts and writes CSV.
    """
    candidates = []
    candidate_id = 0

    for family in SETUP_FAMILIES:
        template_type = TEMPLATE_TYPE_MAP[family]
        hypothesis    = FAMILY_HYPOTHESES[family]
        failure_mode  = FAMILY_FAILURE_MODES[family]

        for ltf_conf in LTF_CONFIRMATIONS:
            for tp_mult, sl_mult, bb_w, adx_t, er_t in itertools.product(
                TP_ATR_MULTS, SL_ATR_MULTS, BB_WIDTH_THRESH, ADX_THRESHOLDS, EXPECTED_R_THRESHOLDS
            ):
                if tp_mult / sl_mult < 1.3:
                    continue

                gate_idx = (candidate_id % len(QUALITY_GATES))
                gates = [QUALITY_GATES[gate_idx], QUALITY_GATES[(gate_idx + 2) % len(QUALITY_GATES)]]
                exit_mod = EXIT_MODULES[candidate_id % len(EXIT_MODULES)]
                risk_mod = RISK_MODULES[candidate_id % len(RISK_MODULES)]
                portfolio_role = "core" if family in ("breakout_retest", "bb_atr_expansion") else "sleeve"

                params = {
                    "template_type": template_type,
                    "regime_filter_mode": "strict" if family in ("breakout_retest", "bb_atr_expansion") else "no_filter",
                    "tp_atr_mult": tp_mult,
                    "sl_atr_mult": sl_mult,
                    "bb_width_thresh": bb_w,
                    "adx_thresh": adx_t,
                    "expected_r_threshold": er_t,
                    "trend_filter": "ema_200" if family in ("trend_pullback_continuation", "ema50_ema200_pullback") else None,
                    "rsi_overbought": 100,
                    "rsi_oversold": 0,
                    "wick_ratio_thresh": 0.45,
                }
                params_json  = json.dumps(params, sort_keys=True)
                cand_hash    = get_hash(f"{family}:{ltf_conf}:{params_json}")
                complexity   = _complexity_score(ltf_conf, gates, exit_mod, risk_mod)
                overfit_risk = _overfit_risk_score(family, tp_mult, sl_mult, adx_t, er_t)

                cand = {
                    "candidate_id":           candidate_id,
                    "candidate_hash":         cand_hash,
                    "family":                 family,
                    "hypothesis":             hypothesis,
                    "primary_1h_setup":       family,
                    "lower_tf_confirmation":  ltf_conf,
                    "quality_gates":          "|".join(gates),
                    "exit_module":            exit_mod,
                    "risk_module":            risk_mod,
                    "portfolio_role":         portfolio_role,
                    "parameters_json":        params_json,
                    "complexity_score":       complexity,
                    "overfit_risk_score":     overfit_risk,
                    "live_known_proof":       "closed_candle_only_no_lookahead",
                    "expected_failure_mode":  failure_mode,
                }
                candidates.append(cand)
                candidate_id += 1

                if candidate_id >= 2000:
                    break
            if candidate_id >= 2000:
                break
        if candidate_id >= 2000:
            break

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    if candidates:
        fieldnames = list(candidates[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)

    print(f"[registry] Generated {len(candidates)} candidates -> {output_path}")
    return candidates
