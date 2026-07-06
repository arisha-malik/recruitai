import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings:
    PROJECT_NAME: str = "RecruitAI Backend API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/recruitai"
    )
    
    # JWT Security
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "super_secret_key_recruit_ai_2026_change_me_in_production"
    )
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
    
    # AWS S3 (Phase 1 mock fallback if not configured)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "recruitai-resumes")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "recruitai-resumes") # Alias from request
    
    # Redis URL for Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Gemini / OpenAI AI Providers
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini") # "gemini" or "openai"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Storage Mode
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "local")
    
    # Run Jobs Synchronously for local dev
    RUN_JOBS_SYNC: bool = os.getenv("RUN_JOBS_SYNC", "false").lower() == "true"
    
    # Embeddings configuration
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "gemini") # "gemini" or "openai"
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004") # "text-embedding-004" or "text-embedding-3-small"
    
    # Celery / Redis (Falls back to PostgreSQL broker/result backend if empty)
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "")
    
    # Qdrant
    QDRANT_ENABLED: bool = os.getenv("QDRANT_ENABLED", "false").lower() == "true"
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_URL: str = os.getenv("QDRANT_URL", "") # Full Qdrant url
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "candidates_vectors")
    
    # Matching Engine Configurations
    MATCHING_TOP_N: int = int(os.getenv("MATCHING_TOP_N", "20"))

settings = Settings()
