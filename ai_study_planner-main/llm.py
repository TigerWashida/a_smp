from __future__ import annotations

import json
from datetime import date


MODEL_NAME = "llama3.2:3b"


def build_context(state: dict, preview: list[dict] | None = None) -> str:
    payload = {
        "today": date.today().isoformat(),
        "study_goals": state.get("study_goals", []),
        "tasks": state.get("tasks", []),
        "preview": preview or [],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _model():
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=MODEL_NAME,
        temperature=0.2,
        client_kwargs={"timeout": 12.0},
    )


def recommend_plan(goal, sessions: list[dict], state: dict) -> str:
    prompt = (
        "You are StudyMate. Explain this recommended study plan in 2-4 concise sentences. "
        "Refer to the deadline, difficulty, preferred time, and session spacing. "
        "Do not invent facts.\n\n"
        f"New goal:\n{goal.model_dump_json()}\n\n"
        f"Current context:\n{build_context(state, sessions)}"
    )
    response = _model().invoke(prompt)
    return str(response.content).strip()


def answer_chat(query: str, state: dict, preview: list[dict] | None = None) -> str:
    prompt = (
        "You are StudyMate, a concise study-planning assistant. Answer using only the supplied "
        "goals, tasks, preview, and the user's question. Say when information is unavailable.\n\n"
        f"Context:\n{build_context(state, preview)}\n\nQuestion:\n{query}"
    )
    response = _model().invoke(prompt)
    return str(response.content).strip()


def fallback_recommendation(goal, sessions: list[dict], warning: str | None = None) -> str:
    count = len(sessions)
    first = sessions[0]
    last = sessions[-1]
    difficulty_note = {
        "Easy": "Short, regular sessions should keep the work moving.",
        "Medium": "The plan balances steady progress with manageable sessions.",
        "Hard": "Sessions are capped at two hours to reduce fatigue on difficult work.",
    }[goal.difficulty]
    return (
        f"StudyMate placed {goal.total_hours:g} hours across {count} session"
        f"{'s' if count != 1 else ''}, from {first['date']} to {last['date']}, "
        f"before the {goal.deadline.isoformat()} deadline. {difficulty_note} "
        f"The initial recommendation uses the {goal.preferred_slot.lower()} window and avoids saved tasks."
    )


def fallback_chat(query: str, state: dict, preview: list[dict] | None = None) -> str:
    tasks = (preview or []) + state.get("tasks", [])
    pending = [task for task in tasks if task.get("status", "pending") != "completed"]
    if not pending:
        return "There are no pending study sessions in the current plan."
    pending.sort(key=lambda item: (item.get("date", ""), item.get("start_time", "")))
    next_task = pending[0]
    total = sum(float(item.get("hours", 0)) for item in pending)
    return (
        f"You have {len(pending)} pending session{'s' if len(pending) != 1 else ''} "
        f"({total:g} hours). Next: {next_task.get('subject', 'Study')} on "
        f"{next_task.get('date')} at {next_task.get('start_time')}. "
        "The local AI was unavailable, so this answer is calculated from the current schedule."
    )
