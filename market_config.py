#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Configuration for Coffee Price Tracker
Centralized configuration for market schedules, timezones, and settings
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import pytz
from datetime import datetime, timedelta

@dataclass
class MarketScheduleConfig:
    """Configuration for individual market schedules"""
    name: str
    name_vi: str  # Vietnamese name
    timezone: str
    open_time: str  # Format: "HH:MM"
    close_time: str  # Format: "HH:MM"
    currency: str
    unit: str
    weekdays_only: bool = True
    pre_market_minutes: int = 30
    after_hours_minutes: int = 30
    coffee_type: str = "robusta"  # Used for scraper mapping
    active: bool = True

@dataclass
class NotificationConfig:
    """Configuration for notification timing"""
    market_open: bool = True
    market_close: bool = True
    pre_market: bool = True
    daily_summary: bool = True
    daily_summary_time: str = "17:00"  # Vietnam time
    weekend_summary: bool = False
    error_notifications: bool = True

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    chat_id: str
    parse_mode: str = "Markdown"
    disable_web_preview: bool = True
    retry_attempts: int = 3
    retry_delay: int = 2

class MarketConfigManager:
    """
    Centralized configuration manager for coffee market tracking
    """
    
    def __init__(self):
        self.vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        
        # Coffee market configurations
        self.market_schedules = {
            'ice_europe_robusta': MarketScheduleConfig(
                name="ICE Europe (London)",
                name_vi="Thị trường London (ICE Europe)",
                timezone="Europe/London",
                open_time="09:00",
                close_time="17:30",
                currency="USD",
                unit="USD/tonne",
                coffee_type="robusta",
                pre_market_minutes=30,
                after_hours_minutes=30,
                active=True
            ),
            
            'ice_us_arabica': MarketScheduleConfig(
                name="ICE US (New York)",
                name_vi="Thị trường New York (ICE US)",
                timezone="America/New_York",
                open_time="09:15",
                close_time="14:30",
                currency="USD",
                unit="cents/lb",
                coffee_type="arabica",
                pre_market_minutes=30,
                after_hours_minutes=30,
                active=True
            ),
            
            # Future expansion: Vietnam domestic markets
            'vietnam_domestic': MarketScheduleConfig(
                name="Vietnam Coffee Exchange",
                name_vi="Sàn Cà Phê Việt Nam",
                timezone="Asia/Ho_Chi_Minh",
                open_time="08:30",
                close_time="15:00",
                currency="VND",
                unit="VND/kg",
                coffee_type="robusta_vietnam",
                pre_market_minutes=15,
                after_hours_minutes=15,
                active=False  # Not implemented yet
            )
        }
        
        # Notification configuration
        self.notifications = NotificationConfig(
            market_open=True,
            market_close=True,
            pre_market=True,
            daily_summary=True,
            daily_summary_time="17:00",  # 5 PM Vietnam time
            weekend_summary=False,
            error_notifications=True
        )
        
        # Telegram configuration from environment
        self.telegram = TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
            parse_mode="Markdown",
            disable_web_preview=True,
            retry_attempts=3,
            retry_delay=2
        )
        
        # General settings
        self.settings = {
            'vietnam_timezone': 'Asia/Ho_Chi_Minh',
            'default_currency_rate': 25000,  # USD to VND
            'log_level': 'INFO',
            'max_retry_attempts': 3,
            'request_timeout': 15,
            'scheduler_check_interval': 60,  # seconds
            'heartbeat_interval': 3600,  # 1 hour
            'price_cache_duration': 300,  # 5 minutes
            'historical_data_retention': 90,  # days
        }
    
    def get_active_markets(self) -> Dict[str, MarketScheduleConfig]:
        """Get only active market configurations"""
        return {
            market_id: config 
            for market_id, config in self.market_schedules.items() 
            if config.active
        }
    
    def get_market_by_coffee_type(self, coffee_type: str) -> Optional[MarketScheduleConfig]:
        """Get market configuration by coffee type"""
        for config in self.market_schedules.values():
            if config.coffee_type == coffee_type and config.active:
                return config
        return None
    
    def get_notification_schedule(self) -> List[Dict[str, Any]]:
        """
        Generate notification schedule for all active markets
        Returns list of scheduled events with timing information
        """
        schedule_events = []
        
        for market_id, market in self.get_active_markets().items():
            market_tz = pytz.timezone(market.timezone)
            
            # Market open notifications
            if self.notifications.market_open:
                schedule_events.append({
                    'market_id': market_id,
                    'market_name': market.name,
                    'market_name_vi': market.name_vi,
                    'event_type': 'market_open',
                    'time': market.open_time,
                    'timezone': market.timezone,
                    'coffee_type': market.coffee_type,
                    'active': True
                })
            
            # Market close notifications
            if self.notifications.market_close:
                schedule_events.append({
                    'market_id': market_id,
                    'market_name': market.name,
                    'market_name_vi': market.name_vi,
                    'event_type': 'market_close',
                    'time': market.close_time,
                    'timezone': market.timezone,
                    'coffee_type': market.coffee_type,
                    'active': True
                })
            
            # Pre-market notifications
            if self.notifications.pre_market:
                pre_market_time = self._calculate_pre_market_time(
                    market.open_time, 
                    market.pre_market_minutes
                )
                
                schedule_events.append({
                    'market_id': market_id,
                    'market_name': market.name,
                    'market_name_vi': market.name_vi,
                    'event_type': 'pre_market',
                    'time': pre_market_time,
                    'timezone': market.timezone,
                    'coffee_type': market.coffee_type,
                    'active': True
                })
        
        # Daily summary (in Vietnam timezone)
        if self.notifications.daily_summary:
            schedule_events.append({
                'market_id': 'daily_summary',
                'market_name': 'Daily Summary',
                'market_name_vi': 'Tổng kết hàng ngày',
                'event_type': 'daily_summary',
                'time': self.notifications.daily_summary_time,
                'timezone': self.settings['vietnam_timezone'],
                'coffee_type': 'all',
                'active': True
            })
        
        return schedule_events
    
    def _calculate_pre_market_time(self, market_open: str, minutes_before: int) -> str:
        """Calculate pre-market notification time"""
        try:
            open_time = datetime.strptime(market_open, "%H:%M")
            pre_market_time = open_time - timedelta(minutes=minutes_before)
            return pre_market_time.strftime("%H:%M")
        except Exception:
            return market_open
    
    def validate_telegram_config(self) -> bool:
        """Validate Telegram configuration"""
        if not self.telegram.bot_token:
            return False
        if not self.telegram.chat_id:
            return False
        return True
    
    def get_market_status_now(self, market_id: str) -> str:
        """Get current market status for a given market"""
        if market_id not in self.market_schedules:
            return "unknown"
        
        market = self.market_schedules[market_id]
        if not market.active:
            return "inactive"
        
        try:
            market_tz = pytz.timezone(market.timezone)
            now = datetime.now(market_tz)
            
            # Check if weekend and market doesn't trade weekends
            if market.weekdays_only and now.weekday() >= 5:
                return "closed_weekend"
            
            # Parse market hours
            open_time = datetime.strptime(market.open_time, "%H:%M").time()
            close_time = datetime.strptime(market.close_time, "%H:%M").time()
            current_time = now.time()
            
            if open_time <= current_time <= close_time:
                return "open"
            elif current_time < open_time:
                return "pre_market"
            else:
                return "after_hours"
        
        except Exception:
            return "error"
    
    def get_next_market_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get upcoming market events sorted by time"""
        events = []
        
        for market_id, market in self.get_active_markets().items():
            market_tz = pytz.timezone(market.timezone)
            now = datetime.now(market_tz)
            
            # Calculate next open and close times
            today_open = now.replace(
                hour=int(market.open_time.split(':')[0]),
                minute=int(market.open_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            today_close = now.replace(
                hour=int(market.close_time.split(':')[0]),
                minute=int(market.close_time.split(':')[1]),
                second=0,
                microsecond=0
            )
            
            # Add events if they're in the future
            if today_open > now:
                events.append({
                    'market_id': market_id,
                    'market_name': market.name_vi,
                    'event_type': 'market_open',
                    'datetime': today_open,
                    'vietnam_time': today_open.astimezone(self.vietnam_timezone)
                })
            
            if today_close > now:
                events.append({
                    'market_id': market_id,
                    'market_name': market.name_vi,
                    'event_type': 'market_close',
                    'datetime': today_close,
                    'vietnam_time': today_close.astimezone(self.vietnam_timezone)
                })
            
            # Add next day's events if today's have passed
            if today_open <= now:
                tomorrow_open = today_open + timedelta(days=1)
                events.append({
                    'market_id': market_id,
                    'market_name': market.name_vi,
                    'event_type': 'market_open',
                    'datetime': tomorrow_open,
                    'vietnam_time': tomorrow_open.astimezone(self.vietnam_timezone)
                })
            
            if today_close <= now:
                tomorrow_close = today_close + timedelta(days=1)
                events.append({
                    'market_id': market_id,
                    'market_name': market.name_vi,
                    'event_type': 'market_close',
                    'datetime': tomorrow_close,
                    'vietnam_time': tomorrow_close.astimezone(self.vietnam_timezone)
                })
        
        # Sort by datetime and return limited results
        events.sort(key=lambda x: x['datetime'])
        return events[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            'market_schedules': {
                market_id: {
                    'name': config.name,
                    'name_vi': config.name_vi,
                    'timezone': config.timezone,
                    'open_time': config.open_time,
                    'close_time': config.close_time,
                    'currency': config.currency,
                    'unit': config.unit,
                    'coffee_type': config.coffee_type,
                    'active': config.active
                }
                for market_id, config in self.market_schedules.items()
            },
            'notifications': {
                'market_open': self.notifications.market_open,
                'market_close': self.notifications.market_close,
                'pre_market': self.notifications.pre_market,
                'daily_summary': self.notifications.daily_summary,
                'daily_summary_time': self.notifications.daily_summary_time
            },
            'settings': self.settings
        }

def main():
    """Test the configuration manager"""
    config = MarketConfigManager()
    
    print("🎯 Coffee Market Configuration Manager")
    print("=" * 50)
    
    # Show active markets
    print("\n📊 Active Markets:")
    for market_id, market in config.get_active_markets().items():
        status = config.get_market_status_now(market_id)
        print(f"  • {market.name_vi} ({market_id})")
        print(f"    Trading: {market.open_time} - {market.close_time} {market.timezone}")
        print(f"    Status: {status}")
        print(f"    Coffee Type: {market.coffee_type}")
        print()
    
    # Show notification schedule
    print("📅 Notification Schedule:")
    schedule_events = config.get_notification_schedule()
    for event in schedule_events[:10]:  # Show first 10 events
        print(f"  • {event['event_type']}: {event['market_name_vi']} at {event['time']} ({event['timezone']})")
    
    # Show next market events
    print("\n⏰ Next Market Events:")
    next_events = config.get_next_market_events(5)
    for event in next_events:
        vn_time = event['vietnam_time'].strftime('%d/%m/%Y %H:%M')
        print(f"  • {event['event_type']}: {event['market_name']} - {vn_time} VN")
    
    # Configuration summary
    print(f"\n⚙️ Configuration Summary:")
    print(f"  • Total markets: {len(config.market_schedules)}")
    print(f"  • Active markets: {len(config.get_active_markets())}")
    print(f"  • Telegram configured: {config.validate_telegram_config()}")
    print(f"  • Vietnam timezone: {config.settings['vietnam_timezone']}")

if __name__ == "__main__":
    main()