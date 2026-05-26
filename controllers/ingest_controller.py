import logging
from fastapi import APIRouter, HTTPException
from models import ProductItem
from dependencies import ingest_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/products')
async def sync_products(products: list[ProductItem]):
    try:
        logger.info(f"Syncing {len(products)} products...")
        # Convert ProductItem Pydantic objects to dicts for the service layer
        products_data = [{"id": p.id, "text": p.text} for p in products]
        ingest_service.update_products_file(products_data)
        return {"status": "success", "message": "products.json file updated successfully."}
    except Exception as e:
        logger.error(f"Error syncing products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/ingest')
async def run_ingest():
    try:
        logger.info("Triggering vector database ingestion...")
        # Trigger ingestion and drop/recreate collection to avoid duplicates
        result = ingest_service.run_ingestion(recreate=True)
        return result
    except Exception as e:
        logger.error(f"Error running ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
