from __future__ import annotations

from collections.abc import Sequence


class BaseLLMProvider:
    def generate_answer(self, question: str, contexts: Sequence[dict]) -> str:
        raise NotImplementedError

    def summarize_agent_run(self, goal: str, tool_outputs: Sequence[dict]) -> str:
        raise NotImplementedError

    def draft_tasks(self, requirement: str, contexts: Sequence[dict]) -> list[dict]:
        raise NotImplementedError


class DeterministicLLMProvider(BaseLLMProvider):
    def generate_answer(self, question: str, contexts: Sequence[dict]) -> str:
        if not contexts:
            return "I could not find enough indexed workspace knowledge to answer this question."
        lines = [f"Question: {question}", "Relevant workspace knowledge:"]
        for index, item in enumerate(contexts[:3], start=1):
            snippet = item["content"][:220]
            lines.append(f"{index}. [{item['filename']}] {snippet}")
        lines.append("Answer: Based on the retrieved workspace documents, the evidence is summarized above.")
        return "\n".join(lines)

    def summarize_agent_run(self, goal: str, tool_outputs: Sequence[dict]) -> str:
        lines = [f"Goal: {goal}", "Execution summary:"]
        for item in tool_outputs:
            lines.append(f"- {item['tool_name']}: {item['summary']}")
        if len(tool_outputs) == 0:
            lines.append("- No tools were executed.")
        lines.append("Recommended next step: review the task drafts or risk notes before creating records.")
        return "\n".join(lines)

    def draft_tasks(self, requirement: str, contexts: Sequence[dict]) -> list[dict]:
        seed_text = requirement.strip().splitlines()[0][:80]
        references = ", ".join(item["filename"] for item in contexts[:2]) if contexts else "requirement only"
        return [
            {
                "title": f"Clarify scope: {seed_text[:40]}",
                "description": f"Refine acceptance criteria and dependencies based on {references}.",
                "priority": 3,
                "rationale": "A scoped task reduces ambiguity before implementation begins.",
            },
            {
                "title": f"Implement core workflow for {seed_text[:30]}",
                "description": "Deliver the main backend flow, include permission checks and persistence changes.",
                "priority": 4,
                "rationale": "This is the primary delivery item implied by the requirement.",
            },
            {
                "title": "Add tests and operational checks",
                "description": "Cover the happy path, permission isolation, and failure handling.",
                "priority": 2,
                "rationale": "The project should demonstrate engineering rigor, not only generated output.",
            },
        ]
