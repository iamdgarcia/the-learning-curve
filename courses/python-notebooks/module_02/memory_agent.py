from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 1. Create a Prompt with History Placeholder
# We need a place to inject the conversation history.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with a good memory."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

# 2. Manage Chat History
# In a real app, this would be a database (Redis, Postgres).
# Here, we use an in-memory dictionary.
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 3. Wrap the Chain with Message History
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

def chat_with_memory():
    print("--- Starting Chat Session (ID: user_123) ---")
    session_id = "user_123"
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        response = with_message_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        
        print(f"Agent: {response.content}")

if __name__ == "__main__":
    print("Try telling the agent your name, then ask 'What is my name?'")
    chat_with_memory()
