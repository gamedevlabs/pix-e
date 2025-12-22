"""
Context Engineering Strategies Module.

Provides multiple context engineering strategies for LLM evaluation:
- Full Context: Unfiltered project + path context for RQ1 baselines
- Structural Memory (Zeng et al. 2024): Knowledge Triples + Atomic Facts
- Hierarchical Graph: Deterministic 4-layer graph traversal
- H-MEM (Sun & Zeng 2025): Vector embeddings with positional index routing
- Combined: Structural data representation + H-MEM hierarchical organization
"""

# Base framework
from pxnodes.llm.context.base import (
    BaseContextStrategy,
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyRegistry,
    StrategyType,
)

# Legacy imports for backward compatibility
from pxnodes.llm.context.change_detection import (
    compute_node_content_hash,
    get_changed_nodes,
    get_processing_stats,
    has_node_changed,
    update_processing_state,
)

# Combined strategy
from pxnodes.llm.context.combined import CombinedStrategy

# Full Context strategy
from pxnodes.llm.context.full_context import FullContextStrategy
from pxnodes.llm.context.generator import (
    GenerationResult,
    StructuralMemoryGenerator,
    generate_structural_memory,
)

# Hierarchical Graph strategy
from pxnodes.llm.context.hierarchical_graph import (
    HierarchicalGraphStrategy,
    PlayerState,
    aggregate_player_state,
    build_category_layer,
    build_domain_layer,
    build_episode_layer,
    build_trace_layer,
    forward_bfs,
    reverse_bfs,
)

# H-MEM strategy
from pxnodes.llm.context.hmem import (
    HMEMContextResult,
    HMEMRetrievalResult,
    HMEMRetriever,
    HMEMStrategy,
    compute_path_hash,
)

# Shared utilities
from pxnodes.llm.context.shared import (
    GraphSlice,
    LLMProviderAdapter,
    OpenAIEmbeddingGenerator,
    VectorStore,
    create_llm_provider,
    get_graph_slice,
    init_database,
)

# Strategy-aware evaluator
from pxnodes.llm.context.strategy_evaluator import (
    ComparisonResult,
    StrategyEvaluationResult,
    StrategyEvaluator,
    compare_all_strategies,
    evaluate_node_with_strategy,
)

# Structural Memory strategy
from pxnodes.llm.context.structural_memory import (
    AtomicFact,
    IterativeRetriever,
    KnowledgeTriple,
    RetrievalResult,
    RetrievedMemory,
    StructuralMemoryContext,
    StructuralMemoryResult,
    StructuralMemoryStrategy,
    build_context,
    extract_atomic_facts,
    extract_llm_triples_only,
    get_context_stats,
)

__all__ = [
    # Base Framework
    "StrategyType",
    "BaseContextStrategy",
    "StrategyRegistry",
    "ContextResult",
    "LayerContext",
    "EvaluationScope",
    # Shared Utilities
    "OpenAIEmbeddingGenerator",
    "VectorStore",
    "init_database",
    "GraphSlice",
    "get_graph_slice",
    "LLMProviderAdapter",
    "create_llm_provider",
    # Structural Memory Strategy
    "StructuralMemoryStrategy",
    "StructuralMemoryContext",
    "StructuralMemoryResult",
    "build_context",
    "get_context_stats",
    "KnowledgeTriple",
    "extract_llm_triples_only",
    "AtomicFact",
    "extract_atomic_facts",
    "IterativeRetriever",
    "RetrievalResult",
    "RetrievedMemory",
    # Hierarchical Graph Strategy
    "HierarchicalGraphStrategy",
    # Full Context Strategy
    "FullContextStrategy",
    "PlayerState",
    "build_domain_layer",
    "build_category_layer",
    "build_trace_layer",
    "build_episode_layer",
    "reverse_bfs",
    "forward_bfs",
    "aggregate_player_state",
    # H-MEM Strategy
    "HMEMStrategy",
    "HMEMRetriever",
    "HMEMRetrievalResult",
    "HMEMContextResult",
    "compute_path_hash",
    # Combined Strategy
    "CombinedStrategy",
    # Strategy Evaluator
    "StrategyEvaluator",
    "StrategyEvaluationResult",
    "ComparisonResult",
    "evaluate_node_with_strategy",
    "compare_all_strategies",
    # Legacy - Generation
    "StructuralMemoryGenerator",
    "GenerationResult",
    "generate_structural_memory",
    # Legacy - Change Detection
    "compute_node_content_hash",
    "has_node_changed",
    "get_changed_nodes",
    "get_processing_stats",
    "update_processing_state",
]
