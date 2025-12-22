"""
PxNodes Coherence Workflows - Agentic and Monolithic evaluation of node coherence.

Agentic Workflow:
Coordinates 4 specialized dimension agents running in parallel:
- PrerequisiteAlignmentAgent
- ForwardSetupAgent
- InternalConsistencyAgent
- ContextualFitAgent

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
    ContextualFitAgent,
    ForwardSetupAgent,
    InternalConsistencyAgent,
    PrerequisiteAlignmentAgent,
)
from pxnodes.llm.agents.coherence.schemas import (
    CoherenceAggregatedResult,
    ContextualFitResult,
    ForwardSetupResult,
    InternalConsistencyResult,
    PrerequisiteAlignmentResult,
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

MONOLITHIC_COHERENCE_PROMPT = """You are a game design coherence analyzer evaluating a node in a game flow chart.  # noqa: E501

CONTEXT:
{context}

TARGET NODE: {target_node_name}

{dimension_context}

TASK: Evaluate ALL FOUR coherence dimensions for the target node.

================================================================================
DIMENSION 1: PREREQUISITE ALIGNMENT
================================================================================
Analyze whether the target node properly respects what came before in the game flow.

CHECK FOR:
1. ITEM/ABILITY PREREQUISITES
   - Does the node require items/abilities the player should have?
   - Are all required mechanics already introduced?
   - Example violation: "Use Double Jump" but player never acquired it

2. NARRATIVE PREREQUISITES
   - Does the node reference events that have occurred?
   - Are character introductions properly sequenced?
   - Example violation: "Return to the castle" but player never visited it

3. MECHANICAL PREREQUISITES
   - Are gameplay mechanics properly introduced before use?
   - Is complexity appropriately ramped up?
   - Example violation: Complex combo required without tutorial

4. STATE PREREQUISITES
   - Does the node assume a game state that is achievable?
   - Are triggers/conditions for reaching this node satisfiable?

================================================================================
DIMENSION 2: FORWARD SETUP
================================================================================
Analyze whether the target node properly sets up what comes next in the game flow.

CHECK FOR:
1. MECHANICAL SETUP
   - Does the node introduce mechanics that will be needed later?
   - Are abilities/items granted that enable future progression?
   - Example: Tutorial teaches wall-jump before wall-jump puzzle

2. NARRATIVE SETUP
   - Are story elements introduced that pay off later?
   - Is foreshadowing appropriate and not heavy-handed?
   - Example: NPC mentions a locked door player will encounter

3. DIFFICULTY RAMP
   - Does the node prepare player for upcoming challenges?
   - Is the skill progression appropriate?
   - Example: Easy enemies before boss teach attack patterns

4. WORLD BUILDING
   - Are locations/characters introduced properly?
   - Is context provided for future events?

================================================================================
DIMENSION 3: INTERNAL CONSISTENCY
================================================================================
Analyze whether the target node is internally coherent and well-defined.

CHECK FOR:
1. CONTRADICTIONS
   - Do different parts of the node contradict each other?
   - Does the description match the node type/category?
   - Example: "Calm exploration" with Tension=95

2. CLARITY
   - Is the node's purpose clear?
   - Are descriptions specific enough to implement?
   - Example violation: "Do the thing with the stuff"

3. COMPONENT HARMONY
   - Do all node components work together?
   - Is the component category and value appropriate for the content?
   - Are visual/audio hints consistent with the experience?

4. COMPLETENESS
   - Is all necessary information present?
   - Are edge cases considered?
   - Are player choices well-defined?

================================================================================
DIMENSION 4: CONTEXTUAL FIT
================================================================================
Analyze whether the target node fits the broader game context and design vision.

CHECK FOR:
1. PILLAR ALIGNMENT
   - Does the node support the game's design pillars?
   - Are there conflicts with stated design goals?
   - Example: Pillar is "Non-violent conflict resolution" but node has combat

2. CONCEPT ALIGNMENT
   - Does the node fit the overall game concept?
   - Is it consistent with the game's genre and target audience?
   - Example: Gritty realistic shooter with cartoon powerups

3. TONE CONSISTENCY
   - Does the node match the game's tone?
   - Is the writing style consistent?
   - Example: Dark horror game with comedic dialogue

4. STYLE COHERENCE
   - Do visual/audio directions fit the game's aesthetic?
   - Are gameplay elements consistent with the genre?

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
  "prerequisite_alignment": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "missing_prerequisites": [
        "List items/abilities/mechanics that are required but not established"
    ],
    "satisfied_prerequisites": ["List prerequisites that ARE properly established"]
  }},
  "forward_setup": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "elements_introduced": ["New elements introduced in this node"],
    "potential_payoffs": ["How these elements might pay off later"]
  }},
  "internal_consistency": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "contradictions": ["List of internal contradictions found"],
    "unclear_elements": ["Vague or unclear elements that need clarification"]
  }},
  "contextual_fit": {{
    "score": <1-6>,
    "reasoning": "Detailed explanation of your score",
    "issues": ["Issue 1", "Issue 2", ...],
    "suggestions": ["Suggestion 1", "Suggestion 2", ...],
    "pillar_alignment": ["How the node aligns (or conflicts) with each pillar"],
    "concept_alignment": "Overall assessment of fit with game concept"
  }}
}}

IMPORTANT: Evaluate ALL 4 dimensions thoroughly. Report genuine issues only."""


# Map of dimension names to agent classes
DIMENSION_AGENTS: Dict[str, Type[BaseAgent]] = {
    "prerequisite_alignment": PrerequisiteAlignmentAgent,
    "forward_setup": ForwardSetupAgent,
    "internal_consistency": InternalConsistencyAgent,
    "contextual_fit": ContextualFitAgent,
}


class PxNodesCoherenceWorkflow:
    """
    Agentic workflow for evaluating node coherence.

    Uses 4 specialized agents running in parallel, each focusing on
    a different dimension of coherence:
    1. Prerequisite Alignment - Does node respect what came before?
    2. Forward Setup - Does node properly set up future?
    3. Internal Consistency - Is node internally coherent?
    4. Contextual Fit - Does node fit game concept/pillars?

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

            include_target_description = not context_result.metadata.get(
                "includes_target_description"
            )

            base_data = {
                "context_string": context_result.context_string,
                "target_node_name": node.name,
                "target_node_description": (
                    node_details.get("description")
                    if include_target_description
                    else None
                ),
                "node_details": node_details,
                "backward_nodes": self._extract_path_nodes(context_result, "backward"),
                "forward_nodes": self._extract_path_nodes(context_result, "forward"),
                "pillars": self._format_pillars(project_pillars),
                "game_concept": game_concept,
                "is_full_context": bool(context_result.metadata.get("full_context")),
                "strategy_type": self.strategy_type.value,
                "player_state": context_result.metadata.get("player_state", {}),
            }

            # Build execution context
            execution_context = {
                "model_manager": self.model_manager,
                "model_id": model_id,
                "data": base_data,
            }

            # Run dimension agents in parallel
            semaphore = asyncio.Semaphore(self.max_parallel)
            tasks = []

            for dimension_name in dimensions_to_run:
                agent_class = DIMENSION_AGENTS.get(dimension_name)
                if agent_class:
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
                prerequisite=dimension_results.get("prerequisite_alignment"),
                forward=dimension_results.get("forward_setup"),
                internal=dimension_results.get("internal_consistency"),
                contextual=dimension_results.get("contextual_fit"),
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
            "prerequisite_alignment": PrerequisiteAlignmentResult,
            "forward_setup": ForwardSetupResult,
            "internal_consistency": InternalConsistencyResult,
            "contextual_fit": ContextualFitResult,
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
    1. Prerequisite Alignment - Does node respect what came before?
    2. Forward Setup - Does node properly set up future?
    3. Internal Consistency - Is node internally coherent?
    4. Contextual Fit - Does node fit game concept/pillars?

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
            target_node_block = node.name
            include_target_description = not context_result.metadata.get(
                "includes_target_description"
            )
            if node.description and include_target_description:
                target_node_block = f"{node.name}\nDescription: {node.description}"

            prompt = MONOLITHIC_COHERENCE_PROMPT.format(
                context=context_result.context_string,
                target_node_name=target_node_block,
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
                prerequisite=dimension_results.get("prerequisite_alignment"),
                forward=dimension_results.get("forward_setup"),
                internal=dimension_results.get("internal_consistency"),
                contextual=dimension_results.get("contextual_fit"),
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
        from asgiref.sync import sync_to_async

        context_parts = []

        # Extract node details (sync Django ORM call)
        node_details = await sync_to_async(
            self._extract_node_details, thread_sensitive=True
        )(node)

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

        # Node details context (for internal consistency)
        if node_details.get("category"):
            context_parts.append(f"Category: {node_details['category']}")
        if node_details.get("components"):
            components = node_details["components"]
            context_parts.append(f"Components: {len(components)} defined")
            for comp in components[:5]:
                name = comp.get("name", "Unknown")
                value = comp.get("value", "")
                context_parts.append(f"  - {name}: {value}")
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
            if "prerequisite_alignment" in data:
                dimension_results["prerequisite_alignment"] = (
                    PrerequisiteAlignmentResult(**data["prerequisite_alignment"])
                )

            if "forward_setup" in data:
                dimension_results["forward_setup"] = ForwardSetupResult(
                    **data["forward_setup"]
                )

            if "internal_consistency" in data:
                dimension_results["internal_consistency"] = InternalConsistencyResult(
                    **data["internal_consistency"]
                )

            if "contextual_fit" in data:
                dimension_results["contextual_fit"] = ContextualFitResult(
                    **data["contextual_fit"]
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
