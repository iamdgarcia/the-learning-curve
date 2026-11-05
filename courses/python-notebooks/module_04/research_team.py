import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# --- The Workers ---

# 1. Researcher
researcher_prompt = ChatPromptTemplate.from_template("""
You are a researcher. You receive a topic and must provide 3 key facts about it.
Topic: {topic}
""")
researcher_chain = researcher_prompt | llm

# 2. Writer
writer_prompt = ChatPromptTemplate.from_template("""
You are a writer. You receive a list of facts and must write a short paragraph summarizing them.
Facts: {facts}
""")
writer_chain = writer_prompt | llm

# --- The Orchestrator ---

class Delegation(BaseModel):
    topic: str = Field(description="The specific topic to research.")

orchestrator_parser = JsonOutputParser(pydantic_object=Delegation)

orchestrator_prompt = ChatPromptTemplate.from_template("""
You are the boss. The user wants to know about a broad subject.
Identify the core topic to research.

User Request: {request}

{format_instructions}
""")

orchestrator_chain = orchestrator_prompt | llm | orchestrator_parser

def run_research_team(request):
    print(f"--- New Request: {request} ---")
    
    # 1. Orchestrator decides what to research
    print("Orchestrator: Delegating task...")
    delegation = orchestrator_chain.invoke({
        "request": request,
        "format_instructions": orchestrator_parser.get_format_instructions()
    })
    topic = delegation["topic"]
    print(f"Topic identified: {topic}")
    
    # 2. Researcher finds facts
    print("Researcher: Gathering facts...")
    facts = researcher_chain.invoke({"topic": topic}).content
    print(f"Facts Found:\n{facts}")
    
    # 3. Writer compiles report
    print("Writer: Writing report...")
    report = writer_chain.invoke({"facts": facts}).content
    print(f"\n--- Final Report ---\n{report}")

if __name__ == "__main__":
    run_research_team("Tell me about the impact of electric cars on the environment.")
