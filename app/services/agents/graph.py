from __future__ import annotations

from app.services.agents.executor import execute_tool
from app.services.agents.planner import plan_tools
from app.services.llm.client import get_llm_provider


def run_controlled_agent(
    *,
    db,
    workspace_id: int,
    project_id: int,
    goal: str,
) -> tuple[list[dict], str]:
    tool_plan = plan_tools(goal)
    outputs: list[dict] = []
    for tool_name in tool_plan:
        result = execute_tool(
            tool_name,
            db=db,
            workspace_id=workspace_id,
            project_id=project_id,
            goal=goal,
        )
        outputs.append(result)

    provider = get_llm_provider()
    final_output = provider.summarize_agent_run(goal, outputs)
    return outputs, final_output
