from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock


class StorageError(RuntimeError):
    pass


class JsonStorage:
    def __init__(self, path: str | Path | None = None):
        default = Path(__file__).resolve().parents[1] / "data" / "study_data.json"
        self.path = Path(path or os.getenv("STUDYMATE_DATA_FILE", default))
        self._lock = RLock()
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"study_goals": [], "tasks": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StorageError(
                f"Could not read {self.path}. Restore a valid backup or remove the corrupt file after saving a copy."
            ) from exc
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("study_goals"), list)
            or not isinstance(value.get("tasks"), list)
        ):
            raise StorageError(
                f"{self.path} has an invalid structure. Restore it from backup before restarting."
            )
        return value

    def snapshot(self) -> dict:
        with self._lock:
            return json.loads(json.dumps(self._data))

    @staticmethod
    def _next_id(items: list[dict]) -> int:
        return max((int(item.get("id", 0)) for item in items), default=0) + 1

    def _write(self, value: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                json.dump(value, temporary, ensure_ascii=False, indent=2, sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_name = temporary.name
            os.replace(temporary_name, self.path)
        except OSError as exc:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
            raise StorageError(f"Could not save study data to {self.path}.") from exc

    def add_plan(self, goal: dict, sessions: list[dict]) -> tuple[dict, list[dict]]:
        with self._lock:
            value = self.snapshot()
            saved_goal = {**goal, "id": self._next_id(value["study_goals"])}
            next_task = self._next_id(value["tasks"])
            saved_sessions = []
            for offset, session in enumerate(sessions):
                saved = {key: item for key, item in session.items() if key != "preview_session_id"}
                saved["id"] = next_task + offset
                saved_sessions.append(saved)
            value["study_goals"].append(saved_goal)
            value["tasks"].extend(saved_sessions)
            self._write(value)
            self._data = value
            return saved_goal, saved_sessions

    def update_task(self, task_id: int, replacement: dict) -> dict:
        with self._lock:
            value = self.snapshot()
            for index, task in enumerate(value["tasks"]):
                if int(task.get("id", -1)) == task_id:
                    value["tasks"][index] = replacement
                    self._write(value)
                    self._data = value
                    return replacement
            raise KeyError(task_id)


storage = JsonStorage()
