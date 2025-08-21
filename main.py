#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coffee Price Tracker - Main Entry Point
Automated coffee price scraping and Telegram notifications
"""

import sys
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import Config, load_env_file
from investing_coffee_scraper import InvestingCoffeeScraper
from telegram_bot import CoffeePriceNotifier

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

async def run_price_update():
    """
    Run coffee price update and send to Telegram
    """
    logger.info("🚀 Starting coffee price update...")
    
    try:
        # Initialize notifier
        notifier = CoffeePriceNotifier()
        
        # Run daily report
        success = await notifier.run_daily_report()
        
        if success:
            logger.info("✅ Coffee price update completed successfully")
            return True
        else:
            logger.error("❌ Coffee price update failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during price update: {e}")
        return False

async def run_system_test():
    """
    Run comprehensive system test
    """
    logger.info("🧪 Starting system test...")
    
    try:
        # Test configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Test scraper
        logger.info("Testing scraper...")
        scraper = InvestingCoffeeScraper()
        
        # Test single coffee scraping
        robusta_data = scraper.scrape_single_coffee('robusta')
        if robusta_data and 'current_price' in robusta_data:
            logger.info(f"✅ Robusta scraping test passed: ${robusta_data['current_price']}")
        else:
            logger.warning("⚠️ Robusta scraping test failed")
        
        # Test Telegram bot
        logger.info("Testing Telegram bot...")
        notifier = CoffeePriceNotifier()
        
        test_success = await notifier.run_system_test()
        
        if test_success:
            logger.info("✅ System test completed successfully")
            return True
        else:
            logger.error("❌ System test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during system test: {e}")
        return False

async def run_test_notification():
    """
    Send a test notification to Telegram
    """
    logger.info("📱 Sending test notification...")
    
    try:
        notifier = CoffeePriceNotifier()
        
        # Create test message
        test_message = f"🧪 **KIỂM TRA THÔNG BÁO**\n\n"
        test_message += f"⏰ Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')} (GMT+7)\n"
        test_message += f"🤖 Bot hoạt động bình thường\n"
        test_message += f"📊 Sẵn sàng cập nhật giá cà phê\n\n"
        test_message += f"✅ Hệ thống đã được kiểm tra!"
        
        success = await notifier.bot.send_message(test_message)
        
        if success:
            logger.info("✅ Test notification sent successfully")
            return True
        else:
            logger.error("❌ Test notification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {e}")
        return False

def print_usage():
    """Print usage information"""
    print("""
☕ Coffee Price Tracker Usage:

Commands:
  python main.py update        # Run price update and send to Telegram
  python main.py test          # Run comprehensive system test
  python main.py notify-test   # Send test notification
  python main.py config        # Show current configuration

GitHub Actions Usage:
  - This script is designed to run automatically via GitHub Actions
  - Scheduled for 8AM and 5PM Vietnam time (1AM and 10AM UTC)
  - Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in repository secrets

Environment Variables:
  TELEGRAM_BOT_TOKEN    # Your Telegram bot token
  TELEGRAM_CHAT_ID      # Target chat/channel ID
  SCRAPER_TIMEOUT       # Request timeout (default: 15)
  SCRAPER_MAX_RETRIES   # Max retry attempts (default: 3)
  USD_TO_VND_RATE       # Exchange rate (default: 24000)

Example:
  export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
  export TELEGRAM_CHAT_ID="-100123456789"
  python main.py update
""")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Coffee Price Tracker')
    parser.add_argument('command', nargs='?', choices=['update', 'test', 'notify-test', 'config', 'help'], 
                       default='help', help='Command to execute')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_env_file()
    
    # Setup logging
    setup_logging()
    
    logger.info(f"🌟 Coffee Price Tracker started - Command: {args.command}")
    logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Handle commands
    if args.command == 'help':
        print_usage()
        return
    
    elif args.command == 'config':
        Config.print_config()
        if Config.validate():
            print("\n✅ Configuration is valid")
        else:
            print("\n❌ Configuration is invalid")
        return
    
    elif args.command == 'test':
        success = await run_system_test()
        sys.exit(0 if success else 1)
    
    elif args.command == 'notify-test':
        success = await run_test_notification()
        sys.exit(0 if success else 1)
    
    elif args.command == 'update':
        # Validate configuration first
        if not Config.validate():
            logger.error("❌ Configuration validation failed")
            sys.exit(1)
        
        success = await run_price_update()
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        print_usage()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)