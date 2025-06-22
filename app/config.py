import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    openai_api_key: str = os.getenv("OPENAI_API_KEY")

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    s3_bucket_name: str

    graphrag_working_dir: str = "./nsf_graphrag_knowledge"

    class Config:
        env_file = ".env"


settings = Settings()