# ============================================================
# engine.py
#
# THE WIRING LAYER
# ─────────────────
# Accepts a raw JSON dict, drives the full pipeline:
#   1. Parse input  →  InboundMessage
#   2. L1 plans     →  List[L1Task]
#   3. For each task:
#        L2 task  → L2Coordinator.execute() → L2Result
#        L3_CROSS → L3Executor.run()        → CrossCuttingResult
#   4. Return OrchestrationResult
# ============================================================

from typing import Any, Dict

import anthropic

from src.models import (
    InboundMessage,
    L2Result,
    CrossCuttingResult,
    OrchestrationResult,
)
from src.agents.l1_orchestrator import L1Orchestrator
from src.agents.l2_coordinator   import L2Coordinator
from src.agents.l3_executor      import L3Executor
from src.architecture import CROSS_CUTTING_AGENTS


class NionEngine:
    """
    Top-level façade.  Callers only interact with this class.

    Usage:
        engine = NionEngine()
        result = engine.run(message_dict)
        print(result)           # uses __str__ of OrchestrationResult
    """

    def __init__(self):
        self.client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from env

    # ── Public API ───────────────────────────────────────────

    def run(self, raw: Dict[str, Any]) -> OrchestrationResult:
        msg = self._parse_message(raw)

        # ── Step 1: L1 planning ──────────────────────────────
        l1 = L1Orchestrator(self.client)
        plan = l1.plan(msg)

        # ── Step 2: Execute each planned task ────────────────
        executions = []
        # Cross-cutting executor (domain-agnostic, reused for L3_CROSS tasks)
        cross_executor = L3Executor(domain="CROSS_CUTTING", client=self.client)

        for task in plan:
            if task.target_type == "L2":
                coordinator = L2Coordinator(task.target, self.client)
                result = coordinator.execute(task, msg)
                executions.append(result)

            elif task.target_type == "L3_CROSS":
                l3_result = cross_executor.run(
                    sub_task_id = task.task_id,
                    agent_name  = task.target,
                    reason      = task.purpose,
                    parent_task = task,
                    msg         = msg,
                )
                cc_result = CrossCuttingResult(
                    task_id      = task.task_id,
                    agent_name   = task.target,
                    status       = l3_result.status,
                    output_lines = l3_result.output_lines,
                )
                executions.append(cc_result)

        return OrchestrationResult(
            message    = msg,
            l1_plan    = plan,
            executions = executions,
        )

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _parse_message(raw: Dict[str, Any]) -> InboundMessage:
        sender = raw.get("sender", {})
        return InboundMessage(
            message_id  = raw.get("message_id", "MSG-???"),
            source      = raw.get("source", "unknown"),
            sender_name = sender.get("name", "Unknown"),
            sender_role = sender.get("role", "Unknown"),
            content     = raw.get("content", ""),
            project     = raw.get("project"),
        )