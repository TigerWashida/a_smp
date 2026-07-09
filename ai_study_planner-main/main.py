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

@app.get("/")
async def health_check():
    return {"status": "running"}

@app.post("/generate-plan")
async def create_study_plan(goal:StudyGoal):
    # print(goal)
    study_goals.append(goal.model_dump())
    try:

        plan = generate_study_plan(
            goal.subject,
            goal.total_hours,
            goal.difficulty,
            goal.preferred_slot,
            goal.exam_date,
            tasks
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    
    for item in plan:
        tasks.append({
            "id": len(tasks) + 1,
            "day": item["day"],
            "subject": item["subject"],
            "hours": item["hours"],
            "difficulty": item["difficulty"],
            "preferred_slot": item["preferred_slot"],
            "start_hour": item["start_hour"],
            "end_hour": item["end_hour"],
            "status": "pending"
        })

    return {"message": "Study plan created successfully",
             "plan": plan
             }


@app.get("/tasks")
async def get_tasks():
    return tasks


@app.patch("/tasks/{task_id}")
async def update_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            if task["status"] == "completed":
                task["status"] = "pending"
            else:
                task["status"] = "completed"

            return {"message": "Task updated successfully", "task": task}
    
    return HTTPException(status_code=404, detail="Task not found")


@app.get("/dashboard")
async def get_dashboard():
    subjects = len(
        set(
            goal["subject"] for goal in study_goals
            )
    )

    planned_hours = sum(
        goal["total_hours"] for goal in study_goals
    )

    completed_hours = sum(
        task["hours"] for task in tasks if task["status"] == "completed"
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

@app.get("/recommendations")
async def get_recommendations():

    total_tasks = len(tasks)

    completed_tasks = len([
        task for task in tasks
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
    print(recommendation)
    return {

        "progress": progress,

        "completed_tasks": completed_tasks,

        "pending_tasks": pending_tasks,

        "total_tasks": total_tasks,

        "recommendation": recommendation
    }

# @app.get("/recommendations")
# async def get_recommendations():

#     recommendations = []

#     pending_tasks = [
#         task for task in tasks
#         if task["status"] == "pending"
#     ]

#     completed_tasks = [
#         task for task in tasks
#         if task["status"] == "completed"
#     ]

#     total_tasks = len(tasks)

#     progress = 0

#     if total_tasks > 0:
#         progress = (
#             len(completed_tasks) / total_tasks
#         ) * 100

#     # Rule 1

#     if progress < 30:
#         recommendations.append(
#             "⚠️ You are behind schedule. Complete at least one session today."
#         )

#     # Rule 2

#     if len(pending_tasks) > 5:
#         recommendations.append(
#             "📚 Multiple study sessions are pending. Consider increasing study hours."
#         )

#     # Rule 3

#     hard_subjects = [
#         task for task in pending_tasks
#         if task.get("difficulty") == "Hard"
#     ]

#     if len(hard_subjects) > 0:
#         recommendations.append(
#             "🔥 Focus on hard subjects first."
#         )

#     # Rule 4

#     if progress >= 80:
#         recommendations.append(
#             "🎉 Great progress! Focus on revision."
#         )

#     # Default

#     if len(recommendations) == 0:
#         recommendations.append(
#             "✅ You are on track with your study plan."
#         )

#     return {
#         "recommendations": recommendations
#     }


@app.post("/chat")
async def chat(request: ChatRequest):
    
    response = llm_chat(request.query)

    return {
        "response": response
    }

# around 5 to 6 apis will create for the study planner, 
# such as creating a study plan, getting the study plan, 
# updating the study plan, deleting the study plan, etc.


# apis
# 1. create_study_plan/generate_plan
# 2. get_study_plan
# 3. update_study_plan
# 4. delete_study_plan
# 5. list_study_plans

#
