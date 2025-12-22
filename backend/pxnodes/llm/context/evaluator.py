"""
Node Coherence Evaluator using Structural Memory.

Evaluates nodes for coherence issues using retrieved knowledge triples
and atomic facts. Implements the evaluation phase of the Zeng et al. (2024)
structural memory approach.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

import logfire

from pxcharts.models import PxChart
from pxnodes.llm.context.graph_retrieval import get_graph_slice
from pxnodes.llm.context.retriever import (
    IterativeRetriever,
    RetrievalResult,
)
from pxnodes.llm.context.triples import _get_component_map
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
class NodeEvaluationResult:
    """Result of evaluating a single node's coherence."""

    node_id: str
    node_name: str
    is_coherent: bool
    issues: list[CoherenceIssue] = field(default_factory=list)
    context_used: str = ""  # The retrieved memories used for evaluation
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "is_coherent": self.is_coherent,
            "issues": [i.to_dict() for i in self.issues],
            "context_used": self.context_used,
            "error": self.error,
        }

    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.severity == "error"])

    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.severity == "warning"])


@dataclass
class ChartEvaluationResult:
    """Result of evaluating all nodes in a chart."""

    chart_id: str
    chart_name: str
    node_results: list[NodeEvaluationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_name": self.chart_name,
            "summary": {
                "total_nodes": len(self.node_results),
                "coherent_nodes": len([n for n in self.node_results if n.is_coherent]),
                "total_errors": sum(n.error_count for n in self.node_results),
                "total_warnings": sum(n.warning_count for n in self.node_results),
            },
            "nodes": [n.to_dict() for n in self.node_results],
        }


# Evaluation prompt template
COHERENCE_EVALUATION_PROMPT = """You are a game design coherence analyzer.
Your task is to evaluate if a game node is coherent with its neighboring nodes.

{context}

[COMPUTED METRICS]
{metrics}

TASK: Analyze the TARGET NODE for coherence issues. Check for:

1. PREREQUISITE VIOLATIONS (severity: error)
   - Items, abilities, or keys required but not granted in previous nodes
   - Example: "Requires Double Jump but player doesn't have it yet"

2. PACING ISSUES (severity: warning)
   - Intensity spikes (jump > 50 points) without narrative justification
   - Sudden drops that feel jarring
   - Example: "Intensity jumps from 10 to 85 without buildup"

3. STORY COHERENCE (severity: warning or error)
   - Narrative inconsistencies or contradictions
   - References to events that haven't happened
   - Example: "Mentions escaping prison but player was never captured"

4. CATEGORY FLOW (severity: info or warning)
   - Unusual gameplay category transitions
   - Example: "Boss fight immediately after Tutorial"

Respond with a JSON object:
{{
  "is_coherent": true or false,
  "issues": [
    {{
      "type": "prerequisite" | "pacing" | "story" | "category",
      "severity": "error" | "warning" | "info",
      "description": "Clear description of the issue",
      "affected_nodes": ["node_id_1", "node_id_2"]
    }}
  ]
}}

If the node is coherent with no issues, respond:
{{"is_coherent": true, "issues": []}}

IMPORTANT: Only report genuine issues.
Do not flag normal game design patterns as problems."""


class NodeCoherenceEvaluator:
    """
    Evaluates node coherence using structural memory retrieval.

    Uses iterative retrieval to gather relevant context (triples + facts)
    from the target node and its neighbors, then uses LLM to identify
    coherence issues.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 3,
        top_k_per_node: int = 10,
    ):
        """
        Initialize the evaluator.

        Args:
            llm_provider: LLM for evaluation
            embedding_model: Model for query embedding
            retrieval_iterations: Number of retrieval refinement iterations
            top_k_per_node: Max memories to retrieve per node
        """
        self.llm_provider = llm_provider
        self.retriever = IterativeRetriever(
            llm_provider=llm_provider,
            embedding_model=embedding_model,
        )
        self.retrieval_iterations = retrieval_iterations
        self.top_k_per_node = top_k_per_node

    def evaluate_node(
        self,
        node: PxNode,
        chart: PxChart,
    ) -> NodeEvaluationResult:
        """
        Evaluate a single node's coherence in context of its neighbors.

        Args:
            node: The target node to evaluate
            chart: The chart containing the node

        Returns:
            NodeEvaluationResult with coherence assessment and issues
        """
        with logfire.span(
            "evaluate_node_coherence",
            node_id=str(node.id),
            node_name=node.name,
        ):
            try:
                # Get graph slice (neighbors)
                graph_slice = get_graph_slice(node, chart, depth=1)

                # Build retrieval query
                query = self._build_retrieval_query(node)

                # Collect node IDs for retrieval
                all_node_ids = [str(node.id)]
                neighbor_ids = []
                for n in graph_slice.previous_nodes + graph_slice.next_nodes:
                    neighbor_ids.append(str(n.id))
                    all_node_ids.append(str(n.id))

                # Retrieve memories for all relevant nodes
                memories_by_node = self.retriever.retrieve_for_nodes(
                    target_node_id=str(node.id),
                    neighbor_node_ids=neighbor_ids,
                    query=query,
                    iterations=self.retrieval_iterations,
                    top_k_per_node=self.top_k_per_node,
                )

                # Build context for evaluation
                context = self._build_evaluation_context(
                    node,
                    graph_slice,
                    memories_by_node,
                )

                # Compute metrics
                metrics = self._compute_metrics(node, graph_slice)

                # Call LLM for evaluation
                result = self._evaluate_with_llm(
                    node,
                    context,
                    metrics,
                    memories_by_node,
                )

                logfire.info(
                    "node_evaluation_complete",
                    node_id=str(node.id),
                    is_coherent=result.is_coherent,
                    issues_count=len(result.issues),
                )

                return result

            except Exception as e:
                logger.exception(f"Failed to evaluate node {node.id}")
                logfire.error(
                    "node_evaluation_failed",
                    node_id=str(node.id),
                    error=str(e),
                )
                return NodeEvaluationResult(
                    node_id=str(node.id),
                    node_name=node.name,
                    is_coherent=False,
                    error=str(e),
                )

    def evaluate_chart(
        self,
        chart: PxChart,
        node_ids: Optional[list[str]] = None,
    ) -> ChartEvaluationResult:
        """
        Evaluate coherence for nodes in a chart.

        Args:
            chart: The chart to evaluate
            node_ids: Optional list of specific node IDs to evaluate.
                     If None, evaluates all nodes in the chart.

        Returns:
            ChartEvaluationResult with results for all evaluated nodes
        """
        with logfire.span(
            "evaluate_chart_coherence",
            chart_id=str(chart.id),
            chart_name=chart.name,
        ):
            result = ChartEvaluationResult(
                chart_id=str(chart.id),
                chart_name=chart.name,
            )

            # Get nodes to evaluate
            if node_ids:
                nodes = list(PxNode.objects.filter(id__in=node_ids))
            else:
                # Get all nodes in chart
                container_node_ids = chart.containers.filter(
                    content__isnull=False
                ).values_list("content_id", flat=True)
                nodes = list(PxNode.objects.filter(id__in=container_node_ids))

            logfire.info(
                "evaluating_chart",
                chart_id=str(chart.id),
                node_count=len(nodes),
            )

            # Evaluate each node
            for node in nodes:
                node_result = self.evaluate_node(node, chart)
                result.node_results.append(node_result)

            logfire.info(
                "chart_evaluation_complete",
                chart_id=str(chart.id),
                total_nodes=len(result.node_results),
                coherent_nodes=len([n for n in result.node_results if n.is_coherent]),
            )

            return result

    def _build_retrieval_query(self, node: PxNode) -> str:
        """Build a query for retrieving relevant memories."""
        parts = [f"Game node: {node.name}"]

        if node.description:
            # Include key terms from description
            parts.append(f"Description context: {node.description[:200]}")

        # Add component info
        components = _get_component_map(node)
        if components:
            component_items = []
            for name, value in list(components.items())[:5]:
                component_items.append(f"{name}={value}")
            if component_items:
                parts.append(f"Components: {', '.join(component_items)}")

        return ". ".join(parts)

    def _build_evaluation_context(
        self,
        target_node: PxNode,
        graph_slice: Any,
        memories_by_node: dict[str, RetrievalResult],
    ) -> str:
        """Build the context section of the evaluation prompt."""
        sections = []

        # Previous nodes context
        if graph_slice.previous_nodes:
            prev_section = "[PREVIOUS NODES - What came before]\n"
            for prev_node in graph_slice.previous_nodes:
                node_id = str(prev_node.id)
                if node_id in memories_by_node:
                    prev_section += f"\n--- {prev_node.name} ---\n"
                    prev_section += memories_by_node[node_id].format_for_prompt()
            sections.append(prev_section)
        else:
            sections.append(
                "[PREVIOUS NODES]\nThis is a starting node (no predecessors)."
            )

        # Target node context
        target_id = str(target_node.id)
        target_section = f"[TARGET NODE - Evaluate This: {target_node.name}]\n"
        if target_id in memories_by_node:
            target_section += memories_by_node[target_id].format_for_prompt()
        if target_node.description:
            target_section += f"\n\nDescription: {target_node.description}"
        sections.append(target_section)

        # Next nodes context
        if graph_slice.next_nodes:
            next_section = "[NEXT NODES - What comes after]\n"
            for next_node in graph_slice.next_nodes:
                node_id = str(next_node.id)
                if node_id in memories_by_node:
                    next_section += f"\n--- {next_node.name} ---\n"
                    next_section += memories_by_node[node_id].format_for_prompt()
            sections.append(next_section)
        else:
            sections.append("[NEXT NODES]\nThis is an ending node (no successors).")

        return "\n\n".join(sections)

    def _compute_metrics(self, node: PxNode, graph_slice: Any) -> str:
        """Compute metrics for the evaluation prompt."""
        metrics = []

        target_components = _get_component_map(node)

        # Component value deltas from previous nodes
        for prev_node in graph_slice.previous_nodes:
            prev_components = _get_component_map(prev_node)
            changes = []
            for name, target_value in target_components.items():
                if name not in prev_components:
                    continue
                prev_value = prev_components[name]
                if isinstance(target_value, (int, float)) and isinstance(
                    prev_value, (int, float)
                ):
                    try:
                        delta = float(target_value) - float(prev_value)
                    except (ValueError, TypeError):
                        continue
                    delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
                    changes.append(
                        f"{name}: {prev_value} -> {target_value} ({delta_str})"
                    )
                elif target_value != prev_value:
                    changes.append(f"{name}: {prev_value} -> {target_value}")

            if changes:
                metrics.append(
                    f"- Components vs {prev_node.name}: " + "; ".join(changes[:3])
                )

        if not metrics:
            metrics.append("- No computed metrics available")

        return "\n".join(metrics)

    def _evaluate_with_llm(
        self,
        node: PxNode,
        context: str,
        metrics: str,
        memories_by_node: dict[str, RetrievalResult],
    ) -> NodeEvaluationResult:
        """Call LLM to evaluate coherence."""
        prompt = COHERENCE_EVALUATION_PROMPT.format(
            context=context,
            metrics=metrics,
        )

        # Generate context_used summary
        context_used = context[:2000] + "..." if len(context) > 2000 else context

        try:
            response = self.llm_provider.generate(prompt)

            # Parse JSON response
            # Try to extract JSON from response
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            # Build result
            issues = []
            for issue_data in data.get("issues", []):
                issues.append(
                    CoherenceIssue(
                        issue_type=issue_data.get("type", "unknown"),
                        severity=issue_data.get("severity", "info"),
                        description=issue_data.get("description", ""),
                        affected_nodes=issue_data.get("affected_nodes", []),
                    )
                )

            return NodeEvaluationResult(
                node_id=str(node.id),
                node_name=node.name,
                is_coherent=data.get("is_coherent", True),
                issues=issues,
                context_used=context_used,
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Return a result indicating evaluation succeeded but parsing failed
            return NodeEvaluationResult(
                node_id=str(node.id),
                node_name=node.name,
                is_coherent=True,  # Assume coherent if we can't parse
                issues=[],
                context_used=context_used,
                error=f"Failed to parse LLM response: {str(e)[:100]}",
            )

    def close(self) -> None:
        """Close resources."""
        self.retriever.close()
