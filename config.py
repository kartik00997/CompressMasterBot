import os
from dataclasses import dataclass


@dataclass
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # Directory for temporary download/compress files
    TEMP_DIR: str = "temp"


settings = Settings()

# Create temp directory if not exists
if not os.path.exists(settings.TEMP_DIR):
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
