"""Pydantic schemas for change propagation findings and reports."""

from typing import List

from pydantic import BaseModel, Field


class PropagationFinding(BaseModel):
    """A single node identified as semantically affected by a change."""

    affected_node_id: str
    affected_node_name: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_action: str


class PropagationReport(BaseModel):
    """Aggregated report of all nodes affected by a change to a single node."""

    changed_node_id: str
    findings: List[PropagationFinding]
