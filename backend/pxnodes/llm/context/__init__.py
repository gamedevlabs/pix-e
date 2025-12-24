"""
Context Engineering Strategies Module.

Lazy re-exports are used to avoid heavy import-time dependencies.
"""

from __future__ import annotations

import importlib
from typing import Any

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
    "SimpleStructuralMemoryStrategy",
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

_EXPORTS: dict[str, tuple[str, str]] = {
    # Base Framework
    "StrategyType": ("pxnodes.llm.context.base.types", "StrategyType"),
    "BaseContextStrategy": ("pxnodes.llm.context.base.strategy", "BaseContextStrategy"),
    "StrategyRegistry": ("pxnodes.llm.context.base.registry", "StrategyRegistry"),
    "ContextResult": ("pxnodes.llm.context.base.types", "ContextResult"),
    "LayerContext": ("pxnodes.llm.context.base.types", "LayerContext"),
    "EvaluationScope": ("pxnodes.llm.context.base.types", "EvaluationScope"),
    # Shared Utilities
    "OpenAIEmbeddingGenerator": (
        "pxnodes.llm.context.shared.embeddings",
        "OpenAIEmbeddingGenerator",
    ),
    "VectorStore": ("pxnodes.llm.context.shared.vector_store", "VectorStore"),
    "init_database": ("pxnodes.llm.context.shared.vector_store", "init_database"),
    "GraphSlice": ("pxnodes.llm.context.shared.graph_retrieval", "GraphSlice"),
    "get_graph_slice": (
        "pxnodes.llm.context.shared.graph_retrieval",
        "get_graph_slice",
    ),
    "LLMProviderAdapter": ("pxnodes.llm.context.shared.llm_adapter", "LLMProviderAdapter"),
    "create_llm_provider": ("pxnodes.llm.context.shared.llm_adapter", "create_llm_provider"),
    # Structural Memory Strategy
    "StructuralMemoryStrategy": (
        "pxnodes.llm.context.structural_memory.strategy",
        "StructuralMemoryStrategy",
    ),
    "SimpleStructuralMemoryStrategy": (
        "pxnodes.llm.context.structural_memory.strategy",
        "SimpleStructuralMemoryStrategy",
    ),
    "StructuralMemoryContext": (
        "pxnodes.llm.context.structural_memory.context",
        "StructuralMemoryContext",
    ),
    "StructuralMemoryResult": (
        "pxnodes.llm.context.structural_memory.context",
        "StructuralMemoryResult",
    ),
    "build_context": ("pxnodes.llm.context.structural_memory.context", "build_context"),
    "get_context_stats": (
        "pxnodes.llm.context.structural_memory.context",
        "get_context_stats",
    ),
    "KnowledgeTriple": ("pxnodes.llm.context.structural_memory.triples", "KnowledgeTriple"),
    "extract_llm_triples_only": (
        "pxnodes.llm.context.structural_memory.triples",
        "extract_llm_triples_only",
    ),
    "AtomicFact": ("pxnodes.llm.context.structural_memory.facts", "AtomicFact"),
    "extract_atomic_facts": (
        "pxnodes.llm.context.structural_memory.facts",
        "extract_atomic_facts",
    ),
    "IterativeRetriever": (
        "pxnodes.llm.context.structural_memory.retriever",
        "IterativeRetriever",
    ),
    "RetrievalResult": (
        "pxnodes.llm.context.structural_memory.retriever",
        "RetrievalResult",
    ),
    "RetrievedMemory": (
        "pxnodes.llm.context.structural_memory.retriever",
        "RetrievedMemory",
    ),
    # Hierarchical Graph Strategy
    "HierarchicalGraphStrategy": (
        "pxnodes.llm.context.hierarchical_graph.strategy",
        "HierarchicalGraphStrategy",
    ),
    "PlayerState": ("pxnodes.llm.context.hierarchical_graph.layers", "PlayerState"),
    "build_domain_layer": (
        "pxnodes.llm.context.hierarchical_graph.layers",
        "build_domain_layer",
    ),
    "build_category_layer": (
        "pxnodes.llm.context.hierarchical_graph.layers",
        "build_category_layer",
    ),
    "build_trace_layer": (
        "pxnodes.llm.context.hierarchical_graph.layers",
        "build_trace_layer",
    ),
    "build_episode_layer": (
        "pxnodes.llm.context.hierarchical_graph.layers",
        "build_episode_layer",
    ),
    "reverse_bfs": ("pxnodes.llm.context.hierarchical_graph.traversal", "reverse_bfs"),
    "forward_bfs": ("pxnodes.llm.context.hierarchical_graph.traversal", "forward_bfs"),
    "aggregate_player_state": (
        "pxnodes.llm.context.hierarchical_graph.traversal",
        "aggregate_player_state",
    ),
    # Full Context Strategy
    "FullContextStrategy": ("pxnodes.llm.context.full_context.strategy", "FullContextStrategy"),
    # H-MEM Strategy
    "HMEMStrategy": ("pxnodes.llm.context.hmem.strategy", "HMEMStrategy"),
    "HMEMRetriever": ("pxnodes.llm.context.hmem.retriever", "HMEMRetriever"),
    "HMEMRetrievalResult": ("pxnodes.llm.context.hmem.retriever", "HMEMRetrievalResult"),
    "HMEMContextResult": ("pxnodes.llm.context.hmem.retriever", "HMEMContextResult"),
    "compute_path_hash": ("pxnodes.llm.context.hmem.retriever", "compute_path_hash"),
    # Combined Strategy
    "CombinedStrategy": ("pxnodes.llm.context.combined.strategy", "CombinedStrategy"),
    # Strategy Evaluator
    "StrategyEvaluator": ("pxnodes.llm.context.strategy_evaluator", "StrategyEvaluator"),
    "StrategyEvaluationResult": (
        "pxnodes.llm.context.strategy_evaluator",
        "StrategyEvaluationResult",
    ),
    "ComparisonResult": ("pxnodes.llm.context.strategy_evaluator", "ComparisonResult"),
    "evaluate_node_with_strategy": (
        "pxnodes.llm.context.strategy_evaluator",
        "evaluate_node_with_strategy",
    ),
    "compare_all_strategies": (
        "pxnodes.llm.context.strategy_evaluator",
        "compare_all_strategies",
    ),
    # Legacy - Generation
    "StructuralMemoryGenerator": ("pxnodes.llm.context.generator", "StructuralMemoryGenerator"),
    "GenerationResult": ("pxnodes.llm.context.generator", "GenerationResult"),
    "generate_structural_memory": ("pxnodes.llm.context.generator", "generate_structural_memory"),
    # Legacy - Change Detection
    "compute_node_content_hash": (
        "pxnodes.llm.context.change_detection",
        "compute_node_content_hash",
    ),
    "has_node_changed": ("pxnodes.llm.context.change_detection", "has_node_changed"),
    "get_changed_nodes": ("pxnodes.llm.context.change_detection", "get_changed_nodes"),
    "get_processing_stats": ("pxnodes.llm.context.change_detection", "get_processing_stats"),
    "update_processing_state": ("pxnodes.llm.context.change_detection", "update_processing_state"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def __dir__() -> list[str]:
    return sorted(list(__all__))
