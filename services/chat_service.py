import os
from groq import Groq
from repositories.qdrant_repository import QdrantRepository

class ChatService:
    def __init__(self, qdrant_repo: QdrantRepository):
        self.qdrant_repo = qdrant_repo
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Load persona system prompt from env with fallback defaults
        store_name = os.getenv('STORE_NAME', 'Playmobil Toy Shop')
        store_description = os.getenv('STORE_DESCRIPTION', 'A premium online store selling high-quality Playmobil toys.')
        
        self.system_prompt = f"""
You are Maya, a personal play consultant at the {store_name}.
{store_description}

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

    def process_chat_message(self, message: str, history: list, products: list) -> str:
        """Processes a chat request by retrieving Qdrant context and calling the Groq LLM model."""
        # 1. Retrieve context using similarity search on Qdrant
        context = self.qdrant_repo.similarity_search(message, k=3)

        # 2. Build full conversation history
        messages = [{'role': 'system', 'content': self.system_prompt}]
        for m in history:
            messages.append({'role': m.get('role', 'user'), 'content': m.get('content', '')})
        
        # 3. Inject context as a system prompt if found
        if context:
            context_prompt = f"""Use the following official Playmobil shop information as your single source of truth for products and policies to answer the user's question:

---
{context}
---

Remember: Do NOT recommend any product not listed above. If the information is not in the context, politely explain that we don't carry that item or don't have that policy, while staying in character as Maya."""
            messages.append({'role': 'system', 'content': context_prompt})

        # Add user's new message
        messages.append({'role': 'user', 'content': message})
        
        # 4. Request response from Groq
        response = self.groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            max_tokens=400,
            temperature=0.6
        )
        
        return response.choices[0].message.content
