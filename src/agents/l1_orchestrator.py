# ============================================================
# agents/l1_orchestrator.py
#
# RESPONSIBILITY
#   • Ingest the inbound message
#   • Call the Claude API to reason about intent
#   • Produce a validated L1Plan (list of L1Task objects)
#     – every task targets either an L2 domain or a
#       cross-cutting agent (visibility rule enforced here)
# ============================================================

import json
import re
from typing import List

import anthropic

from src.architecture import (
    ALL_L2_DOMAINS,
    CROSS_CUTTING_AGENTS,
    l1_visible_targets,
)
from src.models import InboundMessage, L1Task


# ── Prompt builder ───────────────────────────────────────────

SYSTEM_PROMPT = """You are the L1 Orchestrator of Nion, an AI Program Manager agent.

Your job:
1. Analyse the inbound message and understand the sender's intent.
2. Produce a JSON execution plan – a list of tasks.

VISIBILITY RULE (critical):
- You may ONLY delegate to L2 domains or cross-cutting agents.
- You must NEVER reference individual L3 agents directly.
- L2 domains available: TRACKING_EXECUTION, COMMUNICATION_COLLABORATION, LEARNING_IMPROVEMENT
- Cross-cutting agents available: knowledge_retrieval, evaluation

OUTPUT FORMAT (strict JSON, no extra text):
{
  "tasks": [
    {
      "task_id": "TASK-001",
      "target_type": "L2",
      "target": "<L2_DOMAIN_NAME>",
      "purpose": "<what this task achieves>",
      "depends_on": []
    },
    {
      "task_id": "TASK-002",
      "target_type": "L3_CROSS",
      "target": "knowledge_retrieval",
      "purpose": "<what this task achieves>",
      "depends_on": []
    }
  ]
}

Rules:
- target_type must be "L2" (for domain delegation) or "L3_CROSS" (for cross-cutting agents)
- depends_on is a list of task_id strings
- Always include at least one COMMUNICATION_COLLABORATION task to respond to the sender
- Always include an evaluation cross-cutting task before message delivery
- For meeting transcripts (source=meeting), include TRACKING_EXECUTION for issues/action items
- For urgent escalations, prioritise knowledge_retrieval early
- Return ONLY valid JSON, no markdown fences
"""


def build_user_prompt(msg: InboundMessage) -> str:
    return f"""Analyse this inbound message and produce the L1 execution plan.

Message ID : {msg.message_id}
Source     : {msg.source}
Sender     : {msg.sender_name} ({msg.sender_role})
Project    : {msg.project or "UNKNOWN"}
Content    : {msg.content}

Produce the JSON plan now."""


# ── Main class ───────────────────────────────────────────────

class L1Orchestrator:
    """
    Calls Claude to reason about the message and generate a plan.
    Validates that every task respects L1 visibility rules before
    returning.
    """

    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self._visible = l1_visible_targets()

    def plan(self, msg: InboundMessage) -> List[L1Task]:
        raw = self._call_llm(msg)
        tasks = self._parse_and_validate(raw)
        return tasks

    # ── Private helpers ──────────────────────────────────────

    def _call_llm(self, msg: InboundMessage) -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(msg)}],
        )
        return response.content[0].text.strip()

    def _parse_and_validate(self, raw: str) -> List[L1Task]:
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"L1 LLM returned invalid JSON:\n{raw}\n\nError: {exc}")

        tasks: List[L1Task] = []
        for item in data.get("tasks", []):
            target_type = item["target_type"]
            target      = item["target"]

            # ── Enforce visibility ───────────────────────────
            if target_type == "L2":
                if target not in self._visible["l2_domains"]:
                    raise ValueError(
                        f"L1 attempted to delegate to unknown L2 domain: {target}"
                    )
            elif target_type == "L3_CROSS":
                if target not in self._visible["cross_cutting"]:
                    raise ValueError(
                        f"L1 attempted to use unknown cross-cutting agent: {target}"
                    )
            else:
                raise ValueError(
                    f"Invalid target_type '{target_type}'. Must be 'L2' or 'L3_CROSS'."
                )

            tasks.append(
                L1Task(
                    task_id    = item["task_id"],
                    target_type= target_type,
                    target     = target,
                    purpose    = item["purpose"],
                    depends_on = item.get("depends_on", []),
                )
            )

        return tasks