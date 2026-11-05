import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

load_dotenv()

# 1. Setup: Ingest Knowledge
# In a real app, this happens once (offline). Here we do it on startup.
print("--- Indexing Knowledge Base ---")

# Load text
loader = TextLoader("./knowledge.txt")
documents = loader.load()

# Split text
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# Embed and Store
# We use a simple local vector store (Chroma)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="moon_base"
)
retriever = vector_store.as_retriever()

print("--- Indexing Complete ---")

# 2. Define the Tool
@tool
def search_moon_base(query: str) -> str:
    """
    Search the knowledge base for information about the Moon Base (Luna Prime).
    Use this tool whenever the user asks about the moon base, its history, or inhabitants.
    """
    print(f"--- Tool Call: Searching for '{query}' ---")
    docs = retriever.invoke(query)
    
    # Combine results
    result = "\n\n".join([doc.page_content for doc in docs])
    return result

# 3. Create the Agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [search_moon_base]
llm_with_tools = llm.bind_tools(tools)

def run_rag_agent(question):
    print(f"\nUser: {question}")
    messages = [HumanMessage(content=question)]
    
    # First call: Agent decides to use tool
    response = llm_with_tools.invoke(messages)
    
    if response.tool_calls:
        messages.append(response) # Add agent's thought to history
        
        for tool_call in response.tool_calls:
            # Execute tool
            if tool_call["name"] == "search_moon_base":
                tool_result = search_moon_base.invoke(tool_call)
                
                # Add tool result to history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })
        
        # Second call: Agent generates final answer using tool result
        final_response = llm_with_tools.invoke(messages)
        print(f"Agent: {final_response.content}")
    else:
        # Agent didn't need the tool
        print(f"Agent: {response.content}")

if __name__ == "__main__":
    run_rag_agent("What is the primary purpose of Luna Prime?")
    run_rag_agent("Who is the commander?")
    run_rag_agent("Tell me a joke.") # Should not use the tool
