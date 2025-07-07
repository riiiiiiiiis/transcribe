import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/transcription_db")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# App Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Railway
PORT = int(os.getenv("PORT", "8000"))

# Validation will be done at runtime when needed