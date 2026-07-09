"""
services to generate the study plan based on the user's goals and preferences.
"""

"""
services to generate the study plan based on the user's goals and preferences.
"""


def get_start_hour(preferred_slot):

    if preferred_slot == "Morning":
        return 9

    if preferred_slot == "Afternoon":
        return 13

    if preferred_slot == "Evening":
        return 18

    return 9


def has_overlap(new_start, new_end, existing_tasks):

    for task in existing_tasks:

        existing_start = task.get("start_hour")
        existing_end = task.get("end_hour")

        if existing_start is None or existing_end is None:
            continue

        if new_start < existing_end and new_end > existing_start:
            return True

    return False


def generate_study_plan(
    subject,
    total_hours,
    difficulty,
    preferred_slot,
    exam_date,
    existing_tasks=None
):

    if existing_tasks is None:
        existing_tasks = []

    plan = []

    remaining = total_hours
    day = 1

    current_start_hour = get_start_hour(preferred_slot)

    while remaining > 0:

        session_hours = min(2, remaining)

        start_hour = current_start_hour
        end_hour = start_hour + session_hours

        if end_hour > 24:
            raise ValueError(
                "Study plan cannot be created because it goes past the end of the day."
            )

        if has_overlap(start_hour, end_hour, existing_tasks + plan):
            raise ValueError(
                "Study plan cannot be created because it overlaps with an existing session."
            )

        plan.append({
            "day": day,
            "subject": subject,
            "hours": session_hours,
            "difficulty": difficulty,
            "preferred_slot": preferred_slot,
            "start_hour": start_hour,
            "end_hour": end_hour
        })

        remaining -= session_hours
        current_start_hour = end_hour
        day += 1

    return plan