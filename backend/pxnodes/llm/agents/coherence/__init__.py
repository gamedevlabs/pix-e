"""
PxNodes Coherence Agents - Agentic evaluation of node coherence.

Provides 4 specialized agents that evaluate different coherence dimensions:
- PrerequisiteAlignmentAgent: Does node respect what came before?
- ForwardSetupAgent: Does node properly set up future?
- InternalConsistencyAgent: Is node internally coherent?
- ContextualFitAgent: Does node fit game concept/pillars?
"""

from pxnodes.llm.agents.coherence.base import CoherenceDimensionAgent
from pxnodes.llm.agents.coherence.contextual import ContextualFitAgent
from pxnodes.llm.agents.coherence.forward import ForwardSetupAgent
from pxnodes.llm.agents.coherence.internal import InternalConsistencyAgent
from pxnodes.llm.agents.coherence.prerequisite import PrerequisiteAlignmentAgent
from pxnodes.llm.agents.coherence.schemas import (
    CoherenceAggregatedResult,
    CoherenceDimensionResult,
)

__all__ = [
    # Base
    "CoherenceDimensionAgent",
    # Agents
    "PrerequisiteAlignmentAgent",
    "ForwardSetupAgent",
    "InternalConsistencyAgent",
    "ContextualFitAgent",
    # Schemas
    "CoherenceDimensionResult",
    "CoherenceAggregatedResult",
]
