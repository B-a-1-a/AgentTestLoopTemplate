from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sandbox.callback_server import CallbackServer
from src.sandbox.security import SandboxSecurityConfig


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
        }


class SandboxManager:
    def __init__(
        self,
        *,
        image: str = "agent-loop-sandbox:latest",
        callback_host: str = "127.0.0.1",
        callback_port: int = 8765,
        security: SandboxSecurityConfig | None = None,
    ) -> None:
        self.image = image
        self.callback_host = callback_host
        self.callback_port = callback_port
        self.security = security or SandboxSecurityConfig()
        self.callback_server = CallbackServer(host=self.callback_host, port=self.callback_port)
        self.callback_server.start()

    def run_python(self, *, code: str, timeout_s: int = 30) -> SandboxResult:
        execution_id = uuid.uuid4().hex
        callback_url = f"http://host.docker.internal:{self.callback_port}/result/{execution_id}"

        with tempfile.TemporaryDirectory(prefix="agent_sandbox_") as temp_dir:
            code_path = Path(temp_dir) / "code.py"
            code_path.write_text(code, encoding="utf-8")

            container_name = f"agent-sandbox-{execution_id[:12]}"
            cmd = [
                "docker",
                "run",
                "--rm",
                "--name",
                container_name,
                "--memory",
                self.security.memory,
                "--cpus",
                str(self.security.cpus),
                "--pids-limit",
                str(self.security.pids_limit),
                "--security-opt",
                "no-new-privileges",
                "--cap-drop",
                "ALL",
                "--network",
                self.security.network,
                "-e",
                f"CALLBACK_URL={callback_url}",
                "-e",
                f"EXECUTION_ID={execution_id}",
                "-e",
                f"EXECUTION_TIMEOUT={timeout_s}",
                "-v",
                f"{code_path}:/sandbox/code.py:ro",
                self.image,
            ]

            try:
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s + 10,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                self._cleanup_container(container_name)
                return SandboxResult(stdout="", stderr="Sandbox container timeout", exit_code=124, timed_out=True)

            callback_payload = self.callback_server.await_result(execution_id, timeout=2.0)
            if callback_payload:
                return SandboxResult(
                    stdout=str(callback_payload.get("stdout", "")),
                    stderr=str(callback_payload.get("stderr", "")),
                    exit_code=int(callback_payload.get("exit_code", process.returncode)),
                    timed_out=bool(callback_payload.get("timed_out", False)),
                )

            return SandboxResult(
                stdout=process.stdout,
                stderr=(process.stderr or "") + "\nNo callback payload received.",
                exit_code=process.returncode,
                timed_out=False,
            )

    @staticmethod
    def _cleanup_container(container_name: str) -> None:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True, check=False)
