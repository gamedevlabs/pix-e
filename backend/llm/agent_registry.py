"""
Agent Workflow Registry

Central registry for all agent workflows.
Allows discovery and retrieval of agent workflows by operation ID.

This mirrors the handler_registry.py pattern but for agentic execution mode.
"""

from typing import Dict, List, Optional, Type

from llm.exceptions import UnknownOperationError


class AgentRegistry:
    """
    Registry for agent workflows.

    Manages workflow registration and discovery for agentic execution mode.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._workflows: Dict[str, Type] = {}

    def register(self, operation_id: str, workflow_class: Type) -> None:
        """
        Register an agent workflow for an operation.

        Args:
            operation_id: Operation identifier (e.g., "pillars.evaluate_all")
            workflow_class: Agent workflow class (not instance)
        """
        self._workflows[operation_id] = workflow_class

    def get(self, operation_id: str) -> Type:
        """
        Get agent workflow class for an operation.

        Args:
            operation_id: Operation identifier (e.g., "pillars.evaluate_all")
        """
        if operation_id not in self._workflows:
            feature = operation_id.split(".")[0] if "." in operation_id else ""
            operation = (
                operation_id.split(".")[1] if "." in operation_id else operation_id
            )
            raise UnknownOperationError(feature=feature, operation=operation)

        return self._workflows[operation_id]

    def list_workflows(self, feature: Optional[str] = None) -> List[str]:
        """
        List all registered operation IDs.

        Args:
            feature: Optional feature filter (e.g., "pillars")
        """
        if feature:
            return [
                op_id
                for op_id in self._workflows.keys()
                if op_id.startswith(f"{feature}.")
            ]
        return list(self._workflows.keys())

    def list_features(self) -> List[str]:
        """
        List all registered feature IDs.
        """
        features = set()
        for op_id in self._workflows.keys():
            if "." in op_id:
                features.add(op_id.split(".")[0])
        return sorted(features)

    def has_workflow(self, operation_id: str) -> bool:
        """
        Check if operation has a registered workflow.

        Args:
            operation_id: Operation identifier
        """
        return operation_id in self._workflows

    def clear(self) -> None:
        """
        Clear all registered workflows.

        Useful for testing.
        """
        self._workflows.clear()


# Global registry instance
_registry = AgentRegistry()


def register_workflow(operation_id: str, workflow_class: Type) -> None:
    """
    Register an agent workflow in the global registry.

    Args:
        operation_id: Operation identifier (e.g., "pillars.evaluate_all")
        workflow_class: Agent workflow class
    """
    _registry.register(operation_id, workflow_class)


def get_workflow(operation_id: str) -> Type:
    """
    Get agent workflow class from global registry.

    Args:
        operation_id: Operation identifier
    """
    return _registry.get(operation_id)


def list_workflows(feature: Optional[str] = None) -> List[str]:
    """
    List operation IDs from global registry.

    Args:
        feature: Optional feature filter
    """
    return _registry.list_workflows(feature)


def list_features() -> List[str]:
    """
    List features from global registry.
    """
    return _registry.list_features()


def has_workflow(operation_id: str) -> bool:
    """
    Check if operation has a registered workflow.

    Args:
        operation_id: Operation identifier
    """
    return _registry.has_workflow(operation_id)


def get_registry() -> AgentRegistry:
    """
    Get the global registry instance.
    """
    return _registry
