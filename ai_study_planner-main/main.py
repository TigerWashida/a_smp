from fastapi import FastAPI, HTTPException

from backend.models import StudyGoal, ChatRequest
from backend.scheduler import generate_study_plan
from backend.storage import study_goals, tasks

from fastapi.middleware.cors import CORSMiddleware

from llm import llm_chat


app = FastAPI(
    title="Study Planner API",
    description="API to create and manage study plans based on user goals and preferences.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# SLOT LIMITS
# =====================================

SLOT_LIMITS = {
    "Morning": 3,
    "Afternoon": 3,
    "Evening": 3
}


def get_existing_slot_hours(
    preferred_slot: str
):

    total = 0

    for task in tasks:

        if task["preferred_slot"] == preferred_slot:

            total += task["hours"]

    return total


# =====================================
# HEALTH CHECK
# =====================================

@app.get("/")
async def health_check():

    return {
        "status": "running"
    }


# =====================================
# CREATE STUDY PLAN
# =====================================

@app.post("/generate-plan")
async def create_study_plan(
    goal: StudyGoal
):

    existing_slot_hours = get_existing_slot_hours(
        goal.preferred_slot
    )

    slot_limit = SLOT_LIMITS.get(
        goal.preferred_slot,
        3
    )

    if existing_slot_hours + goal.total_hours > slot_limit:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot create this plan because "
                f"{goal.preferred_slot} already has "
                f"{existing_slot_hours} planned hours. "
                f"Each section can only have a maximum of "
                f"{slot_limit} hours."
            )
        )

    study_goals.append(
        goal.model_dump()
    )

    plan = generate_study_plan(
        goal.subject,
        goal.total_hours,
        goal.difficulty,
        goal.preferred_slot,
        goal.deadline
    )

    for item in plan:

        tasks.append({
            "id": len(tasks) + 1,
            "day": item["day"],
            "subject": item["subject"],
            "hours": item["hours"],
            "difficulty": item["difficulty"],
            "preferred_slot": item["preferred_slot"],
            "deadline": item["deadline"],
            "status": "pending"
        })

    return {
        "message": "Study plan created successfully",
        "plan": plan
    }


# =====================================
# GET TASKS
# =====================================

@app.get("/tasks")
async def get_tasks():

    return tasks


# =====================================
# UPDATE TASK STATUS
# =====================================

@app.patch("/tasks/{task_id}")
async def update_task(
    task_id: int
):

    for task in tasks:

        if task["id"] == task_id:

            if task["status"] == "completed":

                task["status"] = "pending"

            else:

                task["status"] = "completed"

            return {
                "message": "Task updated successfully",
                "task": task
            }

    raise HTTPException(
        status_code=404,
        detail="Task not found"
    )


# =====================================
# DASHBOARD
# =====================================

@app.get("/dashboard")
async def get_dashboard():

    subjects = len(
        set(
            goal["subject"]
            for goal in study_goals
        )
    )

    planned_hours = sum(
        goal["total_hours"]
        for goal in study_goals
    )

    completed_hours = sum(
        task["hours"]
        for task in tasks
        if task["status"] == "completed"
    )

    progress = 0

    if planned_hours > 0:

        progress = round(
            (completed_hours / planned_hours) * 100
        )

    return {
        "subjects": subjects,
        "planned_hours": planned_hours,
        "completed_hours": completed_hours,
        "progress": progress
    }


# =====================================
# RECOMMENDATIONS
# =====================================

@app.get("/recommendations")
async def get_recommendations():

    total_tasks = len(tasks)

    completed_tasks = len([
        task
        for task in tasks
        if task["status"] == "completed"
    ])

    pending_tasks = total_tasks - completed_tasks

    progress = 0

    if total_tasks > 0:

        progress = round(
            (completed_tasks / total_tasks) * 100
        )

    if progress < 30:

        recommendation = (
            "⚠️ You are behind schedule. Complete at least one study session today."
        )

    elif progress < 70:

        recommendation = (
            "📚 Good progress. Focus on completing pending tasks."
        )

    elif progress < 100:

        recommendation = (
            "🔥 Great work! You're almost finished."
        )

    else:

        recommendation = (
            "🎉 Congratulations! All study sessions completed."
        )

    return {
        "progress": progress,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "total_tasks": total_tasks,
        "recommendation": recommendation
    }


# =====================================
# CHAT
# =====================================

@app.post("/chat")
async def chat(
    request: ChatRequest
):

    response = llm_chat(
        request.query
    )

    return {
        "response": response
    }