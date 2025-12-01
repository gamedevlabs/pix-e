"""
Agent Graph Registry

Central registry for all agent graphs.
Allows discovery and retrieval of agent graphs by operation ID.

This mirrors the handler_registry.py pattern but for agentic execution mode.
"""

from typing import Dict, List, Optional, Type

from llm.exceptions import UnknownOperationError


class AgentRegistry:
    """
    Registry for agent graphs.

    Manages graph registration and discovery for agentic execution mode.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._graphs: Dict[str, Type] = {}

    def register(self, operation_id: str, graph_class: Type) -> None:
        """
        Register an agent graph for an operation.

        Args:
            operation_id: Operation identifier (e.g., "pillars.evaluate_all")
            graph_class: Agent graph class (not instance)
        """
        self._graphs[operation_id] = graph_class

    def get(self, operation_id: str) -> Type:
        """
        Get agent graph class for an operation.

        Args:
            operation_id: Operation identifier (e.g., "pillars.evaluate_all")
        """
        if operation_id not in self._graphs:
            feature = operation_id.split(".")[0] if "." in operation_id else ""
            operation = (
                operation_id.split(".")[1] if "." in operation_id else operation_id
            )
            raise UnknownOperationError(feature=feature, operation=operation)

        return self._graphs[operation_id]

    def list_graphs(self, feature: Optional[str] = None) -> List[str]:
        """
        List all registered operation IDs.

        Args:
            feature: Optional feature filter (e.g., "pillars")
        """
        if feature:
            return [
                op_id
                for op_id in self._graphs.keys()
                if op_id.startswith(f"{feature}.")
            ]
        return list(self._graphs.keys())

    def list_features(self) -> List[str]:
        """
        List all registered feature IDs.
        """
        features = set()
        for op_id in self._graphs.keys():
            if "." in op_id:
                features.add(op_id.split(".")[0])
        return sorted(features)

    def has_graph(self, operation_id: str) -> bool:
        """
        Check if operation has a registered graph.

        Args:
            operation_id: Operation identifier
        """
        return operation_id in self._graphs

    def clear(self) -> None:
        """
        Clear all registered graphs.

        Useful for testing.
        """
        self._graphs.clear()


# Global registry instance
_registry = AgentRegistry()


def register_graph(operation_id: str, graph_class: Type) -> None:
    """
    Register an agent graph in the global registry.

    Args:
        operation_id: Operation identifier (e.g., "pillars.evaluate_all")
        graph_class: Agent graph class
    """
    _registry.register(operation_id, graph_class)


def get_graph(operation_id: str) -> Type:
    """
    Get agent graph class from global registry.

    Args:
        operation_id: Operation identifier
    """
    return _registry.get(operation_id)


def list_graphs(feature: Optional[str] = None) -> List[str]:
    """
    List operation IDs from global registry.

    Args:
        feature: Optional feature filter
    """
    return _registry.list_graphs(feature)


def list_features() -> List[str]:
    """
    List features from global registry.
    """
    return _registry.list_features()


def has_graph(operation_id: str) -> bool:
    """
    Check if operation has a registered graph.

    Args:
        operation_id: Operation identifier
    """
    return _registry.has_graph(operation_id)


def get_registry() -> AgentRegistry:
    """
    Get the global registry instance.
    """
    return _registry
