"""RQ2 Statistical Analysis Module."""

from .rq2_statistical_analysis import (
    AnalysisResults,
    load_data,
    run_analysis,
    calculate_detection_rates_by_strategy,
    calculate_detection_rates_by_trap_type,
    calculate_detection_heatmap,
    cochrans_q_test,
    mcnemar_pairwise_tests,
    mcnemar_vs_baseline,
    calculate_odds_ratios,
    compare_models,
    analyze_efficiency,
)

__all__ = [
    "AnalysisResults",
    "load_data",
    "run_analysis",
    "calculate_detection_rates_by_strategy",
    "calculate_detection_rates_by_trap_type",
    "calculate_detection_heatmap",
    "cochrans_q_test",
    "mcnemar_pairwise_tests",
    "mcnemar_vs_baseline",
    "calculate_odds_ratios",
    "compare_models",
    "analyze_efficiency",
]
