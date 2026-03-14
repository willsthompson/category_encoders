from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pipeline:pipeline@db:5432/pipeline"


settings = Settings()
