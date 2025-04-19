import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    
    _raw_db_url = os.getenv("DATABASE_URL", "")
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_db_url or "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ASSISTANT_ID = os.getenv("ASSISTANT_ID", "")
    VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")