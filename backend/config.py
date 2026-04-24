from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_MODEL: str
    SERVER_PORT: int = 8000
    DATA_DIR: str = "./data"

    class Config:
        env_file = ".env"


settings = Settings()
