"""
Handler Registry

Central registry for all operation handlers.
Allows discovery and retrieval of handlers by operation ID.
"""

from typing import Dict, List, Optional, Type

from llm_orchestrator.core.operation_handler import BaseOperationHandler
from llm_orchestrator.exceptions import UnknownOperationError


class HandlerRegistry:
    """
    Registry for operation handlers.

    Manages handler registration and discovery.
    """

    def __init__(self):
        self._handlers: Dict[str, Type[BaseOperationHandler]] = {}

    def register(
        self, operation_id: str, handler_class: Type[BaseOperationHandler]
    ) -> None:
        """
        Register a handler for an operation.
        """
        if operation_id in self._handlers:
            raise ValueError(f"Handler for '{operation_id}' already registered")

        self._handlers[operation_id] = handler_class

    def get(self, operation_id: str) -> Type[BaseOperationHandler]:
        """
        Get handler class for an operation.
        """
        if operation_id not in self._handlers:
            feature = operation_id.split(".")[0] if "." in operation_id else ""
            operation = (
                operation_id.split(".")[1] if "." in operation_id else operation_id
            )
            raise UnknownOperationError(feature=feature, operation=operation)

        return self._handlers[operation_id]

    def list_operations(self, feature: Optional[str] = None) -> List[str]:
        """
        List all registered operations.
        """
        if feature:
            return [
                op_id
                for op_id in self._handlers.keys()
                if op_id.startswith(f"{feature}.")
            ]
        return list(self._handlers.keys())

    def has_operation(self, operation_id: str) -> bool:
        """Check if operation is registered."""
        return operation_id in self._handlers


# Global registry instance
_registry = HandlerRegistry()


def register_handler(
    operation_id: str, handler_class: Type[BaseOperationHandler]
) -> None:
    """Register a handler in the global registry."""
    _registry.register(operation_id, handler_class)


def get_handler(operation_id: str) -> Type[BaseOperationHandler]:
    """Get handler from global registry."""
    return _registry.get(operation_id)


def list_operations(feature: Optional[str] = None) -> List[str]:
    """List operations from global registry."""
    return _registry.list_operations(feature)


def get_registry() -> HandlerRegistry:
    """Get the global registry instance."""
    return _registry
