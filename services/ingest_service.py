from repositories.file_repository import FileRepository
from repositories.qdrant_repository import QdrantRepository

class IngestService:
    def __init__(self, file_repo: FileRepository, qdrant_repo: QdrantRepository):
        self.file_repo = file_repo
        self.qdrant_repo = qdrant_repo

    def update_products_file(self, products: list[dict]) -> None:
        """Overwrites products.json with the provided products data."""
        self.file_repo.save_products(products)

    def run_ingestion(self, recreate: bool = False) -> dict:
        """Orchestrates the vector DB ingestion by loading files and inserting into Qdrant."""
        # 1. Initialize/recreate collection
        if recreate:
            self.qdrant_repo.recreate_collection()
        else:
            self.qdrant_repo.ensure_collection_exists()

        # 2. Load data from files
        policies = self.file_repo.load_policies()
        products = self.file_repo.load_products()
        items = policies + products

        if not items:
            raise Exception("No data loaded from policies.json or products.json. Ingestion cancelled.")

        # 3. Insert into Qdrant
        self.qdrant_repo.add_documents(items)

        return {
            "status": "success",
            "message": f"Successfully ingested {len(items)} items ({len(policies)} policies, {len(products)} products)."
        }
