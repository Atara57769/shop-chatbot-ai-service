from repositories.file_repository import FileRepository
from repositories.qdrant_repository import QdrantRepository
from services.chat_service import ChatService as ChatServiceImpl
from services.ingest_service import IngestService

file_repo = FileRepository()
qdrant_repo = QdrantRepository()
chat_service_impl = ChatServiceImpl(qdrant_repo)
ingest_service = IngestService(file_repo, qdrant_repo)
