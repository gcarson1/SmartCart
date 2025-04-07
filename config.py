import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Process DATABASE_URL to fix the dialect if needed.
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # OpenAI and OAuth configuration.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID = os.getenv("ASSISTANT_ID")
    VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
