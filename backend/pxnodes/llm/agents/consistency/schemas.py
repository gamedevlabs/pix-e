"""Pydantic schemas for consistency findings and reports."""

from enum import Enum
from typing import List

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


class ConsistencyReport(BaseModel):
    """Aggregated report of all consistency findings for a check run."""

    findings: List[ConsistencyFinding]
