    # ============================================================
# models.py
# Pure dataclasses – no logic, just typed containers used
# throughout the pipeline.
# ============================================================

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class InboundMessage:
    """Parsed representation of the raw JSON input."""
    message_id: str
    source: str          # email | slack | meeting
    sender_name: str
    sender_role: str
    content: str
    project: Optional[str]


@dataclass
class L1Task:
    """
    A single task planned by the L1 Orchestrator.
    target_type : "L2" | "L3_CROSS"
    target      : domain name (TRACKING_EXECUTION) or agent name (knowledge_retrieval)
    """
    task_id: str
    target_type: str          # "L2" | "L3_CROSS"
    target: str
    purpose: str
    depends_on: List[str] = field(default_factory=list)


@dataclass
class L3Result:
    """Output produced by a single L3 agent execution."""
    task_id: str          # e.g. TASK-001-A
    agent_name: str
    status: str           # COMPLETED | FAILED | SKIPPED
    output_lines: List[str] = field(default_factory=list)


@dataclass
class L2Result:
    """
    Output of one L2 domain execution.
    Contains an ordered list of L3 results it coordinated.
    """
    task_id: str
    domain: str
    l3_results: List[L3Result] = field(default_factory=list)


@dataclass
class CrossCuttingResult:
    """Output of a cross-cutting agent called directly from L1."""
    task_id: str
    agent_name: str
    status: str
    output_lines: List[str] = field(default_factory=list)


@dataclass
class OrchestrationResult:
    """Top-level container returned after full pipeline execution."""
    message: InboundMessage
    l1_plan: List[L1Task]
    executions: List          # List[L2Result | CrossCuttingResult]