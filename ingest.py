import logging
from dotenv import load_dotenv
from repositories.file_repository import FileRepository
from repositories.qdrant_repository import QdrantRepository
from services.ingest_service import IngestService

# Configure logging for standalone script execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_standalone():
    # Load environment variables
    load_dotenv()
    
    # Initialize layered architecture
    file_repo = FileRepository()
    qdrant_repo = QdrantRepository()
    ingest_service = IngestService(file_repo, qdrant_repo)
    
    logger.info("Starting standalone database ingestion...")
    try:
        # Default standalone run behaves like original: ensures collection exists without deleting it
        result = ingest_service.run_ingestion(recreate=False)
        logger.info(f"Ingestion complete: {result['message']}")
    except Exception as e:
        logger.error(f"Standalone ingestion failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_standalone()
