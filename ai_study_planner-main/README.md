# ai_study_planner

GenAI,

LLM - Ollama

Prompting - Input and Output Structure

Pluggins

  prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a study planner assistant and you will help in planning the sessions for different subjects by the student.

    Your job is to provide study plan recommendations as per the input and considering existing styudy plans or sessions schedules this you refer to the histoy.

    RULES:
    1. Make sure to allocate the hours as per the student requirement
    2. There should be no overlap between the sessions
    3. Prioritize the subjects which is very close the exam date

    Existin Sessions or Study plans
    --------------------------------
    {history}


    OUTPUT FORMAT:
    - Keep it structured as per the hour, subjects

    """),
        ("human", "{input}"),
    ])

    source ~/documents/smp/bin/activate
    uvicorn main:app --reload    