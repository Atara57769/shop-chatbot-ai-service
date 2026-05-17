# Playmobil Chat Service & RAG Pipeline

A lightweight, high-performance modular RAG (Retrieval-Augmented Generation) chat service using FastAPI, Groq (Llama-3.3), and remote Qdrant.

## Project Structure

- `chat_service.py`: FastAPI server containing the `/chat` endpoint with integrated remote Qdrant similarity search and Groq-powered completions.
- `ingest.py`: Standalone script to initialize your remote Qdrant collection and ingest products and policies data.
- `products.json` & `policies.json`: Source knowledge files.
- `requirements.txt`: Lightweight project dependencies.

---

## Getting Started

### 1. Environment Setup

Configure your `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
STORE_NAME=Playmobil Toy Shop
STORE_DESCRIPTION=A premium online store selling high-quality Playmobil toys.

# Remote Qdrant Cloud settings
QDRANT_URL=https://your-qdrant-instance.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

### 2. Ingest the Data
Initialize your remote vector database and index the shop policies and products:
```bash
python ingest.py
```

### 3. Run the Chat Service API
Start the FastAPI server:
```bash
uvicorn chat_service:app --reload
```
The server will start listening at `http://127.0.0.1:8000`. You can access the API endpoint `/chat` via HTTP POST.
