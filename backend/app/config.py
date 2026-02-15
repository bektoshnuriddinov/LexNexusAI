from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-masterclass"

    # OpenAI API Key (legacy, used as fallback for LLM and Embedding)
    openai_api_key: str = ""

    # LLM Settings (fallback if global_settings not configured)
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "gpt-4o"

    # Embedding Settings (fallback if global_settings not configured)
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Encryption
    settings_encryption_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        protected_namespaces = ("model_",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
