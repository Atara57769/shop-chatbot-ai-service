import os
import json
import uuid
import gradio as gr
import torch

from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Filter, FieldCondition, MatchValue

from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


# =========================
# CONFIG
# =========================

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]

COLLECTION = "playmobil"


# =========================
# EMBEDDINGS
# =========================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# QDRANT
# =========================

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


def init_db():
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="metadata.type",
        field_schema=models.PayloadSchemaType.KEYWORD
    )


init_db()

db = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION,
    embedding=embeddings
)


# =========================
# LOAD DATA
# =========================

def load_data():
    with open("policies.json", "r", encoding="utf-8") as f:
        policies = json.load(f)

    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    for p in policies:
        p["metadata"] = {"type": "policy"}

    for p in products:
        p["metadata"] = {"type": "product"}

    return policies + products


def ingest():
    items = load_data()

    texts = [x["text"] for x in items]
    metas = [x["metadata"] for x in items]
    ids = [str(uuid.uuid4()) for _ in items]

    db.add_texts(
        texts=texts,
        metadatas=metas,
        ids=ids
    )

    return f"Ingested {len(items)} items"


# =========================
# LLM (STABLE - NO PIPELINE)
# =========================

model_name = "google/flan-t5-base"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)


# =========================
# RETRIEVAL (TOP-2 ONLY)
# =========================

def retrieve_all(question):
    docs = db.similarity_search(question, k=2)

    policies = [d for d in docs if d.metadata.get("type") == "policy"]
    products = [d for d in docs if d.metadata.get("type") == "product"]

    return policies, products


# =========================
# CHAT
# =========================

def chat(question):
    policies, products = retrieve_all(question)

    context_items = policies + products

    context = "\n\n".join(d.page_content for d in context_items)

    prompt = f"""
You are a helpful Playmobil assistant.

Use ONLY the context below.

If the answer is found, explain it in 1-3 short sentences.
If not found, say exactly: I don't know.

Context:
{context}

Question:
{question}

Answer:
"""

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,
            min_new_tokens=20,
            do_sample=False,
            temperature=0.7,
            repetition_penalty=1.2
        )

    answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    return answer

# =========================
# OPTIONAL UI
# =========================

with gr.Blocks() as demo:
    gr.Markdown("## Playmobil RAG")

    q = gr.Textbox(label="Question")
    a = gr.Textbox(label="Answer")

    btn = gr.Button("Ask")
    ingest_btn = gr.Button("Ingest")

    btn.click(chat, inputs=q, outputs=a)
    ingest_btn.click(ingest, outputs=a)

demo.launch(server_name="0.0.0.0", server_port=7860)