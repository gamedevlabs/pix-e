"""
Event utilities for agentic execution tracking.
Provides helpers for generating events, timestamps, and managing event timelines.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from llm.types import (
    AgentOutputEvent,
    AgentStartedEvent,
    ArtifactCreatedEvent,
    ArtifactInfo,
    ErrorEvent,
    ErrorInfo,
    ModelInfo,
    ModelRoutedEvent,
    RunCompletedEvent,
    RunStartedEvent,
    StreamEvent,
    WarningEvent,
    WarningInfo,
)


def generate_run_id() -> str:
    """
    Generate a unique run identifier.
    Returns:
        UUID string in the format: "run_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    """
    return f"run_{uuid.uuid4()}"


def generate_timestamp() -> str:
    """
    Generate an ISO 8601 timestamp in UTC.
    Returns:
        Timestamp string (e.g., "2025-01-15T10:30:45.123456Z")
    """
    return datetime.now(timezone.utc).isoformat()


class EventCollector:
    """
    Collects events during agentic execution.
    Provides helper methods to create and track events in chronological order.
    """

    def __init__(self, run_id: Optional[str] = None):
        """
        Initialize event collector.
        Args:
            run_id: Optional run identifier. If not provided, one will be generated.
        """
        self.run_id = run_id or generate_run_id()
        self.events: List[StreamEvent] = []

    def add_run_started(self, received_at: Optional[str] = None) -> RunStartedEvent:
        """Add a RunStartedEvent."""
        event = RunStartedEvent(
            run_id=self.run_id,
            timestamp=generate_timestamp(),
            received_at=received_at or generate_timestamp(),
        )
        self.events.append(event)
        return event

    def add_model_routed(
        self, to: ModelInfo, reason: str, from_: Optional[str] = None
    ) -> ModelRoutedEvent:
        """Add a ModelRoutedEvent."""
        event_data: dict = {
            "run_id": self.run_id,
            "timestamp": generate_timestamp(),
            "to": to,
            "reason": reason,
        }
        if from_ is not None:
            event_data["from"] = from_

        event = ModelRoutedEvent.model_validate(event_data)
        self.events.append(event)
        return event

    def add_agent_started(self, agent_name: str) -> AgentStartedEvent:
        """Add an AgentStartedEvent."""
        event = AgentStartedEvent(
            run_id=self.run_id, timestamp=generate_timestamp(), name=agent_name
        )
        self.events.append(event)
        return event

    def add_agent_output(
        self, agent_name: str, chunk: Optional[str] = None
    ) -> AgentOutputEvent:
        """Add an AgentOutputEvent."""
        event = AgentOutputEvent(
            run_id=self.run_id,
            timestamp=generate_timestamp(),
            name=agent_name,
            chunk=chunk,
        )
        self.events.append(event)
        return event

    def add_agent_finished(self, agent_name: str) -> AgentOutputEvent:
        """
        Add an event marking agent completion.
        Note: Uses AgentOutputEvent with chunk=None to indicate completion.
        A dedicated AgentFinishedEvent type may be added in the future.
        """
        event = AgentOutputEvent(
            run_id=self.run_id,
            timestamp=generate_timestamp(),
            name=agent_name,
            chunk=None,  # No chunk means finished
        )
        self.events.append(event)
        return event

    def add_artifact_created(self, artifact: ArtifactInfo) -> ArtifactCreatedEvent:
        """Add an ArtifactCreatedEvent."""
        event = ArtifactCreatedEvent(
            run_id=self.run_id, timestamp=generate_timestamp(), artifact=artifact
        )
        self.events.append(event)
        return event

    def add_run_completed(self, success: bool) -> RunCompletedEvent:
        """Add a RunCompletedEvent."""
        event = RunCompletedEvent(
            run_id=self.run_id, timestamp=generate_timestamp(), success=success
        )
        self.events.append(event)
        return event

    def add_error(self, error: ErrorInfo) -> ErrorEvent:
        """Add an ErrorEvent."""
        event = ErrorEvent(
            run_id=self.run_id, timestamp=generate_timestamp(), error=error
        )
        self.events.append(event)
        return event

    def add_warning(self, warning: WarningInfo) -> WarningEvent:
        """Add a WarningEvent."""
        event = WarningEvent(
            run_id=self.run_id, timestamp=generate_timestamp(), warning=warning
        )
        self.events.append(event)
        return event

    def get_events(self) -> List[StreamEvent]:
        """
        Get all collected events.
        Returns:
            List of events in chronological order
        """
        return self.events.copy()

    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()
