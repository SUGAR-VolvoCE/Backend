from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .schema import ChatRequest
from .orchestrator import chat_with_assistant

app = FastAPI()

# Define request body structure
class ChatRequest(BaseModel):
    user_id: str  # Add the user_id here
    message: str
    reset: bool = False

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        # Pass the user_id, phase, and message to chat_with_assistant
        answer = chat_with_assistant(user_id=req.user_id, message=req.message, reset=req.reset)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
