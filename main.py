import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Setup global logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Import Controllers
from controllers import chat_controller, ingest_controller

app = FastAPI(title="Shop Chatbot AI Service")

# Enable CORS for frontend and other services
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

# Register Controller Routers
app.include_router(chat_controller.router)
app.include_router(ingest_controller.router)

logger.info("FastAPI application started and routers registered.")
