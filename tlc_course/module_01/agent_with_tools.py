from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 1. Define a Tool
@tool
def multiply(a: int, b: int) -> int:
    """Multiplies two integers."""
    return a * b

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Mocking the API call
    return f"The weather in {city} is sunny and 25°C."

tools = [multiply, get_weather]

# 2. Bind Tools to LLM
llm_with_tools = llm.bind_tools(tools)

def run_agent(query):
    print(f"\nUser: {query}")
    messages = [HumanMessage(content=query)]
    
    # The LLM will decide if it needs to call a tool
    response = llm_with_tools.invoke(messages)
    
    print(f"Agent Response: {response.content}")
    
    # Check if the agent wants to call a tool
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"--- Tool Call: {tool_call['name']} args={tool_call['args']} ---")
            
            # In a real loop, we would execute the tool here and feed the result back.
            # For this demo, we just show that the agent *chose* the right tool.
    else:
        print("No tool calls made by the agent.")
if __name__ == "__main__":
    run_agent("What is 123 * 456?")

    run_agent("What's the weather in Madrid?")

    run_agent("What is the capital of France?")
