from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

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

# ── SEMANTIC SEARCH / QDRANT SETUP ───────────────────────────
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION = "playmobil"

print(f"[+] Connecting to remote Qdrant at {QDRANT_URL} for Semantic Search...")
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = QdrantVectorStore(
    client=qdrant_client,
    collection_name=COLLECTION,
    embedding=embeddings
)
print("[+] Remote Semantic Search initialized successfully.")



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

# ── RETRIEVAL HELPER ─────────────────────────────────────────
def retrieve_context(question: str) -> str:
    """Performs similarity search against the remote Qdrant database to retrieve relevant context."""
    try:
        docs = db.similarity_search(question, k=3)
        if docs:
            return "\n\n".join(d.page_content for d in docs)
    except Exception as e:
        print(f"[-] Error performing similarity search: {e}")
    return ""


# ── CHAT ENDPOINT ────────────────────────────────────────────
@app.post('/chat')
async def chat(req: ChatRequest):
    # Retrieve matching products/policies context from Qdrant
    context = retrieve_context(req.message)

    # Build the full conversation history
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for m in req.history:
        messages.append({'role': m.role, 'content': m.content})
    
    # Inject retrieved semantic search context if available
    if context:
        context_prompt = f"""Use the following official Playmobil shop information as your single source of truth for products and policies to answer the user's question:

---
{context}
---

Remember: Do NOT recommend any product not listed above. If the information is not in the context, politely explain that we don't carry that item or don't have that policy, while staying in character as Maya."""
        messages.append({'role': 'system', 'content': context_prompt})

    messages.append({'role': 'user', 'content': req.message})
    
    # Call Groq API using llama-3.3-70b-versatile
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=messages,
        max_tokens=400,
        temperature=0.6
    )
    
    return {'reply': response.choices[0].message.content}

