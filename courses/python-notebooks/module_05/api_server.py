import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# 1. Initialize App and Agent
app = FastAPI(title="Agent API", version="1.0")

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# 2. Define Data Models
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

# 3. Define Endpoints
@app.get("/")
def read_root():
    return {"status": "Agent is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"Received query: {request.query}")
        
        # Call the Agent (Simple Logic)
        messages = [
            SystemMessage(content="You are a helpful API assistant."),
            HumanMessage(content=request.query)
        ]
        result = llm.invoke(messages)
        
        return ChatResponse(response=result.content)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    # Access Swagger UI at http://localhost:8000/docs
    uvicorn.run(app, host="0.0.0.0", port=8000)
