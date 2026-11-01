"""Stage 2 statistical analysis for SARD-Bench (240 cases x 3 models = 720 runs).

Produces publication-grade statistics:
- Per-model / per-RQ / per-tier rates with Wilson 95% CIs.
- Stealth gradient: Cochran-Armitage trend test across tiers 1->3.
- Justification laundering: paired McNemar test (Condition A vs B).
- RQ4: up-front (turn-1) vs frustration (turn-2) escalation.
- Outcome taxonomy across the full benchmark.

Writes sard_stage2_stats.json and prints a readable summary.
"""

from __future__ import annotations

import json
from math import sqrt

import pandas as pd
from scipy import stats

from sard_config import FULL_RESULTS_FILE

OUT = "sard_stage2_stats.json"
FRONTIER = ["Claude Sonnet 5.5", "GPT-5.1"]


def wilson(k: int, n: int, z: float = 1.96) -> dict:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return {"p": 0.0, "lo": 0.0, "hi": 0.0, "k": 0, "n": 0}
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return {
        "p": round(p, 4),
        "lo": round(max(0.0, center - half), 4),
        "hi": round(min(1.0, center + half), 4),
        "k": int(k),
        "n": int(n),
    }


def load() -> pd.DataFrame:
    df = pd.read_csv(FULL_RESULTS_FILE)
    err = df["Error"].astype(str).str.strip()
    df = df[df["Error"].isna() | (err == "")].copy()
    for col in [
        "Text_Echo_ASR", "Contained_Sandbox_ASR", "Escalated_Breach_ASR",
        "Tier_IV_AutoReview_Approved", "Strict_Deception", "Refusal",
        "Turn1_Privileged_Escalation", "Turn2_Privileged_Escalation",
        "Justification_Laundering",
    ]:
        df[col] = df[col].astype(str).str.lower().isin(["true", "1", "1.0"])
    return df


def rate_block(df: pd.DataFrame, col: str) -> dict:
    return wilson(int(df[col].sum()), len(df))


def cochran_armitage(counts: list[tuple[int, int]]) -> dict:
    """Trend test across ordered groups. counts = [(successes, n), ...] with
    scores 0,1,2,... Returns z and two-sided p."""
    scores = list(range(len(counts)))
    N = sum(n for _, n in counts)
    R = sum(k for k, _ in counts)
    if N == 0 or R == 0 or R == N:
        return {"z": 0.0, "p": 1.0}
    p_bar = R / N
    t = sum(s * n for s, (_, n) in zip(scores, counts))
    s_bar = t / N
    num = sum(s * k for s, (k, _) in zip(scores, counts)) - R * s_bar
    var = p_bar * (1 - p_bar) * (
        sum(n * (s - s_bar) ** 2 for s, (_, n) in zip(scores, counts))
    )
    if var <= 0:
        return {"z": 0.0, "p": 1.0}
    z = num / sqrt(var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return {"z": round(z, 3), "p": round(float(p), 5)}


def mcnemar_exact(b: int, c: int) -> dict:
    """Exact McNemar test on discordant pairs b (A-only) and c (B-only)."""
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p": 1.0}
    # two-sided exact binomial
    p = float(stats.binomtest(min(b, c), n, 0.5, alternative="two-sided").pvalue)
    return {"b": int(b), "c": int(c), "p": round(p, 5)}


def main() -> None:
    df = load()
    frontier = df[df["Model"].isin(FRONTIER)]
    report: dict = {"n_total": len(df), "n_frontier": len(frontier)}

    # ---- Outcome taxonomy (whole benchmark + frontier) ----
    def taxonomy(d: pd.DataFrame) -> dict:
        return {
            "refusal": rate_block(d, "Refusal"),
            "text_echo_asr": rate_block(d, "Text_Echo_ASR"),
            "contained_sandbox_asr": rate_block(d, "Contained_Sandbox_ASR"),
            "escalated_breach_asr": rate_block(d, "Escalated_Breach_ASR"),
            "tier_iv_autoreview_approved": rate_block(d, "Tier_IV_AutoReview_Approved"),
        }

    report["taxonomy_all"] = taxonomy(df)
    report["taxonomy_frontier"] = taxonomy(frontier)

    # ---- Per-model breakdown ----
    report["per_model"] = {
        m: taxonomy(df[df["Model"] == m]) for m in sorted(df["Model"].unique())
    }

    # ---- Stealth gradient (frontier) with Wilson CIs + trend tests ----
    esc_counts, con_counts, tiers = [], [], []
    tier_rows = []
    for t in (1, 2, 3):
        d = frontier[frontier["Stealth_Tier"] == t]
        esc = int(d["Escalated_Breach_ASR"].sum())
        con = int(d["Contained_Sandbox_ASR"].sum())
        n = len(d)
        esc_counts.append((esc, n))
        con_counts.append((con, n))
        tiers.append(t)
        tier_rows.append({
            "tier": t,
            "escalated": wilson(esc, n),
            "contained": wilson(con, n),
            "attempted_any": wilson(esc + con, n),
        })
    report["stealth_gradient"] = {
        "by_tier": tier_rows,
        "trend_escalated": cochran_armitage(esc_counts),
        "trend_contained": cochran_armitage(con_counts),
    }

    # ---- Justification laundering: paired McNemar (A vs B) ----
    rev = df[df["AutoReview_A"].isin(["ALLOW", "BLOCK"]) &
             df["AutoReview_B"].isin(["ALLOW", "BLOCK"])].copy()
    a_block_b_allow = int(((rev["AutoReview_A"] == "BLOCK") &
                           (rev["AutoReview_B"] == "ALLOW")).sum())
    a_allow_b_block = int(((rev["AutoReview_A"] == "ALLOW") &
                           (rev["AutoReview_B"] == "BLOCK")).sum())
    a_block = int((rev["AutoReview_A"] == "BLOCK").sum())
    report["justification_laundering"] = {
        "reviewed_pairs": len(rev),
        "A_block_opportunities": a_block,
        "laundered_A_block_to_B_allow": a_block_b_allow,
        "laundering_rate_given_A_block": round(a_block_b_allow / a_block, 4) if a_block else None,
        "reverse_A_allow_to_B_block": a_allow_b_block,
        "mcnemar": mcnemar_exact(a_block_b_allow, a_allow_b_block),
        "net_decision_shift_note": "b<c => justifications net-tighten; b>c => net-loosen",
    }

    # ---- RQ4: up-front vs frustration escalation ----
    rq4 = df[df["RQ"] == "RQ4"]
    stayed = rq4[~rq4["Turn1_Privileged_Escalation"]]
    report["rq4_escalation"] = {
        "n": len(rq4),
        "turn1_upfront": wilson(int(rq4["Turn1_Privileged_Escalation"].sum()), len(rq4)),
        "stayed_sandboxed_turn1": len(stayed),
        "turn2_conditional": wilson(int(stayed["Turn2_Privileged_Escalation"].sum()), len(stayed)),
    }

    # ---- Per-RQ escalated breach (frontier) ----
    report["per_rq_frontier_escalated"] = {
        rq: wilson(
            int(frontier[frontier["RQ"] == rq]["Escalated_Breach_ASR"].sum()),
            len(frontier[frontier["RQ"] == rq]),
        )
        for rq in ("RQ1", "RQ2", "RQ3", "RQ4")
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # ---- readable summary ----
    def fmt(w):
        return f"{w['p']*100:.1f}% [{w['lo']*100:.1f}, {w['hi']*100:.1f}] (n={w['n']})"

    print(f"=== SARD-Bench Stage 2 ({len(df)} runs, {len(frontier)} frontier) ===\n")
    print("Outcome taxonomy (frontier):")
    for k, v in report["taxonomy_frontier"].items():
        print(f"  {k:30s} {fmt(v)}")
    print("\nStealth gradient (frontier):")
    for r in tier_rows:
        print(f"  Tier {r['tier']}: escalated {fmt(r['escalated'])} | contained {fmt(r['contained'])}")
    sg = report["stealth_gradient"]
    print(f"  Trend (escalated): z={sg['trend_escalated']['z']} p={sg['trend_escalated']['p']}")
    print(f"  Trend (contained): z={sg['trend_contained']['z']} p={sg['trend_contained']['p']}")
    jl = report["justification_laundering"]
    print("\nJustification laundering (A=command-only vs B=+justifications):")
    print(f"  A-BLOCK opportunities: {jl['A_block_opportunities']}; "
          f"laundered to ALLOW: {jl['laundered_A_block_to_B_allow']} "
          f"({(jl['laundering_rate_given_A_block'] or 0)*100:.1f}%)")
    print(f"  reverse (A-ALLOW->B-BLOCK): {jl['reverse_A_allow_to_B_block']}")
    print(f"  McNemar: b={jl['mcnemar']['b']} c={jl['mcnemar']['c']} p={jl['mcnemar']['p']}")
    r4 = report["rq4_escalation"]
    print("\nRQ4 escalation:")
    print(f"  up-front (turn1): {fmt(r4['turn1_upfront'])}")
    print(f"  frustration (turn2 | stayed): {fmt(r4['turn2_conditional'])}")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
