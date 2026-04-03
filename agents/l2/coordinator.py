"""
agents/l2/coordinator.py
------------------------
L2 Coordinator: receives delegated task from L1,
selects appropriate L3 agents, coordinates execution,
and aggregates results.

Visibility: Own L3 agents + Cross-Cutting agents ONLY.
Each L2 domain can only use its own L3 agents.
"""

from typing import List, Dict, Any, Optional

from core.models import (
    PlannedTask, ExecutedTask, L3ExecutionResult,
    TaskStatus, TaskType, InputMessage
)
from agents.l3.agents import (
    run_l3_agent,
    TRACKING_EXECUTION_AGENTS,
    COMMUNICATION_COLLABORATION_AGENTS,
    LEARNING_IMPROVEMENT_AGENTS,
    CROSS_CUTTING_AGENTS,
    DOMAIN_AGENTS,
)

# ─────────────────────────────────────────────────────────────
# Domain → primary agent selection logic
# ─────────────────────────────────────────────────────────────

def _select_l3_agents_for_task(domain: str, purpose: str, context: Dict) -> List[str]:
    """
    Given a domain and task purpose, select the most appropriate L3 agent(s).
    Each L2 coordinator can only choose from its own L3 agents.
    """
    p = purpose.lower()
    content = context.get("content", "").lower()

    if domain == "TRACKING_EXECUTION":
        agents = []

        # Action items
        if any(kw in p for kw in ["action item", "task", "to-do", "todo"]):
            agents.append("action_item_extraction")

        # Risks
        if any(kw in p for kw in ["risk", "threat", "danger", "blocker"]):
            agents.append("risk_extraction")

        # Issues
        if any(kw in p for kw in ["issue", "problem", "bug", "blocker", "blocked", "down", "critical"]):
            agents.append("issue_extraction")

        # Decisions
        if any(kw in p for kw in ["decision", "decide", "choice", "priorit", "should we", "go/no-go"]):
            agents.append("decision_extraction")

        # Tracking follow-ups
        if any(kw in p for kw in ["track", "status", "snapshot", "progress", "update"]):
            if not agents:  # If no extraction needed, just track
                agents.append("action_item_tracking")

        # Validation
        if "validat" in p:
            agents.append("action_item_validation")

        # Default: extract action items
        if not agents:
            agents.append("action_item_extraction")

        return agents

    elif domain == "COMMUNICATION_COLLABORATION":
        # Delivery (send/deliver/distribute) — check before meeting/report
        if any(kw in p for kw in ["send", "deliver", "dispatch", "forward", "distribute"]):
            return ["message_delivery"]

        # Meeting transcript/minutes capture
        if any(kw in p for kw in ["meeting", "transcript", "capture", "minutes", "attendance"]):
            return ["meeting_attendance"]

        # Report generation
        if any(kw in p for kw in ["report", "summary", "digest", "document", "generate"]):
            return ["report_generation"]

        # Q&A / formulate response (default for this domain)
        return ["qna"]

    elif domain == "LEARNING_IMPROVEMENT":
        return ["instruction_led_learning"]

    else:
        return []


# ─────────────────────────────────────────────────────────────
# L2 Coordinator
# ─────────────────────────────────────────────────────────────

class L2Coordinator:
    """
    L2 Coordinator: executes a single L2 domain task by
    coordinating the appropriate L3 agents.
    """

    def execute(
        self,
        planned_task: PlannedTask,
        message: InputMessage,
        task_context: Dict[str, Any],
    ) -> ExecutedTask:
        """
        Execute a planned L2 task. Returns an ExecutedTask with all L3 results.
        """
        domain = planned_task.domain  # e.g. "TRACKING_EXECUTION"

        # Build execution context for L3 agents
        context = {
            "content": message.content,
            "sender_name": message.sender.name,
            "sender_role": message.sender.role,
            "project": message.project or "N/A",
            "source": message.source,
            "purpose": planned_task.purpose,
            "extra": task_context.get("accumulated_context", ""),
        }

        # Select which L3 agents to run
        l3_agent_names = _select_l3_agents_for_task(domain, planned_task.purpose, context)

        l3_results = []
        sub_idx = ord("A")

        for agent_name in l3_agent_names:
            # Enforce visibility: agent must belong to this domain
            allowed = DOMAIN_AGENTS.get(domain, set()) | CROSS_CUTTING_AGENTS
            if agent_name not in allowed:
                continue

            sub_task_id = f"{planned_task.task_id}-{chr(sub_idx)}"
            sub_idx += 1

            try:
                output_lines = run_l3_agent(agent_name, context)
                status = TaskStatus.COMPLETED
            except Exception as e:
                output_lines = [f"Error: {str(e)}"]
                status = TaskStatus.FAILED

            l3_results.append(L3ExecutionResult(
                sub_task_id=sub_task_id,
                agent_name=agent_name,
                status=status,
                output_lines=output_lines,
            ))

        return ExecutedTask(
            task_id=planned_task.task_id,
            target=planned_task.target,
            task_type=planned_task.task_type,
            status=TaskStatus.COMPLETED,
            l3_results=l3_results,
        )


# ─────────────────────────────────────────────────────────────
# Cross-Cutting Task Executor
# ─────────────────────────────────────────────────────────────

class CrossCuttingExecutor:
    """
    Executes cross-cutting L3 tasks (knowledge_retrieval, evaluation).
    These are directly callable by L1 and all L2s.
    """

    def execute(
        self,
        planned_task: PlannedTask,
        message: InputMessage,
        task_context: Dict[str, Any],
    ) -> ExecutedTask:
        agent_name = planned_task.domain  # e.g. "knowledge_retrieval"

        if agent_name not in CROSS_CUTTING_AGENTS:
            return ExecutedTask(
                task_id=planned_task.task_id,
                target=planned_task.target,
                task_type=planned_task.task_type,
                status=TaskStatus.FAILED,
                output_lines=[f"'{agent_name}' is not a cross-cutting agent"],
            )

        context = {
            "content": message.content,
            "sender_name": message.sender.name,
            "sender_role": message.sender.role,
            "project": message.project or "N/A",
            "source": message.source,
            "purpose": planned_task.purpose,
            "extra": task_context.get("accumulated_context", ""),
        }

        try:
            output_lines = run_l3_agent(agent_name, context)
            status = TaskStatus.COMPLETED
        except Exception as e:
            output_lines = [f"Error: {str(e)}"]
            status = TaskStatus.FAILED

        return ExecutedTask(
            task_id=planned_task.task_id,
            target=planned_task.target,
            task_type=planned_task.task_type,
            status=status,
            output_lines=output_lines,
        )
