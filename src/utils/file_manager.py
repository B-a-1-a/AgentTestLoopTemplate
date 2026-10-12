from __future__ import annotations

from pathlib import Path


class WorkspacePathError(ValueError):
    pass


class WorkspaceFileManager:
    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, rel_path: str) -> Path:
        candidate = (self.workspace_root / rel_path).resolve()
        if not str(candidate).startswith(str(self.workspace_root)):
            raise WorkspacePathError("Path escapes workspace root")
        return candidate

    def list_files(self, rel_path: str = ".") -> list[str]:
        target = self.resolve_path(rel_path)
        if target.is_file():
            return [str(target.relative_to(self.workspace_root))]
        files: list[str] = []
        for p in sorted(target.rglob("*")):
            if p.is_file():
                files.append(str(p.relative_to(self.workspace_root)))
        return files

    def read_text(self, rel_path: str) -> str:
        path = self.resolve_path(rel_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(rel_path)
        return path.read_text(encoding="utf-8")

    def write_text(self, rel_path: str, content: str) -> str:
        path = self.resolve_path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.workspace_root))
