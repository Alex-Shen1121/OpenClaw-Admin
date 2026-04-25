"""Session state with undo/redo for OpenClaw Admin config changes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SESSION_FILE = ".openclaw-admin-cli-session.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SessionState:
    history: list[dict[str, Any]] = field(default_factory=list)
    undone: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, root: Path) -> "SessionState":
        path = root / SESSION_FILE
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(history=data.get("history", []), undone=data.get("undone", []))

    def save(self, root: Path) -> Path:
        path = root / SESSION_FILE
        payload = {"history": self.history, "undone": self.undone}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def record_config_change(self, root: Path, label: str, env_file: str, before: str | None, after: str | None) -> None:
        self.history.append(
            {
                "type": "config",
                "label": label,
                "envFile": env_file,
                "before": before,
                "after": after,
                "createdAt": utc_now(),
            }
        )
        self.undone.clear()
        self.save(root)

    def undo(self, root: Path) -> dict[str, Any]:
        if not self.history:
            raise RuntimeError("No config change to undo.")
        item = self.history.pop()
        self._restore(root, item["envFile"], item.get("before"))
        self.undone.append(item)
        self.save(root)
        return item

    def redo(self, root: Path) -> dict[str, Any]:
        if not self.undone:
            raise RuntimeError("No config change to redo.")
        item = self.undone.pop()
        self._restore(root, item["envFile"], item.get("after"))
        self.history.append(item)
        self.save(root)
        return item

    def status(self) -> dict[str, Any]:
        return {
            "historyCount": len(self.history),
            "redoCount": len(self.undone),
            "last": self.history[-1] if self.history else None,
        }

    @staticmethod
    def _restore(root: Path, env_file: str, content: str | None) -> None:
        path = root / env_file
        if content is None:
            if path.exists():
                path.unlink()
            return
        path.write_text(content, encoding="utf-8")
