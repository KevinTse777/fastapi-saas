from __future__ import annotations

from app.services.agents.guardrails import MAX_AGENT_STEPS


def plan_tools(goal: str) -> list[str]:
    lowered = goal.lower()
    plan: list[str] = []

    if any(token in lowered for token in ("doc", "knowledge", "requirement", "spec", "文档", "需求")):
        plan.append("search_knowledge")
    if any(token in lowered for token in ("task", "tasks", "todo", "risk", "blocked", "进度", "风险")):
        plan.append("list_project_tasks")
    if any(token in lowered for token in ("dashboard", "status", "summary", "report", "周报", "汇总")):
        plan.append("summarize_workspace_dashboard")
    if any(token in lowered for token in ("draft", "breakdown", "split", "任务拆解", "草稿")):
        plan.append("create_task_draft")

    if not plan:
        plan = ["search_knowledge", "list_project_tasks", "summarize_workspace_dashboard"]

    deduped: list[str] = []
    for tool_name in plan:
        if tool_name not in deduped:
            deduped.append(tool_name)
    return deduped[:MAX_AGENT_STEPS]
