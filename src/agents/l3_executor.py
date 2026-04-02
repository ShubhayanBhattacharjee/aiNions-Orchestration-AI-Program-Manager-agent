# ============================================================
# agents/l3_executor.py
#
# RESPONSIBILITY
#   • Execute a single L3 agent against the message context
#   • Return an L3Result with realistic bullet-point output
# ============================================================

import re
from typing import List

import anthropic

from src.architecture import L3_AGENTS, CROSS_CUTTING_AGENTS
from src.models import InboundMessage, L1Task, L3Result


# ── Agent-specific prompts ───────────────────────────────────
# Each agent has a tailored system prompt so its output
# reflects what that specialist would actually produce.

AGENT_SYSTEM_PROMPTS = {
    # ── TRACKING_EXECUTION ──────────────────────────────────
    "action_item_extraction": """You are the action_item_extraction L3 agent.
Extract concrete action items from the message. For each item output:
  • AI-NNN: "<description>"  Owner: <name or ?> | Due: <date or ?> | Flags: [<MISSING_* flags if applicable>]
Output ONLY the bullet lines. No preamble.""",

    "action_item_validation": """You are the action_item_validation L3 agent.
Review previously extracted action items and flag any with missing required fields.
Output validation results as bullets:
  • AI-NNN: <VALID or list of issues>
Output ONLY the bullet lines.""",

    "action_item_tracking": """You are the action_item_tracking L3 agent.
Provide a status snapshot of all tracked action items.
Output as bullets:
  • AI-NNN: "<description>" | Status: <status> | Owner: <owner>
Output ONLY the bullet lines.""",

    "risk_extraction": """You are the risk_extraction L3 agent.
Extract risks from the message. For each risk output:
  • RISK-NNN: "<description>"  Likelihood: <HIGH|MEDIUM|LOW> | Impact: <HIGH|MEDIUM|LOW>
Output ONLY the bullet lines.""",

    "risk_tracking": """You are the risk_tracking L3 agent.
Provide a risk snapshot. Output as bullets:
  • RISK-NNN: "<description>" | Status: <OPEN|MITIGATED|CLOSED>
Output ONLY the bullet lines.""",

    "issue_extraction": """You are the issue_extraction L3 agent.
Extract issues or blockers from the message. For each issue output:
  • ISS-NNN: "<description>"  Severity: <CRITICAL|HIGH|MEDIUM|LOW> | Reported By: <name>
Output ONLY the bullet lines.""",

    "issue_tracking": """You are the issue_tracking L3 agent.
Provide an issue status snapshot. Output as bullets:
  • ISS-NNN: "<description>" | Status: <OPEN|IN_PROGRESS|RESOLVED>
Output ONLY the bullet lines.""",

    "decision_extraction": """You are the decision_extraction L3 agent.
Extract decisions required or made in the message. For each decision output:
  • DEC-NNN: "<decision description>"  Decision Maker: <name or ?> | Status: <PENDING|MADE>
Output ONLY the bullet lines.""",

    "decision_tracking": """You are the decision_tracking L3 agent.
Track decisions to implementation. Output as bullets:
  • DEC-NNN: "<description>" | Status: <PENDING|APPROVED|REJECTED|IMPLEMENTED>
Output ONLY the bullet lines.""",

    # ── COMMUNICATION_COLLABORATION ─────────────────────────
    "qna": """You are the qna L3 agent.
Formulate a clear, gap-aware response to the sender's question.
Structure your response using these sections as applicable:
  WHAT I KNOW: (bullet facts retrieved)
  WHAT I'VE LOGGED: (bullet tracked items)
  WHAT I NEED: (bullet gaps / open questions)
  Closing sentence summarising feasibility or next step.
Output the response as a single bullet:
  • Response: "<full response text>"
Keep it concise but complete.""",

    "report_generation": """You are the report_generation L3 agent.
Generate a short formatted status report based on the message context.
Output as bullets covering: summary, key items, risks, next steps.
  • Summary: <one sentence>
  • Key Items: <count> tracked
  • Risk Level: <LOW|MEDIUM|HIGH>
  • Next Steps: <action>
Output ONLY the bullet lines.""",

    "message_delivery": """You are the message_delivery L3 agent.
Determine delivery details and simulate sending the response.
Output as bullets:
  • Channel: <channel>
  • Recipient: <name>
  • CC: <names if applicable>
  • Delivery Status: SENT
Output ONLY the bullet lines.""",

    "meeting_attendance": """You are the meeting_attendance L3 agent.
Process the meeting transcript and generate structured minutes.
Output as bullets:
  • Attendees: <list>
  • Key Discussion Points: <point 1>; <point 2>
  • Decisions Made: <or NONE>
  • Action Items Identified: <count>
  • Minutes Status: CAPTURED
Output ONLY the bullet lines.""",

    # ── LEARNING_IMPROVEMENT ────────────────────────────────
    "instruction_led_learning": """You are the instruction_led_learning L3 agent.
Extract any explicit instructions, SOPs, or rules from the message and store them.
Output as bullets:
  • SOP-NNN: "<instruction learned>"  Source: <sender role> | Stored: YES
Output ONLY the bullet lines.""",

    # ── CROSS-CUTTING ────────────────────────────────────────
    "knowledge_retrieval": """You are the knowledge_retrieval cross-cutting agent.
Retrieve relevant project context. Generate plausible but clearly labelled context data.
Output as bullets covering: project name, timeline, team capacity, key personnel, progress %.
  • Project: <name>
  • Current Release Date: <date>
  • Days Remaining: <N>
  • Code Freeze: <date>
  • Current Progress: <N>%
  • Team Capacity: <N>% utilized
  • Engineering Manager: <name>
  • Tech Lead: <name>
Output ONLY the bullet lines.""",

    "evaluation": """You are the evaluation cross-cutting agent.
Evaluate the output from previous tasks for accuracy, tone, completeness, and gap acknowledgement.
Output as bullets:
  • Relevance: PASS or FAIL
  • Accuracy: PASS or FAIL
  • Tone: PASS or FAIL
  • Gaps Acknowledged: PASS or FAIL
  • Result: APPROVED or REJECTED
Output ONLY the bullet lines.""",
}

DEFAULT_SYSTEM_PROMPT = """You are a specialised L3 agent in the Nion orchestration system.
Execute your assigned task and output results as concise bullet lines starting with •.
Output ONLY the bullet lines, no preamble."""


# ── User prompt builder ──────────────────────────────────────

def _build_user_prompt(
    agent_name: str,
    reason: str,
    parent_task: L1Task,
    msg: InboundMessage,
) -> str:
    return f"""Your assigned sub-task:
  Sub-task reason : {reason}
  Parent task     : {parent_task.purpose}

Message context:
  Source   : {msg.source}
  Sender   : {msg.sender_name} ({msg.sender_role})
  Project  : {msg.project or "UNKNOWN"}
  Content  : {msg.content}

Execute now and output ONLY bullet lines."""


# ── Main class ───────────────────────────────────────────────

class L3Executor:
    """
    Executes individual L3 agents.
    One instance per L2 domain, but can also run cross-cutting
    agents (called directly from the engine for L3_CROSS tasks).
    """

    def __init__(self, domain: str, client: anthropic.Anthropic):
        self.domain = domain
        self.client = client

    def run(
        self,
        sub_task_id: str,
        agent_name: str,
        reason: str,
        parent_task: L1Task,
        msg: InboundMessage,
    ) -> L3Result:
        system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_name, DEFAULT_SYSTEM_PROMPT)
        user_prompt   = _build_user_prompt(agent_name, reason, parent_task, msg)

        try:
            response = self.client.messages.create(
                model      = "claude-sonnet-4-20250514",
                max_tokens = 1000,
                system     = system_prompt,
                messages   = [{"role": "user", "content": user_prompt}],
            )
            raw_output = response.content[0].text.strip()
            lines      = self._parse_bullets(raw_output)
            status     = "COMPLETED"
        except Exception as exc:
            lines  = [f"Error: {exc}"]
            status = "FAILED"

        return L3Result(
            task_id      = sub_task_id,
            agent_name   = agent_name,
            status       = status,
            output_lines = lines,
        )

    # ── Private helpers ──────────────────────────────────────

    @staticmethod
    def _parse_bullets(text: str) -> List[str]:
        """
        Split multi-line LLM output into individual bullet strings.
        Handles both • and - prefixes.
        """
        lines  = text.split("\n")
        result = []
        current = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # New bullet starts
            if stripped.startswith(("•", "-", "*")):
                if current:
                    result.append(current)
                current = stripped.lstrip("•-* ").strip()
            else:
                # Continuation of previous bullet
                if current:
                    current += " " + stripped
                else:
                    current = stripped

        if current:
            result.append(current)

        return result if result else [text]