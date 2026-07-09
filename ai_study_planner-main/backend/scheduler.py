"""
Services to generate the study plan based on the user's goals and preferences.
"""


def generate_study_plan(
    subject,
    total_hours,
    difficulty,
    preferred_slot,
    deadline
):

    plan = []

    remaining = total_hours
    day = 1

    while remaining > 0:

        session_hours = min(
            2,
            remaining
        )

        plan.append({
            "day": day,
            "subject": subject,
            "hours": session_hours,
            "difficulty": difficulty,
            "preferred_slot": preferred_slot,
            "deadline": deadline
        })

        remaining -= session_hours
        day += 1

    return plan