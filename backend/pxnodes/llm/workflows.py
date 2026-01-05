"""
PxNodes Coherence Workflows - Agentic and Monolithic evaluation of node coherence.

Agentic Workflow:
Coordinates 4 specialized dimension agents running in parallel:
- BackwardCoherenceAgent
- ForwardCoherenceAgent
- GlobalFitAgent
- NodeIntegrityAgent

Monolithic Workflow:
Single LLM call evaluating all 4 dimensions with unified prompt.
Designed for thesis comparison between agentic vs monolithic approaches.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Protocol, Type

from llm.agent_runtime import BaseAgent
from llm.providers.manager import ModelManager
from llm.types import AgentResult, ErrorInfo
from pxcharts.models import PxChart
from pxnodes.llm.agents.coherence import (
    BackwardCoherenceAgent,
    ForwardCoherenceAgent,
    GlobalFitAgent,
    NodeIntegrityAgent,
)
from pxnodes.llm.agents.coherence.schemas import (
    BackwardCoherenceResult,
    CoherenceAggregatedResult,
    ForwardCoherenceResult,
    GlobalFitResult,
    NodeIntegrityResult,
)
from pxnodes.llm.context.base import (
    BaseContextStrategy,
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


# =============================================================================
# MONOLITHIC EVALUATION PROMPT
# =============================================================================
# This prompt mirrors the 4 agent prompts but in a single unified call.
# Each dimension has the same evaluation criteria as its corresponding agent.

MONOLITHIC_COHERENCE_PROMPT = """You are a game design coherence analyzer \
evaluating a node in a game flow chart.

EVIDENCE RULES (general):
- Only use information explicitly stated in the CONTEXT below. Do NOT assume \
missing mechanics, items, or events.
- Evidence must be a direct quote (or near-direct paraphrase) from the \
CONTEXT.
- If you cite a node title, include a quoted fragment from that node's \
description that supports the claim.

TARGET NODE DETAILS:
{target_node_block}

CONTEXT:
{context}

{dimension_context}

TASK: Evaluate ALL FOUR coherence dimensions for the target node.

================================================================================
DIMENSION 1: BACKWARD COHERENCE
================================================================================
Analyze whether the target node properly respects what came before across
all valid predecessor paths.

EVIDENCE RULES (backward coherence):
- The TARGET NODE text is not evidence of prior acquisition; it only defines \
requirements.
- You may only cite PREVIOUS NODES as evidence for prerequisites. Do not \
cite the target node or future nodes.
- Any item in "satisfied_prerequisites" must include a quoted fragment from \
previous node descriptions.
- A prerequisite cannot be both "missing_prerequisites" and \
"satisfied_prerequisites". If evidence is absent or invalid, it must be \
missing.

CHECK FOR:
1. REQUIRED MECHANICS/ITEMS
   - Are required mechanics or items established on ALL incoming paths?
   - If only on some paths, flag as path-dependent.

2. NARRATIVE PREREQUISITES
   - Does the node reference events that have occurred?
   - Are character introductions properly sequenced?
   - Example violation: "Return to the castle" but player never visited it

3. STATE PREREQUISITES
   - Does the node assume a game state that is achievable on all paths?
   - Are triggers/conditions for reaching this node satisfiable?

PREREQUISITE CHECKLIST:
1) Extract required mechanics/items/abilities from the TARGET NODE text.
2) For each requirement, find explicit evidence in PREVIOUS NODES only.
3) If no quote exists, mark it as missing (do not invent evidence).

================================================================================
DIMENSION 2: FORWARD COHERENCE
================================================================================
Analyze whether the target node properly sets up what comes next across \
all valid outgoing paths.

EVIDENCE RULES (forward coherence):
- The TARGET NODE can be cited as setup for future elements.
- Use FUTURE NODES as evidence of payoff/setup.

CHECK FOR:
1. MECHANICAL SETUP
   - If the node introduces mechanics, are they used/referenced in a \
    future node?

2. NARRATIVE SETUP
   - Do the story elements introduced in this node pay off later?
   - Is foreshadowing appropriate and not heavy-handed?

3. WORLD BUILDING
   - Are locations/characters introduced properly?
   - Is context provided for future events?

================================================================================
DIMENSION 3: GLOBAL FIT
================================================================================
Analyze whether the node aligns with the overall game concept and design pillars.

EVIDENCE RULES (global fit):
- Use the GAME CONCEPT and DESIGN PILLARS provided in CONTEXT.

CHECK FOR:
1. PILLAR ALIGNMENT
   - Does the node reinforce or conflict with the stated design pillars?
   - Are there explicit violations (e.g., non-violent pillar vs combat-only node)?

2. CONCEPT ALIGNMENT
   - Is the node consistent with what the game concept defines?
   - Does it introduce mechanics/themes that contradict the game concept?

3. WORLD/TONE CONSISTENCY
   - Is the node consistent with the setting?

================================================================================
DIMENSION 4: NODE INTEGRITY
================================================================================
Analyze whether the node is internally coherent and well-defined.

EVIDENCE RULES (node integrity):
- Use only the TARGET NODE DETAILS (title/description/components).

CHECK FOR:
1. CONTRADICTIONS
   - Does the title match the description?
   - If there are components, does the description match the node components?
   - Does a part of the node description contradict another part of the
     node description?

2. COMPONENT HARMONY
   - Do all node components work together?
   - Is component category/value appropriate for the content?

================================================================================
SCORING SCALE (1-6):
================================================================================
1 - Very Poor: Major issues that break coherence
2 - Poor: Significant issues that harm coherence
3 - Below Average: Notable issues that need attention
4 - Above Average: Minor issues, generally coherent
5 - Good: Very few issues, well-designed
6 - Excellent: No issues, exemplary coherence

================================================================================
RESPONSE FORMAT:
================================================================================
Respond with a JSON object containing evaluations for ALL 4 dimensions:

{{
  "backward_coherence": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "evidence": ["Short references to nodes/edges/quotes"],
    "unknowns": ["What could not be verified from context"],
    "path_variance": "consistent across paths OR depends on path: <details>",
    "missing_prerequisites": [
        "List items/abilities/mechanics that are required but not established"
    ],
    "satisfied_prerequisites": ["List prerequisites that ARE properly established"]
  }},
  "forward_coherence": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "evidence": ["Short references to nodes/edges/quotes"],
    "unknowns": ["What could not be verified from context"],
    "path_variance": "consistent across paths OR depends on path: <details>",
    "elements_introduced": ["New elements introduced in this node"],
    "potential_payoffs": ["How these elements might pay off later"]
  }},
  "global_fit": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "evidence": ["Short references to nodes/edges/quotes"],
    "unknowns": ["What could not be verified from context"],
    "path_variance": "consistent across paths OR depends on path: <details>",
    "pillar_alignment": ["How the node aligns or conflicts with each pillar"],
    "concept_alignment": "Overall alignment with game concept and tone"
  }},
  "node_integrity": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "evidence": ["Short references to nodes/edges/quotes"],
    "unknowns": ["What could not be verified from context"],
    "path_variance": "consistent across paths OR depends on path: <details>",
    "contradictions": ["List of internal contradictions found"],
    "unclear_elements": ["Vague or unclear elements that need clarification"]
  }}
}}

IMPORTANT: Evaluate ALL 4 dimensions thoroughly. Report genuine issues only."""


# Map of dimension names to agent classes
DIMENSION_AGENTS: Dict[str, Type[BaseAgent]] = {
    "backward_coherence": BackwardCoherenceAgent,
    "forward_coherence": ForwardCoherenceAgent,
    "global_fit": GlobalFitAgent,
    "node_integrity": NodeIntegrityAgent,
}


class PxNodesCoherenceWorkflow:
    """
    Agentic workflow for evaluating node coherence.

    Uses 4 specialized agents running in parallel, each focusing on
    a different dimension of coherence:
    1. Backward Coherence - Does node respect what came before?
    2. Forward Coherence - Does node properly set up future?
    3. Global Fit - Does node align with concept and pillars?
    4. Node Integrity - Is node internally coherent?

    Integrates with existing context strategies for context building.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        strategy_type: StrategyType = StrategyType.STRUCTURAL_MEMORY,
        max_parallel: int = 4,
        llm_provider: Optional[Any] = None,
        use_iterative_retrieval: bool = True,
    ):
        """
        Initialize the workflow.

        Args:
            model_manager: ModelManager for LLM access
            strategy_type: Context strategy to use
            max_parallel: Maximum concurrent agent executions
            llm_provider: Optional LLM provider for context strategies
            use_iterative_retrieval: Whether to use iterative retrieval from
            vector store. Default False to use direct extraction which
            does fresh LLM-based fact/summary extraction.
        """
        self.model_manager = model_manager
        self.strategy_type = strategy_type
        self.max_parallel = max_parallel
        self.llm_provider = llm_provider
        self.use_iterative_retrieval = use_iterative_retrieval

        # Create strategy instance
        self._strategy: Optional[BaseContextStrategy] = None

    def _get_strategy(self) -> BaseContextStrategy:
        """Get or create the context strategy."""
        if self._strategy is None:
            self._strategy = StrategyRegistry.create(
                self.strategy_type,
                llm_provider=self.llm_provider,
                # Use direct extraction by default to ensure fresh LLM-based
                # fact/summary extraction. Iterative retrieval requires pre-indexed
                # memories in the vector store.
                use_iterative_retrieval=self.use_iterative_retrieval,
            )
        return self._strategy

    async def evaluate_node(
        self,
        node: PxNode,
        chart: PxChart,
        model_id: Optional[str] = None,
        project: Optional[Any] = None,
        project_pillars: Optional[List] = None,
        game_concept: Optional[Any] = None,
        dimensions: Optional[List[str]] = None,
    ) -> CoherenceAggregatedResult:
        """
        Evaluate a node's coherence using parallel dimension agents.

        Args:
            node: The target node to evaluate
            chart: The chart containing the node
            model_id: Optional specific model to use
            project_pillars: Optional design pillars for contextual fit
            game_concept: Optional game concept for contextual fit
            dimensions: Optional list of specific dimensions to evaluate
                       (default: all 4 dimensions)

        Returns:
            CoherenceAggregatedResult with all dimension scores
        """
        import logfire
        from asgiref.sync import sync_to_async

        start_time = time.time()
        total_tokens = 0

        span_name = f"coherence.evaluate.pxnodes.{self.strategy_type.value}.agentic"

        # Determine which dimensions to evaluate
        dimensions_to_run = dimensions or list(DIMENSION_AGENTS.keys())

        with logfire.span(
            span_name,
            feature="pxnodes",
            strategy=self.strategy_type.value,
            execution_mode="agentic",
            node_id=str(node.id),
            node_name=node.name,
        ):
            # Build context using strategy
            # Use async version for parallel extraction if available (StructuralMemory)
            strategy = self._get_strategy()
            scope = EvaluationScope(
                target_node=node,
                chart=chart,
                project=project,
                project_pillars=project_pillars,
                game_concept=game_concept,
            )

            # Use async build_context if available (for parallel extraction)
            if hasattr(strategy, "build_context_async"):
                with logfire.span(
                    "context.build.async",
                    strategy=self.strategy_type.value,
                    target_node=node.name,
                ):
                    context_result = await strategy.build_context_async(scope)
            else:
                # Fallback to sync version wrapped in async
                context_result = await sync_to_async(
                    strategy.build_context, thread_sensitive=True
                )(scope)

            # Prepare shared context data for all agents
            # Note: _extract_node_details contains Django ORM calls
            # (node.components.all()). Wrap in sync_to_async to avoid
            # SynchronousOnlyOperation errors.
            node_details = await sync_to_async(
                self._extract_node_details, thread_sensitive=True
            )(node)
            path_metadata = await sync_to_async(
                self._build_path_metadata, thread_sensitive=True
            )(node, chart)

            base_data = {
                "target_node_name": node.name,
                "target_node_description": node_details.get("description"),
                "node_details": node_details,
                "backward_nodes": self._extract_path_nodes(context_result, "backward"),
                "forward_nodes": self._extract_path_nodes(context_result, "forward"),
                "backward_paths": context_result.metadata.get("backward_paths", []),
                "forward_paths": context_result.metadata.get("forward_paths", []),
                "pillars": self._format_pillars(project_pillars),
                "game_concept": game_concept,
                "is_full_context": bool(context_result.metadata.get("full_context")),
                "strategy_type": self.strategy_type.value,
                "path_order": path_metadata.get("order", {}),
                "path_predecessors": path_metadata.get("predecessors", set()),
                "path_successors": path_metadata.get("successors", set()),
            }
            if self.strategy_type in {
                StrategyType.SIMPLE_SM,
                StrategyType.STRUCTURAL_MEMORY,
            }:
                base_data.update(
                    self._build_structural_memory_target_artifacts(
                        context_result=context_result,
                        node_details=node_details,
                        include_summaries=self.strategy_type
                        == StrategyType.STRUCTURAL_MEMORY,
                        include_chunks=self.strategy_type
                        == StrategyType.STRUCTURAL_MEMORY,
                    )
                )
            context_result.metadata["path_order"] = path_metadata.get("order", {})
            context_result.metadata["path_predecessors"] = path_metadata.get(
                "predecessors", set()
            )
            context_result.metadata["path_successors"] = path_metadata.get(
                "successors", set()
            )

            # Run dimension agents in parallel
            semaphore = asyncio.Semaphore(self.max_parallel)
            tasks = []

            for dimension_name in dimensions_to_run:
                agent_class = DIMENSION_AGENTS.get(dimension_name)
                if agent_class:
                    agent_data = self._build_agent_data(
                        dimension_name=dimension_name,
                        base_data=base_data,
                        context_result=context_result,
                        node_details=node_details,
                        project_pillars=project_pillars,
                        game_concept=game_concept,
                    )
                    execution_context = {
                        "model_manager": self.model_manager,
                        "model_id": model_id,
                        "data": agent_data,
                    }
                    tasks.append(
                        self._run_dimension_agent(
                            agent_class=agent_class,
                            context=execution_context,
                            semaphore=semaphore,
                        )
                    )

            # Gather all results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results into typed dimension results
            dimension_results = self._process_dimension_results(
                results, dimensions_to_run
            )

            # Calculate total tokens
            for r in results:
                if isinstance(r, AgentResult) and r.success:
                    total_tokens += r.total_tokens

            # Build aggregated result
            execution_time_ms = int((time.time() - start_time) * 1000)

            return CoherenceAggregatedResult.from_dimension_results(
                node_id=str(node.id),
                node_name=node.name,
                strategy_used=self.strategy_type.value,
                backward=dimension_results.get("backward_coherence"),
                forward=dimension_results.get("forward_coherence"),
                global_fit=dimension_results.get("global_fit"),
                integrity=dimension_results.get("node_integrity"),
                execution_time_ms=execution_time_ms,
                total_tokens=total_tokens,
            )

    async def _run_dimension_agent(
        self,
        agent_class: Type[BaseAgent],
        context: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> AgentResult:
        """Run a single dimension agent with semaphore control."""
        async with semaphore:
            agent = agent_class()
            try:
                result = await agent.run(context)
                return result
            except Exception as e:
                logger.exception(f"Agent {agent.name} failed: {e}")
                return AgentResult(
                    agent_name=agent.name,
                    success=False,
                    data=None,
                    error=ErrorInfo(
                        code="AGENT_EXCEPTION",
                        message=str(e),
                        severity="error",
                    ),
                    execution_time_ms=0,
                )

    def _process_dimension_results(
        self,
        results: List[Any],
        dimension_names: List[str],
    ) -> Dict[str, Any]:
        """Convert raw agent results to typed dimension results."""
        dimension_results = {}

        result_schema_map = {
            "backward_coherence": BackwardCoherenceResult,
            "forward_coherence": ForwardCoherenceResult,
            "global_fit": GlobalFitResult,
            "node_integrity": NodeIntegrityResult,
        }

        for i, result in enumerate(results):
            if i >= len(dimension_names):
                break

            dimension_name = dimension_names[i]
            schema_class = result_schema_map.get(dimension_name)

            if schema_class is None:
                logger.warning(f"No schema class found for dimension {dimension_name}")
                continue

            if isinstance(result, AgentResult) and result.success and result.data:
                try:
                    # Parse result data into typed schema
                    typed_result = schema_class(**result.data)
                    dimension_results[dimension_name] = typed_result
                except Exception as e:
                    logger.warning(f"Failed to parse {dimension_name} result: {e}")
            elif isinstance(result, Exception):
                logger.warning(f"Agent {dimension_name} raised exception: {result}")

        return dimension_results

    def _build_agent_data(
        self,
        dimension_name: str,
        base_data: Dict[str, Any],
        context_result: Any,
        node_details: Dict[str, Any],
        project_pillars: Optional[List],
        game_concept: Optional[Any],
    ) -> Dict[str, Any]:
        """Build dimension-specific input for agentic evaluation."""
        agent_data = dict(base_data)
        context_string = self._build_dimension_context_string(
            dimension_name=dimension_name,
            context_result=context_result,
            node_details=node_details,
            project_pillars=project_pillars,
            game_concept=game_concept,
        )
        agent_data["context_string"] = (
            context_string if context_string else "No additional context."
        )

        if dimension_name == "global_fit":
            agent_data["pillars"] = []
            agent_data["game_concept"] = None
        else:
            agent_data["pillars"] = []
            agent_data["game_concept"] = None

        return agent_data

    def _build_dimension_context_string(
        self,
        dimension_name: str,
        context_result: Any,
        node_details: Dict[str, Any],
        project_pillars: Optional[List],
        game_concept: Optional[Any],
    ) -> str:
        """Filter context for agentic dimensions to reduce leakage."""
        if dimension_name == "global_fit":
            return self._build_global_fit_context(
                context_result, project_pillars, game_concept
            )
        if dimension_name == "node_integrity":
            return "No additional context."
        if dimension_name == "backward_coherence":
            return self._build_path_context(
                context_result, node_details, direction="backward"
            )
        if dimension_name == "forward_coherence":
            return self._build_path_context(
                context_result, node_details, direction="forward"
            )
        return context_result.context_string

    def _build_global_fit_context(
        self,
        context_result: Any,
        project_pillars: Optional[List],
        game_concept: Optional[Any],
    ) -> str:
        layer = context_result.get_layer(1) if context_result else None
        if layer and getattr(layer, "content", None):
            return self._strip_target_block(layer.content)

        # Fallback for non-layered contexts
        parts = []
        if game_concept:
            concept_text = getattr(game_concept, "content", "") or ""
            if concept_text:
                parts.append("Game Concept:")
                parts.append(concept_text)
        if project_pillars:
            parts.append("Design Pillars:")
            for pillar in project_pillars:
                name = getattr(pillar, "name", "") or "Pillar"
                desc = getattr(pillar, "description", "")
                parts.append(f"- {name}: {desc}")
        return "\n".join(parts) if parts else "No global context provided."

    def _build_node_integrity_context(
        self,
        context_result: Any,
        node_details: Dict[str, Any],
    ) -> str:
        layer = context_result.get_layer(4) if context_result else None
        if layer and getattr(layer, "content", None):
            return layer.content
        return self._format_target_node(node_details)

    def _build_path_context(
        self,
        context_result: Any,
        node_details: Dict[str, Any],
        direction: str,
    ) -> str:
        layer = context_result.get_layer(3) if context_result else None
        layer_content = getattr(layer, "content", "") if layer else ""
        layer_has_trace = (
            layer_content and "no trace layer" not in layer_content.lower()
        )

        if layer_has_trace:
            trace = self._filter_trace_content(layer_content, direction)
            trace = self._filter_hmem_trace(
                trace,
                node_details,
                direction,
                context_result.metadata.get("path_predecessors", set()),
                context_result.metadata.get("path_successors", set()),
            )
        else:
            trace = self._extract_full_chart_nodes(context_result.context_string)

        return trace or context_result.context_string

    def _filter_trace_content(self, content: str, direction: str) -> str:
        """Trim trace layer content to backward or forward sections."""
        if "Previous:" in content or "Next:" in content:
            lines = [line for line in content.splitlines() if line.strip()]
            if direction == "backward":
                return next(
                    (line for line in lines if line.startswith("Previous:")), ""
                )
            return next((line for line in lines if line.startswith("Next:")), "")

        # Handle new H-Graph format with pools and explicit paths
        if (
            "POOL OF ALL PRIOR NODES" in content
            or "POOL OF ALL FUTURE NODES" in content
        ):
            if direction == "backward":
                # Extract prior nodes pool + paths to target
                prior_pool = self._extract_section(
                    content, "POOL OF ALL PRIOR NODES", "ALL POSSIBLE PATHS TO TARGET"
                )
                paths_to = self._extract_section(
                    content, "ALL POSSIBLE PATHS TO TARGET", "POOL OF ALL FUTURE NODES"
                )
                return "\n\n".join([p for p in [prior_pool, paths_to] if p])
            else:
                # Extract future nodes pool + paths from target
                future_pool = self._extract_section(
                    content,
                    "POOL OF ALL FUTURE NODES",
                    "ALL POSSIBLE PATHS FROM TARGET",
                )
                paths_from = self._extract_section(
                    content, "ALL POSSIBLE PATHS FROM TARGET"
                )
                return "\n\n".join([p for p in [future_pool, paths_from] if p])

        # Handle old format with PREVIOUS NODES / FUTURE NODES
        if "PREVIOUS NODES" in content or "FUTURE NODES" in content:
            if direction == "backward":
                previous = self._extract_section(
                    content, "PREVIOUS NODES", "FUTURE NODES"
                )
                accumulated = self._extract_section(content, "ACCUMULATED PLAYER STATE")
                return "\n\n".join([p for p in [previous, accumulated] if p])
            future = self._extract_section(
                content, "FUTURE NODES", "ACCUMULATED PLAYER STATE"
            )
            return future

        return content

    def _extract_section(
        self,
        content: str,
        start_marker: str,
        end_marker: Optional[str] = None,
    ) -> str:
        start = content.find(start_marker)
        if start == -1:
            return ""
        if end_marker:
            end = content.find(end_marker, start)
            if end == -1:
                end = len(content)
        else:
            end = len(content)
        return content[start:end].strip()

    def _extract_full_chart_nodes(self, content: str) -> str:
        nodes = self._extract_section(content, "FULL CHART NODES", "FULL CHART EDGES")
        edges = self._extract_section(content, "FULL CHART EDGES")
        parts = [p for p in [nodes, edges] if p]
        return "\n\n".join(parts)

    def _filter_hmem_trace(
        self,
        content: str,
        node_details: Dict[str, Any],
        direction: str,
        predecessors: set[str],
        successors: set[str],
    ) -> str:
        """Filter HMEM L3 entries based on direction markers.

        New HMEM format uses direction prefixes:
        - [BACKWARD] / [FORWARD] for node entries (including immediate neighbors)
        - [BACKWARD TRANSITION] / [FORWARD TRANSITION] for transitions

        For backward coherence: keep [BACKWARD...] entries
        For forward coherence: keep [FORWARD...] entries
        """
        # Check for new format markers (direction-prefixed entries)
        has_new_format = any(
            marker in content
            for marker in [
                "[BACKWARD]",
                "[FORWARD]",
                "[BACKWARD TRANSITION]",
                "[FORWARD TRANSITION]",
            ]
        )

        if has_new_format:
            return self._filter_hmem_new_format(content, direction)

        # Legacy format handling (Path snippet: and Node:)
        if "Path snippet:" not in content and "Node:" not in content:
            return content

        target_name = (node_details.get("name") or "").strip()
        if not target_name:
            return content
        allowed_names = (
            set(predecessors) if direction == "backward" else set(successors)
        )
        allowed_names.add(target_name)

        snippets: list[tuple[list[str], str]] = []
        allowed: list[str] = []
        for block in content.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            if block.startswith("Path snippet:"):
                header = block.splitlines()[0]
                if ":" not in header:
                    continue
                snippet = header.split(":", 1)[1].strip()
                nodes = [n.strip() for n in snippet.split("->") if n.strip()]
                if not nodes:
                    continue
                if any(n not in allowed_names for n in nodes):
                    continue
                if direction == "backward":
                    if target_name in nodes and nodes[-1] != target_name:
                        continue
                else:
                    if target_name in nodes and nodes[0] != target_name:
                        continue
                snippets.append((nodes, block))
            elif block.startswith("Node:"):
                # Exclude target node summaries from path context
                if target_name and f"Node: {target_name}" in block:
                    continue
                line = block.splitlines()[0]
                node_name = line.replace("Node:", "").strip()
                if node_name in allowed_names:
                    allowed.append(block)
            else:
                allowed.append(block)

        snippets = self._drop_subset_snippets(snippets)
        allowed.extend([block for _, block in snippets])

        return "\n\n".join(allowed) if allowed else content

    def _filter_hmem_new_format(self, content: str, direction: str) -> str:
        """Filter HMEM entries with new direction-prefixed format.

        STRICT filtering: only keeps blocks that start with the correct
        direction marker. Does NOT keep "neutral" blocks (like old format
        Path snippet: or Node: entries) because those are legacy data that
        shouldn't appear in new format mode.
        """
        # Use prefix patterns to match "[BACKWARD]" and "[BACKWARD TRANSITION]"
        # (Immediate neighbors now use regular [BACKWARD]/[FORWARD] tags)
        if direction == "backward":
            allowed_patterns = ["[BACKWARD"]
        else:
            allowed_patterns = ["[FORWARD"]

        filtered_blocks: list[str] = []
        for block in content.split("\n\n"):
            block = block.strip()
            if not block:
                continue

            # STRICT: only keep blocks that start with allowed direction patterns
            if any(block.startswith(pattern) for pattern in allowed_patterns):
                filtered_blocks.append(block)
            # Skip everything else - old format entries, wrong direction, etc.

        return "\n\n".join(filtered_blocks) if filtered_blocks else content

    def _drop_subset_snippets(
        self, snippets: list[tuple[list[str], str]]
    ) -> list[tuple[list[str], str]]:
        """Remove snippet blocks that are strict contiguous subsets of longer ones."""
        if len(snippets) < 2:
            return snippets
        kept: list[tuple[list[str], str]] = []
        for nodes, block in snippets:
            is_subset = False
            for other_nodes, _ in snippets:
                if nodes == other_nodes or len(nodes) >= len(other_nodes):
                    continue
                for i in range(len(other_nodes) - len(nodes) + 1):
                    if other_nodes[i : i + len(nodes)] == nodes:
                        is_subset = True
                        break
                if is_subset:
                    break
            if not is_subset:
                kept.append((nodes, block))
        return kept

    def _build_path_metadata(self, node: PxNode, chart: PxChart) -> Dict[str, Any]:
        """Build connected predecessor/successor sets for filtering."""
        from collections import deque

        node_id = str(getattr(node, "id", ""))
        if not node_id:
            return {"order": {}, "predecessors": set(), "successors": set()}

        edges = chart.edges.select_related("source__content", "target__content").all()
        forward: Dict[str, list[str]] = {}
        backward: Dict[str, list[str]] = {}
        name_map: Dict[str, str] = {node_id: getattr(node, "name", "")}

        for edge in edges:
            source = getattr(edge, "source", None)
            target = getattr(edge, "target", None)
            if not source or not target:
                continue
            source_node = getattr(source, "content", None)
            target_node = getattr(target, "content", None)
            if not source_node or not target_node:
                continue
            source_id = str(getattr(source_node, "id", ""))
            target_id = str(getattr(target_node, "id", ""))
            if not source_id or not target_id:
                continue
            forward.setdefault(source_id, []).append(target_id)
            backward.setdefault(target_id, []).append(source_id)
            if source_id not in name_map:
                name_map[source_id] = getattr(source_node, "name", "")
            if target_id not in name_map:
                name_map[target_id] = getattr(target_node, "name", "")

        def traverse(start: str, adjacency: Dict[str, list[str]]) -> set[str]:
            visited: set[str] = set()
            queue: deque[str] = deque([start])
            while queue:
                current = queue.popleft()
                for nxt in adjacency.get(current, []):
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    queue.append(nxt)
            return visited

        predecessor_ids = traverse(node_id, backward)
        successor_ids = traverse(node_id, forward)
        predecessors = {
            name_map.get(nid, "") for nid in predecessor_ids if nid in name_map
        }
        successors = {name_map.get(nid, "") for nid in successor_ids if nid in name_map}
        return {"order": {}, "predecessors": predecessors, "successors": successors}

    def _strip_target_block(self, content: str) -> str:
        if "TARGET NODE DETAILS:" not in content:
            return content
        start = content.find("TARGET NODE DETAILS:")
        end = content.find("CONTEXT:", start)
        if end == -1:
            return content[:start].strip()
        return (content[:start] + content[end:]).strip()

    def _build_structural_memory_target_artifacts(
        self,
        context_result: Any,
        node_details: Dict[str, Any],
        include_summaries: bool,
        include_chunks: bool,
    ) -> Dict[str, Any]:
        node_id = str(node_details.get("id") or node_details.get("node_id") or "")
        node_name = node_details.get("name", "")

        facts = [
            fact.fact
            for fact in getattr(context_result, "facts", [])
            if getattr(fact, "node_id", "") == node_id
        ]
        triples = [
            str(triple)
            for triple in getattr(context_result, "triples", [])
            if getattr(triple, "head", "") == node_name
        ]
        summary = None
        if include_summaries:
            for s in getattr(context_result, "summaries", []):
                if getattr(s, "node_id", "") == node_id:
                    summary = getattr(s, "content", None)
                    break
        chunks = []
        if include_chunks:
            for c in getattr(context_result, "chunks", []):
                if getattr(c, "node_id", "") == node_id:
                    content = getattr(c, "content", "")
                    if content:
                        chunks.append(content)

        return {
            "target_node_facts": facts,
            "target_node_triples": triples,
            "target_node_summary": summary,
            "target_node_chunks": chunks,
        }

    def _format_target_node(self, node_details: Dict[str, Any]) -> str:
        return self._format_target_block(node_details)

    def _format_target_block(self, node_details: Dict[str, Any]) -> str:
        lines = [f"Title: {node_details.get('name', 'Unknown')}"]
        description = node_details.get("description")
        if description:
            lines.append(f"Description: {description}")
        components = node_details.get("components", [])
        if components:
            lines.append("Components:")
            for comp in components:
                name = comp.get("name", "Component")
                value = comp.get("value", "")
                lines.append(f"- {name}: {value}")
        return "\n".join(lines)

    def _extract_node_details(self, node: PxNode) -> Dict[str, Any]:
        """Extract node details for internal consistency evaluation."""
        components: List[Dict[str, Any]] = []

        # Extract components if available
        if hasattr(node, "components") and node.components:
            for comp in node.components.all()[:10]:
                definition = getattr(comp, "definition", None)
                definition_name = getattr(definition, "name", None)
                components.append(
                    {
                        "name": definition_name or getattr(comp, "name", "Unknown"),
                        "value": getattr(comp, "value", ""),
                    }
                )

        details: Dict[str, Any] = {
            "name": node.name,
            "id": str(node.id),
            "category": getattr(node, "category", None),
            "description": getattr(node, "description", None),
            "components": components,
        }

        return details

    def _extract_path_nodes(
        self,
        context_result: Any,
        direction: str,
    ) -> List[Dict[str, Any]]:
        """Extract path nodes from context result."""
        nodes = []

        # Try to get from metadata
        path_key = f"{direction}_path" if direction else "path"
        path_data = context_result.metadata.get(path_key, [])

        for node_data in path_data[:10]:  # Limit to 10 nodes
            if isinstance(node_data, dict):
                nodes.append(node_data)
            elif hasattr(node_data, "name"):
                nodes.append(
                    {
                        "name": node_data.name,
                        "id": str(getattr(node_data, "id", "")),
                        "category": getattr(node_data, "category", None),
                    }
                )

        return nodes

    def _format_pillars(self, pillars: Optional[List]) -> List[Dict[str, Any]]:
        """Format pillars for agent consumption."""
        if not pillars:
            return []

        formatted = []
        for pillar in pillars[:6]:  # Limit to 6 pillars
            if isinstance(pillar, dict):
                formatted.append(pillar)
            elif hasattr(pillar, "name"):
                formatted.append(
                    {
                        "name": pillar.name,
                        "description": getattr(pillar, "description", ""),
                    }
                )

        return formatted


class PxNodesCoherenceMonolithicWorkflow:
    """
    Monolithic workflow for evaluating node coherence.

    Uses a single LLM call with a unified prompt covering all 4 dimensions:
    1. Backward Coherence - Does node respect what came before?
    2. Forward Coherence - Does node properly set up future?
    3. Global Fit - Does node align with concept and pillars?
    4. Node Integrity - Is node internally coherent?

    Designed for thesis comparison between agentic vs monolithic approaches.
    Uses the same context strategies and response schemas as the agentic version.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        strategy_type: StrategyType = StrategyType.STRUCTURAL_MEMORY,
        llm_provider: Optional[LLMProvider] = None,
        use_iterative_retrieval: bool = True,
    ):
        """
        Initialize the workflow.

        Args:
            model_manager: ModelManager for LLM access
            strategy_type: Context strategy to use
            llm_provider: LLM provider for context strategies and evaluation
            use_iterative_retrieval: Whether to use iterative retrieval from
                vector store. Default False to use direct extraction.
        """
        self.model_manager = model_manager
        self.strategy_type = strategy_type
        self.llm_provider = llm_provider
        self.use_iterative_retrieval = use_iterative_retrieval

        # Create strategy instance
        self._strategy: Optional[BaseContextStrategy] = None

    def _get_strategy(self) -> BaseContextStrategy:
        """Get or create the context strategy."""
        if self._strategy is None:
            self._strategy = StrategyRegistry.create(
                self.strategy_type,
                llm_provider=self.llm_provider,
                use_iterative_retrieval=self.use_iterative_retrieval,
            )
        return self._strategy

    async def evaluate_node(
        self,
        node: PxNode,
        chart: PxChart,
        model_id: Optional[str] = None,
        project: Optional[Any] = None,
        project_pillars: Optional[List] = None,
        game_concept: Optional[Any] = None,
    ) -> CoherenceAggregatedResult:
        """
        Evaluate a node's coherence using a single unified LLM call.

        Args:
            node: The target node to evaluate
            chart: The chart containing the node
            model_id: Optional specific model to use
            project_pillars: Optional design pillars for contextual fit
            game_concept: Optional game concept for contextual fit

        Returns:
            CoherenceAggregatedResult with all dimension scores
        """
        import logfire
        from asgiref.sync import sync_to_async

        if self.llm_provider is None:
            raise ValueError("llm_provider is required for monolithic evaluation")

        start_time = time.time()

        span_name = f"coherence.evaluate.pxnodes.{self.strategy_type.value}.monolithic"
        with logfire.span(
            span_name,
            feature="pxnodes",
            strategy=self.strategy_type.value,
            execution_mode="monolithic",
            node_id=str(node.id),
            node_name=node.name,
        ):
            # Build context using strategy
            strategy = self._get_strategy()
            scope = EvaluationScope(
                target_node=node,
                chart=chart,
                project=project,
                project_pillars=project_pillars,
                game_concept=game_concept,
            )

            # Use async build_context if available (for parallel extraction)
            if hasattr(strategy, "build_context_async"):
                with logfire.span(
                    "context.build.async",
                    strategy=self.strategy_type.value,
                    target_node=node.name,
                ):
                    context_result = await strategy.build_context_async(scope)
            else:
                # Fallback to sync version wrapped in async
                context_result = await sync_to_async(
                    strategy.build_context, thread_sensitive=True
                )(scope)

            # Build dimension context (same as agentic version)
            dimension_context = await self._build_dimension_context(
                node=node,
                context_result=context_result,
                project_pillars=project_pillars,
                game_concept=game_concept,
            )

            # Build the unified prompt
            node_details = await sync_to_async(
                self._extract_node_details, thread_sensitive=True
            )(node)
            target_node_block = self._format_target_block(node_details)

            prompt = MONOLITHIC_COHERENCE_PROMPT.format(
                context=context_result.context_string,
                target_node_block=target_node_block,
                dimension_context=dimension_context,
            )

            # Single LLM call for all 4 dimensions
            with logfire.span(
                "llm.generate.coherence_monolithic",
                node_name=node.name,
                prompt_length=len(prompt),
            ):
                response = await sync_to_async(
                    self.llm_provider.generate, thread_sensitive=False
                )(prompt)

            # Parse response into dimension results
            dimension_results = self._parse_response(response)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            total_tokens = getattr(self.llm_provider, "last_total_tokens", 0)
            if not total_tokens:
                # Fallback when provider does not report usage
                total_tokens = len(prompt.split()) + len(response.split())

            logfire.info(
                "monolithic_evaluation_complete",
                node_id=str(node.id),
                node_name=node.name,
                execution_time_ms=execution_time_ms,
                overall_score=self._calculate_overall_score(dimension_results),
            )

            return CoherenceAggregatedResult.from_dimension_results(
                node_id=str(node.id),
                node_name=node.name,
                strategy_used=self.strategy_type.value,
                backward=dimension_results.get("backward_coherence"),
                forward=dimension_results.get("forward_coherence"),
                global_fit=dimension_results.get("global_fit"),
                integrity=dimension_results.get("node_integrity"),
                execution_time_ms=execution_time_ms,
                total_tokens=total_tokens,
            )

    async def _build_dimension_context(
        self,
        node: PxNode,
        context_result: Any,
        project_pillars: Optional[List],
        game_concept: Optional[Any],
    ) -> str:
        """Build additional context for all dimensions."""
        context_parts = []

        # Backward path context (for prerequisite alignment)
        backward_path = context_result.metadata.get("backward_path", [])
        if backward_path:
            context_parts.append(
                f"BACKWARD PATH: {len(backward_path)} nodes lead to this point"
            )
            node_names = [
                (
                    n.get("name", "Unknown")
                    if isinstance(n, dict)
                    else getattr(n, "name", "Unknown")
                )
                for n in backward_path[:5]
            ]
            context_parts.append(f"Recent path: {' → '.join(node_names)}")

        # Forward path context (for forward setup)
        forward_path = context_result.metadata.get("forward_path", [])
        if forward_path:
            context_parts.append(
                f"FORWARD PATH: {len(forward_path)} nodes follow this point"
            )
            node_names = [
                (
                    n.get("name", "Unknown")
                    if isinstance(n, dict)
                    else getattr(n, "name", "Unknown")
                )
                for n in forward_path[:5]
            ]
            context_parts.append(f"Upcoming nodes: {' → '.join(node_names)}")

        return "\n".join(context_parts) if context_parts else "No additional context"

    def _extract_node_details(self, node: PxNode) -> Dict[str, Any]:
        """Extract node details for internal consistency evaluation."""
        components: List[Dict[str, Any]] = []

        # Extract components if available
        if hasattr(node, "components") and node.components:
            for comp in node.components.all()[:10]:
                definition = getattr(comp, "definition", None)
                definition_name = getattr(definition, "name", None)
                components.append(
                    {
                        "name": definition_name or getattr(comp, "name", "Unknown"),
                        "value": getattr(comp, "value", ""),
                    }
                )

        details: Dict[str, Any] = {
            "name": node.name,
            "category": getattr(node, "category", None),
            "description": getattr(node, "description", None),
            "components": components,
        }

        return details

    def _format_target_block(self, node_details: Dict[str, Any]) -> str:
        lines = [f"Title: {node_details.get('name', 'Unknown')}"]
        description = node_details.get("description")
        if description:
            lines.append(f"Description: {description}")
        components = node_details.get("components", [])
        if components:
            lines.append("Components:")
            for comp in components:
                name = comp.get("name", "Component")
                value = comp.get("value", "")
                lines.append(f"- {name}: {value}")
        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into typed dimension results."""
        dimension_results: Dict[str, Any] = {}

        try:
            # Extract JSON from response
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)

            # Parse each dimension
            if "backward_coherence" in data:
                dimension_results["backward_coherence"] = BackwardCoherenceResult(
                    **data["backward_coherence"]
                )

            if "forward_coherence" in data:
                dimension_results["forward_coherence"] = ForwardCoherenceResult(
                    **data["forward_coherence"]
                )

            if "global_fit" in data:
                dimension_results["global_fit"] = GlobalFitResult(**data["global_fit"])

            if "node_integrity" in data:
                dimension_results["node_integrity"] = NodeIntegrityResult(
                    **data["node_integrity"]
                )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response[:500]}")
        except Exception as e:
            logger.warning(f"Failed to build dimension results: {e}")

        return dimension_results

    def _calculate_overall_score(self, dimension_results: Dict[str, Any]) -> float:
        """Calculate overall score from dimension results."""
        scores = []
        for result in dimension_results.values():
            if hasattr(result, "score"):
                scores.append(result.score)
        return sum(scores) / len(scores) if scores else 3.0


def evaluate_node_agentic(
    node_id: str,
    chart_id: str,
    model_id: Optional[str] = None,
    strategy: str = "structural_memory",
    dimensions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to evaluate a node using agentic workflow.

    Args:
        node_id: UUID of the node to evaluate
        chart_id: UUID of the chart
        model_id: Optional specific model to use
        strategy: Context strategy name
        dimensions: Optional list of dimensions to evaluate

    Returns:
        Evaluation result dictionary
    """
    import asyncio

    from pxnodes.llm.context.shared import create_llm_provider

    node = PxNode.objects.get(id=node_id)
    chart = PxChart.objects.get(id=chart_id)

    llm_provider = create_llm_provider(model_name=model_id or "gpt-4o-mini")
    model_manager = ModelManager()

    strategy_type = StrategyType(strategy)

    workflow = PxNodesCoherenceWorkflow(
        model_manager=model_manager,
        strategy_type=strategy_type,
        llm_provider=llm_provider,
    )

    result = asyncio.run(
        workflow.evaluate_node(
            node=node,
            chart=chart,
            model_id=model_id,
            dimensions=dimensions,
        )
    )

    return result.model_dump()


def evaluate_node_monolithic(
    node_id: str,
    chart_id: str,
    model_id: Optional[str] = None,
    strategy: str = "structural_memory",
) -> Dict[str, Any]:
    """
    Convenience function to evaluate a node using monolithic workflow.

    Args:
        node_id: UUID of the node to evaluate
        chart_id: UUID of the chart
        model_id: Optional specific model to use
        strategy: Context strategy name

    Returns:
        Evaluation result dictionary
    """
    import asyncio

    from pxnodes.llm.context.shared import create_llm_provider

    node = PxNode.objects.get(id=node_id)
    chart = PxChart.objects.get(id=chart_id)

    llm_provider = create_llm_provider(model_name=model_id or "gpt-4o-mini")
    model_manager = ModelManager()

    strategy_type = StrategyType(strategy)

    workflow = PxNodesCoherenceMonolithicWorkflow(
        model_manager=model_manager,
        strategy_type=strategy_type,
        llm_provider=llm_provider,
    )

    result = asyncio.run(
        workflow.evaluate_node(
            node=node,
            chart=chart,
            model_id=model_id,
        )
    )

    return result.model_dump()
