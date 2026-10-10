import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

def simple_agent(query):
    print(f"User: {query}")
    print("Agent: Thinking...")
    
    # Step 1: Reasoning (The Plan)
    messages = [
        SystemMessage(content="You are a helpful assistant. Before answering, explain your thought process."),
        HumanMessage(content=query)
    ]
    
    response = llm.invoke(messages)
    
    print(f"Agent Response:\n{response.content}")

if __name__ == "__main__":
    simple_agent("What is the capital of France?")