import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Keep these for backup
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # File settings
    MAX_FILE_SIZE_MB: int = 10
    CHUNK_SIZE_CHARS: int = 8000
    ALLOWED_EXTENSIONS: set = {"pdf", "docx", "txt"}

    # Ollama settings (local AI)
    OLLAMA_MODEL: str = "llama3.2"      # Running locally
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Cache & Cloud
    ENABLE_CACHE: bool = True
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0") # Using 6380 to match docker-compose
    
    # Vector DB
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333") # e.g. http://localhost:6333
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    
    # Security
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://127.0.0.1,http://localhost")

settings = Settings()