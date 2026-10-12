from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agent.parser import ToolCall
from src.sandbox.manager import SandboxManager
from src.utils.file_manager import WorkspaceFileManager, WorkspacePathError


@dataclass
class ToolContext:
    file_manager: WorkspaceFileManager
    sandbox_manager: SandboxManager


def available_tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": "list_files",
            "description": "List files under workspace path",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": [],
            },
        },
        {
            "name": "read_file",
            "description": "Read text file under workspace",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "write_file",
            "description": "Write text to file under workspace",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "run_code",
            "description": "Run Python code in Docker sandbox",
            "input_schema": {
                "type": "object",
                "properties": {"code": {"type": "string"}, "timeout_s": {"type": "integer"}},
                "required": ["code"],
            },
        },
    ]


def execute_tool(call: ToolCall, context: ToolContext) -> dict[str, Any]:
    try:
        if call.name == "list_files":
            path = str(call.arguments.get("path", "."))
            return {"ok": True, "files": context.file_manager.list_files(path)}

        if call.name == "read_file":
            path = str(call.arguments["path"])
            return {"ok": True, "path": path, "content": context.file_manager.read_text(path)}

        if call.name == "write_file":
            path = str(call.arguments["path"])
            content = str(call.arguments["content"])
            stored = context.file_manager.write_text(path, content)
            return {"ok": True, "path": stored}

        if call.name == "run_code":
            code = str(call.arguments["code"])
            timeout_s = int(call.arguments.get("timeout_s", 30))
            result = context.sandbox_manager.run_python(code=code, timeout_s=timeout_s)
            return {"ok": True, "result": result.to_dict()}

        return {"ok": False, "error": f"Unknown tool: {call.name}"}
    except KeyError as exc:
        return {"ok": False, "error": f"Missing argument: {exc}"}
    except WorkspacePathError as exc:
        return {"ok": False, "error": str(exc)}
    except FileNotFoundError as exc:
        return {"ok": False, "error": f"File not found: {exc}"}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": f"Tool execution failed: {exc}"}
