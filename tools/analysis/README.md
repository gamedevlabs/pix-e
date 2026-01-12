# RQ2 Statistical Analysis

This module performs comprehensive statistical analysis on the RQ2 trap detection experiments.

## Quick Start

```bash
# From the pix-e/tools/analysis directory
python run_rq2_analysis.py
```

This will analyze both GPT-4o-mini and GPT-5.2 results and generate:
- Detection rate tables and visualizations
- Statistical test results (Cochran's Q, McNemar's)
- Effect sizes (odds ratios)
- Model comparison
- Efficiency analysis

## Output

Results are saved to `docs/experiments/analysis_results/`:

```
analysis_results/
├── gpt4o_mini/
│   ├── analysis_report.md           # Full markdown report
│   ├── detection_rates_by_strategy.csv
│   ├── detection_rates_by_trap_type.csv
│   ├── detection_heatmap.csv
│   ├── mcnemar_pairwise.csv
│   ├── mcnemar_vs_baseline.csv
│   ├── odds_ratios.csv
│   ├── efficiency.csv
│   ├── cochrans_q.json
│   ├── detection_rates_by_strategy.pdf
│   ├── detection_heatmap.pdf
│   └── odds_ratios.pdf
├── gpt5/
│   └── (same structure)
└── model_comparison/
    ├── model_comparison.csv
    ├── model_comparison_overall.json
    └── model_comparison.pdf
```

## Statistical Tests Performed

| Test | Purpose |
|------|---------|
| **Cochran's Q** | Compare all 5 strategies simultaneously (extension of McNemar for >2 groups) |
| **McNemar's (pairwise)** | Compare each pair of strategies with Bonferroni correction |
| **McNemar's (vs baseline)** | Compare each strategy to Full Context baseline |
| **Odds Ratios** | Effect size with 95% CI for each strategy vs baseline |
| **McNemar's (models)** | Compare GPT-4o-mini vs GPT-5.2 on same traps |

## Requirements

```bash
pip install pandas numpy scipy matplotlib seaborn
```

## Usage Options

```bash
# Analyze both models
python run_rq2_analysis.py

# Analyze only GPT-4o-mini
python run_rq2_analysis.py --gpt4o-mini-only

# Analyze only GPT-5.2
python run_rq2_analysis.py --gpt5-only

# Custom output directory
python run_rq2_analysis.py --output /path/to/output
```

## Direct Module Usage

```python
from rq2_statistical_analysis import load_data, run_analysis

# Load data
df = load_data(Path("path/to/results.csv"))

# Run analysis
results = run_analysis(df, Path("output_dir"), "Model Name")

# Access results
print(results.detection_rates_by_strategy)
print(results.cochrans_q_result)
print(results.mcnemar_vs_baseline)
```

## Expected Data Format

CSV with semicolon delimiter and columns:
- `node_title`: Unique trap identifier
- `strategy`: One of `full_context`, `structural_memory`, `simple_sm`, `hierarchical_graph`, `hmem`
- `detected`: `TRUE` or `FALSE`
- `trap_type`: Trap category
- `total_tokens`: (optional) Token count for efficiency
- `execution_time_ms`: (optional) Execution time for efficiency

## Interpreting Results

### Cochran's Q Test
- **p < 0.05**: Strategies have significantly different detection rates
- Follow up with pairwise McNemar's tests to identify which pairs differ

### McNemar's Test
- Compares paired binary outcomes (same trap, different strategies)
- **p < 0.05** (after Bonferroni correction): Significant difference

### Odds Ratios
- **OR > 1**: Strategy detects more than baseline
- **OR < 1**: Strategy detects less than baseline
- **95% CI excludes 1**: Significant effect
