import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Literal
import sys
sys.path.append(".")  # Ensure current directory is in the path to import reflective_agent
from reflective_agent import reflective_coder
load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 1. Define the Specialists
math_prompt = ChatPromptTemplate.from_template("You are a mathematician. Solve this: {query}")
math_chain = math_prompt | llm

history_prompt = ChatPromptTemplate.from_template("You are a historian. Answer this: {query}")
history_chain = history_prompt | llm

general_prompt = ChatPromptTemplate.from_template("You are a helpful assistant. Answer this: {query}")
general_chain = general_prompt | llm

# 2. Define the Router
class Route(BaseModel):
    destination: Literal["math", "history", "general","code"] = Field(
        description="The specialist to route the query to."
    )

router_parser = JsonOutputParser(pydantic_object=Route)

router_prompt = ChatPromptTemplate.from_template("""
Route the user's query to the best specialist.
- 'math': For calculations and logic problems.
- 'history': For past events and figures.
- 'general': For greetings and general questions.
- 'code': For programming questions.

Query: {query}

{format_instructions}
""")

router_chain = router_prompt | llm | router_parser

def run_router_system(query):
    print(f"\n--- Query: {query} ---")
    
    # Step 1: Route
    route = router_chain.invoke({
        "query": query,
        "format_instructions": router_parser.get_format_instructions()
    })
    destination = route["destination"]
    print(f"Routing to: {destination.upper()}")
    
    # Step 2: Execute
    if destination == "math":
        response = math_chain.invoke({"query": query})
    elif destination == "history":
        response = history_chain.invoke({"query": query})
    elif destination == "code":
        # For code-related queries, we can use the reflective agent logic
        response = reflective_coder(query)
        print(f"Code Response:\n{response}")
        return
    else:
        response = general_chain.invoke({"query": query})
        
    print(f"Response: {response.content}")

if __name__ == "__main__":
    run_router_system("What is the derivative of x^2?")
    run_router_system("Who was the first emperor of Rome?")
    run_router_system("Hello, how are you?")
    run_router_system("Create a python function to calculate the 100th Fibonacci number efficiently.")