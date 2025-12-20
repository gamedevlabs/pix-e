"""
Combined Strategy Implementation.

Combines Mixed Structural Memory (Zeng et al. 2024) data representation with
Hierarchical Graph traversal for context organization.

This strategy uses all four memory structures from Zeng et al. (2024):
- Chunks: Raw text segments
- Knowledge Triples: Structured relationships
- Atomic Facts: Indivisible information units
- Summaries: Condensed overviews

Combined with Hierarchical Graph's deterministic traversal:
- L1 Domain: Project-level context (full game concept + all pillars)
- L2 Category: Chart-level context
- L3 Trace: FULL path context via BFS (backward + forward)
- L4 Episode: Target node with all four memory structures

Key principle: NO ARBITRARY TRUNCATION - preserve full content.

Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries
"""

import asyncio
from typing import Any, Optional, cast

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
    get_layer_name,
)
from pxnodes.llm.context.hierarchical_graph.traversal import (
    forward_bfs,
    reverse_bfs,
)
from pxnodes.llm.context.structural_memory.chunks import (
    Chunk,
    extract_chunks,
)
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
)
from pxnodes.llm.context.structural_memory.facts import LLMProvider as FactsLLMProvider
from pxnodes.llm.context.structural_memory.facts import (
    extract_atomic_facts,
    extract_atomic_facts_async,
)
from pxnodes.llm.context.structural_memory.summaries import (
    LLMProvider as SummariesLLMProvider,
)
from pxnodes.llm.context.structural_memory.summaries import (
    Summary,
    create_fallback_summary,
    extract_summary,
    extract_summary_async,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)

# Combined context template with hierarchical graph + structural memory
COMBINED_CONTEXT_TEMPLATE = """### COMBINED CONTEXT (Graph + Structural Memory)

**[L1 DOMAIN - Project Level]**
{l1_content}

**[L2 CATEGORY - Chart Level]**
{l2_content}

**[L3 TRACE - Full Path Context]**
{l3_content}

**[L4 EPISODE - Target Node]**

Summary:
{l4_summary}

Description:
{l4_description}

Knowledge Triples:
{l4_triples}

Atomic Facts:
{l4_facts}

**[COMPUTED METRICS]**
{derived_triples}
"""


@StrategyRegistry.register(StrategyType.COMBINED)
class CombinedStrategy(BaseContextStrategy):
    """
    Combined strategy using Mixed Structural Memory + Hierarchical Graph traversal.

    This hybrid approach combines:

    1. Mixed Structural Memory (Zeng et al. 2024) - all four structures:
       - Chunks: Raw text segments (deterministic)
       - Knowledge Triples: Structured relationships (deterministic)
       - Atomic Facts: Indivisible information units (LLM-based)
       - Summaries: Condensed overviews (LLM-based)

    2. Hierarchical Graph traversal (deterministic BFS):
       - L1 Domain: FULL project context (game concept + all pillars, no truncation)
       - L2 Category: Chart-level context
       - L3 Trace: FULL backward + forward path via BFS with structural data
       - L4 Episode: Target node with all four memory structures

    Key principle: NO ARBITRARY TRUNCATION - preserve full content.

    Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries

    This allows thesis comparison of:
    - Pure structural approach (StructuralMemoryStrategy)
    - Pure hierarchical approach (HierarchicalGraphStrategy)
    - Pure embedding approach (HMEMStrategy)
    - Combined approach (this strategy)
    """

    strategy_type = StrategyType.COMBINED

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
        include_derived_triples: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the Combined strategy.

        Args:
            llm_provider: LLM for fact/summary extraction
            skip_fact_extraction: Skip LLM-based fact extraction
            skip_summary_extraction: Skip LLM-based summary extraction
            include_derived_triples: Include computed metrics (intensity deltas)
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.skip_fact_extraction = skip_fact_extraction
        self.skip_summary_extraction = skip_summary_extraction
        self.include_derived_triples = include_derived_triples

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build combined context using all four memory structures + BFS traversal.

        Extracts all four memory structures from Zeng et al. (2024):
        - Chunks: Raw text segments
        - Knowledge Triples: Structured relationships
        - Atomic Facts: Indivisible information units
        - Summaries: Condensed overviews

        Organized using Hierarchical Graph's BFS traversal:
        - L1 Domain: FULL project context (no truncation)
        - L2 Category: Chart context
        - L3 Trace: FULL backward + forward path via BFS with mixed memory
        - L4 Episode: Target node with all four structures

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional query (not used in combined approach)

        Returns:
            ContextResult with all four memory structures in hierarchical format
        """
        # Use hierarchical graph's BFS for FULL path traversal
        backward_nodes = reverse_bfs(
            scope.target_node,
            scope.chart,
            max_depth=None,  # Get complete backward path
            stop_at_checkpoint=False,  # Don't stop at checkpoints
        )
        forward_nodes = forward_bfs(
            scope.target_node,
            scope.chart,
            max_depth=None,  # Get complete forward path
        )
        all_nodes = [scope.target_node] + backward_nodes + forward_nodes

        # Build hierarchical layers (L1-L2 from H-MEM style)
        l1_domain = self._build_domain_layer(scope)
        l2_category = self._build_category_layer(scope)

        # 1. Extract CHUNKS (deterministic - raw text segments)
        all_chunks: list[Chunk] = []
        for node in all_nodes:
            all_chunks.extend(extract_chunks(node))

        # 2. Extract KNOWLEDGE TRIPLES (deterministic)
        all_triples: list[KnowledgeTriple] = []
        for node in all_nodes:
            all_triples.extend(
                extract_all_triples(node, scope.chart, include_neighbors=False)
            )

        # Compute derived triples (intensity deltas, transitions)
        derived_triples: list[KnowledgeTriple] = []
        if self.include_derived_triples:
            derived_triples = compute_derived_triples(
                scope.target_node,
                backward_nodes,
                forward_nodes,
            )
        all_triples.extend(derived_triples)

        # 3. Extract ATOMIC FACTS (LLM-based)
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            all_facts = self._extract_facts_parallel(all_nodes)

        # 4. Extract SUMMARIES (LLM-based)
        all_summaries: list[Summary] = []
        if self.llm_provider and not self.skip_summary_extraction:
            all_summaries = self._extract_summaries_parallel(all_nodes)
        else:
            for node in all_nodes:
                all_summaries.append(create_fallback_summary(node))

        # Build L3 with FULL path context (backward + forward)
        l3_trace = self._build_trace_layer_with_mixed_memory(
            scope,
            backward_nodes,
            forward_nodes,
            all_chunks,
            all_triples,
            all_facts,
            all_summaries,
        )

        # Build L4 with all four structures for target node
        l4_episode = self._build_episode_layer_with_mixed_memory(
            scope, all_chunks, all_triples, all_facts, all_summaries
        )

        # Format context string
        context_string = self._format_context(
            l1_domain,
            l2_category,
            l3_trace,
            scope,
            all_chunks,
            all_triples,
            all_facts,
            all_summaries,
            derived_triples,
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain, l2_category, l3_trace, l4_episode],
            chunks=all_chunks,
            triples=all_triples,
            facts=all_facts,
            summaries=all_summaries,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "chunk_count": len(all_chunks),
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
                "summary_count": len(all_summaries),
                "derived_triple_count": len(derived_triples),
                "backward_path_length": len(backward_nodes),
                "forward_path_length": len(forward_nodes),
            },
        )

    def _extract_facts_parallel(self, nodes: list[Any]) -> list[AtomicFact]:
        async def run() -> list[AtomicFact]:
            # Cast LLMProvider since both protocols are compatible
            assert self.llm_provider is not None
            tasks = [
                extract_atomic_facts_async(
                    node, cast(FactsLLMProvider, self.llm_provider)
                )
                for node in nodes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            facts: list[AtomicFact] = []
            for result in results:
                if isinstance(result, list):
                    facts.extend(result)
            return facts

        try:
            return asyncio.run(run())
        except RuntimeError:
            facts: list[AtomicFact] = []
            for node in nodes:
                facts.extend(extract_atomic_facts(node, self.llm_provider))
            return facts

    def _extract_summaries_parallel(self, nodes: list[Any]) -> list[Summary]:
        async def run() -> list[Summary]:
            # Cast LLMProvider since both protocols are compatible
            assert self.llm_provider is not None
            tasks = [
                extract_summary_async(
                    node, cast(SummariesLLMProvider, self.llm_provider)
                )
                for node in nodes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            summaries: list[Summary] = []
            for result in results:
                if isinstance(result, Summary):
                    summaries.append(result)
            return summaries

        try:
            return asyncio.run(run())
        except RuntimeError:
            return [extract_summary(node, self.llm_provider) for node in nodes]

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """Get context for a specific layer."""
        if layer == 1:
            return self._build_domain_layer(scope)
        elif layer == 2:
            return self._build_category_layer(scope)
        elif layer == 3:
            # Build full context to get L3
            result = self.build_context(scope)
            return (
                result.layers[2]
                if len(result.layers) > 2
                else LayerContext(
                    layer=3, layer_name="trace", content="No path context"
                )
            )
        else:  # layer == 4
            result = self.build_context(scope)
            return (
                result.layers[3]
                if len(result.layers) > 3
                else LayerContext(
                    layer=4, layer_name="episode", content="No episode context"
                )
            )

    def _build_domain_layer(self, scope: EvaluationScope) -> LayerContext:
        """
        Build L1 Domain layer from project context.

        NO TRUNCATION - preserve full game concept and all pillars.
        """
        content_parts = []

        # Full game concept - no truncation
        if scope.game_concept:
            concept = getattr(scope.game_concept, "content", "")
            if concept:
                content_parts.append(f"Game Concept:\n{concept}")

        # All pillars with full descriptions - no truncation
        if scope.project_pillars:
            pillar_texts = []
            for p in scope.project_pillars:  # All pillars, not limited
                name = getattr(p, "name", "")
                desc = getattr(p, "description", "")  # Full description
                if desc:
                    pillar_texts.append(f"- {name}: {desc}")
                else:
                    pillar_texts.append(f"- {name}")
            content_parts.append("Design Pillars:\n" + "\n".join(pillar_texts))

        return LayerContext(
            layer=1,
            layer_name=get_layer_name(1),
            content=(
                "\n\n".join(content_parts) if content_parts else "No project context"
            ),
            metadata={"source": "combined_l1"},
        )

    def _build_category_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L2 Category layer from chart."""
        chart = scope.chart
        content = f"Chart: {chart.name}\nDescription: {chart.description or 'N/A'}"

        return LayerContext(
            layer=2,
            layer_name=get_layer_name(2),
            content=content,
            metadata={"chart_id": str(chart.id), "source": "combined_l2"},
        )

    def _build_trace_layer_with_mixed_memory(
        self,
        scope: EvaluationScope,
        backward_nodes: list[Any],
        forward_nodes: list[Any],
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
    ) -> LayerContext:
        """
        Build L3 Trace layer with mixed memory from FULL path.

        Uses hierarchical graph's BFS traversal for complete path context.
        """
        content_parts = []

        # PREVIOUS NODES (backward path) - full content
        if backward_nodes:
            path_names = [n.name for n in backward_nodes]
            content_parts.append(
                f"PREVIOUS NODES (Path leading to target):\n"
                f"  {' -> '.join(path_names)} -> [TARGET]"
            )

            # Format each previous node with mixed memory
            for i, node in enumerate(backward_nodes, 1):
                node_content = self._format_node_mixed_memory(
                    node.name,
                    str(node.id),
                    chunks,
                    triples,
                    facts,
                    summaries,
                    index=i,
                )
                if node_content:
                    content_parts.append(node_content)
        else:
            content_parts.append("PREVIOUS NODES: None (this is the start)")

        # FUTURE NODES (forward path) - full content
        if forward_nodes:
            next_names = [n.name for n in forward_nodes]
            content_parts.append(
                f"\nFUTURE NODES (What comes after target):\n"
                f"  [TARGET] -> {' -> '.join(next_names)}"
            )

            for i, node in enumerate(forward_nodes, 1):
                node_content = self._format_node_mixed_memory(
                    node.name,
                    str(node.id),
                    chunks,
                    triples,
                    facts,
                    summaries,
                    index=i,
                )
                if node_content:
                    content_parts.append(node_content)
        else:
            content_parts.append("\nFUTURE NODES: None (this is the end)")

        return LayerContext(
            layer=3,
            layer_name=get_layer_name(3),
            content="\n".join(content_parts) if content_parts else "No path context",
            metadata={
                "backward_count": len(backward_nodes),
                "forward_count": len(forward_nodes),
                "source": "combined_l3",
            },
        )

    def _build_episode_layer_with_mixed_memory(
        self,
        scope: EvaluationScope,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
    ) -> LayerContext:
        """Build L4 Episode layer with all four memory structures."""
        node = scope.target_node
        node_id = str(node.id)
        node_name = node.name

        content_parts = [f"Target Node: {node_name}"]

        # Filter for target node
        node_summaries = [s for s in summaries if s.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        node_facts = [f for f in facts if f.node_id == node_id]
        node_chunks = [c for c in chunks if c.node_id == node_id]

        # 1. Summary
        if node_summaries:
            content_parts.append("\nSummary:")
            for s in node_summaries:
                content_parts.append(f"  {s.content}")

        # 2. Knowledge Triples
        if node_triples:
            content_parts.append("\nKnowledge Triples:")
            for t in node_triples[:20]:
                content_parts.append(f"  - {t}")

        # 3. Atomic Facts
        if node_facts:
            content_parts.append("\nAtomic Facts:")
            for f in node_facts[:15]:
                content_parts.append(f"  - {f.fact}")

        # 4. Raw Text (description chunks only)
        desc_chunks = [c for c in node_chunks if c.source == "description"]
        if desc_chunks:
            content_parts.append("\nRaw Text:")
            for c in desc_chunks:
                content_parts.append(f"  {c.content}")

        return LayerContext(
            layer=4,
            layer_name=get_layer_name(4),
            content="\n".join(content_parts),
            metadata={
                "node_id": node_id,
                "summary_count": len(node_summaries),
                "triples_count": len(node_triples),
                "facts_count": len(node_facts),
                "chunks_count": len(node_chunks),
                "source": "combined_l4",
            },
        )

    def _format_node_mixed_memory(
        self,
        node_name: str,
        node_id: str,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        index: int = 0,
    ) -> str:
        """
        Format all four memory structures for a single node.

        NO TRUNCATION - preserve full content for each node.
        """
        # Filter for this node
        node_summaries = [s for s in summaries if s.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        node_facts = [f for f in facts if f.node_id == node_id]
        node_chunks = [c for c in chunks if c.node_id == node_id]

        # Get description chunk for raw text
        desc_chunks = [c for c in node_chunks if c.source == "description"]

        if not any([node_summaries, node_triples, node_facts, desc_chunks]):
            return ""

        lines = [f"\n  {index}. {node_name}:"]

        # Summary - full content (no truncation)
        if node_summaries:
            lines.append(f"     Summary: {node_summaries[0].content}")

        # Raw description - full content
        if desc_chunks:
            lines.append(f"     Description: {desc_chunks[0].content}")

        # Triples - all relevant triples
        if node_triples:
            lines.append("     Triples:")
            for t in node_triples:
                lines.append(f"       - {t}")

        # Facts - all facts
        if node_facts:
            lines.append("     Facts:")
            for f in node_facts:
                lines.append(f"       - {f.fact}")

        return "\n".join(lines)

    def _format_context(
        self,
        l1: LayerContext,
        l2: LayerContext,
        l3: LayerContext,
        scope: EvaluationScope,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        derived_triples: list[KnowledgeTriple],
    ) -> str:
        """
        Format all components into combined context string.

        NO TRUNCATION - preserve full content for target node.
        """
        target_id = str(scope.target_node.id)
        target_name = scope.target_node.name

        # Filter for target node
        target_summaries = [s for s in summaries if s.node_id == target_id]
        target_triples = [t for t in triples if t.head == target_name]
        target_facts = [f for f in facts if f.node_id == target_id]

        # Format L4 sections - NO TRUNCATION
        l4_summary_str = (
            target_summaries[0].content if target_summaries else "(no summary)"
        )

        # Full description from node
        l4_description_str = scope.target_node.description or "(no description)"

        # All triples - no limit
        l4_triples_str = (
            "\n".join(f"  - {t}" for t in target_triples)
            if target_triples
            else "  (none)"
        )

        # All facts - no limit
        l4_facts_str = (
            "\n".join(f"  - {f.fact}" for f in target_facts)
            if target_facts
            else "  (none)"
        )

        # Derived triples (computed metrics)
        derived_str = (
            "\n".join(f"  - {t}" for t in derived_triples)
            if derived_triples
            else "  (none)"
        )

        return COMBINED_CONTEXT_TEMPLATE.format(
            l1_content=l1.content,
            l2_content=l2.content,
            l3_content=l3.content,
            l4_summary=l4_summary_str,
            l4_description=l4_description_str,
            l4_triples=l4_triples_str,
            l4_facts=l4_facts_str,
            derived_triples=derived_str,
        )

    @property
    def requires_embeddings(self) -> bool:
        """Combined uses structural data, not necessarily embeddings."""
        return False

    @property
    def requires_llm(self) -> bool:
        """Requires LLM for atomic fact extraction (unless skipped)."""
        return not self.skip_fact_extraction
