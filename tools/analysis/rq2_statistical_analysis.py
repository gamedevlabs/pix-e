#!/usr/bin/env python3
"""
RQ2 Statistical Analysis for Trap Detection Experiments.

This script performs comprehensive statistical analysis on trap detection results
comparing 5 context engineering strategies across 2 models.

Analyses performed:
1. Detection rates per strategy (with 95% CI)
2. Detection rates per trap type x strategy (heatmap)
3. Cochran's Q test (compare all 5 strategies)
4. McNemar's tests (pairwise with Bonferroni correction)
5. Odds ratios with 95% CI (effect sizes vs baseline)
6. Model comparison (GPT-4o-mini vs GPT-5.2)
7. Efficiency analysis (tokens, execution time)

Usage:
    python rq2_statistical_analysis.py --gpt4o-mini <path> --gpt5 <path> --output <dir>
"""

import argparse
import json
import warnings
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=RuntimeWarning)


# =============================================================================
# Configuration
# =============================================================================

STRATEGIES = [
    "full_context",
    "structural_memory",
    "simple_sm",
    "hierarchical_graph",
    "hmem",
]

STRATEGY_DISPLAY_NAMES = {
    "full_context": "Full Context",
    "structural_memory": "Structural Memory",
    "simple_sm": "Simple SM",
    "hierarchical_graph": "H-Graph",
    "hmem": "H-MEM",
}

TRAP_TYPES = [
    "missing_mpip",
    "misapplied_mpip",
    "path_mismatch",
    "global_incoherence",
    "internal_incoherence",
]

BASELINE_STRATEGY = "full_context"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AnalysisResults:
    """Container for all analysis results."""

    # Detection rates
    detection_rates_by_strategy: pd.DataFrame
    detection_rates_by_trap_type: pd.DataFrame
    detection_rates_heatmap: pd.DataFrame

    # Statistical tests
    cochrans_q_result: dict
    mcnemar_pairwise: pd.DataFrame
    mcnemar_vs_baseline: pd.DataFrame

    # Effect sizes
    odds_ratios_vs_baseline: pd.DataFrame

    # Model comparison (if two models provided)
    model_comparison: Optional[pd.DataFrame]
    model_mcnemar: Optional[dict]

    # Efficiency
    efficiency_by_strategy: pd.DataFrame

    # Raw data
    raw_data: pd.DataFrame


# =============================================================================
# Data Loading
# =============================================================================


def load_data(filepath: Path) -> pd.DataFrame:
    """Load and validate trap detection CSV data."""
    # Try semicolon delimiter first (based on your data format)
    df = pd.read_csv(filepath, delimiter=";")

    # Validate required columns
    required_cols = ["node_title", "strategy", "detected", "trap_type"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Normalize detected column to boolean
    if df["detected"].dtype == object:
        df["detected"] = df["detected"].str.upper().map({"TRUE": True, "FALSE": False})
    df["detected"] = df["detected"].astype(bool)

    # Normalize strategy names to lowercase
    df["strategy"] = df["strategy"].str.lower().str.strip()

    # Normalize trap types
    df["trap_type"] = df["trap_type"].str.lower().str.strip()

    print(f"Loaded {len(df)} rows from {filepath.name}")
    print(f"  Strategies: {df['strategy'].unique().tolist()}")
    print(f"  Trap types: {df['trap_type'].unique().tolist()}")
    print(f"  Detection rate: {df['detected'].mean():.1%}")

    return df


# =============================================================================
# Detection Rate Calculations
# =============================================================================


def calculate_detection_rates_by_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate detection rate per strategy with 95% CI."""
    results = []

    for strategy in STRATEGIES:
        strategy_data = df[df["strategy"] == strategy]
        n = len(strategy_data)
        detected = strategy_data["detected"].sum()
        rate = detected / n if n > 0 else 0

        # Wilson score interval for 95% CI
        ci_low, ci_high = wilson_ci(detected, n)

        results.append(
            {
                "strategy": STRATEGY_DISPLAY_NAMES.get(strategy, strategy),
                "strategy_key": strategy,
                "n": n,
                "detected": detected,
                "detection_rate": rate,
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )

    return pd.DataFrame(results)


def calculate_detection_rates_by_trap_type(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate detection rate per trap type with 95% CI."""
    results = []

    for trap_type in df["trap_type"].unique():
        trap_data = df[df["trap_type"] == trap_type]
        n = len(trap_data)
        detected = trap_data["detected"].sum()
        rate = detected / n if n > 0 else 0

        ci_low, ci_high = wilson_ci(detected, n)

        results.append(
            {
                "trap_type": trap_type,
                "n": n,
                "detected": detected,
                "detection_rate": rate,
                "ci_low": ci_low,
                "ci_high": ci_high,
            }
        )

    return pd.DataFrame(results)


def calculate_detection_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate detection rate matrix: trap_type x strategy."""
    # Pivot to get rates
    pivot = df.pivot_table(
        values="detected", index="trap_type", columns="strategy", aggfunc="mean"
    )

    # Reorder columns to match STRATEGIES order
    available_strategies = [s for s in STRATEGIES if s in pivot.columns]
    pivot = pivot[available_strategies]

    # Rename columns for display
    pivot.columns = [STRATEGY_DISPLAY_NAMES.get(s, s) for s in pivot.columns]

    return pivot


def wilson_ci(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0

    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p = successes / n

    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator

    return max(0, center - margin), min(1, center + margin)


# =============================================================================
# Statistical Tests
# =============================================================================


def cochrans_q_test(df: pd.DataFrame) -> dict:
    """
    Perform Cochran's Q test to compare all strategies.

    Cochran's Q is the extension of McNemar's test for >2 related samples.
    Tests whether the detection rates differ significantly across strategies.
    """
    # Create binary matrix: rows = traps, columns = strategies
    # Each trap should appear once per strategy
    pivot = df.pivot_table(
        values="detected",
        index="node_title",
        columns="strategy",
        aggfunc="first",  # Take first if duplicates
    )

    # Keep only strategies we care about
    available_strategies = [s for s in STRATEGIES if s in pivot.columns]
    pivot = pivot[available_strategies]

    # Drop rows with any missing values
    pivot = pivot.dropna()

    if len(pivot) < 5:
        return {
            "statistic": np.nan,
            "p_value": np.nan,
            "df": np.nan,
            "n_samples": len(pivot),
            "error": "Insufficient complete cases",
        }

    # Convert to numpy array for calculation
    data = pivot.values.astype(int)
    k = data.shape[1]  # Number of strategies
    n = data.shape[0]  # Number of traps

    # Row sums (number of strategies that detected each trap)
    row_sums = data.sum(axis=1)

    # Column sums (number of traps detected by each strategy)
    col_sums = data.sum(axis=0)

    # Cochran's Q statistic
    grand_sum = data.sum()
    numerator = (k - 1) * (k * np.sum(col_sums**2) - grand_sum**2)
    denominator = k * grand_sum - np.sum(row_sums**2)

    if denominator == 0:
        q_stat = 0
        p_value = 1.0
    else:
        q_stat = numerator / denominator
        # Q follows chi-square distribution with k-1 degrees of freedom
        p_value = 1 - stats.chi2.cdf(q_stat, k - 1)

    return {
        "statistic": q_stat,
        "p_value": p_value,
        "df": k - 1,
        "n_samples": n,
        "n_strategies": k,
        "strategies": available_strategies,
    }


def mcnemar_pairwise_tests(
    df: pd.DataFrame, correction: bool = True
) -> pd.DataFrame:
    """
    Perform pairwise McNemar's tests between all strategy pairs.

    Returns matrix of p-values with Bonferroni correction.
    """
    # Pivot data
    pivot = df.pivot_table(
        values="detected",
        index="node_title",
        columns="strategy",
        aggfunc="first",
    )

    available_strategies = [s for s in STRATEGIES if s in pivot.columns]
    pivot = pivot[available_strategies].dropna()

    n_comparisons = len(list(combinations(available_strategies, 2)))
    results = []

    for strat1, strat2 in combinations(available_strategies, 2):
        a = pivot[strat1].values.astype(int)
        b = pivot[strat2].values.astype(int)

        # Contingency table
        # b01: strat1=0, strat2=1 (strat2 detected, strat1 didn't)
        # b10: strat1=1, strat2=0 (strat1 detected, strat2 didn't)
        b01 = np.sum((a == 0) & (b == 1))
        b10 = np.sum((a == 1) & (b == 0))

        # McNemar's test
        if b01 + b10 == 0:
            p_value = 1.0
            statistic = 0
        else:
            if correction and b01 + b10 < 25:
                # Exact binomial test for small samples
                result = stats.binomtest(b01, b01 + b10, 0.5)
                p_value = result.pvalue
                statistic = np.nan
            else:
                # Chi-square approximation with continuity correction
                statistic = (abs(b01 - b10) - 1) ** 2 / (b01 + b10)
                p_value = 1 - stats.chi2.cdf(statistic, 1)

        # Bonferroni correction
        p_adjusted = min(1.0, p_value * n_comparisons)

        results.append(
            {
                "strategy_1": STRATEGY_DISPLAY_NAMES.get(strat1, strat1),
                "strategy_2": STRATEGY_DISPLAY_NAMES.get(strat2, strat2),
                "strategy_1_key": strat1,
                "strategy_2_key": strat2,
                "b01": b01,
                "b10": b10,
                "statistic": statistic,
                "p_value": p_value,
                "p_adjusted": p_adjusted,
                "significant": p_adjusted < 0.05,
            }
        )

    return pd.DataFrame(results)


def mcnemar_vs_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform McNemar's test comparing each strategy to baseline (full_context).
    """
    pivot = df.pivot_table(
        values="detected",
        index="node_title",
        columns="strategy",
        aggfunc="first",
    )

    if BASELINE_STRATEGY not in pivot.columns:
        raise ValueError(f"Baseline strategy '{BASELINE_STRATEGY}' not in data")

    baseline = pivot[BASELINE_STRATEGY].values.astype(int)
    available_strategies = [
        s for s in STRATEGIES if s in pivot.columns and s != BASELINE_STRATEGY
    ]

    n_comparisons = len(available_strategies)
    results = []

    for strategy in available_strategies:
        other = pivot[strategy].values.astype(int)

        # b01: baseline=0, other=1 (other detected, baseline didn't)
        # b10: baseline=1, other=0 (baseline detected, other didn't)
        b01 = np.sum((baseline == 0) & (other == 1))
        b10 = np.sum((baseline == 1) & (other == 0))

        if b01 + b10 == 0:
            p_value = 1.0
            statistic = 0
        elif b01 + b10 < 25:
            p_value = stats.binomtest(b01, b01 + b10, 0.5).pvalue
            statistic = np.nan
        else:
            statistic = (abs(b01 - b10) - 1) ** 2 / (b01 + b10)
            p_value = 1 - stats.chi2.cdf(statistic, 1)

        p_adjusted = min(1.0, p_value * n_comparisons)

        results.append(
            {
                "strategy": STRATEGY_DISPLAY_NAMES.get(strategy, strategy),
                "strategy_key": strategy,
                "baseline_only": b10,
                "strategy_only": b01,
                "both": np.sum((baseline == 1) & (other == 1)),
                "neither": np.sum((baseline == 0) & (other == 0)),
                "statistic": statistic,
                "p_value": p_value,
                "p_adjusted": p_adjusted,
                "significant": p_adjusted < 0.05,
                "direction": "better" if b01 > b10 else ("worse" if b10 > b01 else "equal"),
            }
        )

    return pd.DataFrame(results)


def calculate_odds_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate odds ratios comparing each strategy to baseline.

    OR > 1 means strategy detects more than baseline.
    """
    pivot = df.pivot_table(
        values="detected",
        index="node_title",
        columns="strategy",
        aggfunc="first",
    )

    if BASELINE_STRATEGY not in pivot.columns:
        raise ValueError(f"Baseline strategy '{BASELINE_STRATEGY}' not in data")

    baseline = pivot[BASELINE_STRATEGY].values.astype(int)
    available_strategies = [
        s for s in STRATEGIES if s in pivot.columns and s != BASELINE_STRATEGY
    ]

    results = []

    for strategy in available_strategies:
        other = pivot[strategy].values.astype(int)

        # 2x2 contingency table
        a = np.sum((baseline == 1) & (other == 1))  # Both detect
        b = np.sum((baseline == 1) & (other == 0))  # Baseline only
        c = np.sum((baseline == 0) & (other == 1))  # Strategy only
        d = np.sum((baseline == 0) & (other == 0))  # Neither

        # Odds ratio with Haldane-Anscombe correction for zeros
        a_adj, b_adj, c_adj, d_adj = a + 0.5, b + 0.5, c + 0.5, d + 0.5

        odds_ratio = (a_adj * d_adj) / (b_adj * c_adj)

        # Log odds ratio and SE for CI
        log_or = np.log(odds_ratio)
        se_log_or = np.sqrt(1 / a_adj + 1 / b_adj + 1 / c_adj + 1 / d_adj)

        ci_low = np.exp(log_or - 1.96 * se_log_or)
        ci_high = np.exp(log_or + 1.96 * se_log_or)

        results.append(
            {
                "strategy": STRATEGY_DISPLAY_NAMES.get(strategy, strategy),
                "strategy_key": strategy,
                "odds_ratio": odds_ratio,
                "or_ci_low": ci_low,
                "or_ci_high": ci_high,
                "log_or": log_or,
                "se_log_or": se_log_or,
                "significant": ci_low > 1 or ci_high < 1,  # CI doesn't include 1
            }
        )

    return pd.DataFrame(results)


# =============================================================================
# Model Comparison
# =============================================================================


def compare_models(df1: pd.DataFrame, df2: pd.DataFrame, name1: str, name2: str) -> tuple[pd.DataFrame, dict]:
    """
    Compare detection rates between two models on the same traps.
    """
    # Add model identifier
    df1 = df1.copy()
    df2 = df2.copy()
    df1["model"] = name1
    df2["model"] = name2

    # Merge on node_title + strategy
    merged = pd.merge(
        df1[["node_title", "strategy", "detected"]],
        df2[["node_title", "strategy", "detected"]],
        on=["node_title", "strategy"],
        suffixes=(f"_{name1}", f"_{name2}"),
    )

    # Overall model comparison
    results = []
    for strategy in STRATEGIES:
        strat_data = merged[merged["strategy"] == strategy]
        if len(strat_data) == 0:
            continue

        rate1 = strat_data[f"detected_{name1}"].mean()
        rate2 = strat_data[f"detected_{name2}"].mean()

        # McNemar's test
        a = strat_data[f"detected_{name1}"].values.astype(int)
        b = strat_data[f"detected_{name2}"].values.astype(int)

        b01 = np.sum((a == 0) & (b == 1))
        b10 = np.sum((a == 1) & (b == 0))

        if b01 + b10 == 0:
            p_value = 1.0
        elif b01 + b10 < 25:
            p_value = stats.binomtest(b01, b01 + b10, 0.5).pvalue
        else:
            statistic = (abs(b01 - b10) - 1) ** 2 / (b01 + b10)
            p_value = 1 - stats.chi2.cdf(statistic, 1)

        results.append(
            {
                "strategy": STRATEGY_DISPLAY_NAMES.get(strategy, strategy),
                f"rate_{name1}": rate1,
                f"rate_{name2}": rate2,
                "difference": rate2 - rate1,
                "p_value": p_value,
                "significant": p_value < 0.05,
            }
        )

    comparison_df = pd.DataFrame(results)

    # Overall model comparison (across all strategies)
    a_all = merged[f"detected_{name1}"].values.astype(int)
    b_all = merged[f"detected_{name2}"].values.astype(int)

    b01_all = np.sum((a_all == 0) & (b_all == 1))
    b10_all = np.sum((a_all == 1) & (b_all == 0))

    if b01_all + b10_all == 0:
        p_overall = 1.0
    elif b01_all + b10_all < 25:
        p_overall = stats.binomtest(b01_all, b01_all + b10_all, 0.5).pvalue
    else:
        stat_overall = (abs(b01_all - b10_all) - 1) ** 2 / (b01_all + b10_all)
        p_overall = 1 - stats.chi2.cdf(stat_overall, 1)

    overall = {
        f"overall_rate_{name1}": a_all.mean(),
        f"overall_rate_{name2}": b_all.mean(),
        "overall_difference": b_all.mean() - a_all.mean(),
        f"{name2}_only": b01_all,
        f"{name1}_only": b10_all,
        "p_value": p_overall,
        "n_samples": len(merged),
    }

    return comparison_df, overall


# =============================================================================
# Efficiency Analysis
# =============================================================================


def analyze_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze token usage and execution time per strategy."""
    results = []

    for strategy in STRATEGIES:
        strat_data = df[df["strategy"] == strategy]
        if len(strat_data) == 0:
            continue

        # Tokens
        if "total_tokens" in df.columns:
            tokens = strat_data["total_tokens"].dropna()
            tokens_mean = tokens.mean()
            tokens_std = tokens.std()
            tokens_median = tokens.median()
        else:
            tokens_mean = tokens_std = tokens_median = np.nan

        # Execution time
        if "execution_time_ms" in df.columns:
            time = strat_data["execution_time_ms"].dropna()
            time_mean = time.mean()
            time_std = time.std()
            time_median = time.median()
        else:
            time_mean = time_std = time_median = np.nan

        results.append(
            {
                "strategy": STRATEGY_DISPLAY_NAMES.get(strategy, strategy),
                "strategy_key": strategy,
                "n": len(strat_data),
                "tokens_mean": tokens_mean,
                "tokens_std": tokens_std,
                "tokens_median": tokens_median,
                "time_mean_ms": time_mean,
                "time_std_ms": time_std,
                "time_median_ms": time_median,
            }
        )

    return pd.DataFrame(results)


# =============================================================================
# Visualization
# =============================================================================


def plot_detection_rates(
    rates_df: pd.DataFrame, output_path: Path, title: str = "Detection Rate by Strategy"
):
    """Plot detection rates with confidence intervals."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(rates_df))
    rates = rates_df["detection_rate"].values
    ci_low = rates_df["ci_low"].values
    ci_high = rates_df["ci_high"].values

    # Error bars
    yerr_low = rates - ci_low
    yerr_high = ci_high - rates

    bars = ax.bar(x, rates, yerr=[yerr_low, yerr_high], capsize=5, color="steelblue", alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(rates_df["strategy"].values, rotation=45, ha="right")
    ax.set_ylabel("Detection Rate")
    ax.set_title(title)
    ax.set_ylim(0, 1)

    # Add value labels
    for i, (rate, low, high) in enumerate(zip(rates, ci_low, ci_high)):
        ax.text(i, rate + 0.02, f"{rate:.1%}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path / "detection_rates_by_strategy.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_path / "detection_rates_by_strategy.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_heatmap(heatmap_df: pd.DataFrame, output_path: Path, title: str = "Detection Rate: Trap Type x Strategy"):
    """Plot detection rate heatmap."""
    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(
        heatmap_df,
        annot=True,
        fmt=".1%",
        cmap="RdYlGn",
        vmin=0,
        vmax=1,
        ax=ax,
        cbar_kws={"label": "Detection Rate"},
    )

    ax.set_title(title)
    ax.set_xlabel("Strategy")
    ax.set_ylabel("Trap Type")

    plt.tight_layout()
    plt.savefig(output_path / "detection_heatmap.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_path / "detection_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_model_comparison(
    comparison_df: pd.DataFrame,
    output_path: Path,
    name1: str = "GPT-4o-mini",
    name2: str = "GPT-5.2",
):
    """Plot model comparison bar chart."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(comparison_df))
    width = 0.35

    rate1_col = f"rate_{name1}"
    rate2_col = f"rate_{name2}"

    bars1 = ax.bar(x - width / 2, comparison_df[rate1_col], width, label=name1, alpha=0.8)
    bars2 = ax.bar(x + width / 2, comparison_df[rate2_col], width, label=name2, alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df["strategy"], rotation=45, ha="right")
    ax.set_ylabel("Detection Rate")
    ax.set_title(f"Detection Rate Comparison: {name1} vs {name2}")
    ax.legend()
    ax.set_ylim(0, 1)

    # Add significance markers
    for i, sig in enumerate(comparison_df["significant"]):
        if sig:
            max_rate = max(comparison_df[rate1_col].iloc[i], comparison_df[rate2_col].iloc[i])
            ax.text(i, max_rate + 0.02, "*", ha="center", va="bottom", fontsize=14, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path / "model_comparison.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_path / "model_comparison.png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_odds_ratios(or_df: pd.DataFrame, output_path: Path):
    """Plot odds ratios with confidence intervals (forest plot style)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    y = range(len(or_df))
    ors = or_df["odds_ratio"].values
    ci_low = or_df["or_ci_low"].values
    ci_high = or_df["or_ci_high"].values

    # Error bars
    xerr_low = ors - ci_low
    xerr_high = ci_high - ors

    ax.errorbar(
        ors,
        y,
        xerr=[xerr_low, xerr_high],
        fmt="o",
        capsize=5,
        color="steelblue",
        markersize=8,
    )

    # Reference line at OR=1
    ax.axvline(x=1, color="red", linestyle="--", alpha=0.7, label="No effect (OR=1)")

    ax.set_yticks(y)
    ax.set_yticklabels(or_df["strategy"].values)
    ax.set_xlabel("Odds Ratio (vs Full Context)")
    ax.set_title("Effect Size: Odds Ratios vs Baseline")
    ax.legend()

    # Add value labels
    for i, (or_val, low, high) in enumerate(zip(ors, ci_low, ci_high)):
        ax.text(or_val, i + 0.2, f"{or_val:.2f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path / "odds_ratios.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(output_path / "odds_ratios.png", dpi=300, bbox_inches="tight")
    plt.close()


# =============================================================================
# Report Generation
# =============================================================================


def generate_report(results: AnalysisResults, output_path: Path, model_name: str = ""):
    """Generate markdown report of all results."""
    report_lines = [
        "# RQ2 Statistical Analysis Report",
        f"\n**Model:** {model_name}" if model_name else "",
        f"\n**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        "\n---\n",
        "## 1. Detection Rates by Strategy\n",
    ]

    # Detection rates table
    rates = results.detection_rates_by_strategy
    report_lines.append("| Strategy | N | Detected | Rate | 95% CI |")
    report_lines.append("|----------|---|----------|------|--------|")
    for _, row in rates.iterrows():
        report_lines.append(
            f"| {row['strategy']} | {row['n']} | {row['detected']} | "
            f"{row['detection_rate']:.1%} | [{row['ci_low']:.1%}, {row['ci_high']:.1%}] |"
        )

    # Cochran's Q
    report_lines.append("\n## 2. Cochran's Q Test (All Strategies)\n")
    q = results.cochrans_q_result
    report_lines.append(f"- **Q statistic:** {q['statistic']:.2f}")
    report_lines.append(f"- **df:** {q['df']}")
    report_lines.append(f"- **p-value:** {q['p_value']:.4f}")
    report_lines.append(f"- **N samples:** {q['n_samples']}")
    sig = "Yes" if q["p_value"] < 0.05 else "No"
    report_lines.append(f"- **Significant (p < 0.05):** {sig}")

    # McNemar vs baseline
    report_lines.append("\n## 3. McNemar's Test vs Baseline (Full Context)\n")
    report_lines.append(
        "| Strategy | Strategy Only | Baseline Only | p-value | p-adjusted | Direction |"
    )
    report_lines.append("|----------|---------------|---------------|---------|------------|-----------|")
    for _, row in results.mcnemar_vs_baseline.iterrows():
        sig_marker = "*" if row["significant"] else ""
        report_lines.append(
            f"| {row['strategy']} | {row['strategy_only']} | {row['baseline_only']} | "
            f"{row['p_value']:.4f} | {row['p_adjusted']:.4f}{sig_marker} | {row['direction']} |"
        )

    # Odds ratios
    report_lines.append("\n## 4. Odds Ratios vs Baseline\n")
    report_lines.append("| Strategy | OR | 95% CI | Significant |")
    report_lines.append("|----------|----|----- --|-------------|")
    for _, row in results.odds_ratios_vs_baseline.iterrows():
        sig = "Yes" if row["significant"] else "No"
        report_lines.append(
            f"| {row['strategy']} | {row['odds_ratio']:.2f} | "
            f"[{row['or_ci_low']:.2f}, {row['or_ci_high']:.2f}] | {sig} |"
        )

    # Detection heatmap (as table)
    report_lines.append("\n## 5. Detection Rate by Trap Type x Strategy\n")
    heatmap = results.detection_rates_heatmap
    report_lines.append("| Trap Type | " + " | ".join(heatmap.columns) + " |")
    report_lines.append("|-----------|" + "|".join(["-------"] * len(heatmap.columns)) + "|")
    for trap_type, row in heatmap.iterrows():
        values = " | ".join([f"{v:.1%}" for v in row.values])
        report_lines.append(f"| {trap_type} | {values} |")

    # Model comparison
    if results.model_comparison is not None:
        report_lines.append("\n## 6. Model Comparison\n")
        mc = results.model_comparison
        cols = mc.columns.tolist()
        report_lines.append("| " + " | ".join(cols) + " |")
        report_lines.append("|" + "|".join(["-------"] * len(cols)) + "|")
        for _, row in mc.iterrows():
            vals = []
            for col in cols:
                v = row[col]
                if isinstance(v, float):
                    if "rate" in col.lower():
                        vals.append(f"{v:.1%}")
                    elif "p_value" in col.lower():
                        vals.append(f"{v:.4f}")
                    else:
                        vals.append(f"{v:.2f}")
                else:
                    vals.append(str(v))
            report_lines.append("| " + " | ".join(vals) + " |")

        if results.model_mcnemar:
            mm = results.model_mcnemar
            report_lines.append(f"\n**Overall Model Comparison:**")
            for k, v in mm.items():
                if isinstance(v, float):
                    report_lines.append(f"- {k}: {v:.4f}")
                else:
                    report_lines.append(f"- {k}: {v}")

    # Efficiency
    report_lines.append("\n## 7. Efficiency Analysis\n")
    eff = results.efficiency_by_strategy
    report_lines.append(
        "| Strategy | N | Tokens (mean) | Tokens (median) | Time ms (mean) | Time ms (median) |"
    )
    report_lines.append("|----------|---|---------------|-----------------|----------------|------------------|")
    for _, row in eff.iterrows():
        report_lines.append(
            f"| {row['strategy']} | {row['n']} | "
            f"{row['tokens_mean']:.0f} | {row['tokens_median']:.0f} | "
            f"{row['time_mean_ms']:.0f} | {row['time_median_ms']:.0f} |"
        )

    # Write report
    report_path = output_path / "analysis_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Report saved to {report_path}")


# =============================================================================
# Main Analysis
# =============================================================================


def run_analysis(
    df: pd.DataFrame, output_path: Path, model_name: str = ""
) -> AnalysisResults:
    """Run complete analysis on a single dataset."""
    print(f"\n{'='*60}")
    print(f"Running analysis for {model_name or 'dataset'}")
    print(f"{'='*60}\n")

    # Detection rates
    print("Calculating detection rates...")
    rates_by_strategy = calculate_detection_rates_by_strategy(df)
    rates_by_trap = calculate_detection_rates_by_trap_type(df)
    heatmap = calculate_detection_heatmap(df)

    # Statistical tests
    print("Running Cochran's Q test...")
    cochrans_q = cochrans_q_test(df)

    print("Running McNemar's pairwise tests...")
    mcnemar_pairs = mcnemar_pairwise_tests(df)

    print("Running McNemar's tests vs baseline...")
    mcnemar_baseline = mcnemar_vs_baseline(df)

    print("Calculating odds ratios...")
    odds_ratios = calculate_odds_ratios(df)

    # Efficiency
    print("Analyzing efficiency...")
    efficiency = analyze_efficiency(df)

    results = AnalysisResults(
        detection_rates_by_strategy=rates_by_strategy,
        detection_rates_by_trap_type=rates_by_trap,
        detection_rates_heatmap=heatmap,
        cochrans_q_result=cochrans_q,
        mcnemar_pairwise=mcnemar_pairs,
        mcnemar_vs_baseline=mcnemar_baseline,
        odds_ratios_vs_baseline=odds_ratios,
        model_comparison=None,
        model_mcnemar=None,
        efficiency_by_strategy=efficiency,
        raw_data=df,
    )

    # Generate visualizations
    print("Generating visualizations...")
    plot_detection_rates(rates_by_strategy, output_path, f"Detection Rate by Strategy ({model_name})")
    plot_heatmap(heatmap, output_path, f"Detection Rate Heatmap ({model_name})")
    plot_odds_ratios(odds_ratios, output_path)

    # Generate report
    generate_report(results, output_path, model_name)

    # Save raw results as CSV
    rates_by_strategy.to_csv(output_path / "detection_rates_by_strategy.csv", index=False)
    rates_by_trap.to_csv(output_path / "detection_rates_by_trap_type.csv", index=False)
    heatmap.to_csv(output_path / "detection_heatmap.csv")
    mcnemar_pairs.to_csv(output_path / "mcnemar_pairwise.csv", index=False)
    mcnemar_baseline.to_csv(output_path / "mcnemar_vs_baseline.csv", index=False)
    odds_ratios.to_csv(output_path / "odds_ratios.csv", index=False)
    efficiency.to_csv(output_path / "efficiency.csv", index=False)

    # Save Cochran's Q as JSON
    with open(output_path / "cochrans_q.json", "w") as f:
        json.dump(cochrans_q, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="RQ2 Statistical Analysis")
    parser.add_argument(
        "--gpt4o-mini",
        type=Path,
        help="Path to GPT-4o-mini results CSV",
    )
    parser.add_argument(
        "--gpt5",
        type=Path,
        help="Path to GPT-5.2 results CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis_output"),
        help="Output directory for results",
    )
    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    results = {}

    # Analyze GPT-4o-mini
    if args.gpt4o_mini and args.gpt4o_mini.exists():
        gpt4_output = args.output / "gpt4o_mini"
        gpt4_output.mkdir(exist_ok=True)
        df_gpt4 = load_data(args.gpt4o_mini)
        results["gpt4o_mini"] = run_analysis(df_gpt4, gpt4_output, "GPT-4o-mini")

    # Analyze GPT-5.2
    if args.gpt5 and args.gpt5.exists():
        gpt5_output = args.output / "gpt5"
        gpt5_output.mkdir(exist_ok=True)
        df_gpt5 = load_data(args.gpt5)
        results["gpt5"] = run_analysis(df_gpt5, gpt5_output, "GPT-5.2")

    # Model comparison
    if "gpt4o_mini" in results and "gpt5" in results:
        print("\n" + "=" * 60)
        print("Running model comparison...")
        print("=" * 60 + "\n")

        comparison_output = args.output / "model_comparison"
        comparison_output.mkdir(exist_ok=True)

        comparison_df, overall = compare_models(
            results["gpt4o_mini"].raw_data,
            results["gpt5"].raw_data,
            "GPT-4o-mini",
            "GPT-5.2",
        )

        comparison_df.to_csv(comparison_output / "model_comparison.csv", index=False)
        with open(comparison_output / "model_comparison_overall.json", "w") as f:
            json.dump(overall, f, indent=2, default=str)

        plot_model_comparison(comparison_df, comparison_output)

        # Update results with comparison
        results["gpt4o_mini"].model_comparison = comparison_df
        results["gpt4o_mini"].model_mcnemar = overall

        print(f"Model comparison saved to {comparison_output}")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
