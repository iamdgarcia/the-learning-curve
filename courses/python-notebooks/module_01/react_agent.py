from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# A fake tool
def get_planet_mass(planet):
    if planet.lower() == "earth":
        return "5.972 × 10^24 kg"
    elif planet.lower() == "mars":
        return "6.39 × 10^23 kg"
    else:
        return "Unknown planet."

def react_agent(question):
    print(f"Question: {question}")
    
    # Step 1: Reasoning
    prompt = f"""
    Answer the question: {question}
    
    You have access to a tool 'get_planet_mass(planet_name)'.
    
    If you need to use the tool, output:
    ACTION: get_planet_mass: [planet_name]
    
    If you have the answer, output:
    FINAL ANSWER: [answer]
    """
    
    response = llm.invoke(prompt).content
    print(f"Agent: {response}")
    
    # Step 2: Action (Simulation of the loop)
    if "ACTION:" in response:
        action = response.split("ACTION:")[1].strip()
        tool_name, arg = action.split(":")
        arg = arg.strip()
        
        if "get_planet_mass" in tool_name:
            print(f"--- Tool Execution: {tool_name}('{arg}') ---")
            observation = get_planet_mass(arg)
            print(f"Observation: {observation}")
            
            # Step 3: Re-Reasoning with Observation
            prompt_2 = f"""
            Question: {question}
            Previous Thought: {response}
            Observation: {observation}
            
            Now provide the final answer.
            """
            final_response = llm.invoke(prompt_2).content
            print(f"Agent: {final_response}")

if __name__ == "__main__":
    react_agent("What is the mass of Earth?")
