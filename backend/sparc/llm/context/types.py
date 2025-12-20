"""
Types for SPARC context strategies.

Defines the core structures for building aspect-specific context
using interchangeable strategy implementations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class ContextStrategyType(Enum):
    """Available SPARC context strategies."""

    ROUTER = "router"
    FULL_TEXT = "full_text"
    STRUCTURAL_MEMORY = "structural_memory"
    HMEM = "hmem"
    COMBINED = "combined"


@dataclass
class AspectContext:
    """Context payload for a single SPARC aspect."""

    aspect_name: str
    extracted_sections: List[str] = field(default_factory=list)
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class AspectContextResult:
    """Context result for multiple SPARC aspects."""

    strategy: ContextStrategyType
    contexts: Dict[str, AspectContext] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)

    def get_sections(self, aspect_name: str) -> List[str]:
        """Return extracted sections for a given aspect."""
        context = self.contexts.get(aspect_name)
        if not context:
            return []
        return context.extracted_sections
