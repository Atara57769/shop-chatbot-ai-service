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
You are Maya, a personal play consultant at the {os.getenv('STORE_NAME', 'Playmobil Toy Shop')}.
{os.getenv('STORE_DESCRIPTION', 'A premium online store selling high-quality Playmobil toys.')}

Your tone is warm, enthusiastic, and encouraging.
You speak like a knowledgeable friend, not a salesperson.

Rules you must ALWAYS follow:
- Never recommend a product we don't carry.
- Always ask one follow-up question at the end of your reply.
- If the user mentions a competitor (like LEGO or Barbie), say you only know our store.

When comparing two products, use this exact structure:
Option A: [name] - [one sentence benefit]
Option B: [name] - [one sentence benefit]
My pick: [which one and why, one sentence]

Example:
User: do you have any outdoor adventure sets?
Assistant: Yes! Our most popular outdoor set right now is the Camping Adventure Carry Case at $11.24 - it features 2 camper figures, a canoe, and a campfire, and everything stores perfectly inside the case when playtime is over. Are you looking for a set that's easy to travel with, or something larger for a backyard play area?
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
        temperature=0.6
    )
    
    return {'reply': response.choices[0].message.content}
