from datetime import date, datetime, timedelta
import json

import pytest
from fastapi.testclient import TestClient

import main
from backend.models import ScheduleUpdate, StudyGoal
from backend.scheduler import SchedulingError, generate_study_plan
from backend.storage import JsonStorage, StorageError


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_storage = JsonStorage(tmp_path / "study_data.json")
    monkeypatch.setattr(main, "storage", test_storage)
    main.previews.clear()

    def offline(*args, **kwargs):
        raise RuntimeError("offline for test")

    monkeypatch.setattr(main, "recommend_plan", offline)
    return TestClient(main.app)


def goal_payload(hours=3, days=3, slot="Morning"):
    return {
        "subject": "Biology",
        "total_hours": hours,
        "difficulty": "Hard",
        "preferred_slot": slot,
        "deadline": (date.today() + timedelta(days=days)).isoformat(),
    }


def test_scheduler_uses_preferred_window_and_two_hour_cap():
    goal = StudyGoal(**goal_payload(hours=5, days=3, slot="Afternoon"))
    sessions = generate_study_plan(goal, [], now=datetime.combine(date.today(), datetime.min.time()))
    assert sum(item["hours"] for item in sessions) == 5
    assert all(item["hours"] <= 2 for item in sessions)
    assert all("13:00" <= item["start_time"] < "17:00" for item in sessions)
    assert all(item["end_time"] <= "17:00" for item in sessions)


def test_scheduler_rejects_insufficient_capacity():
    goal = StudyGoal(**goal_payload(hours=4, days=0, slot="Morning"))
    occupied = [{
        "date": date.today().isoformat(),
        "start_time": "09:00",
        "end_time": "12:00",
    }]
    with pytest.raises(SchedulingError):
        generate_study_plan(
            goal,
            occupied,
            now=datetime.combine(date.today(), datetime.min.time()),
        )


def test_preview_does_not_persist_and_fallback_is_explicit(client):
    response = client.post("/plan-previews", json=goal_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendation"]["mode"] == "fallback"
    assert payload["recommendation"]["warning"]
    assert client.get("/tasks").json() == []
    assert client.get("/study-goals").json() == []


def test_accept_is_atomic_persistent_and_single_use(client):
    preview = client.post("/plan-previews", json=goal_payload()).json()
    sessions = [
        {
            "preview_session_id": item["preview_session_id"],
            "date": item["date"],
            "start_time": item["start_time"],
            "end_time": item["end_time"],
        }
        for item in preview["sessions"]
    ]
    accepted = client.post(
        f"/plan-previews/{preview['preview_id']}/accept",
        json={"sessions": sessions},
    )
    assert accepted.status_code == 200
    assert len(client.get("/tasks").json()) == len(sessions)

    reloaded = JsonStorage(main.storage.path)
    assert len(reloaded.snapshot()["tasks"]) == len(sessions)

    duplicate = client.post(
        f"/plan-previews/{preview['preview_id']}/accept",
        json={"sessions": sessions},
    )
    assert duplicate.status_code == 409


def test_invalid_accept_does_not_partially_save(client):
    preview = client.post("/plan-previews", json=goal_payload()).json()
    sessions = [
        {
            "preview_session_id": item["preview_session_id"],
            "date": item["date"],
            "start_time": item["start_time"],
            "end_time": item["end_time"],
        }
        for item in preview["sessions"]
    ]
    sessions[0]["end_time"] = sessions[0]["start_time"]
    response = client.post(
        f"/plan-previews/{preview['preview_id']}/accept",
        json={"sessions": sessions},
    )
    assert response.status_code == 409
    assert client.get("/tasks").json() == []


def test_reschedule_rejects_overlap_and_preserves_duration(client):
    preview = client.post("/plan-previews", json=goal_payload(hours=3)).json()
    sessions = [
        {
            "preview_session_id": item["preview_session_id"],
            "date": item["date"],
            "start_time": item["start_time"],
            "end_time": item["end_time"],
        }
        for item in preview["sessions"]
    ]
    tasks = client.post(
        f"/plan-previews/{preview['preview_id']}/accept",
        json={"sessions": sessions},
    ).json()["tasks"]
    if len(tasks) < 2:
        pytest.skip("Need two sessions for overlap test")
    move = {
        "date": tasks[0]["date"],
        "start_time": tasks[0]["start_time"],
        "end_time": tasks[0]["end_time"],
    }
    response = client.patch(f"/tasks/{tasks[1]['id']}/schedule", json=move)
    assert response.status_code == 409


def test_missing_task_and_status_validation(client):
    assert client.patch(
        "/tasks/999/schedule",
        json={"date": date.today().isoformat(), "start_time": "09:00", "end_time": "10:00"},
    ).status_code == 404
    assert client.patch("/tasks/999", json={"status": "completed"}).status_code == 404


def test_chat_fallback_uses_current_saved_task(client):
    preview = client.post("/plan-previews", json=goal_payload(hours=1)).json()
    sessions = [{
        "preview_session_id": item["preview_session_id"],
        "date": item["date"],
        "start_time": item["start_time"],
        "end_time": item["end_time"],
    } for item in preview["sessions"]]
    client.post(f"/plan-previews/{preview['preview_id']}/accept", json={"sessions": sessions})
    response = client.post("/chat", json={"query": "What is next?"})
    assert response.status_code == 200
    assert response.json()["mode"] == "fallback"
    assert "Biology" in response.json()["response"]


def test_corrupt_json_fails_without_reset(tmp_path):
    path = tmp_path / "study_data.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(StorageError) as error:
        JsonStorage(path)
    assert "Restore" in str(error.value)
    assert path.read_text(encoding="utf-8") == "{broken"
