from fastapi import FastAPI
from .schema import ChatRequest
from .orchestrator import chat_with_assistant

app = FastAPI()

@app.post("/chat")
def chat(req: ChatRequest):
    answer = chat_with_assistant(phase=req.phase, message=req.message)
    return {"answer": answer}
