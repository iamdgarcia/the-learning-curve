import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def reflective_coder(task):
    print(f"--- Task: {task} ---")
    
    # Step 1: Draft
    print("\n1. Drafting Code...")
    draft_prompt = ChatPromptTemplate.from_template("Write Python code to: {task}")
    draft_chain = draft_prompt | llm
    draft_code = draft_chain.invoke({"task": task}).content
    print(f"Draft:\n{draft_code}")
    
    # Step 2: Critique
    print("\n2. Critiquing...")
    critique_prompt = ChatPromptTemplate.from_template("""
    Review the following python code for bugs, efficiency, and style.
    If it is perfect, say "LGTM".
    Otherwise, list the issues.
    Never output the corrected code, only the critique.
    
    Code:
    {code}
    """)
    critique_chain = critique_prompt | llm
    critique = critique_chain.invoke({"code": draft_code}).content
    print(f"Critique: {critique}")
    
    if "LGTM" in critique:
        print("\nCode is good to go!")
        return draft_code
    
    # Step 3: Revise
    print("\n3. Revising...")
    revise_prompt = ChatPromptTemplate.from_template("""
    Rewrite the following code to fix the issues listed in the critique.
    
    Original Code:
    {code}
    
    Critique:
    {critique}
    
    Return only the fixed code.
    """)
    revise_chain = revise_prompt | llm
    final_code = revise_chain.invoke({"code": draft_code, "critique": critique}).content
    print(f"Final Code:\n{final_code}")
    return final_code

if __name__ == "__main__":
    # We give it a tricky task that might need imports or specific logic
    reflective_coder("Calculate the 100th Fibonacci number efficiently.")
