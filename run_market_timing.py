#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Timing Runner - Main Entry Point for GitHub Actions
Coordinates the market timing system with different operational modes
"""

import sys
import asyncio
import logging
from datetime import datetime
import pytz
from typing import Dict, Any

# Import our market timing system
from investing_market_scraper import InvestingMarketScraper
from telegram_bot import TelegramBot
from market_config import MarketConfigManager
from test_market_timing import MarketTimingTestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coffee_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketTimingRunner:
    """
    Main runner for market timing operations in GitHub Actions
    """
    
    def __init__(self):
        self.config = MarketConfigManager()
        self.scraper = InvestingMarketScraper()
        self.telegram_bot = None
        
        # Vietnam timezone for logging
        self.vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        # Initialize Telegram bot if configured
        if self.config.validate_telegram_config():
            try:
                self.telegram_bot = TelegramBot(
                    self.config.telegram.bot_token,
                    self.config.telegram.chat_id
                )
                logger.info("Telegram bot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
    
    async def run_market_update(self) -> bool:
        """
        Run market update - main operation for scheduled runs
        """
        logger.info("🚀 Starting market timing update...")
        vn_time = datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S')
        logger.info(f"Vietnam time: {vn_time}")
        
        try:
            # Determine message type based on current time and market status
            message_type = await self.determine_message_type()
            logger.info(f"Message type determined: {message_type}")
            
            # Scrape current market data
            logger.info("Scraping coffee market data...")
            market_data = self.scraper.scrape_coffee_prices()
            
            if not market_data:
                raise Exception("Failed to scrape market data")
            
            # Send to Telegram if bot is available
            if self.telegram_bot:
                logger.info(f"Sending {message_type} message to Telegram...")
                success = await self.telegram_bot.send_coffee_report(market_data, message_type)
                
                if success:
                    logger.info("✅ Market update completed successfully")
                    return True
                else:
                    raise Exception("Failed to send Telegram message")
            else:
                logger.warning("No Telegram bot configured - skipping notification")
                logger.info("✅ Market data scraped successfully (no notification sent)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Market update failed: {e}")
            
            # Send error notification if possible
            if self.telegram_bot:
                try:
                    await self.telegram_bot.send_error_notification(str(e), "Market Update")
                except:
                    pass
            
            return False
    
    async def determine_message_type(self) -> str:
        """
        Determine the appropriate message type based on current time and market status
        """
        vn_time = datetime.now(self.vn_tz)
        current_hour = vn_time.hour
        
        # Check market status for both markets
        robusta_status = self.scraper.get_market_status('robusta')
        arabica_status = self.scraper.get_market_status('arabica')
        
        logger.info(f"Market status - Robusta: {robusta_status}, Arabica: {arabica_status}")
        
        # Determine message type based on time and status
        if current_hour == 8:  # 8 AM Vietnam time - morning update
            if 'pre_market' in [robusta_status, arabica_status]:
                return "pre_market"
            elif 'open' in [robusta_status, arabica_status]:
                return "market_open"
            else:
                return "morning_summary"
        
        elif current_hour == 17:  # 5 PM Vietnam time - evening update
            if 'after_hours' in [robusta_status, arabica_status]:
                return "market_close"
            else:
                return "daily_summary"
        
        else:
            # Default update message
            return "update"
    
    async def run_system_test(self) -> bool:
        """
        Run comprehensive system test
        """
        logger.info("🧪 Running comprehensive system test...")
        
        try:
            test_suite = MarketTimingTestSuite()
            results = await test_suite.run_all_tests()
            
            # Check test results
            summary = results.get('summary', {})
            total_tests = summary.get('total_tests', 0)
            failed_tests = summary.get('failed_tests', 0)
            success_rate = (total_tests - failed_tests) / total_tests * 100 if total_tests > 0 else 0
            
            logger.info(f"Test Results: {total_tests - failed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            
            # Send test results to Telegram if available
            if self.telegram_bot and success_rate >= 80:
                test_message = f"🧪 **KIỂM TRA HỆ THỐNG**\n\n"
                test_message += f"✅ **Kết quả:** {total_tests - failed_tests}/{total_tests} tests passed\n"
                test_message += f"📊 **Tỷ lệ thành công:** {success_rate:.1f}%\n"
                test_message += f"⏰ **Thời gian:** {datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                
                if failed_tests == 0:
                    test_message += f"🎉 **Tất cả kiểm tra đều thành công!**"
                else:
                    test_message += f"⚠️ **{failed_tests} kiểm tra thất bại - cần xem xét**"
                
                await self.telegram_bot.send_message(test_message)
            
            return failed_tests == 0
            
        except Exception as e:
            logger.error(f"❌ System test failed: {e}")
            
            # Send error notification
            if self.telegram_bot:
                try:
                    await self.telegram_bot.send_error_notification(str(e), "System Test")
                except:
                    pass
            
            return False
    
    async def run_quick_test(self) -> bool:
        """
        Run quick connectivity and configuration test
        """
        logger.info("⚡ Running quick system test...")
        
        try:
            # Test 1: Configuration
            if not self.config.validate_telegram_config():
                logger.warning("Telegram configuration missing or invalid")
            else:
                logger.info("✅ Configuration valid")
            
            # Test 2: Telegram connectivity
            if self.telegram_bot:
                connection_ok = await self.telegram_bot.test_connection()
                if connection_ok:
                    logger.info("✅ Telegram connection OK")
                else:
                    logger.warning("⚠️ Telegram connection failed")
            else:
                logger.warning("⚠️ Telegram bot not configured")
            
            # Test 3: Basic scraping
            try:
                market_data = self.scraper.scrape_coffee_prices()
                success_count = market_data.get('success_count', 0)
                if success_count > 0:
                    logger.info(f"✅ Scraping test OK ({success_count} markets)")
                else:
                    logger.warning("⚠️ Scraping test returned no data")
            except Exception as e:
                logger.warning(f"⚠️ Scraping test failed: {e}")
            
            logger.info("⚡ Quick test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Quick test failed: {e}")
            return False

async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = "update"
    else:
        command = sys.argv[1].lower()
    
    logger.info(f"🎯 Market Timing Runner - Command: {command}")
    
    runner = MarketTimingRunner()
    success = False
    
    try:
        if command == "update":
            success = await runner.run_market_update()
        elif command == "test":
            success = await runner.run_system_test()
        elif command == "quick-test":
            success = await runner.run_quick_test()
        elif command == "notify-test":
            if runner.telegram_bot:
                test_msg = f"🧪 **TEST NOTIFICATION**\n\nThời gian: {datetime.now(runner.vn_tz).strftime('%d/%m/%Y %H:%M:%S')}\n\n✅ Hệ thống hoạt động bình thường!"
                success = await runner.telegram_bot.send_message(test_msg)
                logger.info("✅ Test notification sent" if success else "❌ Test notification failed")
            else:
                logger.error("❌ Telegram bot not configured")
        else:
            logger.error(f"❌ Unknown command: {command}")
            logger.info("Available commands: update, test, quick-test, notify-test")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Runner failed: {e}")
        success = False
    
    # Exit with appropriate code
    if success:
        logger.info("🎉 Operation completed successfully")
        sys.exit(0)
    else:
        logger.error("💥 Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())