# ============================================================
# agents/l2_coordinator.py
#
# RESPONSIBILITY
#   • Receive a delegation from L1 (an L1Task targeting an L2)
#   • Call the Claude API to decide which L3 agents to invoke
#     and in what order (visibility: own L3s + cross-cutting)
#   • Execute each L3 agent (via L3Executor) and collect results
#   • Return an L2Result
# ============================================================

import json
import re
from typing import List

import anthropic

from src.architecture import L3_AGENTS, CROSS_CUTTING_AGENTS, l2_visible_targets
from src.models import InboundMessage, L1Task, L2Result, L3Result
from src.agents.l3_executor import L3Executor


# ── Prompt builder ───────────────────────────────────────────

def _build_system_prompt(domain: str) -> str:
    own_agents   = L3_AGENTS.get(domain, {})
    cross_agents = CROSS_CUTTING_AGENTS

    agent_list = "\n".join(
        [f"  - {name}: {desc}" for name, desc in own_agents.items()]
        + [f"  - {name} (cross-cutting): {desc}" for name, desc in cross_agents.items()]
    )

    return f"""You are the L2 Coordinator for the {domain} domain of Nion.

Your job:
1. Receive a task delegated from the L1 Orchestrator.
2. Decide which L3 agents to invoke to fulfil that task.
3. Return a JSON list of agent invocations in execution order.

VISIBILITY RULE: You may ONLY use agents in YOUR domain or cross-cutting agents.
Agents you can use:
{agent_list}

OUTPUT FORMAT (strict JSON, no extra text):
{{
  "agents": [
    {{
      "sub_task_id": "TASK-XXX-A",
      "agent": "<agent_name>",
      "reason": "<why this agent is needed>"
    }}
  ]
}}

Rules:
- sub_task_id suffix must be a letter (A, B, C …)
- Only include agents genuinely needed for this task
- Order matters – list them in execution sequence
- Return ONLY valid JSON, no markdown fences
"""


def _build_user_prompt(task: L1Task, msg: InboundMessage) -> str:
    return f"""Task delegated to you:
Task ID  : {task.task_id}
Purpose  : {task.purpose}

Original message context:
  Source  : {msg.source}
  Sender  : {msg.sender_name} ({msg.sender_role})
  Project : {msg.project or "UNKNOWN"}
  Content : {msg.content}

Which L3 agents should you invoke, and in what order? Return the JSON plan."""


# ── Main class ───────────────────────────────────────────────

class L2Coordinator:
    """
    One L2Coordinator instance per domain.  L1 instantiates the
    right coordinator and calls .execute(task, message).
    """

    def __init__(self, domain: str, client: anthropic.Anthropic):
        self.domain   = domain
        self.client   = client
        self.executor = L3Executor(domain, client)
        self._visible = l2_visible_targets(domain)

    def execute(self, task: L1Task, msg: InboundMessage) -> L2Result:
        agent_plan = self._call_llm(task, msg)
        validated  = self._validate(agent_plan, task)
        l3_results = self._run_agents(validated, task, msg)
        return L2Result(task_id=task.task_id, domain=self.domain, l3_results=l3_results)

    # ── Private helpers ──────────────────────────────────────

    def _call_llm(self, task: L1Task, msg: InboundMessage) -> List[dict]:
        response = self.client.messages.create(
            model  = "claude-sonnet-4-20250514",
            max_tokens = 1000,
            system = _build_system_prompt(self.domain),
            messages = [{"role": "user", "content": _build_user_prompt(task, msg)}],
        )
        raw     = response.content[0].text.strip()
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"L2 [{self.domain}] LLM returned invalid JSON:\n{raw}\n\nError: {exc}"
            )

        return data.get("agents", [])

    def _validate(self, agent_plan: List[dict], task: L1Task) -> List[dict]:
        allowed = set(self._visible["l3_agents"]) | set(self._visible["cross_cutting"])
        validated = []
        for item in agent_plan:
            name = item["agent"]
            if name not in allowed:
                # Silently skip agents outside visibility scope (defensive)
                continue
            validated.append(item)
        return validated

    def _run_agents(
        self, agent_plan: List[dict], task: L1Task, msg: InboundMessage
    ) -> List[L3Result]:
        results = []
        for item in agent_plan:
            result = self.executor.run(
                sub_task_id = item["sub_task_id"],
                agent_name  = item["agent"],
                reason      = item["reason"],
                parent_task = task,
                msg         = msg,
            )
            results.append(result)
        return results