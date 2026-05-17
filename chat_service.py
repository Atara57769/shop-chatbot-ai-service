from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = FastAPI()

# Enable CORS for frontend and other services
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

# Initialize Groq client
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# ── SYSTEM PROMPT ────────────────────────────────────────────
# This is the agent's persona. Edit this — not the code below.
SYSTEM_PROMPT = f"""
You are a friendly shopping assistant for {os.getenv('STORE_NAME', 'Playmobil Toy Shop')}.
{os.getenv('STORE_DESCRIPTION', 'A premium online store selling high-quality Playmobil toys.')}
Rules:
- Always ask about the customer's budget before recommending products.
- Keep answers to 3-4 sentences maximum.
- If you don't know something, say so honestly.
"""

# ── DATA MODELS ──────────────────────────────────────────────
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []
    products: list = []  # will be filled in Hours 5-6

# ── CHAT ENDPOINT ────────────────────────────────────────────
@app.post('/chat')
async def chat(req: ChatRequest):
    # Build the full conversation history
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for m in req.history:
        messages.append({'role': m.role, 'content': m.content})
    messages.append({'role': 'user', 'content': req.message})
    
    # Call Groq API using llama-3.3-70b-versatile
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=messages,
        max_tokens=400,
        temperature=0.5
    )
    
    return {'reply': response.choices[0].message.content}
