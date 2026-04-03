"""
agents/l3/agents.py
-------------------
All L3 agent implementations.

Each L3 agent is a function that receives context and returns output lines.
Agents are grouped by their L2 domain (visibility rules enforced at L2 level).

L3 Agents by domain:
  TRACKING_EXECUTION:
    - action_item_extraction
    - action_item_validation
    - action_item_tracking
    - risk_extraction
    - risk_tracking
    - issue_extraction
    - issue_tracking
    - decision_extraction
    - decision_tracking

  COMMUNICATION_COLLABORATION:
    - qna
    - report_generation
    - message_delivery
    - meeting_attendance

  LEARNING_IMPROVEMENT:
    - instruction_led_learning

  CROSS_CUTTING (visible to all):
    - knowledge_retrieval
    - evaluation
"""

import os
from typing import List, Dict, Any
from core.llm_provider import call_llm

# ─────────────────────────────────────────────────────────────
# Domain membership (for visibility enforcement)
# ─────────────────────────────────────────────────────────────
TRACKING_EXECUTION_AGENTS = {
    "action_item_extraction",
    "action_item_validation",
    "action_item_tracking",
    "risk_extraction",
    "risk_tracking",
    "issue_extraction",
    "issue_tracking",
    "decision_extraction",
    "decision_tracking",
}

COMMUNICATION_COLLABORATION_AGENTS = {
    "qna",
    "report_generation",
    "message_delivery",
    "meeting_attendance",
}

LEARNING_IMPROVEMENT_AGENTS = {
    "instruction_led_learning",
}

CROSS_CUTTING_AGENTS = {
    "knowledge_retrieval",
    "evaluation",
}

# Domain → agent set map (used by L2 coordinators)
DOMAIN_AGENTS: Dict[str, set] = {
    "TRACKING_EXECUTION": TRACKING_EXECUTION_AGENTS,
    "COMMUNICATION_COLLABORATION": COMMUNICATION_COLLABORATION_AGENTS,
    "LEARNING_IMPROVEMENT": LEARNING_IMPROVEMENT_AGENTS,
}


def run_l3_agent(agent_name: str, context: Dict[str, Any]) -> List[str]:
    """
    Execute a named L3 agent with the given context.
    Returns a list of output bullet lines.
    """
    dispatch = {
        # Tracking / Execution
        "action_item_extraction":  _action_item_extraction,
        "action_item_validation":  _action_item_validation,
        "action_item_tracking":    _action_item_tracking,
        "risk_extraction":         _risk_extraction,
        "risk_tracking":           _risk_tracking,
        "issue_extraction":        _issue_extraction,
        "issue_tracking":          _issue_tracking,
        "decision_extraction":     _decision_extraction,
        "decision_tracking":       _decision_tracking,
        # Communication / Collaboration
        "qna":                     _qna,
        "report_generation":       _report_generation,
        "message_delivery":        _message_delivery,
        "meeting_attendance":      _meeting_attendance,
        # Learning / Improvement
        "instruction_led_learning": _instruction_led_learning,
        # Cross-Cutting
        "knowledge_retrieval":     _knowledge_retrieval,
        "evaluation":              _evaluation,
    }

    fn = dispatch.get(agent_name)
    if fn is None:
        return [f"Agent '{agent_name}' not found — skipped"]

    raw = fn(context)
    return _parse_output(raw)


def _parse_output(raw: str) -> List[str]:
    """Split LLM/mock output into bullet lines."""
    lines = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if line:
            # Remove leading bullet chars if already present
            line = line.lstrip("•-* ").strip()
            if line:
                lines.append(line)
    return lines if lines else ["Task completed successfully"]


def _build_prompt(agent_name: str, context: Dict[str, Any]) -> str:
    return (
        f"You are the {agent_name} L3 agent in Nion's orchestration engine.\n\n"
        f"Message Content: {context.get('content', '')}\n"
        f"Sender: {context.get('sender_name', 'Unknown')} ({context.get('sender_role', 'Unknown')})\n"
        f"Project: {context.get('project', 'N/A')}\n"
        f"Source: {context.get('source', 'unknown')}\n"
        f"Task Purpose: {context.get('purpose', '')}\n"
        f"Additional Context: {context.get('extra', '')}\n\n"
        f"Execute your role as {agent_name}. Return results as short bullet lines "
        f"(one item per line, no markdown). Be specific and realistic."
    )


# ─────────────────────────────────────────────────────────────
# TRACKING_EXECUTION Agents
# ─────────────────────────────────────────────────────────────

def _action_item_extraction(ctx: Dict) -> str:
    prompt = _build_prompt("action_item_extraction", ctx)
    prompt += "\nExtract specific action items with: AI-XXX ID, description, inferred owner (or ?), inferred due date (or ?), and any flags like [MISSING_OWNER, MISSING_DUE_DATE, URGENT, CRITICAL]."
    return call_llm(prompt, max_tokens=500)


def _action_item_validation(ctx: Dict) -> str:
    prompt = _build_prompt("action_item_validation", ctx)
    prompt += "\nValidate action items: check for missing owners, due dates, completeness. Report validation results."
    return call_llm(prompt, max_tokens=400)


def _action_item_tracking(ctx: Dict) -> str:
    prompt = _build_prompt("action_item_tracking", ctx)
    prompt += "\nProvide action item tracking snapshot: counts by status (open/in-progress/complete/overdue)."
    return call_llm(prompt, max_tokens=300)


def _risk_extraction(ctx: Dict) -> str:
    prompt = _build_prompt("risk_extraction", ctx)
    prompt += "\nExtract risks with: RISK-XXX ID, description, Likelihood (LOW/MEDIUM/HIGH/CONFIRMED), Impact (LOW/MEDIUM/HIGH/CRITICAL)."
    return call_llm(prompt, max_tokens=500)


def _risk_tracking(ctx: Dict) -> str:
    prompt = _build_prompt("risk_tracking", ctx)
    prompt += "\nProvide risk tracking snapshot: total risks, breakdown by severity level."
    return call_llm(prompt, max_tokens=300)


def _issue_extraction(ctx: Dict) -> str:
    prompt = _build_prompt("issue_extraction", ctx)
    prompt += "\nExtract issues/problems with: ISSUE-XXX ID, description, Severity (LOW/MEDIUM/HIGH/CRITICAL), Owner (or ?)."
    return call_llm(prompt, max_tokens=500)


def _issue_tracking(ctx: Dict) -> str:
    prompt = _build_prompt("issue_tracking", ctx)
    prompt += "\nProvide issue tracking snapshot: total issues, breakdown by severity."
    return call_llm(prompt, max_tokens=300)


def _decision_extraction(ctx: Dict) -> str:
    prompt = _build_prompt("decision_extraction", ctx)
    prompt += "\nExtract decisions needed with: DEC-XXX ID, decision description, Decision Maker (or ?), Status (PENDING/APPROVED/REJECTED)."
    return call_llm(prompt, max_tokens=400)


def _decision_tracking(ctx: Dict) -> str:
    prompt = _build_prompt("decision_tracking", ctx)
    prompt += "\nProvide decision tracking snapshot: pending decisions and their owners."
    return call_llm(prompt, max_tokens=300)


# ─────────────────────────────────────────────────────────────
# COMMUNICATION_COLLABORATION Agents
# ─────────────────────────────────────────────────────────────

def _qna(ctx: Dict) -> str:
    prompt = _build_prompt("qna", ctx)
    prompt += (
        "\nFormulate a gap-aware response. Structure it with sections:\n"
        "WHAT I KNOW, WHAT I'VE LOGGED, WHAT I NEED.\n"
        "Be specific. Acknowledge missing information honestly.\n"
        "Format as: Response: \"<full response text>\""
    )
    return call_llm(prompt, max_tokens=600)


def _report_generation(ctx: Dict) -> str:
    prompt = _build_prompt("report_generation", ctx)
    prompt += "\nDescribe the report generated: format, key sections, word count estimate, delivery status."
    return call_llm(prompt, max_tokens=400)


def _message_delivery(ctx: Dict) -> str:
    prompt = _build_prompt("message_delivery", ctx)
    prompt += f"\nConfirm message delivery details: channel ({ctx.get('source','email')}), recipient, any CC recipients, delivery status."
    return call_llm(prompt, max_tokens=300)


def _meeting_attendance(ctx: Dict) -> str:
    prompt = _build_prompt("meeting_attendance", ctx)
    prompt += "\nCapture meeting summary: duration estimate, participants detected, key topics, action items count detected, issues detected."
    return call_llm(prompt, max_tokens=500)


# ─────────────────────────────────────────────────────────────
# LEARNING_IMPROVEMENT Agents
# ─────────────────────────────────────────────────────────────

def _instruction_led_learning(ctx: Dict) -> str:
    prompt = _build_prompt("instruction_led_learning", ctx)
    prompt += "\nConfirm: what instruction/SOP was learned, where it was stored, rule added."
    return call_llm(prompt, max_tokens=300)


# ─────────────────────────────────────────────────────────────
# CROSS-CUTTING Agents
# ─────────────────────────────────────────────────────────────

def _knowledge_retrieval(ctx: Dict) -> str:
    prompt = _build_prompt("knowledge_retrieval", ctx)
    prompt += (
        "\nRetrieve realistic project context: project details, timeline, team capacity, "
        "stakeholder names, recent status. Make it specific and plausible for the project mentioned."
    )
    return call_llm(prompt, max_tokens=500)


def _evaluation(ctx: Dict) -> str:
    prompt = _build_prompt("evaluation", ctx)
    prompt += (
        "\nValidate the output on these criteria (each PASS or FAIL with brief reason):\n"
        "- Relevance: Does it address the original message?\n"
        "- Accuracy: Are the facts consistent with available context?\n"
        "- Tone: Is it professional and appropriate?\n"
        "- Gaps Acknowledged: Are unknowns clearly flagged?\n"
        "End with: Result: APPROVED or Result: NEEDS_REVISION"
    )
    return call_llm(prompt, max_tokens=400)
