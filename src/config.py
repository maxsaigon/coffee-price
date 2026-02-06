import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Financial Modeling Prep (Optional/Legacy)
    FMP_API_KEY = os.getenv('FMP_API_KEY')
    
    # System
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'coffee_tracker.log'
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        missing = []
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
            
        if missing:
            print(f"❌ Missing configuration: {', '.join(missing)}")
            return False
        return True
