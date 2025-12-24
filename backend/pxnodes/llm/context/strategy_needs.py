"""
Strategy needs matrix for artifact inventory.

Defines which artifacts are required per strategy so callers can
precompute only what they need.
"""

from dataclasses import dataclass, field

from pxnodes.llm.context.artifacts import (
    ARTIFACT_CHART_OVERVIEW,
    ARTIFACT_CHART_PACING,
    ARTIFACT_CHART_MECHANICS,
    ARTIFACT_CHART_NARRATIVE,
    ARTIFACT_CHUNKS,
    ARTIFACT_EDGE_TRIPLES,
    ARTIFACT_FACTS,
    ARTIFACT_NODE_LIST,
    ARTIFACT_PATH_SUMMARY,
    ARTIFACT_RAW_TEXT,
    ARTIFACT_SUMMARY,
    ARTIFACT_TRIPLES,
)
from pxnodes.llm.context.base.types import StrategyType


@dataclass(frozen=True)
class StrategyNeeds:
    node_artifacts: list[str] = field(default_factory=list)
    concept_artifacts: list[str] = field(default_factory=list)
    pillar_artifacts: list[str] = field(default_factory=list)
    chart_artifacts: list[str] = field(default_factory=list)
    path_artifacts: list[str] = field(default_factory=list)
    requires_embeddings: bool = False


STRATEGY_NEEDS: dict[StrategyType, StrategyNeeds] = {
    StrategyType.FULL_CONTEXT: StrategyNeeds(
        node_artifacts=[ARTIFACT_RAW_TEXT],
        concept_artifacts=[ARTIFACT_RAW_TEXT],
        pillar_artifacts=[ARTIFACT_RAW_TEXT],
        chart_artifacts=[ARTIFACT_CHART_OVERVIEW, ARTIFACT_NODE_LIST],
        path_artifacts=[],
        requires_embeddings=False,
    ),
    StrategyType.SIMPLE_SM: StrategyNeeds(
        node_artifacts=[ARTIFACT_FACTS, ARTIFACT_TRIPLES],
        concept_artifacts=[ARTIFACT_FACTS, ARTIFACT_TRIPLES],
        pillar_artifacts=[ARTIFACT_FACTS, ARTIFACT_TRIPLES],
        chart_artifacts=[ARTIFACT_EDGE_TRIPLES],
        path_artifacts=[],
        requires_embeddings=False,
    ),
    StrategyType.STRUCTURAL_MEMORY: StrategyNeeds(
        node_artifacts=[
            ARTIFACT_CHUNKS,
            ARTIFACT_FACTS,
            ARTIFACT_TRIPLES,
            ARTIFACT_SUMMARY,
        ],
        concept_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_FACTS, ARTIFACT_TRIPLES],
        pillar_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_FACTS, ARTIFACT_TRIPLES],
        chart_artifacts=[ARTIFACT_CHART_OVERVIEW, ARTIFACT_EDGE_TRIPLES],
        path_artifacts=[],
        requires_embeddings=True,
    ),
    StrategyType.HIERARCHICAL_GRAPH: StrategyNeeds(
        node_artifacts=[ARTIFACT_RAW_TEXT],
        concept_artifacts=[ARTIFACT_RAW_TEXT],
        pillar_artifacts=[ARTIFACT_RAW_TEXT],
        chart_artifacts=[ARTIFACT_CHART_OVERVIEW, ARTIFACT_NODE_LIST],
        path_artifacts=[],
        requires_embeddings=False,
    ),
    StrategyType.HMEM: StrategyNeeds(
        node_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_RAW_TEXT],
        concept_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_RAW_TEXT],
        pillar_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_RAW_TEXT],
        chart_artifacts=[
            ARTIFACT_CHART_OVERVIEW,
            ARTIFACT_NODE_LIST,
            ARTIFACT_CHART_PACING,
            ARTIFACT_CHART_MECHANICS,
            ARTIFACT_CHART_NARRATIVE,
        ],
        path_artifacts=[ARTIFACT_PATH_SUMMARY],
        requires_embeddings=True,
    ),
    StrategyType.COMBINED: StrategyNeeds(
        node_artifacts=[
            ARTIFACT_CHUNKS,
            ARTIFACT_FACTS,
            ARTIFACT_TRIPLES,
            ARTIFACT_SUMMARY,
            ARTIFACT_RAW_TEXT,
        ],
        concept_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_RAW_TEXT],
        pillar_artifacts=[ARTIFACT_SUMMARY, ARTIFACT_RAW_TEXT],
        chart_artifacts=[ARTIFACT_CHART_OVERVIEW, ARTIFACT_NODE_LIST],
        path_artifacts=[ARTIFACT_PATH_SUMMARY],
        requires_embeddings=True,
    ),
}


def get_strategy_needs(strategy_type: StrategyType) -> StrategyNeeds:
    return STRATEGY_NEEDS.get(strategy_type, StrategyNeeds())
