from pydantic import BaseModel

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []

class ProductItem(BaseModel):
    id: str
    text: str
