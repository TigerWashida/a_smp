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
    temperature=0.1,
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

def llm_chat(
    query: str,
    session_id: str = "default"
):

    # context = build_context()
    context = "Tasks = Mathematics, progress(existing schedules) = none, difficulty levels = Medium, preferred study times = Morning, and deadlines(date) = 2026-07-15"

    response = chat_chain.invoke(

        {
            "question": query,
            "study_context": context,
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