"""
RetailPulse BI Agent Configuration.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "retailpulse.db"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    APP_NAME: str = "RetailPulse AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DB_PATH.as_posix()}"
    
    # LLM Settings
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    DEFAULT_LLM_PROVIDER: str = "gemini"  # "gemini", "openai", or "heuristic"
    LLM_MODEL_NAME: str = "gemini-2.5-flash"
    
    # Business Rules
    INACTIVE_CUSTOMER_DAYS: int = 90  # Customers without an order in 90 days are inactive
    TOP_N_DEFAULT: int = 5

settings = Settings()
