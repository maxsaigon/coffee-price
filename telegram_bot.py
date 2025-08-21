#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot Integration for Coffee Price Notifications
Sends daily coffee price reports to specified Telegram channels/groups
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import aiohttp
import json

# Configure logging
logger = logging.getLogger(__name__)

class TelegramBot:
    """
    Telegram Bot service for sending coffee price notifications
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        if not self.chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        logger.info(f"Telegram bot initialized for chat: {self.chat_id}")
    
    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message to Telegram chat
        """
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info("Message sent successfully to Telegram")
                            return True
                        else:
                            logger.error(f"Telegram API error: {result.get('description')}")
                            return False
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    async def send_coffee_report(self, price_data: Dict[str, Any]) -> bool:
        """
        Send formatted coffee price report
        """
        try:
            from investing_coffee_scraper import InvestingCoffeeScraper
            
            scraper = InvestingCoffeeScraper()
            message = scraper.format_telegram_message(price_data)
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending coffee report: {e}")
            
            # Send error notification
            error_message = f"❌ **LỖI CẬP NHẬT GIÁ CÀ PHÊ**\n\n"
            error_message += f"🕐 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            error_message += f"🐛 Lỗi: {str(e)}\n\n"
            error_message += f"🔧 Vui lòng kiểm tra hệ thống"
            
            return await self.send_message(error_message)
    
    async def send_startup_notification(self) -> bool:
        """
        Send notification when bot starts
        """
        message = f"🤖 **BOT CẬP NHẬT GIÁ CÀ PHÊ ĐÃ KHỞI ĐỘNG**\n\n"
        message += f"⏰ Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')} (GMT+7)\n"
        message += f"📅 Lịch cập nhật: 8:00 & 17:00 hàng ngày\n"
        message += f"📊 Nguồn dữ liệu: Investing.com\n\n"
        message += f"✅ Hệ thống sẵn sàng hoạt động!"
        
        return await self.send_message(message)
    
    async def send_error_notification(self, error: str, context: str = "") -> bool:
        """
        Send error notification to admin
        """
        message = f"🚨 **LỖI HỆ THỐNG**\n\n"
        message += f"🕐 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        
        if context:
            message += f"📍 Ngữ cảnh: {context}\n"
        
        message += f"🐛 Chi tiết lỗi:\n```\n{error}\n```\n\n"
        message += f"🔧 Cần kiểm tra và xử lý"
        
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """
        Test bot connection and permissions
        """
        url = f"{self.base_url}/getMe"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            bot_info = result.get('result', {})
                            logger.info(f"Bot connection test successful: @{bot_info.get('username')}")
                            return True
                        else:
                            logger.error(f"Bot API error: {result.get('description')}")
                            return False
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Bot connection test failed: {e}")
            return False
    
    async def get_chat_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the target chat
        """
        url = f"{self.base_url}/getChat"
        
        payload = {
            'chat_id': self.chat_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            return result.get('result')
                        else:
                            logger.error(f"Get chat error: {result.get('description')}")
                            return None
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to get chat info: {e}")
            return None

class CoffeePriceNotifier:
    """
    High-level service for managing coffee price notifications
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot = TelegramBot(bot_token, chat_id)
        self.last_successful_run = None
        self.consecutive_failures = 0
    
    async def run_daily_report(self) -> bool:
        """
        Run daily coffee price report
        """
        logger.info("Starting daily coffee price report...")
        
        try:
            # Import here to avoid circular imports
            from investing_coffee_scraper import InvestingCoffeeScraper
            
            # Initialize scraper
            scraper = InvestingCoffeeScraper()
            
            # Scrape price data
            logger.info("Scraping coffee prices...")
            price_data = scraper.scrape_all_prices()
            
            if not price_data or price_data.get('success_count', 0) == 0:
                raise Exception("No price data could be scraped")
            
            # Send report
            logger.info("Sending Telegram report...")
            success = await self.bot.send_coffee_report(price_data)
            
            if success:
                self.last_successful_run = datetime.now()
                self.consecutive_failures = 0
                logger.info("✅ Daily report completed successfully")
                return True
            else:
                raise Exception("Failed to send Telegram message")
                
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"❌ Daily report failed: {e}")
            
            # Send error notification if multiple failures
            if self.consecutive_failures >= 2:
                await self.bot.send_error_notification(
                    str(e), 
                    f"Daily report (failures: {self.consecutive_failures})"
                )
            
            return False
    
    async def run_system_test(self) -> bool:
        """
        Test entire system
        """
        logger.info("Running system test...")
        
        # Test bot connection
        if not await self.bot.test_connection():
            logger.error("Bot connection test failed")
            return False
        
        # Test chat access
        chat_info = await self.bot.get_chat_info()
        if not chat_info:
            logger.error("Cannot access target chat")
            return False
        
        logger.info(f"Target chat: {chat_info.get('title', chat_info.get('type', 'Unknown'))}")
        
        # Test scraper
        try:
            from investing_coffee_scraper import InvestingCoffeeScraper
            scraper = InvestingCoffeeScraper()
            
            # Quick test scrape
            test_data = scraper.scrape_single_coffee('robusta')
            if not test_data:
                logger.warning("Scraper test returned no data")
            else:
                logger.info("Scraper test successful")
        
        except Exception as e:
            logger.error(f"Scraper test failed: {e}")
            return False
        
        # Send test notification
        test_message = f"🧪 **KIỂM TRA HỆ THỐNG**\n\n"
        test_message += f"⏰ Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        test_message += f"✅ Bot connection: OK\n"
        test_message += f"✅ Chat access: OK\n"
        test_message += f"✅ Scraper: OK\n\n"
        test_message += f"🎯 Hệ thống hoạt động bình thường!"
        
        success = await self.bot.send_message(test_message)
        
        if success:
            logger.info("✅ System test completed successfully")
            return True
        else:
            logger.error("❌ System test failed")
            return False

async def main():
    """Main function for testing"""
    try:
        # Initialize notifier
        notifier = CoffeePriceNotifier()
        
        # Run system test
        print("🧪 Running system test...")
        test_result = await notifier.run_system_test()
        
        if test_result:
            print("✅ System test passed")
            
            # Run daily report
            print("\n📊 Running daily report...")
            report_result = await notifier.run_daily_report()
            
            if report_result:
                print("✅ Daily report sent successfully")
            else:
                print("❌ Daily report failed")
        else:
            print("❌ System test failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())