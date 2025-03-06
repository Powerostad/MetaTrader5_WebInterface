import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API settings
API_KEY = os.getenv("MT5_API_KEY", "default-insecure-key")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))