from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

def run_cot_agent(question):
    print(f"\n--- Chain of Thought Agent ---")
    print(f"Question: {question}")
    
    # Chain of Thought Prompt
    template = """
    Answer the following question. 
    
    First, think step-by-step about how to solve it. 
    List your steps as:
    1. [Step 1]
    2. [Step 2]
    
    Then, provide the final answer as:
    FINAL ANSWER: [Answer]
    
    Question: {question}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    response = chain.invoke({"question": question})
    print(f"Response:\n{response.content}")

def run_persona_agent(question, persona):
    print(f"\n--- Persona Agent ({persona}) ---")
    print(f"Question: {question}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a {persona}. Answer the question in character."),
        ("user", "{question}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"question": question})
    print(f"Response:\n{response.content}")

if __name__ == "__main__":
    # 1. Chain of Thought Example
    run_cot_agent("If a train leaves Chicago at 80mph and another leaves New York at 90mph, and they are 800 miles apart, when do they meet?")
    
    # 2. Persona Example
    run_persona_agent("Explain quantum physics.", "pirate")
