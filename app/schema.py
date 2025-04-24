from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    phase: str  # 'info', 'troubleshoot', 'solve'
