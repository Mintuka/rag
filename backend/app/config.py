from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://rag:ragpassword@localhost:5432/ragdb"
    jwt_secret: str = "super-secret-jwt-key-change-in-production-32chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
