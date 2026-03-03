from __future__ import annotations


def build_agent_memory(goal: str, tool_outputs: list[dict]) -> dict:
    return {
        "goal": goal,
        "steps": len(tool_outputs),
        "tool_names": [item["tool_name"] for item in tool_outputs],
    }
