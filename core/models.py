"""
core/models.py
--------------
Data models for the Nion Orchestration Engine.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskType(str, Enum):
    L2_DOMAIN = "l2"
    CROSS_CUTTING = "cross_cutting"


@dataclass
class Sender:
    name: str
    role: str


@dataclass
class InputMessage:
    message_id: str
    source: str
    sender: Sender
    content: str
    project: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputMessage":
        sender_data = data.get("sender", {})
        return cls(
            message_id=data.get("message_id", "MSG-UNKNOWN"),
            source=data.get("source", "unknown"),
            sender=Sender(
                name=sender_data.get("name", "Unknown"),
                role=sender_data.get("role", "Unknown"),
            ),
            content=data.get("content", ""),
            project=data.get("project"),
        )


@dataclass
class PlannedTask:
    task_id: str
    target: str          # e.g. "L2:TRACKING_EXECUTION" or "L3:knowledge_retrieval"
    task_type: TaskType
    purpose: str
    depends_on: List[str] = field(default_factory=list)

    @property
    def is_cross_cutting(self) -> bool:
        return self.task_type == TaskType.CROSS_CUTTING

    @property
    def domain(self) -> str:
        """Return domain/agent name from target string."""
        return self.target.split(":", 1)[-1] if ":" in self.target else self.target


@dataclass
class L3ExecutionResult:
    sub_task_id: str       # e.g. "TASK-001-A"
    agent_name: str        # e.g. "action_item_extraction"
    status: TaskStatus
    output_lines: List[str] = field(default_factory=list)


@dataclass
class ExecutedTask:
    task_id: str
    target: str
    task_type: TaskType
    status: TaskStatus
    l3_results: List[L3ExecutionResult] = field(default_factory=list)
    output_lines: List[str] = field(default_factory=list)   # for cross-cutting tasks


@dataclass
class OrchestrationResult:
    message: InputMessage
    planned_tasks: List[PlannedTask]
    executed_tasks: List[ExecutedTask]
