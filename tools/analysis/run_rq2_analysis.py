#!/usr/bin/env python3
"""
Convenience script to run RQ2 analysis with the thesis data files.

Usage:
    python run_rq2_analysis.py
    python run_rq2_analysis.py --gpt4o-mini-only
    python run_rq2_analysis.py --gpt5-only
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rq2_statistical_analysis import load_data, run_analysis, compare_models, plot_model_comparison

# =============================================================================
# File Paths (Update if files move)
# =============================================================================

EXPERIMENTS_DIR = Path(__file__).parent.parent.parent / "docs" / "experiments"

GPT4O_MINI_FILE = EXPERIMENTS_DIR / "trap_detection_combined_fixed_prompts_a12574c.csv"
GPT5_FILE = EXPERIMENTS_DIR / "gpt_5.2_results_with_updated_prompts.csv"

OUTPUT_DIR = EXPERIMENTS_DIR / "analysis_results"


def main():
    parser = argparse.ArgumentParser(description="Run RQ2 Analysis on thesis data")
    parser.add_argument("--gpt4o-mini-only", action="store_true", help="Only analyze GPT-4o-mini")
    parser.add_argument("--gpt5-only", action="store_true", help="Only analyze GPT-5.2")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("RQ2 Statistical Analysis - Trap Detection Experiments")
    print("=" * 70)
    print(f"\nData files:")
    print(f"  GPT-4o-mini: {GPT4O_MINI_FILE}")
    print(f"  GPT-5.2:     {GPT5_FILE}")
    print(f"\nOutput: {args.output}")
    print()

    results = {}

    # Analyze GPT-4o-mini
    if not args.gpt5_only:
        if GPT4O_MINI_FILE.exists():
            print(f"\nLoading GPT-4o-mini data...")
            gpt4_output = args.output / "gpt4o_mini"
            gpt4_output.mkdir(exist_ok=True)
            df_gpt4 = load_data(GPT4O_MINI_FILE)
            results["gpt4o_mini"] = run_analysis(df_gpt4, gpt4_output, "GPT-4o-mini")
        else:
            print(f"WARNING: GPT-4o-mini file not found: {GPT4O_MINI_FILE}")

    # Analyze GPT-5.2
    if not args.gpt4o_mini_only:
        if GPT5_FILE.exists():
            print(f"\nLoading GPT-5.2 data...")
            gpt5_output = args.output / "gpt5"
            gpt5_output.mkdir(exist_ok=True)
            df_gpt5 = load_data(GPT5_FILE)
            results["gpt5"] = run_analysis(df_gpt5, gpt5_output, "GPT-5.2")
        else:
            print(f"WARNING: GPT-5.2 file not found: {GPT5_FILE}")

    # Model comparison
    if "gpt4o_mini" in results and "gpt5" in results:
        print("\n" + "=" * 70)
        print("Running model comparison...")
        print("=" * 70 + "\n")

        comparison_output = args.output / "model_comparison"
        comparison_output.mkdir(exist_ok=True)

        comparison_df, overall = compare_models(
            results["gpt4o_mini"].raw_data,
            results["gpt5"].raw_data,
            "GPT-4o-mini",
            "GPT-5.2",
        )

        comparison_df.to_csv(comparison_output / "model_comparison.csv", index=False)

        import json
        with open(comparison_output / "model_comparison_overall.json", "w") as f:
            json.dump(overall, f, indent=2, default=str)

        plot_model_comparison(comparison_df, comparison_output)

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        print("\n## Detection Rates by Strategy\n")
        print("### GPT-4o-mini")
        for _, row in results["gpt4o_mini"].detection_rates_by_strategy.iterrows():
            print(f"  {row['strategy']:20s}: {row['detection_rate']:.1%} (n={row['n']})")

        print("\n### GPT-5.2")
        for _, row in results["gpt5"].detection_rates_by_strategy.iterrows():
            print(f"  {row['strategy']:20s}: {row['detection_rate']:.1%} (n={row['n']})")

        print("\n## Cochran's Q Test")
        q4 = results["gpt4o_mini"].cochrans_q_result
        q5 = results["gpt5"].cochrans_q_result
        print(f"  GPT-4o-mini: Q={q4['statistic']:.2f}, p={q4['p_value']:.4f}")
        print(f"  GPT-5.2:     Q={q5['statistic']:.2f}, p={q5['p_value']:.4f}")

        print("\n## Model Comparison (Overall)")
        print(f"  GPT-4o-mini overall rate: {overall['overall_rate_GPT-4o-mini']:.1%}")
        print(f"  GPT-5.2 overall rate:     {overall['overall_rate_GPT-5.2']:.1%}")
        print(f"  Difference:               {overall['overall_difference']:.1%}")
        print(f"  McNemar p-value:          {overall['p_value']:.4f}")

        print(f"\nResults saved to {args.output}")

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
