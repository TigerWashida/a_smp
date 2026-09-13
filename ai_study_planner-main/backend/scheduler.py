from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable
from uuid import uuid4


SLOT_WINDOWS = {
    "Morning": (time(9, 0), time(12, 0)),
    "Afternoon": (time(13, 0), time(17, 0)),
    "Evening": (time(18, 0), time(21, 0)),
}
STEP = timedelta(minutes=30)
MAX_SESSION_HOURS = 2.0


class SchedulingError(ValueError):
    pass


def parse_clock(value: str) -> time:
    try:
        parsed = datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError) as exc:
        raise SchedulingError("Times must use 24-hour HH:MM format.") from exc
    if parsed.minute not in (0, 30) or parsed.second or parsed.microsecond:
        raise SchedulingError("Times must be on a 30-minute boundary.")
    return parsed


def combine(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock)


def overlap(start: datetime, end: datetime, other_start: datetime, other_end: datetime) -> bool:
    return start < other_end and other_start < end


def task_interval(task: dict) -> tuple[datetime, datetime] | None:
    try:
        day = date.fromisoformat(str(task["date"]))
        return combine(day, parse_clock(str(task["start_time"]))), combine(
            day, parse_clock(str(task["end_time"]))
        )
    except (KeyError, TypeError, ValueError, SchedulingError):
        return None


def ceil_half_hour(moment: datetime) -> datetime:
    moment = moment.replace(second=0, microsecond=0)
    remainder = moment.minute % 30
    if remainder:
        moment += timedelta(minutes=30 - remainder)
    return moment


def _available(candidate_start: datetime, candidate_end: datetime, occupied: Iterable[tuple[datetime, datetime]]) -> bool:
    return all(not overlap(candidate_start, candidate_end, start, end) for start, end in occupied)


def generate_study_plan(goal, existing_tasks: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    if goal.deadline < now.date():
        raise SchedulingError("The deadline is in the past.")

    occupied = [interval for task in existing_tasks if (interval := task_interval(task))]
    sessions: list[dict] = []
    remaining = float(goal.total_hours)
    window_start, window_end = SLOT_WINDOWS[goal.preferred_slot]
    day = now.date()

    while remaining > 0.0001:
        duration_hours = min(MAX_SESSION_HOURS, remaining)
        duration = timedelta(minutes=round(duration_hours * 2) * 30)
        placed = False
        scan_day = day

        while scan_day <= goal.deadline and not placed:
            candidate = combine(scan_day, window_start)
            if scan_day == now.date():
                candidate = max(candidate, ceil_half_hour(now))
            latest_end = combine(scan_day, window_end)
            while candidate + duration <= latest_end:
                candidate_end = candidate + duration
                if _available(candidate, candidate_end, occupied):
                    session = {
                        "preview_session_id": str(uuid4()),
                        "date": scan_day.isoformat(),
                        "start_time": candidate.strftime("%H:%M"),
                        "end_time": candidate_end.strftime("%H:%M"),
                        "subject": goal.subject,
                        "hours": duration.total_seconds() / 3600,
                        "difficulty": goal.difficulty,
                        "preferred_slot": goal.preferred_slot,
                        "deadline": goal.deadline.isoformat(),
                        "status": "pending",
                    }
                    sessions.append(session)
                    occupied.append((candidate, candidate_end))
                    remaining -= session["hours"]
                    placed = True
                    break
                candidate += STEP
            scan_day += timedelta(days=1)

        if not placed:
            raise SchedulingError(
                "There is not enough free time in the preferred slot before the deadline."
            )

    return sessions


def validate_adjusted_sessions(
    goal,
    expected_sessions: list[dict],
    updates: list,
    existing_tasks: list[dict],
    now: datetime | None = None,
) -> list[dict]:
    now = now or datetime.now()
    expected = {item["preview_session_id"]: item for item in expected_sessions}
    if len(updates) != len(expected) or {item.preview_session_id for item in updates} != set(expected):
        raise SchedulingError("The accepted plan must contain every recommended session exactly once.")

    occupied = [interval for task in existing_tasks if (interval := task_interval(task))]
    accepted: list[dict] = []
    total = 0.0

    for update in updates:
        original = expected[update.preview_session_id]
        start_clock, end_clock = parse_clock(update.start_time), parse_clock(update.end_time)
        start, end = combine(update.date, start_clock), combine(update.date, end_clock)
        expected_minutes = round(float(original["hours"]) * 60)
        if end <= start or int((end - start).total_seconds() / 60) != expected_minutes:
            raise SchedulingError("Session duration cannot be changed.")
        if start < now:
            raise SchedulingError("Sessions cannot be scheduled in the past.")
        if update.date > goal.deadline:
            raise SchedulingError("A session is later than the deadline.")
        if not _available(start, end, occupied):
            raise SchedulingError("The adjusted plan overlaps another study session.")
        occupied.append((start, end))
        total += original["hours"]
        accepted.append(
            {
                **original,
                "date": update.date.isoformat(),
                "start_time": update.start_time,
                "end_time": update.end_time,
            }
        )

    if abs(total - float(goal.total_hours)) > 0.001:
        raise SchedulingError("The accepted sessions do not match the requested total hours.")
    return accepted


def validate_task_move(task: dict, update, other_tasks: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now()
    start_clock, end_clock = parse_clock(update.start_time), parse_clock(update.end_time)
    start, end = combine(update.date, start_clock), combine(update.date, end_clock)
    original_minutes = round(float(task["hours"]) * 60)
    if end <= start or int((end - start).total_seconds() / 60) != original_minutes:
        raise SchedulingError("Session duration cannot be changed.")
    if start < now:
        raise SchedulingError("Sessions cannot be moved into the past.")
    if update.date > date.fromisoformat(task["deadline"]):
        raise SchedulingError("This move is later than the goal deadline.")

    occupied = [interval for item in other_tasks if (interval := task_interval(item))]
    if not _available(start, end, occupied):
        raise SchedulingError("This move overlaps another study session.")
    return {
        **task,
        "date": update.date.isoformat(),
        "start_time": update.start_time,
        "end_time": update.end_time,
    }
