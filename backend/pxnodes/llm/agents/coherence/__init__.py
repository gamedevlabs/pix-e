"""
PxNodes Coherence Agents - Agentic evaluation of node coherence.

Provides 4 specialized agents that evaluate different coherence dimensions:
- BackwardCoherenceAgent: Does node respect what came before?
- ForwardCoherenceAgent: Does node properly set up future?
- PathRobustnessAgent: Does node work across paths?
- NodeIntegrityAgent: Is node internally coherent?
"""

from pxnodes.llm.agents.coherence.base import CoherenceDimensionAgent
from pxnodes.llm.agents.coherence.contextual import PathRobustnessAgent
from pxnodes.llm.agents.coherence.forward import ForwardCoherenceAgent
from pxnodes.llm.agents.coherence.internal import NodeIntegrityAgent
from pxnodes.llm.agents.coherence.prerequisite import BackwardCoherenceAgent
from pxnodes.llm.agents.coherence.schemas import (
    CoherenceAggregatedResult,
    CoherenceDimensionResult,
)

__all__ = [
    # Base
    "CoherenceDimensionAgent",
    # Agents
    "BackwardCoherenceAgent",
    "ForwardCoherenceAgent",
    "NodeIntegrityAgent",
    "PathRobustnessAgent",
    # Schemas
    "CoherenceDimensionResult",
    "CoherenceAggregatedResult",
]
