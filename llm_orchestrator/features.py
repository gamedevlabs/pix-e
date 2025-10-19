"""
Feature and operation definitions for the LLM Orchestrator.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ============================================
# Feature IDs (Type-safe enums)
# ============================================


class FeatureID(str, Enum):
    """
    Registered features in pix:e.

    These are the main features that use LLM orchestration.
    """

    PILLARS = "pillars"
    SPARC = "sparc"
    MOODBOARDS = "moodboards"

    def __str__(self) -> str:
        return self.value


# ============================================
# Operation IDs per Feature (Type-safe enums)
# ============================================


class PillarsOperations(str, Enum):
    """Operations for the Pillars feature."""

    VALIDATE = "validate"
    IMPROVE = "improve"
    EVALUATE_CONSISTENCY = "evaluate_consistency"

    def __str__(self) -> str:
        return self.value


class SPARCOperations(str, Enum):
    """Operations for the SPARC feature."""

    EVALUATE_CONCEPT = "evaluate_concept"
    COMPARE_CONCEPTS = "compare_concepts"

    def __str__(self) -> str:
        return self.value


class MoodboardsOperations(str, Enum):
    """Operations for the Moodboards feature."""

    GENERATE_IMAGES = "generate_images"
    SUGGEST_VARIATIONS = "suggest_variations"
    ALIGN_WITH_PILLARS = "align_with_pillars"

    def __str__(self) -> str:
        return self.value


# ============================================
# Operation Metadata
# ============================================


@dataclass
class OperationMetadata:
    """
    Metadata for a registered operation.

    This stores information about an operation including its schemas,
    version, and description.
    """

    id: str
    feature_id: str
    description: str
    version: str = "1.0.0"
    request_schema_uri: Optional[str] = None
    response_schema_uri: Optional[str] = None

    @property
    def full_id(self) -> str:
        """Get full operation ID: feature.operation@version"""
        return f"{self.feature_id}.{self.id}@{self.version}"


# ============================================
# Operation Registry
# ============================================


class OperationRegistry:
    """
    Central registry for all operations.
    """

    # Registry of all operations: (feature_id, operation_id) -> OperationMetadata
    _operations: Dict[Tuple[str, str], OperationMetadata] = {
        # ============================================
        # Pillars Feature
        # ============================================
        (FeatureID.PILLARS, PillarsOperations.VALIDATE): OperationMetadata(
            id=PillarsOperations.VALIDATE,
            feature_id=FeatureID.PILLARS,
            description="Validate a game design pillar for structural issues",
            request_schema_uri="store://schemas/pillars.validate@1.0.0.req.json",
            response_schema_uri="store://schemas/pillars.validate@1.0.0.res.json",
        ),
        (FeatureID.PILLARS, PillarsOperations.IMPROVE): OperationMetadata(
            id=PillarsOperations.IMPROVE,
            feature_id=FeatureID.PILLARS,
            description="Generate improved version of a pillar",
            request_schema_uri="store://schemas/pillars.improve@1.0.0.req.json",
            response_schema_uri="store://schemas/pillars.improve@1.0.0.res.json",
        ),
        (
            FeatureID.PILLARS,
            PillarsOperations.EVALUATE_CONSISTENCY,
        ): OperationMetadata(
            id=PillarsOperations.EVALUATE_CONSISTENCY,
            feature_id=FeatureID.PILLARS,
            description=("Check multiple pillars for contradictions and alignment"),
            request_schema_uri=(
                "store://schemas/" "pillars.evaluate_consistency@1.0.0.req.json"
            ),
            response_schema_uri=(
                "store://schemas/" "pillars.evaluate_consistency@1.0.0.res.json"
            ),
        ),
        # ============================================
        # SPARC Feature
        # ============================================
        (
            FeatureID.SPARC,
            SPARCOperations.EVALUATE_CONCEPT,
        ): OperationMetadata(
            id=SPARCOperations.EVALUATE_CONCEPT,
            feature_id=FeatureID.SPARC,
            description=("Evaluate a game concept against SPARC framework aspects"),
            request_schema_uri=(
                "store://schemas/sparc.evaluate_concept@1.0.0.req.json"
            ),
            response_schema_uri=(
                "store://schemas/sparc.evaluate_concept@1.0.0.res.json"
            ),
        ),
        (FeatureID.SPARC, SPARCOperations.COMPARE_CONCEPTS): OperationMetadata(
            id=SPARCOperations.COMPARE_CONCEPTS,
            feature_id=FeatureID.SPARC,
            description="Compare multiple game concepts",
            request_schema_uri="store://schemas/sparc.compare_concepts@1.0.0.req.json",
            response_schema_uri="store://schemas/sparc.compare_concepts@1.0.0.res.json",
        ),
        # ============================================
        # Moodboards Feature
        # ============================================
        (
            FeatureID.MOODBOARDS,
            MoodboardsOperations.GENERATE_IMAGES,
        ): OperationMetadata(
            id=MoodboardsOperations.GENERATE_IMAGES,
            feature_id=FeatureID.MOODBOARDS,
            description="Generate images from a text prompt",
            request_schema_uri=(
                "store://schemas/" "moodboards.generate_images@1.0.0.req.json"
            ),
            response_schema_uri=(
                "store://schemas/" "moodboards.generate_images@1.0.0.res.json"
            ),
        ),
        (
            FeatureID.MOODBOARDS,
            MoodboardsOperations.SUGGEST_VARIATIONS,
        ): OperationMetadata(
            id=MoodboardsOperations.SUGGEST_VARIATIONS,
            feature_id=FeatureID.MOODBOARDS,
            description="Suggest prompt variations for exploration",
            request_schema_uri=(
                "store://schemas/" "moodboards.suggest_variations@1.0.0.req.json"
            ),
            response_schema_uri=(
                "store://schemas/" "moodboards.suggest_variations@1.0.0.res.json"
            ),
        ),
        (
            FeatureID.MOODBOARDS,
            MoodboardsOperations.ALIGN_WITH_PILLARS,
        ): OperationMetadata(
            id=MoodboardsOperations.ALIGN_WITH_PILLARS,
            feature_id=FeatureID.MOODBOARDS,
            description=(
                "Evaluate how well generated images align with " "design pillars"
            ),
            request_schema_uri=(
                "store://schemas/" "moodboards.align_with_pillars@1.0.0.req.json"
            ),
            response_schema_uri=(
                "store://schemas/" "moodboards.align_with_pillars@1.0.0.res.json"
            ),
        ),
    }

    @classmethod
    def get(cls, feature: str, operation: str) -> OperationMetadata:
        """
        Get operation metadata.
        """
        # Import here to avoid circular dependency
        from llm_orchestrator.exceptions import (
            UnknownFeatureError,
            UnknownOperationError,
        )

        # Check if feature exists
        feature_operations = [k for k in cls._operations.keys() if k[0] == feature]
        if not feature_operations:
            available_features = list(set(k[0] for k in cls._operations.keys()))
            raise UnknownFeatureError(feature, available_features)

        # Check if operation exists
        key = (feature, operation)
        if key not in cls._operations:
            available_ops = [k[1] for k in feature_operations]
            raise UnknownOperationError(feature, operation, available_ops)

        return cls._operations[key]

    @classmethod
    def list_operations(cls, feature: Optional[str] = None) -> List[OperationMetadata]:
        """
        List all operations, optionally filtered by feature.
        """
        if feature:
            return [op for (f, _), op in cls._operations.items() if f == feature]
        return list(cls._operations.values())

    @classmethod
    def list_features(cls) -> List[str]:
        """
        List all registered features.
        """
        return list(set(k[0] for k in cls._operations.keys()))

    @classmethod
    def has_operation(cls, feature: str, operation: str) -> bool:
        """
        Check if an operation exists.
        """
        return (feature, operation) in cls._operations

    @classmethod
    def register_operation(
        cls,
        feature: str,
        operation: str,
        description: str,
        version: str = "1.0.0",
        request_schema_uri: Optional[str] = None,
        response_schema_uri: Optional[str] = None,
    ) -> None:
        """
        Register a new operation (for dynamic feature addition).

        Args:
            feature: Feature ID
            operation: Operation ID
            description: Operation description
            version: Schema version
            request_schema_uri: Request schema URI
            response_schema_uri: Response schema URI
        """
        metadata = OperationMetadata(
            id=operation,
            feature_id=feature,
            description=description,
            version=version,
            request_schema_uri=request_schema_uri,
            response_schema_uri=response_schema_uri,
        )
        cls._operations[(feature, operation)] = metadata


# ============================================
# Convenience Functions
# ============================================


def get_operation(feature: str, operation: str) -> OperationMetadata:
    """
    Convenience function to get operation metadata.
    """
    return OperationRegistry.get(str(feature), str(operation))


def list_features() -> List[str]:
    """Get list of all registered features."""
    return OperationRegistry.list_features()


def list_operations(feature: Optional[str] = None) -> List[OperationMetadata]:
    """
    List operations, optionally filtered by feature.

    Args:
        feature: Optional feature ID to filter by

    Returns:
        List of operation metadata
    """
    return OperationRegistry.list_operations(str(feature) if feature else None)
