"""
agents/l1/orchestrator.py
--------------------------
L1 Orchestrator: ingests message, reasons about intent,
identifies gaps, selects strategy, generates task plan.

Visibility: L2 domain agents + Cross-Cutting agents ONLY.
L1 does NOT see individual L3 agents directly.
"""

import json
import re
from typing import List

from core.models import InputMessage, PlannedTask, TaskType
from core.llm_provider import call_llm

# ─────────────────────────────────────────────────────────────
# What L1 can see (visibility rules enforced here)
# ─────────────────────────────────────────────────────────────
VISIBLE_L2_DOMAINS = [
    "L2:TRACKING_EXECUTION",
    "L2:COMMUNICATION_COLLABORATION",
    "L2:LEARNING_IMPROVEMENT",
]

VISIBLE_CROSS_CUTTING = [
    "L3:knowledge_retrieval",
    "L3:evaluation",
]

L1_SYSTEM_PROMPT = """
You are the L1 Orchestrator of Nion — an AI Program Manager agent.

Your job is to:
1. Ingest and parse the input message
2. Reason about the sender's intent
3. Identify what information is available vs what is missing
4. Select the correct strategy
5. Generate a task plan as a JSON array

VISIBILITY RULES (strictly enforced):
- You can ONLY delegate to L2 domain agents or Cross-Cutting agents
- You CANNOT delegate directly to L3 agents (except Cross-Cutting ones)
- Available L2 domains: L2:TRACKING_EXECUTION, L2:COMMUNICATION_COLLABORATION, L2:LEARNING_IMPROVEMENT
- Available Cross-Cutting (L3): L3:knowledge_retrieval, L3:evaluation

DOMAIN PURPOSES:
- L2:TRACKING_EXECUTION → Extract and track action items, risks, issues, decisions
- L2:COMMUNICATION_COLLABORATION → Q&A responses, reports, message delivery, meeting minutes
- L2:LEARNING_IMPROVEMENT → Learn from explicit instructions, update SOPs
- L3:knowledge_retrieval (Cross-Cutting) → Retrieve project context, history, stakeholder info
- L3:evaluation (Cross-Cutting) → Validate outputs before delivery

OUTPUT FORMAT: Return ONLY a valid JSON array. No markdown, no explanation.
Each task object must have:
{
  "task_id": "TASK-001",
  "target": "L2:TRACKING_EXECUTION",  // or L3:knowledge_retrieval, L3:evaluation
  "type": "l2",  // or "cross_cutting"
  "purpose": "Brief description of what this task should accomplish",
  "depends_on": []  // list of task_ids this depends on, or empty array
}

Rules:
- Number tasks TASK-001, TASK-002, etc.
- Keep purposes specific to the message content
- Order tasks logically (dependencies before dependents)
- A typical plan has 4-8 tasks
- For extraction tasks, use L2:TRACKING_EXECUTION
- For Q&A/responses/delivery, use L2:COMMUNICATION_COLLABORATION
- For retrieving context FIRST, use L3:knowledge_retrieval
- ALWAYS end with L3:evaluation then delivery via L2:COMMUNICATION_COLLABORATION
- For meeting transcripts, start with L2:COMMUNICATION_COLLABORATION (meeting_attendance)
- For learning/instruction messages, include L2:LEARNING_IMPROVEMENT
""".strip()


def create_l1_prompt(message: InputMessage) -> str:
    return f"""
Analyze this message and create a task plan:

Message ID: {message.message_id}
Source: {message.source}
Sender: {message.sender.name} ({message.sender.role})
Project: {message.project or 'NOT SPECIFIED'}
Content: {message.content}

Generate the task plan JSON array now:
""".strip()


def parse_task_plan(raw: str) -> List[dict]:
    """Extract JSON array from LLM response, even if wrapped in markdown."""
    # Strip markdown code fences
    clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Try to find JSON array
    match = re.search(r"\[.*\]", clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return []


def build_planned_tasks(task_dicts: List[dict]) -> List[PlannedTask]:
    tasks = []
    for t in task_dicts:
        raw_type = t.get("type", "l2").lower()
        task_type = TaskType.CROSS_CUTTING if raw_type == "cross_cutting" else TaskType.L2_DOMAIN
        tasks.append(PlannedTask(
            task_id=t.get("task_id", "TASK-???"),
            target=t.get("target", "L2:TRACKING_EXECUTION"),
            task_type=task_type,
            purpose=t.get("purpose", ""),
            depends_on=t.get("depends_on", []),
        ))
    return tasks


class L1Orchestrator:
    """
    L1 Orchestrator: plans the full task graph.
    Only sees L2 domains and cross-cutting agents.
    """

    def plan(self, message: InputMessage) -> List[PlannedTask]:
        prompt = create_l1_prompt(message)
        raw = call_llm(
            prompt=prompt,
            system=L1_SYSTEM_PROMPT,
            max_tokens=1500,
        )

        task_dicts = parse_task_plan(raw)

        if not task_dicts:
            # Fallback: generic plan
            task_dicts = [
                {"task_id": "TASK-001", "target": "L3:knowledge_retrieval",
                 "type": "cross_cutting", "purpose": "Retrieve project context", "depends_on": []},
                {"task_id": "TASK-002", "target": "L2:TRACKING_EXECUTION",
                 "type": "l2", "purpose": "Extract action items from message", "depends_on": ["TASK-001"]},
                {"task_id": "TASK-003", "target": "L2:COMMUNICATION_COLLABORATION",
                 "type": "l2", "purpose": "Formulate response", "depends_on": ["TASK-001", "TASK-002"]},
                {"task_id": "TASK-004", "target": "L3:evaluation",
                 "type": "cross_cutting", "purpose": "Evaluate response", "depends_on": ["TASK-003"]},
                {"task_id": "TASK-005", "target": "L2:COMMUNICATION_COLLABORATION",
                 "type": "l2", "purpose": "Deliver response", "depends_on": ["TASK-004"]},
            ]

        return build_planned_tasks(task_dicts)
