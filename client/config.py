import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigError(RuntimeError):
    """Raised when required environment variables are missing or invalid."""

def load_config(env_path: str | Path | None = None) -> dict:
    """Load and validate configuration from a .env file.

    Returns a dictionary with keys:
        - SERVER_URL
        - DOWNLOAD_DIR
        - API_TOKEN
    Raises ConfigError if any required variable is missing.
    """
    # In a packaged app, use the editable .env beside the executable.
    load_dotenv(dotenv_path=env_path)
    required = ["SERVER_URL", "FOLDER_SIMPAN", "API_TOKEN"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ConfigError(f"Missing required .env variables: {', '.join(missing)}")
    return {
        "SERVER_URL": os.getenv("SERVER_URL"),
        "DOWNLOAD_DIR": os.getenv("FOLDER_SIMPAN"),
        "API_TOKEN": os.getenv("API_TOKEN"),
    }
