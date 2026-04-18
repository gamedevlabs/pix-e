"""
SPARC V2 response schemas.

Simplified schemas for router-based agentic evaluation.
"""

from sparc.llm.schemas.v2.aspects import SimplifiedAspectResponse
from sparc.llm.schemas.v2.router import AspectExtraction, RouterResponse
from sparc.llm.schemas.v2.synthesis import SPARCSynthesis, SPARCV2Response

__all__ = [
    # Router schemas
    "AspectExtraction",
    "RouterResponse",
    # Aspect schemas
    "SimplifiedAspectResponse",
    # Synthesis schemas
    "SPARCSynthesis",
    "SPARCV2Response",
]
