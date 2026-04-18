"""
Strategy-Aware Node Coherence Evaluator.

Evaluates nodes for coherence issues using any of the 4 context strategies.
Supports strategy comparison for thesis research.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

import logfire

from pxcharts.models import PxChart
from pxnodes.llm.context.base import (
    BaseContextStrategy,
    ContextResult,
    EvaluationScope,
    StrategyRegistry,
    StrategyType,
)
from pxnodes.models import PxNode

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class CoherenceIssue:
    """A coherence issue detected in a node."""

    issue_type: str  # "prerequisite", "pacing", "story", "category"
    severity: str  # "error", "warning", "info"
    description: str
    affected_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "affected_nodes": self.affected_nodes,
        }


@dataclass
class StrategyEvaluationResult:
    """Result of evaluating a node with a specific strategy."""

    node_id: str
    node_name: str
    strategy: str
    is_coherent: bool
    issues: list[CoherenceIssue] = field(default_factory=list)
    context_result: Optional[ContextResult] = None
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "strategy": self.strategy,
            "is_coherent": self.is_coherent,
            "issues": [i.to_dict() for i in self.issues],
            "context_metadata": (
                self.context_result.metadata if self.context_result else {}
            ),
            "error": self.error,
        }

    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == "error"])

    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == "warning"])


@dataclass
class ComparisonResult:
    """Result of comparing multiple strategies for a single node."""

    node_id: str
    node_name: str
    results_by_strategy: dict[str, StrategyEvaluationResult] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "strategies": {k: v.to_dict() for k, v in self.results_by_strategy.items()},
            "summary": self._build_summary(),
        }

    def _build_summary(self) -> dict[str, Any]:
        """Build comparison summary."""
        return {
            "strategies_compared": list(self.results_by_strategy.keys()),
            "coherent_by_strategy": {
                k: v.is_coherent for k, v in self.results_by_strategy.items()
            },
            "issues_by_strategy": {
                k: len(v.issues) for k, v in self.results_by_strategy.items()
            },
            "agreement": len(
                set(v.is_coherent for v in self.results_by_strategy.values())
            )
            == 1,
        }


# Evaluation prompt template (strategy-agnostic)
COHERENCE_EVALUATION_PROMPT = """You are a game design coherence analyzer.
Your task is to evaluate how well a node fits in a chart based on the provided context.

EVIDENCE RULES (apply to ALL dimensions):
- Only use information explicitly stated in the CONTEXT below. Do NOT assume \
missing mechanics, items, or events.
- The TARGET NODE text is not evidence of prior acquisition; it only defines \
requirements or acts as setup for future nodes.
- If a prerequisite is not explicitly supported by earlier context, list it \
under "missing_prerequisites" (or "unknowns" if ambiguous).
- Any mechanic or item in "satisfied_prerequisites" must cite a specific \
earlier node/title/quote from the context.
- Do NOT use words like "implied" or "assumed" as evidence. If you cannot \
cite a passage from a previous node, it is missing.
- In "satisfied_prerequisites", include the evidence inline, e.g., \
"Ability X — evidence: <quoted passage from a previous node>".
- Evidence must be a direct quote (or near-direct paraphrase) from the \
CONTEXT. If the quoted phrase does not appear in a prior node description, \
it does NOT count.
- You may only cite PREVIOUS NODES as evidence for prerequisites. Do not \
cite the target node or future nodes for prerequisites.
- If you cite a node title, you MUST include a quoted fragment from that \
node's description that proves the prerequisite.
- A prerequisite cannot be both "missing_prerequisites" and \
"satisfied_prerequisites". If evidence is absent or invalid, it must be \
missing.

{context}

PREREQUISITE CHECKLIST (for backward coherence):
1) Extract required mechanics/items/abilities from the TARGET NODE text.
2) For each requirement, find explicit evidence in PREVIOUS NODES only.
3) If no quote exists, mark it as missing (do not invent evidence).

TASK: Evaluate ALL FOUR coherence dimensions for the target node.

DIMENSIONS:
1) BACKWARD COHERENCE (prerequisites across incoming paths)
2) FORWARD COHERENCE (setup across outgoing paths)
3) GLOBAL FIT (concept + pillars alignment)
4) NODE INTEGRITY (title/description/components alignment)

Respond with a JSON object:
{{
  "backward_coherence": {{
    "score": <1-6>,
    "reasoning": "...",
    "issues": ["..."],
    "suggestions": ["..."],
    "evidence": ["..."],
    "unknowns": ["..."],
    "path_variance": "...",
    "missing_prerequisites": ["..."],
    "satisfied_prerequisites": ["..."]
  }},
  "forward_coherence": {{
    "score": <1-6>,
    "reasoning": "...",
    "issues": ["..."],
    "suggestions": ["..."],
    "evidence": ["..."],
    "unknowns": ["..."],
    "path_variance": "...",
    "elements_introduced": ["..."],
    "potential_payoffs": ["..."]
  }},
  "global_fit": {{
    "score": <1-6>,
    "reasoning": "...",
    "issues": ["..."],
    "suggestions": ["..."],
    "evidence": ["..."],
    "unknowns": ["..."],
    "path_variance": "...",
    "pillar_alignment": ["..."],
    "concept_alignment": "..."
  }},
  "node_integrity": {{
    "score": <1-6>,
    "reasoning": "...",
    "issues": ["..."],
    "suggestions": ["..."],
    "evidence": ["..."],
    "unknowns": ["..."],
    "path_variance": "...",
    "contradictions": ["..."],
    "unclear_elements": ["..."]
  }}
}}

IMPORTANT: Only report genuine issues. If context is insufficient,
list in "unknowns"."""


class StrategyEvaluator:
    """
    Evaluates node coherence using any context strategy.

    Supports:
    - Single strategy evaluation
    - Multi-strategy comparison for thesis research
    - All strategies: structural_memory, simple_sm, hierarchical_graph, hmem, combined
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        default_strategy: StrategyType = StrategyType.STRUCTURAL_MEMORY,
    ):
        """
        Initialize the evaluator.

        Args:
            llm_provider: LLM for evaluation and fact extraction
            default_strategy: Default strategy to use
        """
        self.llm_provider = llm_provider
        self.default_strategy = default_strategy
        self._strategy_cache: dict[StrategyType, BaseContextStrategy] = {}

    def _get_strategy(self, strategy_type: StrategyType) -> BaseContextStrategy:
        """Get or create a strategy instance."""
        if strategy_type not in self._strategy_cache:
            self._strategy_cache[strategy_type] = StrategyRegistry.create(
                strategy_type,
                llm_provider=self.llm_provider,
                # Use direct extraction to ensure fresh LLM-based fact/summary
                # extraction. Iterative retrieval requires pre-indexed memories.
                use_iterative_retrieval=False,
            )
        return self._strategy_cache[strategy_type]

    def evaluate_node(
        self,
        node: PxNode,
        chart: PxChart,
        strategy_type: Optional[StrategyType] = None,
        project_pillars: Optional[list] = None,
        game_concept: Optional[Any] = None,
    ) -> StrategyEvaluationResult:
        """
        Evaluate a node's coherence using a specific strategy.

        Args:
            node: The target node to evaluate
            chart: The chart containing the node
            strategy_type: Strategy to use (default if not specified)
            project_pillars: Optional project pillars for L1 context
            game_concept: Optional game concept for L1 context

        Returns:
            StrategyEvaluationResult with coherence assessment
        """
        strategy_type = strategy_type or self.default_strategy
        strategy = self._get_strategy(strategy_type)

        with logfire.span(
            "strategy_evaluator.evaluate_node",
            node_id=str(node.id),
            strategy=strategy_type.value,
        ):
            try:
                # Build evaluation scope
                scope = EvaluationScope(
                    target_node=node,
                    chart=chart,
                    project=getattr(game_concept, "project", None),
                    project_pillars=project_pillars,
                    game_concept=game_concept,
                )

                # Build context using strategy
                context_result = strategy.build_context(scope)

                # Evaluate with LLM
                result = self._evaluate_with_llm(
                    node=node,
                    strategy_type=strategy_type,
                    context_result=context_result,
                )

                logfire.info(
                    "strategy_evaluation_complete",
                    node_id=str(node.id),
                    strategy=strategy_type.value,
                    is_coherent=result.is_coherent,
                    issues_count=len(result.issues),
                )

                return result

            except Exception as e:
                logger.exception(f"Evaluation failed for node {node.id}")
                logfire.error(
                    "strategy_evaluation_failed",
                    node_id=str(node.id),
                    strategy=strategy_type.value,
                    error=str(e),
                )
                return StrategyEvaluationResult(
                    node_id=str(node.id),
                    node_name=node.name,
                    strategy=strategy_type.value,
                    is_coherent=False,
                    error=str(e),
                )

    def compare_strategies(
        self,
        node: PxNode,
        chart: PxChart,
        strategies: Optional[list[StrategyType]] = None,
        project_pillars: Optional[list] = None,
        game_concept: Optional[Any] = None,
    ) -> ComparisonResult:
        """
        Evaluate a node using multiple strategies for comparison.

        Useful for thesis research to compare strategy effectiveness.

        Args:
            node: The target node to evaluate
            chart: The chart containing the node
            strategies: List of strategies to compare (default: all 4)
            project_pillars: Optional project pillars
            game_concept: Optional game concept

        Returns:
            ComparisonResult with results from all strategies
        """
        strategies = strategies or list(StrategyType)

        with logfire.span(
            "strategy_evaluator.compare_strategies",
            node_id=str(node.id),
            strategies=[s.value for s in strategies],
        ):
            comparison = ComparisonResult(
                node_id=str(node.id),
                node_name=node.name,
            )

            for strategy_type in strategies:
                result = self.evaluate_node(
                    node=node,
                    chart=chart,
                    strategy_type=strategy_type,
                    project_pillars=project_pillars,
                    game_concept=game_concept,
                )
                comparison.results_by_strategy[strategy_type.value] = result

            logfire.info(
                "strategy_comparison_complete",
                node_id=str(node.id),
                strategies_compared=len(strategies),
                agreement=comparison._build_summary()["agreement"],
            )

            return comparison

    def evaluate_chart(
        self,
        chart: PxChart,
        strategy_type: Optional[StrategyType] = None,
        node_ids: Optional[list[str]] = None,
        project_pillars: Optional[list] = None,
        game_concept: Optional[Any] = None,
    ) -> list[StrategyEvaluationResult]:
        """
        Evaluate all nodes in a chart using a strategy.

        Args:
            chart: The chart to evaluate
            strategy_type: Strategy to use
            node_ids: Optional specific node IDs to evaluate
            project_pillars: Optional project pillars
            game_concept: Optional game concept

        Returns:
            List of StrategyEvaluationResult for each node
        """
        strategy_type = strategy_type or self.default_strategy

        with logfire.span(
            "strategy_evaluator.evaluate_chart",
            chart_id=str(chart.id),
            strategy=strategy_type.value,
        ):
            results = []

            # Get nodes to evaluate
            if node_ids:
                nodes = list(PxNode.objects.filter(id__in=node_ids))
            else:
                container_node_ids = chart.containers.filter(
                    content__isnull=False
                ).values_list("content_id", flat=True)
                nodes = list(PxNode.objects.filter(id__in=container_node_ids))

            for node in nodes:
                result = self.evaluate_node(
                    node=node,
                    chart=chart,
                    strategy_type=strategy_type,
                    project_pillars=project_pillars,
                    game_concept=game_concept,
                )
                results.append(result)

            return results

    def _evaluate_with_llm(
        self,
        node: PxNode,
        strategy_type: StrategyType,
        context_result: ContextResult,
    ) -> StrategyEvaluationResult:
        """Use LLM to evaluate coherence based on context."""
        prompt = COHERENCE_EVALUATION_PROMPT.format(
            context=context_result.context_string
        )

        try:
            response = self.llm_provider.generate(prompt)

            # Parse JSON response
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            issues: list[CoherenceIssue] = []
            scores: list[float] = []
            dimension_keys = [
                "backward_coherence",
                "forward_coherence",
                "global_fit",
                "node_integrity",
            ]
            for key in dimension_keys:
                dim = data.get(key, {}) or {}
                score = dim.get("score")
                if isinstance(score, (int, float)):
                    scores.append(float(score))
                dim_issues = dim.get("issues", []) or []
                severity = "info"
                if isinstance(score, (int, float)):
                    if score <= 2:
                        severity = "error"
                    elif score <= 4:
                        severity = "warning"
                for issue in dim_issues:
                    issues.append(
                        CoherenceIssue(
                            issue_type=key,
                            severity=severity,
                            description=str(issue),
                            affected_nodes=[],
                        )
                    )

            overall_score = sum(scores) / len(scores) if scores else 3.0
            is_coherent = overall_score >= 4.0

            return StrategyEvaluationResult(
                node_id=str(node.id),
                node_name=node.name,
                strategy=strategy_type.value,
                is_coherent=is_coherent,
                issues=issues,
                context_result=context_result,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return StrategyEvaluationResult(
                node_id=str(node.id),
                node_name=node.name,
                strategy=strategy_type.value,
                is_coherent=True,
                issues=[],
                context_result=context_result,
                error=f"Failed to parse LLM response: {str(e)[:100]}",
            )


def evaluate_node_with_strategy(
    node_id: str,
    chart_id: str,
    strategy: str = "structural_memory",
    llm_provider: Optional[LLMProvider] = None,
) -> dict[str, Any]:
    """
    Convenience function to evaluate a node with a specific strategy.

    Args:
        node_id: UUID of the node to evaluate
        chart_id: UUID of the chart
        strategy: Strategy name (structural_memory, hierarchical_graph, hmem, combined)
        llm_provider: Optional LLM provider

    Returns:
        Evaluation result dictionary
    """
    from pxnodes.llm.context.shared import create_llm_provider

    node = PxNode.objects.get(id=node_id)
    chart = PxChart.objects.get(id=chart_id)

    llm = llm_provider or create_llm_provider()
    strategy_type = StrategyType(strategy)

    evaluator = StrategyEvaluator(llm_provider=llm)
    result = evaluator.evaluate_node(node, chart, strategy_type)

    return result.to_dict()


def compare_all_strategies(
    node_id: str,
    chart_id: str,
    llm_provider: Optional[LLMProvider] = None,
) -> dict[str, Any]:
    """
    Compare all strategies for a single node.

    Args:
        node_id: UUID of the node to evaluate
        chart_id: UUID of the chart
        llm_provider: Optional LLM provider

    Returns:
        Comparison result dictionary
    """
    from pxnodes.llm.context.shared import create_llm_provider

    node = PxNode.objects.get(id=node_id)
    chart = PxChart.objects.get(id=chart_id)

    llm = llm_provider or create_llm_provider()

    evaluator = StrategyEvaluator(llm_provider=llm)
    result = evaluator.compare_strategies(node, chart)

    return result.to_dict()
