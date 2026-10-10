import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 1. Define the Plan Structure
class Plan(BaseModel):
    steps: List[str] = Field(description="A list of steps to complete the task.")

parser = JsonOutputParser(pydantic_object=Plan)

# 2. The Planner
planner_prompt = ChatPromptTemplate.from_template("""
You are a project manager. Break down the following task into 3-5 clear, actionable steps.
Return the result as a JSON object with a 'steps' key.

Task: {task}

{format_instructions}
""")

planner_chain = planner_prompt | llm | parser

# 3. The Executor
# In a real system, this would be an agent with tools.
# Here, we simulate it with a simple LLM call.
executor_prompt = ChatPromptTemplate.from_template("""
You are a worker. Complete the following step.
Provide a concise result.

Step: {step}
Context from previous steps: {context}
""")

executor_chain = executor_prompt | llm

def run_planning_agent(task):
    print(f"--- New Task: {task} ---")
    print(parser.get_format_instructions())
    # Step 1: Generate Plan
    print("Planner: Generating plan...")
    plan = planner_chain.invoke({
        "task": task,
        "format_instructions": parser.get_format_instructions()
    })
    
    steps = plan["steps"]
    print(f"Plan: {steps}")
    
    # Step 2: Execute Plan
    context = ""
    for i, step in enumerate(steps):
        print(f"\n--- Executing Step {i+1}: {step} ---")
        result = executor_chain.invoke({"step": step, "context": context})
        print(f"Result: {result.content}")
        
        # Append result to context for the next step
        context += f"\nStep {i+1} Result: {result.content}"

    print("\n--- Task Complete ---")

if __name__ == "__main__":
    run_planning_agent("Research the history of the internet and write a short poem about it.")
