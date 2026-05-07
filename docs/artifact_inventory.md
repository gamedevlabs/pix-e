# Artifact Inventory (Draft)

This document outlines the precompute cache for context artifacts.

## Goals

- Separate setup cost (artifact generation) from strategy runtime cost.
- Scope node and path artifacts to a chart only.
- Reuse artifacts when source content or edges have not changed.

## Core Tables

- `ContextArtifact`: stores text or structured artifacts with source and content hashes.
- `ArtifactEmbedding`: optional metadata for embeddings keyed to artifacts.

## Draft Usage

```
from pxnodes.llm.context.artifacts import ArtifactInventory

inventory = ArtifactInventory(llm_provider=provider)
node_artifacts = inventory.get_or_build_node_artifacts(
    chart=chart,
    nodes=nodes_in_chart,
    artifact_types=["facts", "triples", "summary"],
)
```

## Scope Rules

- Node artifacts are generated only for nodes in the target chart.
- Path artifacts are keyed by ordered node ids within the chart.

## Strategy Needs Matrix (Draft)

Legend:
- Required: artifact must exist for strategy execution.
- Optional: artifact improves quality but is not required.
- None: not used.

Source of truth for runtime: `backend/pxnodes/llm/context/strategy_needs.py`.

| Strategy | Node Artifacts | Concept/Pillars | Chart Artifacts | Path Artifacts | Embeddings |
| --- | --- | --- | --- | --- | --- |
| Full Context (FC) | raw_text | raw_text | chart_overview, node_list | raw_text path nodes | None |
| SM-Lite (facts + triples) | facts, triples | facts, triples | None | None | None |
| SM (mixed, no retrieval) | chunks, facts, triples, summary | summary, facts, triples | chart_overview | None | Optional |
| SM + Iterative Retrieval | facts, triples, summary, chunks (for output) | summary, facts, triples | chart_overview | None | Required (facts + triples) |
| H-Graph | raw_text | raw_text | chart_overview, node_list | raw_text path nodes | None |
| H-MEM | summary, raw_text (L4) | summary, raw_text | chart_overview, node_list | summary (path nodes) | Required |

Notes:
- H-MEM L3 uses generic node summaries via the artifact inventory.
- For SM-Lite, consider capping per-node facts/triples to control input size.

## Precompute Scopes

- `global`: concept + pillars + chart artifacts only.
- `node`: node + path artifacts (and embeddings if required).
- `all`: global + node artifacts.
