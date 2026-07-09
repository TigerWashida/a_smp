from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

from backend.storage import study_goals, tasks


# =====================================
# LLM
# =====================================

llm = ChatOllama(
    model="llama3:latest",
    temperature=0,
)

# =====================================
# Prompt
# =====================================
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an AI Study Partner for a student

            Your goal is to help the student study smarter by using their tasks, progress(existing schedules), difficulty levels, preferred study times, and deadlines(date). 
            All of this data is provided below study context. You should help the student prioritize their tasks and create a realistic study plan.

            You should act like a supportive but practical study coach.

            Core behavior:
            - Give clear and realistic study advice.
            - Help the student decide what to study next.
            - Explain priorities using deadlines, difficulty, and completion status.
            - Encourage the student without sounding too casual.
            - Keep answers short enough to be useful during studying.

            Rules:
            1. Use only the tasks provided in the context.
            2. Do not make up deadlines, tasks, subjects, or completion data.
            3. If there is not enough information, ask one short follow-up question.
            4. If the student has pending tasks, recommend the most important next task.
            5. If the student has completed all tasks, suggest review, rest, or preparation for tomorrow.
            6. If the student asks for a schedule, avoid overlapping study blocks.
            7. If the student seems overloaded, suggest a smaller realistic plan.
            8. Use simple language that a student can quickly understand.

            Preferred response format:

            Recommendation:
            ...

            Reason:
            ...

            Next action:
            ...

            Study context:
            {study_context}
            """
        ),

        MessagesPlaceholder(
            variable_name="chat_history"
        ),

        (
            "human",
            "{question}"
        )
    ]
)


# =====================================
# Chain
# =====================================

chain = prompt | llm


# =====================================
# Session Store
# =====================================

store = {}


def get_session_history(
    session_id: str,
):

    if session_id not in store:

        store[session_id] = (
            InMemoryChatMessageHistory()
        )

    return store[session_id]


chat_chain = RunnableWithMessageHistory(

    chain,

    get_session_history,

    input_messages_key="question",

    history_messages_key="chat_history",
)


# =====================================
# Chat
# =====================================

def build_study_context():

    if len(study_goals) == 0 and len(tasks) == 0:
        return """
No study goals or tasks have been created yet.
Tell the student to create a study plan first before asking for recommendations.
"""

    goals_text = ""

    for goal in study_goals:

        goals_text += f"""
Subject: {goal.get("subject")}
Total Hours: {goal.get("total_hours")}
Difficulty: {goal.get("difficulty")}
Preferred Slot: {goal.get("preferred_slot")}
Deadline Date: {goal.get("exam_date")}
"""

    tasks_text = ""

    for task in tasks:

        tasks_text += f"""
Task ID: {task.get("id")}
Day: {task.get("day")}
Subject: {task.get("subject")}
Hours: {task.get("hours")}
Difficulty: {task.get("difficulty")}
Preferred Slot: {task.get("preferred_slot")}
Status: {task.get("status")}
"""

    return f"""
Study Goals:
{goals_text}

Tasks:
{tasks_text}
"""


def llm_chat(
    query: str,
    session_id: str = "default"
):

    study_context = build_study_context()

    response = chat_chain.invoke(

        {
            "question": query,
            "study_context": study_context,
        },

        config={
            "configurable": {
                "session_id": session_id
            }
        }

    )

    return str(response.content)

# while True:
#     user_input = input("User: ")
#     if user_input.lower() == "exit":
#         break
#     response = llm_chat(user_input)
#     print("AI Trip Planner:", response)