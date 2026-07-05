from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama

from backend.storage import study_goals, tasks


# =====================================
# LLM
# =====================================

llm = ChatOllama(
    model="llama3.2:latest",
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
You are an AI Trip Planner

    Resposibilities:
    - You will create a travel plan for the user by using user inputs such has name of the place and days available to visit
    - Don't hallucinate information, if you don't know the answer, say "I don't know" and stick to the information provided by the user

days available:
{context}
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
    context = 7

    response = chat_chain.invoke(

        {
            "question": query,
            "context": context,
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