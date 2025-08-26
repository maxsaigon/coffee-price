#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Timing Scheduler for Coffee Price Tracker
Automatically sends Telegram messages at market open/close times
Uses timezone-aware scheduling with market hours tracking
"""

import schedule
import time
import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
import pytz
from typing import Dict, Any, Optional
import threading
import json
from dataclasses import dataclass

# Import our existing modules
from investing_market_scraper import InvestingMarketScraper
from telegram_bot import TelegramBot
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketSchedule:
    """Market schedule configuration"""
    name: str
    timezone: str
    open_time: str  # Format: "HH:MM"
    close_time: str  # Format: "HH:MM"
    weekdays_only: bool = True
    pre_market_minutes: int = 30  # Minutes before market open
    after_hours_minutes: int = 30  # Minutes after market close

class MarketTimingScheduler:
    """
    Advanced scheduler for market timing notifications
    Handles multiple market timezones and schedules
    """
    
    def __init__(self):
        self.config = Config()
        self.scraper = InvestingMarketScraper()
        self.telegram_bot = None
        self.scheduler_thread = None
        self.is_running = False
        
        # Market schedules for coffee futures
        self.market_schedules = {
            'ice_europe': MarketSchedule(
                name="ICE Europe (London)",
                timezone="Europe/London",
                open_time="09:00",
                close_time="17:30",
                weekdays_only=True
            ),
            'ice_us': MarketSchedule(
                name="ICE US (New York)",
                timezone="America/New_York", 
                open_time="09:15",
                close_time="14:30",
                weekdays_only=True
            )
        }
        
        # Vietnam timezone for message formatting
        self.vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
    def initialize_telegram_bot(self):
        """Initialize Telegram bot with retry mechanism"""
        try:
            self.telegram_bot = TelegramBot()
            logger.info("Telegram bot initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            return False
    
    def setup_market_schedules(self):
        """Set up all market timing schedules"""
        logger.info("Setting up market timing schedules...")
        
        for market_id, market_schedule in self.market_schedules.items():
            try:
                # Schedule market open notifications
                self.schedule_market_event(
                    market_id=market_id,
                    market_schedule=market_schedule,
                    event_type="open",
                    target_time=market_schedule.open_time
                )
                
                # Schedule market close notifications
                self.schedule_market_event(
                    market_id=market_id,
                    market_schedule=market_schedule,
                    event_type="close", 
                    target_time=market_schedule.close_time
                )
                
                # Schedule pre-market notification (30 minutes before open)
                pre_market_time = self.calculate_pre_market_time(
                    market_schedule.open_time,
                    market_schedule.pre_market_minutes
                )
                
                self.schedule_market_event(
                    market_id=market_id,
                    market_schedule=market_schedule,
                    event_type="pre_market",
                    target_time=pre_market_time
                )
                
                logger.info(f"Scheduled events for {market_schedule.name}")
                
            except Exception as e:
                logger.error(f"Failed to schedule {market_id}: {e}")
    
    def schedule_market_event(self, market_id: str, market_schedule: MarketSchedule, 
                            event_type: str, target_time: str):
        """Schedule a specific market event"""
        market_tz = pytz.timezone(market_schedule.timezone)
        
        def job_wrapper():
            """Wrapper to handle timezone-aware execution"""
            try:
                # Check if it's a weekday (if required)
                if market_schedule.weekdays_only:
                    current_time = datetime.now(market_tz)
                    if current_time.weekday() >= 5:  # Saturday=5, Sunday=6
                        logger.info(f"Skipping {event_type} for {market_id} - weekend")
                        return
                
                # Execute the market event
                asyncio.run(self.execute_market_event(market_id, market_schedule, event_type))
                
            except Exception as e:
                logger.error(f"Error in {event_type} job for {market_id}: {e}")
        
        # Schedule the job for each weekday
        if market_schedule.weekdays_only:
            schedule.every().monday.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
            schedule.every().tuesday.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
            schedule.every().wednesday.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
            schedule.every().thursday.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
            schedule.every().friday.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
        else:
            schedule.every().day.at(target_time).do(job_wrapper).tag(f"{market_id}_{event_type}")
    
    def calculate_pre_market_time(self, market_open: str, minutes_before: int) -> str:
        """Calculate pre-market notification time"""
        try:
            open_time = datetime.strptime(market_open, "%H:%M")
            pre_market_time = open_time - timedelta(minutes=minutes_before)
            return pre_market_time.strftime("%H:%M")
        except Exception as e:
            logger.error(f"Error calculating pre-market time: {e}")
            return market_open
    
    async def execute_market_event(self, market_id: str, market_schedule: MarketSchedule, 
                                 event_type: str):
        """Execute a scheduled market event"""
        logger.info(f"Executing {event_type} event for {market_schedule.name}")
        
        try:
            # Scrape current market data
            market_data = self.scraper.scrape_coffee_prices()
            
            # Format message based on event type
            if event_type == "open":
                message = self.scraper.format_market_telegram_message(market_data, "market_open")
            elif event_type == "close":
                message = self.scraper.format_market_telegram_message(market_data, "market_close")
            elif event_type == "pre_market":
                message = self.format_pre_market_message(market_data, market_schedule)
            else:
                message = self.scraper.format_market_telegram_message(market_data, "update")
            
            # Send to Telegram
            if self.telegram_bot:
                success = await self.telegram_bot.send_message(message)
                if success:
                    logger.info(f"Successfully sent {event_type} message for {market_schedule.name}")
                else:
                    logger.error(f"Failed to send {event_type} message for {market_schedule.name}")
            else:
                logger.error("Telegram bot not initialized")
                
        except Exception as e:
            logger.error(f"Error executing {event_type} event: {e}")
    
    def format_pre_market_message(self, market_data: Dict[str, Any], 
                                market_schedule: MarketSchedule) -> str:
        """Format pre-market notification message"""
        vn_time = datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S')
        market_tz = pytz.timezone(market_schedule.timezone)
        market_time = datetime.now(market_tz).strftime('%H:%M')
        
        message = f"🔔 **CHUẨN BỊ MỞ CỬA THỊ TRƯỜNG**\n"
        message += f"📅 {vn_time} (GMT+7)\n"
        message += f"🌍 {market_schedule.name} sẽ mở cửa lúc {market_schedule.open_time} ({market_time} hiện tại)\n\n"
        
        # Add current market summary
        markets = market_data.get('markets', {})
        
        if 'robusta' in markets and 'current_price' in markets['robusta']:
            robusta = markets['robusta']
            price_vnd = robusta['current_price'] * 25000
            message += f"🌱 **ROBUSTA (London ICE)**\n"
            message += f"💰 Giá hiện tại: ${robusta['current_price']:,.2f}/tấn\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n\n"
        
        if 'arabica' in markets and 'current_price' in markets['arabica']:
            arabica = markets['arabica']
            price_usd_tonne = (arabica['current_price'] / 100) * 2204.62
            price_vnd = price_usd_tonne * 25000
            message += f"☕ **ARABICA (New York ICE)**\n"
            message += f"💰 Giá hiện tại: {arabica['current_price']:.2f} cents/lb\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n\n"
        
        message += f"⏰ **Chuẩn bị theo dõi thị trường mở cửa!**\n\n"
        message += f"🤖 **GiaNongSan Bot** - Thông báo tự động"
        
        return message
    
    def start_scheduler(self):
        """Start the market timing scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting market timing scheduler...")
        
        # Initialize Telegram bot
        if not self.initialize_telegram_bot():
            logger.error("Cannot start scheduler without Telegram bot")
            return
        
        # Set up market schedules
        self.setup_market_schedules()
        
        # Start scheduler in separate thread
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Market timing scheduler started successfully")
        
        # Log scheduled jobs
        self.log_scheduled_jobs()
    
    def _run_scheduler(self):
        """Internal scheduler loop"""
        logger.info("Scheduler thread started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Log heartbeat every hour
                if datetime.now().minute == 0:
                    self.log_scheduler_status()
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def log_scheduled_jobs(self):
        """Log all scheduled jobs for debugging"""
        logger.info("=== SCHEDULED JOBS ===")
        for job in schedule.jobs:
            logger.info(f"Job: {job.job_func.__name__} - Next run: {job.next_run}")
        logger.info("=====================")
    
    def log_scheduler_status(self):
        """Log scheduler status periodically"""
        vn_time = datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S')
        active_jobs = len(schedule.jobs)
        logger.info(f"Scheduler heartbeat - {vn_time} - {active_jobs} active jobs")
    
    def stop_scheduler(self):
        """Stop the market timing scheduler"""
        logger.info("Stopping market timing scheduler...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Market timing scheduler stopped")
    
    def get_next_market_events(self) -> Dict[str, Any]:
        """Get information about upcoming market events"""
        events = []
        
        for market_id, market_schedule in self.market_schedules.items():
            market_tz = pytz.timezone(market_schedule.timezone)
            now = datetime.now(market_tz)
            
            # Calculate next open and close times
            today_open = now.replace(
                hour=int(market_schedule.open_time.split(':')[0]),
                minute=int(market_schedule.open_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            today_close = now.replace(
                hour=int(market_schedule.close_time.split(':')[0]),
                minute=int(market_schedule.close_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            # Find next events
            next_open = today_open if today_open > now else today_open + timedelta(days=1)
            next_close = today_close if today_close > now else today_close + timedelta(days=1)
            
            events.append({
                'market': market_schedule.name,
                'timezone': market_schedule.timezone,
                'next_open': next_open.isoformat(),
                'next_close': next_close.isoformat(),
                'market_status': self.scraper.get_market_status(
                    'robusta' if 'europe' in market_id.lower() else 'arabica'
                )
            })
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'vietnam_time': datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S'),
            'upcoming_events': events
        }
    
    async def send_test_message(self, event_type: str = "test"):
        """Send a test message to verify Telegram integration"""
        logger.info(f"Sending test message: {event_type}")
        
        try:
            # Get current market data
            market_data = self.scraper.scrape_coffee_prices()
            
            # Format test message
            message = f"🧪 **TEST MESSAGE - {event_type.upper()}**\n\n"
            message += self.scraper.format_market_telegram_message(market_data)
            message += f"\n\n✅ **Hệ thống hoạt động bình thường**"
            
            # Send message
            if self.telegram_bot:
                success = await self.telegram_bot.send_message(message)
                if success:
                    logger.info("Test message sent successfully")
                    return True
                else:
                    logger.error("Failed to send test message")
                    return False
            else:
                logger.error("Telegram bot not initialized")
                return False
                
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False

def main():
    """Main function for testing the scheduler"""
    scheduler = MarketTimingScheduler()
    
    print("🕐 Market Timing Scheduler for Coffee Prices")
    print("=" * 50)
    
    try:
        # Show next market events
        next_events = scheduler.get_next_market_events()
        print("\n📅 Upcoming Market Events:")
        print(json.dumps(next_events, indent=2, default=str, ensure_ascii=False))
        
        # Test Telegram integration
        print("\n📱 Testing Telegram Integration...")
        async def test_telegram():
            if scheduler.initialize_telegram_bot():
                success = await scheduler.send_test_message("scheduler_test")
                if success:
                    print("✅ Telegram test message sent successfully")
                else:
                    print("❌ Failed to send test message")
            else:
                print("❌ Failed to initialize Telegram bot")
        
        asyncio.run(test_telegram())
        
        # Start scheduler (commented out for testing)
        # print("\n🚀 Starting Market Timing Scheduler...")
        # scheduler.start_scheduler()
        # 
        # try:
        #     while True:
        #         time.sleep(60)
        # except KeyboardInterrupt:
        #     print("\n⏹️ Stopping scheduler...")
        #     scheduler.stop_scheduler()
        #     print("✅ Scheduler stopped")
        
        print("\n✅ Market timing scheduler test completed")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    
if __name__ == "__main__":
    main()