import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# A simple list of forbidden topics
FORBIDDEN_TOPICS = ["hack", "violence", "bomb", "steal"]

def input_guardrail(query):
    """Checks if the query contains forbidden words."""
    for topic in FORBIDDEN_TOPICS:
        if topic in query.lower():
            return False, f"I cannot answer questions about {topic}."
    return True, ""

def run_safe_agent(query):
    print(f"\nUser: {query}")
    
    # 1. Input Guardrail
    is_safe, refusal_message = input_guardrail(query)
    
    if not is_safe:
        print(f"Agent (Guardrail): {refusal_message}")
        return

    # 2. Safe Execution
    prompt = ChatPromptTemplate.from_template("Answer this question helpfully: {query}")
    chain = prompt | llm
    response = chain.invoke({"query": query})
    
    print(f"Agent: {response.content}")

if __name__ == "__main__":
    run_safe_agent("How do I bake a cake?")
    run_safe_agent("How do I hack into a bank?")
