# ============================================================
# utils/renderer.py
#
# Converts an OrchestrationResult into the exact text format
# specified in the assessment:
#
#   ════ NION ORCHESTRATION MAP ════
#   Message / From / Project
#   ════ L1 PLAN ════
#   [TASK-XXX] → L2:DOMAIN  |  L3:agent (Cross-Cutting)
#   ════ L2/L3 EXECUTION ════
#   [TASK-XXX] L2:DOMAIN
#     └─▶ [TASK-XXX-A] L3:agent
#           Status: COMPLETED
#           Output:
#             • line
# ============================================================

from src.models import OrchestrationResult, L2Result, CrossCuttingResult

SEP = "=" * 78


def render(result: OrchestrationResult) -> str:
    parts = []

    # ── Header ───────────────────────────────────────────────
    msg = result.message
    parts.append(SEP)
    parts.append("NION ORCHESTRATION MAP")
    parts.append(SEP)
    parts.append(f"Message : {msg.message_id}")
    parts.append(f"From    : {msg.sender_name} ({msg.sender_role})")
    parts.append(f"Project : {msg.project or 'N/A'}")
    parts.append("")

    # ── L1 Plan ──────────────────────────────────────────────
    parts.append(SEP)
    parts.append("L1 PLAN")
    parts.append(SEP)

    for task in result.l1_plan:
        if task.target_type == "L2":
            target_label = f"L2:{task.target}"
        else:
            target_label = f"L3:{task.target} (Cross-Cutting)"

        parts.append(f"[{task.task_id}] → {target_label}")
        parts.append(f"  Purpose    : {task.purpose}")
        if task.depends_on:
            parts.append(f"  Depends On : {', '.join(task.depends_on)}")
        parts.append("")

    # ── L2/L3 Execution ──────────────────────────────────────
    parts.append(SEP)
    parts.append("L2/L3 EXECUTION")
    parts.append(SEP)
    parts.append("")

    for execution in result.executions:
        if isinstance(execution, L2Result):
            parts.append(f"[{execution.task_id}] L2:{execution.domain}")
            for l3 in execution.l3_results:
                parts.append(f"  └─▶ [{l3.task_id}] L3:{l3.agent_name}")
                parts.append(f"        Status : {l3.status}")
                parts.append(f"        Output :")
                for line in l3.output_lines:
                    parts.append(f"          • {line}")
            parts.append("")

        elif isinstance(execution, CrossCuttingResult):
            parts.append(
                f"[{execution.task_id}] L3:{execution.agent_name} (Cross-Cutting)"
            )
            parts.append(f"  Status : {execution.status}")
            parts.append(f"  Output :")
            for line in execution.output_lines:
                parts.append(f"    • {line}")
            parts.append("")

    parts.append(SEP)
    return "\n".join(parts)