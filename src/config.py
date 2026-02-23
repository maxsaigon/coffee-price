import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration with validation and sensible defaults."""

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

    # Financial Modeling Prep (Optional/Legacy)
    FMP_API_KEY: Optional[str] = os.getenv('FMP_API_KEY')

    # Scraper settings
    SCRAPER_TIMEOUT: int = int(os.getenv('SCRAPER_TIMEOUT', '15'))
    SCRAPER_MAX_RETRIES: int = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))
    SCRAPER_RETRY_DELAY: float = float(os.getenv('SCRAPER_RETRY_DELAY', '2.0'))

    # Exchange rate
    USD_TO_VND_RATE: float = float(os.getenv('USD_TO_VND_RATE', '25000'))

    # System
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'coffee_tracker.log')

    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration. Returns True if valid."""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')

        if missing:
            print(f"❌ Missing configuration: {', '.join(missing)}")
            return False
        return True
