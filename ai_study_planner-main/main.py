from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from uuid import uuid4

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.models import (
    AcceptPreviewRequest,
    ChatRequest,
    ScheduleUpdate,
    StudyGoal,
    TaskStatusUpdate,
)
from backend.scheduler import (
    SchedulingError,
    generate_study_plan,
    validate_adjusted_sessions,
    validate_task_move,
)
from backend.storage import StorageError, storage
from llm import (
    answer_chat,
    fallback_chat,
    fallback_recommendation,
    recommend_plan,
)


BASE_DIR = Path(__file__).resolve().parent
PREVIEW_TTL = timedelta(minutes=30)
LLM_TIMEOUT_SECONDS = 12
previews: dict[str, dict] = {}
preview_lock = RLock()

app = FastAPI(title="StudyMate", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")


@app.on_event("startup")
def verify_storage() -> None:
    try:
        storage.snapshot()
    except StorageError as exc:
        raise RuntimeError(str(exc)) from exc


def _prune_previews() -> None:
    now = datetime.now()
    with preview_lock:
        for preview_id in [
            key for key, value in previews.items() if value["expires_at"] <= now
        ]:
            previews.pop(preview_id, None)


async def _recommendation(goal: StudyGoal, sessions: list[dict], state: dict) -> dict:
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(recommend_plan, goal, sessions, state),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if not text:
            raise RuntimeError("Ollama returned an empty response.")
        return {"text": text, "mode": "llm", "warning": None}
    except Exception as exc:
        warning = f"Local AI unavailable: {type(exc).__name__}. A deterministic recommendation is shown."
        return {
            "text": fallback_recommendation(goal, sessions, warning),
            "mode": "fallback",
            "warning": warning,
        }


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "frontend" / "index.html")


@app.get("/application-overview.html")
def application_overview():
    return FileResponse(BASE_DIR / "application-overview.html")


@app.get("/implementation-changes.html")
def implementation_changes():
    return FileResponse(BASE_DIR / "implementation-changes.html")


@app.get("/health")
def health():
    return {"status": "ok", "storage": str(storage.path)}


@app.get("/study-goals")
def get_study_goals():
    return storage.snapshot()["study_goals"]


@app.get("/tasks")
def get_tasks():
    return storage.snapshot()["tasks"]


@app.get("/dashboard")
def dashboard():
    state = storage.snapshot()
    tasks = state["tasks"]
    pending = [task for task in tasks if task.get("status") != "completed"]
    completed = [task for task in tasks if task.get("status") == "completed"]
    return {
        "goals": len(state["study_goals"]),
        "pending_tasks": len(pending),
        "completed_tasks": len(completed),
        "pending_hours": sum(float(task.get("hours", 0)) for task in pending),
    }


@app.post("/plan-previews")
async def create_plan_preview(goal: StudyGoal):
    _prune_previews()
    state = storage.snapshot()
    try:
        sessions = generate_study_plan(goal, state["tasks"])
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    preview_id = str(uuid4())
    created = datetime.now()
    recommendation = await _recommendation(goal, sessions, state)
    record = {
        "preview_id": preview_id,
        "goal": goal,
        "sessions": sessions,
        "recommendation": recommendation,
        "created_at": created,
        "expires_at": created + PREVIEW_TTL,
        "accepted": False,
    }
    with preview_lock:
        previews[preview_id] = record
    return {
        "preview_id": preview_id,
        "goal": goal.model_dump(mode="json"),
        "sessions": sessions,
        "recommendation": recommendation,
        "expires_at": record["expires_at"].isoformat(timespec="seconds"),
    }


@app.post("/plan-previews/{preview_id}/accept")
def accept_plan_preview(preview_id: str, payload: AcceptPreviewRequest):
    _prune_previews()
    with preview_lock:
        record = previews.get(preview_id)
        if not record:
            raise HTTPException(status_code=404, detail="Preview not found or expired.")
        if record["accepted"]:
            raise HTTPException(status_code=409, detail="This preview has already been accepted.")
        state = storage.snapshot()
        try:
            sessions = validate_adjusted_sessions(
                record["goal"], record["sessions"], payload.sessions, state["tasks"]
            )
            goal, tasks = storage.add_plan(
                record["goal"].model_dump(mode="json"), sessions
            )
        except SchedulingError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except StorageError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        record["accepted"] = True
    return {"goal": goal, "tasks": tasks}


@app.post("/generate-plan", deprecated=True)
async def generate_plan_compatibility(goal: StudyGoal):
    state = storage.snapshot()
    try:
        sessions = generate_study_plan(goal, state["tasks"])
        saved_goal, saved_tasks = storage.add_plan(
            goal.model_dump(mode="json"), sessions
        )
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "goal": saved_goal,
        "tasks": saved_tasks,
        "deprecated": True,
        "warning": "Use /plan-previews and then accept the preview.",
    }


@app.patch("/tasks/{task_id}")
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate | None = Body(default=None),
    status: str | None = Query(default=None),
):
    chosen = payload.status if payload else status
    if chosen not in {"pending", "completed"}:
        raise HTTPException(status_code=422, detail="Status must be pending or completed.")
    state = storage.snapshot()
    task = next((item for item in state["tasks"] if int(item.get("id", -1)) == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    replacement = {**task, "status": chosen}
    try:
        return storage.update_task(task_id, replacement)
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.patch("/tasks/{task_id}/schedule")
def update_task_schedule(task_id: int, payload: ScheduleUpdate):
    state = storage.snapshot()
    task = next((item for item in state["tasks"] if int(item.get("id", -1)) == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    others = [item for item in state["tasks"] if int(item.get("id", -1)) != task_id]
    try:
        replacement = validate_task_move(task, payload, others)
        return storage.update_task(task_id, replacement)
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/recommendations")
def recommendations():
    state = storage.snapshot()
    pending = [task for task in state["tasks"] if task.get("status") != "completed"]
    if not pending:
        return {"text": "Create a study goal to receive a recommendation.", "mode": "fallback", "warning": None}
    pending.sort(key=lambda item: (item["date"], item["start_time"]))
    next_task = pending[0]
    return {
        "text": f"Next, study {next_task['subject']} on {next_task['date']} at {next_task['start_time']}.",
        "mode": "fallback",
        "warning": "This quick recommendation is calculated from saved tasks.",
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    state = storage.snapshot()
    preview_sessions = None
    if request.preview_id:
        _prune_previews()
        with preview_lock:
            preview = previews.get(request.preview_id)
            preview_sessions = preview["sessions"] if preview else None
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(answer_chat, request.query, state, preview_sessions),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if not response:
            raise RuntimeError("Ollama returned an empty response.")
        return {"response": response, "mode": "llm", "warning": None}
    except Exception as exc:
        warning = f"Local AI unavailable: {type(exc).__name__}. A schedule-based answer is shown."
        return {
            "response": fallback_chat(request.query, state, preview_sessions),
            "mode": "fallback",
            "warning": warning,
        }
