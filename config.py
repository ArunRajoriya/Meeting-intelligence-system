from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Groq API (for LLM and Whisper)
    groq_api_key: str
    whisper_model: str = "whisper-large-v3-turbo"
    llama_model: str = "llama-3.3-70b-versatile"  # Updated to current model
    
    # Alternative transcription providers (optional)
    openai_api_key: Optional[str] = None
    assemblyai_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
