import os
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client import models
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class QdrantRepository:
    def __init__(self):
        self.url = os.environ["QDRANT_URL"]
        self.api_key = os.environ["QDRANT_API_KEY"]
        self.collection_name = "playmobil"
        
        logger.info(f"Connecting to remote Qdrant at {self.url}...")
        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        
        logger.info("Initializing HuggingFaceEmbeddings...")
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

    def recreate_collection(self) -> None:
        """Deletes the Qdrant collection if it exists and creates a brand new one."""
        logger.info(f"Deleting collection '{self.collection_name}' if it exists...")
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        
        logger.info(f"Creating collection '{self.collection_name}' (384 dims, Cosine)...")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        
        logger.info("Ensuring payload index on metadata.type exists...")
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.type",
            field_schema=models.PayloadSchemaType.KEYWORD
        )

    def ensure_collection_exists(self) -> None:
        """Ensures the collection exists without deleting it if it does."""
        if not self.client.collection_exists(self.collection_name):
            self.recreate_collection()

    def add_documents(self, items: list) -> None:
        """Ingests a list of dictionary items (each with 'text' and 'metadata') into Qdrant."""
        texts = [x["text"] for x in items]
        metas = [x["metadata"] for x in items]
        ids = [str(uuid.uuid4()) for _ in items]
        
        logger.info(f"Ingesting {len(items)} items into Qdrant collection '{self.collection_name}'...")
        self.vector_store.add_texts(
            texts=texts,
            metadatas=metas,
            ids=ids
        )

    def similarity_search(self, query: str, k: int = 3) -> str:
        """Performs similarity search and returns concatenated page contents."""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            if docs:
                return "\n\n".join(d.page_content for d in docs)
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}", exc_info=True)
        return ""
