import os
import json
import uuid
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client import models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env
load_dotenv()

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION = "playmobil"

# Initialize Qdrant Client strictly as in app.py
print(f"[+] Connecting to remote Qdrant at {QDRANT_URL}...")
try:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )
except Exception as e:
    print(f"[-] Failed to create Qdrant client: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize Embeddings
print("[+] Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def init_db():
    """Initializes the Qdrant collection and metadata index if they don't exist."""
    print(f"[+] Checking if Qdrant collection '{COLLECTION}' exists...")
    try:
        if not client.collection_exists(COLLECTION):
            print(f"[+] Creating collection '{COLLECTION}' (384 dims, Cosine)...")
            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )
        else:
            print(f"[+] Collection '{COLLECTION}' already exists.")

        # Ensure payload index on type metadata exists for robust filtering
        print("[+] Ensuring payload index on metadata.type exists...")
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="metadata.type",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    except Exception as e:
        print(f"[-] Error during collection/index initialization: {e}", file=sys.stderr)
        sys.exit(1)

def load_data():
    """Loads policies and products from JSON files and sets metadata."""
    items = []
    
    # Load policies.json
    policies_path = "policies.json"
    if os.path.exists(policies_path):
        print(f"[+] Loading policies from {policies_path}...")
        with open(policies_path, "r", encoding="utf-8") as f:
            policies = json.load(f)
        for p in policies:
            p["metadata"] = {"type": "policy"}
        items.extend(policies)
    else:
        print(f"[-] Warning: {policies_path} not found.")

    # Load products.json
    products_path = "products.json"
    if os.path.exists(products_path):
        print(f"[+] Loading products from {products_path}...")
        with open(products_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        for p in products:
            p["metadata"] = {"type": "product"}
        items.extend(products)
    else:
        print(f"[-] Warning: {products_path} not found.")

    return items

def ingest():
    """Performs the full DB setup and loads the documents into the Qdrant database."""
    # Ensure collection exists
    init_db()

    # Load items
    items = load_data()
    if not items:
        print("[-] Error: No data loaded. Ingestion cancelled.", file=sys.stderr)
        return

    # Initialize langchain vector store wrapper
    db = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=embeddings
    )

    # Ingest
    texts = [x["text"] for x in items]
    metas = [x["metadata"] for x in items]
    ids = [str(uuid.uuid4()) for _ in items]

    print(f"[+] Ingesting {len(items)} items into Qdrant collection '{COLLECTION}'...")
    try:
        db.add_texts(
            texts=texts,
            metadatas=metas,
            ids=ids
        )
        print(f"[+] Success! Ingested {len(items)} items.")
    except Exception as e:
        print(f"[-] Error during database ingestion: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    ingest()
