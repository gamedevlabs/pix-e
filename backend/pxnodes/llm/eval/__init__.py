"""Evaluation harness for the Consistency and Change Propagation agents.

This package provides a reproducible, automated way to measure agent quality
against a frozen, ground-truth-labelled dataset (Anno 1404 Mission I). It
replaces manual TP/FP/FN counting with a re-runnable pipeline that reports
Precision / Recall / F1 as mean ± std over N runs.

Modules:
- metrics:           pure functions for matching findings to traps and computing
                     P/R/F1 (no Django or LLM dependency — unit-testable).
- loader:            loads a frozen dataset JSON into an isolated eval project.
- consistency_runner: runs the Consistency agent N times and aggregates metrics.
"""
