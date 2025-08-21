#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration settings for Coffee Price Tracker
"""

import os
from typing import Optional

class Config:
    """
    Configuration class for the coffee price tracker
    """
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
    
    # Scraper Settings
    SCRAPER_TIMEOUT: int = int(os.getenv('SCRAPER_TIMEOUT', '15'))
    SCRAPER_MAX_RETRIES: int = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))
    SCRAPER_DELAY: float = float(os.getenv('SCRAPER_DELAY', '2.0'))
    
    # Scheduling Settings (Vietnam timezone UTC+7)
    MORNING_SCHEDULE: str = os.getenv('MORNING_SCHEDULE', '01:00')  # 8AM Vietnam = 1AM UTC
    EVENING_SCHEDULE: str = os.getenv('EVENING_SCHEDULE', '10:00')  # 5PM Vietnam = 10AM UTC
    
    # Data Storage
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'coffee_prices.db')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'coffee_tracker.log')
    
    # Exchange Rates (for VND conversion)
    USD_TO_VND_RATE: float = float(os.getenv('USD_TO_VND_RATE', '24000'))
    
    # Coffee Sources
    COFFEE_SOURCES = {
        'robusta': {
            'url': 'https://www.investing.com/commodities/london-coffee',
            'name': 'Robusta Coffee (London)',
            'unit': 'USD/tonne',
            'symbol': 'LCF',
            'market': 'London Commodity Exchange'
        },
        'arabica': {
            'url': 'https://www.investing.com/commodities/us-coffee-c',
            'name': 'Arabica Coffee (NYC)',
            'unit': 'cents/lb',
            'symbol': 'KC',
            'market': 'Intercontinental Exchange'
        }
    }
    
    # User Agent strings for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15'
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration
        """
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID is required")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """
        Print current configuration (hiding sensitive data)
        """
        print("📋 Current Configuration:")
        print(f"   Bot Token: {'✓ Set' if cls.TELEGRAM_BOT_TOKEN else '❌ Missing'}")
        print(f"   Chat ID: {'✓ Set' if cls.TELEGRAM_CHAT_ID else '❌ Missing'}")
        print(f"   Timeout: {cls.SCRAPER_TIMEOUT}s")
        print(f"   Max Retries: {cls.SCRAPER_MAX_RETRIES}")
        print(f"   Morning Schedule: {cls.MORNING_SCHEDULE} UTC (8AM Vietnam)")
        print(f"   Evening Schedule: {cls.EVENING_SCHEDULE} UTC (5PM Vietnam)")
        print(f"   Database: {cls.DATABASE_PATH}")
        print(f"   Log Level: {cls.LOG_LEVEL}")
        print(f"   USD/VND Rate: {cls.USD_TO_VND_RATE:,}")

# Environment setup helper
def setup_environment():
    """
    Setup environment variables for development
    """
    env_file = '.env'
    
    if not os.path.exists(env_file):
        sample_env = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Scraper Settings
SCRAPER_TIMEOUT=15
SCRAPER_MAX_RETRIES=3
SCRAPER_DELAY=2.0

# Scheduling (UTC times)
MORNING_SCHEDULE=01:00  # 8AM Vietnam
EVENING_SCHEDULE=10:00  # 5PM Vietnam

# Data Storage
DATABASE_PATH=coffee_prices.db
LOG_LEVEL=INFO
LOG_FILE=coffee_tracker.log

# Exchange Rate
USD_TO_VND_RATE=24000
"""
        
        with open(env_file, 'w') as f:
            f.write(sample_env)
        
        print(f"📝 Created sample {env_file} file")
        print("   Please update it with your actual values")
        return False
    
    return True

def load_env_file():
    """
    Load environment variables from .env file
    """
    env_file = '.env'
    
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            
            print(f"✅ Loaded environment variables from {env_file}")
            return True
        except Exception as e:
            print(f"❌ Error loading {env_file}: {e}")
            return False
    
    return False

if __name__ == "__main__":
    # Test configuration
    load_env_file()
    Config.print_config()
    
    if Config.validate():
        print("\n✅ Configuration is valid")
    else:
        print("\n❌ Configuration is invalid")
        setup_environment()