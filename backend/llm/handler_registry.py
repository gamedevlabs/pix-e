"""
Handler Registry

Central registry for all operation handlers.
Allows discovery, metadata access, and retrieval of handlers by operation ID.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from llm.exceptions import UnknownOperationError
from llm.operation_handler import BaseOperationHandler


@dataclass
class OperationMetadata:
    """Metadata about a registered operation."""

    operation_id: str
    feature_id: str
    operation_name: str
    description: str
    version: str
    handler_class: Type[BaseOperationHandler]

    @property
    def full_id(self) -> str:
        """Return full operation identifier: feature.operation@version"""
        return f"{self.operation_id}@{self.version}"


class HandlerRegistry:
    """
    Registry for operation handlers.

    Manages handler registration and discovery.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Type[BaseOperationHandler]] = {}

    def register(
        self, operation_id: str, handler_class: Type[BaseOperationHandler]
    ) -> None:
        """Register a handler for an operation."""
        # Allow idempotent registration to ease reloads during development
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

    def get_metadata(self, operation_id: str) -> OperationMetadata:
        """Return metadata for a registered operation."""
        handler_class = self.get(operation_id)
        parts = operation_id.split(".")
        feature_id = parts[0] if len(parts) > 1 else ""
        operation_name = parts[1] if len(parts) > 1 else operation_id
        description = getattr(handler_class, "description", "")
        version = getattr(handler_class, "version", "1.0.0")

        return OperationMetadata(
            operation_id=operation_id,
            feature_id=feature_id,
            operation_name=operation_name,
            description=description,
            version=version,
            handler_class=handler_class,
        )

    def list_operations(self, feature: Optional[str] = None) -> List[str]:
        """List all registered operation IDs (optionally filtered by feature)."""
        if feature:
            return [
                op_id
                for op_id in self._handlers.keys()
                if op_id.startswith(f"{feature}.")
            ]
        return list(self._handlers.keys())

    def list_metadata(self, feature: Optional[str] = None) -> List[OperationMetadata]:
        """List metadata for registered operations (optionally filtered)."""
        return [self.get_metadata(op) for op in self.list_operations(feature)]

    def list_features(self) -> List[str]:
        """List registered feature IDs."""
        features = set()
        for op_id in self._handlers.keys():
            if "." in op_id:
                features.add(op_id.split(".")[0])
        return sorted(features)

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


def get_metadata(operation_id: str) -> OperationMetadata:
    """Get operation metadata from the global registry."""
    return _registry.get_metadata(operation_id)


def list_operations(feature: Optional[str] = None) -> List[str]:
    """List operations from global registry."""
    return _registry.list_operations(feature)


def list_metadata(feature: Optional[str] = None) -> List[OperationMetadata]:
    """List operation metadata from global registry."""
    return _registry.list_metadata(feature)


def list_features() -> List[str]:
    """List features from global registry."""
    return _registry.list_features()


def get_registry() -> HandlerRegistry:
    """Get the global registry instance."""
    return _registry
