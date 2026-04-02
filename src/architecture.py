# ============================================================
# architecture.py
# Defines the full L1 → L2 → L3 agent hierarchy,
# visibility rules, and agent metadata.
# ============================================================

# ── L2 Domain Names ─────────────────────────────────────────
L2_TRACKING_EXECUTION          = "TRACKING_EXECUTION"
L2_COMMUNICATION_COLLABORATION = "COMMUNICATION_COLLABORATION"
L2_LEARNING_IMPROVEMENT        = "LEARNING_IMPROVEMENT"

ALL_L2_DOMAINS = [
    L2_TRACKING_EXECUTION,
    L2_COMMUNICATION_COLLABORATION,
    L2_LEARNING_IMPROVEMENT,
]

# ── Cross-Cutting Agents (visible to L1 + all L2s) ──────────
CROSS_CUTTING_AGENTS = {
    "knowledge_retrieval": "Retrieves context from database – project info, stakeholder details, historical data",
    "evaluation":          "Validates outputs before delivery – checks accuracy, tone, completeness",
}

# ── L3 Agents per L2 Domain ─────────────────────────────────
L3_AGENTS = {
    L2_TRACKING_EXECUTION: {
        "action_item_extraction": "Extracts action items from message content, infers owners and due dates",
        "action_item_validation": "Validates action items have required fields, flags missing info",
        "action_item_tracking":   "Tracks action items to completion, provides status snapshots",
        "risk_extraction":        "Extracts risks from message content, assesses likelihood and impact",
        "risk_tracking":          "Tracks risks, provides risk snapshots",
        "issue_extraction":       "Extracts issues/problems from message content, assesses severity",
        "issue_tracking":         "Tracks issues to resolution, provides issue snapshots",
        "decision_extraction":    "Extracts decisions from message content, identifies decision maker",
        "decision_tracking":      "Tracks decisions to implementation",
    },
    L2_COMMUNICATION_COLLABORATION: {
        "qna":                "Formulates responses to questions, handles both direct answers and gap-aware responses",
        "report_generation":  "Creates formatted reports (status reports, summaries, digests)",
        "message_delivery":   "Sends messages via appropriate channels (email, Slack, Teams)",
        "meeting_attendance": "Captures meeting transcripts, generates meeting minutes",
    },
    L2_LEARNING_IMPROVEMENT: {
        "instruction_led_learning": "Learns from explicit instructions, stores SOPs and rules",
    },
}

# ── Visibility Rules ─────────────────────────────────────────
# L1 can see: all L2 domains + cross-cutting agents
# L2 can see: its own L3 agents + cross-cutting agents
# L3 sees: nothing (leaf executor)

def l1_visible_targets():
    """Returns what L1 is allowed to delegate to."""
    return {
        "l2_domains":       ALL_L2_DOMAINS,
        "cross_cutting":    list(CROSS_CUTTING_AGENTS.keys()),
    }

def l2_visible_targets(domain: str):
    """Returns what a specific L2 domain is allowed to coordinate."""
    return {
        "l3_agents":     list(L3_AGENTS.get(domain, {}).keys()),
        "cross_cutting": list(CROSS_CUTTING_AGENTS.keys()),
    }