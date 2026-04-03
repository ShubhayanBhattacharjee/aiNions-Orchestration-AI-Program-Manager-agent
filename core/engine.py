import os
from typing import Dict, Any, List

from core.models import (
    InputMessage, PlannedTask, ExecutedTask,
    OrchestrationResult, TaskType, TaskStatus
)
from agents.l1.orchestrator import L1Orchestrator
from agents.l2.coordinator import L2Coordinator, CrossCuttingExecutor


class NionOrchestrationEngine:
    def __init__(self):
        self.l1 = L1Orchestrator()
        self.l2 = L2Coordinator()
        self.cross_cutting = CrossCuttingExecutor()
        self.verbose = os.getenv("VERBOSE", "false").lower() == "true"

    def run(self, message: InputMessage) -> OrchestrationResult:
        """
        Full orchestration pipeline:
        1. L1 creates task plan
        2. Execute tasks in dependency order
        3. Return complete orchestration result
        """
        if self.verbose:
            print(f"\n[ENGINE] Processing message: {message.message_id}")
            print(f"[ENGINE] Provider: {os.getenv('LLM_PROVIDER', 'mock')}")

        # Step 1: L1 Planning
        if self.verbose:
            print("[L1] Generating task plan...")
        planned_tasks = self.l1.plan(message)
        if self.verbose:
            print(f"[L1] Planned {len(planned_tasks)} tasks")

        # Step 2: Execute tasks in dependency order
        executed_tasks = self._execute_tasks(planned_tasks, message)
        return OrchestrationResult(
            message=message,
            planned_tasks=planned_tasks,
            executed_tasks=executed_tasks,
        )
    def _execute_tasks(
        self,
        planned_tasks: List[PlannedTask],
        message: InputMessage,
    ) -> List[ExecutedTask]:
        """
        Execute tasks respecting dependency order.
        Accumulates context from completed tasks.
        """
        # Build task map for dependency resolution
        task_map = {t.task_id: t for t in planned_tasks}
        executed_map: Dict[str, ExecutedTask] = {}
        executed_list: List[ExecutedTask] = []
        # Topological sort by dependency order
        execution_order = self._topological_sort(planned_tasks)
        for task_id in execution_order:
            planned = task_map.get(task_id)
            if not planned:
                continue
            if self.verbose:
                print(f"[EXEC] {task_id} → {planned.target}")
            # Accumulate context from completed dependency tasks
            context = self._build_context(planned, executed_map)
            # Execute based on task type
            if planned.task_type == TaskType.CROSS_CUTTING:
                result = self.cross_cutting.execute(planned, message, context)
            else:
                result = self.l2.execute(planned, message, context)
            executed_map[task_id] = result
            executed_list.append(result)
        return executed_list
    def _build_context(
        self,
        task: PlannedTask,
        executed_map: Dict[str, ExecutedTask],
    ) -> Dict[str, Any]:
        """Build context dict from outputs of dependency tasks."""
        accumulated = []
        for dep_id in task.depends_on:
            dep = executed_map.get(dep_id)
            if not dep:
                continue
            if dep.task_type == TaskType.CROSS_CUTTING:
                if dep.output_lines:
                    accumulated.append(f"[{dep_id} output]: " + "; ".join(dep.output_lines[:5]))
            else:
                for l3r in dep.l3_results:
                    if l3r.output_lines:
                        accumulated.append(
                            f"[{l3r.sub_task_id} {l3r.agent_name}]: "
                            + "; ".join(l3r.output_lines[:5])
                        )
        return {"accumulated_context": "\n".join(accumulated)}
    def _topological_sort(self, tasks: List[PlannedTask]) -> List[str]:
        """
        Kahn's algorithm topological sort for dependency resolution.
        Tasks with no dependencies execute first.
        """
        from collections import defaultdict, deque

        in_degree = {t.task_id: 0 for t in tasks}
        adj = defaultdict(list)

        for t in tasks:
            for dep in t.depends_on:
                if dep in in_degree:
                    adj[dep].append(t.task_id)
                    in_degree[t.task_id] += 1

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        order = []
        while queue:
            tid = queue.popleft()
            order.append(tid)
            for neighbor in adj[tid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        # Add any remaining (handles cycles gracefully)
        for t in tasks:
            if t.task_id not in order:
                order.append(t.task_id)
        return order
