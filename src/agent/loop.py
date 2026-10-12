from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.agent.parser import ParseResult, parse_agent_response
from src.agent.tools import ToolContext, available_tool_schemas, execute_tool
from src.providers.registry import ProviderRegistry
from src.sandbox.manager import SandboxManager
from src.utils.file_manager import WorkspaceFileManager


@dataclass
class AgentLoopResult:
    final_answer: str
    stop_reason: str
    iterations: int
    trace: list[dict[str, Any]] = field(default_factory=list)


class AgentLoopEngine:
    def __init__(self, registry: ProviderRegistry, workspace_root: str = "workspace") -> None:
        self.registry = registry
        self.workspace_root = workspace_root

    def run(
        self,
        *,
        provider_name: str,
        model_id: str,
        user_query: str,
        system_prompt: str,
        max_iterations: int,
        params: dict[str, Any],
        sandbox_manager: SandboxManager,
    ) -> AgentLoopResult:
        provider = self.registry.get_provider(provider_name)
        snapshot = self.registry.validate_models_from_api()
        remote_ids: list[str] = []
        for status in snapshot.provider_statuses:
            if status.provider == provider_name:
                remote_ids = status.available_remote_models
                break

        model_resolution = self.registry.resolve_model_id(provider_name, model_id, remote_ids)
        selected_model = model_resolution.selected_model_id

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        file_manager = WorkspaceFileManager(self.workspace_root)
        context = ToolContext(file_manager=file_manager, sandbox_manager=sandbox_manager)
        trace: list[dict[str, Any]] = [
            {
                "event": "model_resolution",
                "requested_model": model_id,
                "selected_model": selected_model,
                "used_fallback": model_resolution.used_fallback,
                "reason": model_resolution.reason,
            }
        ]

        for i in range(max_iterations):
            provider_response = provider.chat(
                messages=messages,
                model=selected_model,
                params=params,
                tools=available_tool_schemas(),
            )
            trace.append({"event": "provider_response", "iteration": i + 1, "text": provider_response.text})

            parsed: ParseResult = parse_agent_response(provider_response.text)
            if parsed.error:
                return AgentLoopResult(
                    final_answer=provider_response.text,
                    stop_reason=f"parse_error: {parsed.error}",
                    iterations=i + 1,
                    trace=trace,
                )

            if not parsed.tool_calls:
                final_answer = parsed.final_answer or provider_response.text
                return AgentLoopResult(
                    final_answer=final_answer,
                    stop_reason="final_answer",
                    iterations=i + 1,
                    trace=trace,
                )

            messages.append({"role": "assistant", "content": provider_response.text})
            for call in parsed.tool_calls:
                result = execute_tool(call, context)
                trace.append({"event": "tool_result", "iteration": i + 1, "tool": call.name, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps({"id": call.id, "name": call.name, "result": result}),
                    }
                )

        return AgentLoopResult(
            final_answer="Reached max iterations without final answer.",
            stop_reason="max_iterations",
            iterations=max_iterations,
            trace=trace,
        )
