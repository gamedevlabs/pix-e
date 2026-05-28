"""Pydantic schemas for consistency findings and reports."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class FindingSeverity(str, Enum):
    """Severity levels for a consistency finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ConsistencyFinding(BaseModel):
    """A single consistency issue detected by structural or semantic checks."""

    severity: FindingSeverity
    category: str
    entity_id: str
    message: str


class ConsistencyMeta(BaseModel):
    """Diagnostic metadata about what the check actually ran on."""

    nodes_checked: int
    pillars_checked: int
    agents_run: List[str]
    agents_skipped: Dict[str, str]


class ConsistencyReport(BaseModel):
    """Aggregated report of all consistency findings for a check run."""

    findings: List[ConsistencyFinding]
    meta: Optional[ConsistencyMeta] = None
