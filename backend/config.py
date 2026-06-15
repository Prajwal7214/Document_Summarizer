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

    # Cache
    ENABLE_CACHE: bool = True

settings = Settings()