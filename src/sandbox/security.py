from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SandboxSecurityConfig:
    memory: str = "256m"
    cpus: float = 0.5
    pids_limit: int = 64
    network: str = "sandbox-net"
    no_new_privileges: bool = True
    cap_drop_all: bool = True
