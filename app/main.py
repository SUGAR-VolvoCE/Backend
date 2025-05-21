from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .orchestrator import chat_with_assistant
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: int
    message: str
    reset: bool = False
    media_url: Optional[str] = None

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        print("URL: ", req.media_url)
        print(req.message)
        response, url = chat_with_assistant(user_id=req.user_id, message=req.message, reset=req.reset, file_url=req.media_url)
        return {
            "response": response or "Desculpe, algo deu errado.",
            "image_url": url or None
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
