"""
core/formatter.py
-----------------
Renders the NION ORCHESTRATION MAP in the required text format.
"""

from core.models import OrchestrationResult, ExecutedTask, TaskType

SEP = "=" * 78


def format_orchestration_map(result: OrchestrationResult) -> str:
    lines = []

    # ── Header ────────────────────────────────────────────────
    lines.append(SEP)
    lines.append("NION ORCHESTRATION MAP")
    lines.append(SEP)

    msg = result.message
    lines.append(f"Message: {msg.message_id}")
    lines.append(f"From:    {msg.sender.name} ({msg.sender.role})")
    lines.append(f"Project: {msg.project or 'N/A'}")
    lines.append(f"Source:  {msg.source}")
    lines.append("")

    # ── L1 Plan ───────────────────────────────────────────────
    lines.append(SEP)
    lines.append("L1 PLAN")
    lines.append(SEP)

    for task in result.planned_tasks:
        suffix = " (Cross-Cutting)" if task.is_cross_cutting else ""
        lines.append(f"[{task.task_id}] → {task.target}{suffix}")
        lines.append(f"  Purpose: {task.purpose}")
        if task.depends_on:
            lines.append(f"  Depends On: {', '.join(task.depends_on)}")
        lines.append("")

    # ── L2/L3 Execution ───────────────────────────────────────
    lines.append(SEP)
    lines.append("L2/L3 EXECUTION")
    lines.append(SEP)
    lines.append("")

    for task in result.executed_tasks:
        _format_executed_task(lines, task)

    lines.append(SEP)
    return "\n".join(lines)


def _format_executed_task(lines: list, task: ExecutedTask) -> None:
    if task.task_type == TaskType.CROSS_CUTTING:
        # Cross-cutting: no L2 wrapper, direct L3 output
        agent = task.target.split(":", 1)[-1] if ":" in task.target else task.target
        lines.append(f"[{task.task_id}] L3:{agent} (Cross-Cutting)")
        lines.append(f"  Status: {task.status.value}")
        if task.output_lines:
            lines.append("  Output:")
            for line in task.output_lines:
                lines.append(f"    • {line}")
        lines.append("")
    else:
        # L2 domain task — show L2 header + L3 sub-tasks
        lines.append(f"[{task.task_id}] {task.target}")
        for l3 in task.l3_results:
            lines.append(f"  └─▶ [{l3.sub_task_id}] L3:{l3.agent_name}")
            lines.append(f"        Status: {l3.status.value}")
            if l3.output_lines:
                lines.append("        Output:")
                for line in l3.output_lines:
                    lines.append(f"          • {line}")
        lines.append("")
