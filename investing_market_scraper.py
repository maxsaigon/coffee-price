#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Investing.com Coffee Market Scraper
Focuses on open/close prices with market timing for coffee futures
Sends Telegram notifications based on market hours
"""

import requests
import time
import re
import json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any, List
import logging
import pytz
import schedule
import threading
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketHours:
    """Coffee market trading hours"""
    name: str
    open_time: str  # Format: "HH:MM"
    close_time: str  # Format: "HH:MM" 
    timezone: str
    weekend_closed: bool = True

@dataclass
class PricePoint:
    """Individual price data point"""
    price: float
    change: float
    change_percent: float
    volume: str
    timestamp: datetime
    market_status: str  # "open", "closed", "pre_market", "after_hours"

class InvestingMarketScraper:
    """
    Advanced scraper for coffee futures with market timing awareness
    Tracks open/close prices and sends notifications at market events
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Coffee markets and their hours
        self.markets = {
            'robusta': {
                'url': 'https://www.investing.com/commodities/london-coffee',
                'name': 'Robusta Coffee',
                'symbol': 'LCF',
                'exchange': 'ICE Europe (London)',
                'unit': 'USD/tonne',
                'market_hours': MarketHours(
                    name="ICE Europe",
                    open_time="09:00",
                    close_time="17:30", 
                    timezone="Europe/London"
                )
            },
            'arabica': {
                'url': 'https://www.investing.com/commodities/us-coffee-c', 
                'name': 'Arabica Coffee',
                'symbol': 'KC',
                'exchange': 'ICE US (New York)',
                'unit': 'cents/lb',
                'market_hours': MarketHours(
                    name="ICE US",
                    open_time="09:15",
                    close_time="14:30",
                    timezone="America/New_York"
                )
            }
        }
        
        # Vietnam timezone for notifications
        self.vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
        # Enhanced selectors for different price types
        self.selectors = {
            'current_price': [
                '[data-test="instrument-price-last"]',
                '.text-2xl.font-bold',
                '.instrument-price_last__JQN7_',
                '.pid-8830-last',  # Robusta
                '.pid-8832-last',  # Arabica
                '.text-xl.font-semibold'
            ],
            'open_price': [
                '[data-test="open-price"]',
                '.pid-8830-open',
                '.pid-8832-open', 
                'td[data-test="open"]',
                '.summary-item-open .summary-item-value'
            ],
            'high_price': [
                '[data-test="high-price"]',
                '.pid-8830-high',
                '.pid-8832-high',
                'td[data-test="high"]',
                '.summary-item-high .summary-item-value'
            ],
            'low_price': [
                '[data-test="low-price"]',
                '.pid-8830-low', 
                '.pid-8832-low',
                'td[data-test="low"]',
                '.summary-item-low .summary-item-value'
            ],
            'change': [
                '[data-test="instrument-price-change"]',
                '.instrument-price_change__GYX5t',
                '.pid-8830-pc',
                '.pid-8832-pc'
            ],
            'change_percent': [
                '[data-test="instrument-price-change-percent"]', 
                '.instrument-price_change-percent__5_bhJ',
                '.pid-8830-pcp',
                '.pid-8832-pcp'
            ],
            'volume': [
                '.pid-8830-turnover',
                '.pid-8832-turnover',
                '[data-test="trading-volume"]',
                '.summary-item-volume .summary-item-value'
            ],
            'prev_close': [
                '.pid-8830-prev-close',
                '.pid-8832-prev-close',
                '[data-test="prev-close"]',
                '.summary-item-prev-close .summary-item-value'
            ]
        }

        # Price history for trend analysis
        self.price_history = {
            'robusta': [],
            'arabica': []
        }
        
    def setup_session(self):
        """Configure session with rotating user agents"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        import random
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        })

    def get_market_status(self, coffee_type: str) -> str:
        """Determine if market is open, closed, or in pre/after hours"""
        if coffee_type not in self.markets:
            return "unknown"
            
        market_info = self.markets[coffee_type]
        market_hours = market_info['market_hours']
        
        # Get current time in market timezone
        market_tz = pytz.timezone(market_hours.timezone)
        now = datetime.now(market_tz)
        
        # Check if weekend
        if market_hours.weekend_closed and now.weekday() >= 5:  # Saturday=5, Sunday=6
            return "closed_weekend"
        
        # Parse market hours
        open_time = datetime.strptime(market_hours.open_time, "%H:%M").time()
        close_time = datetime.strptime(market_hours.close_time, "%H:%M").time()
        current_time = now.time()
        
        if open_time <= current_time <= close_time:
            return "open"
        elif current_time < open_time:
            return "pre_market"
        else:
            return "after_hours"

    def get_page_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Enhanced page content fetching with better error handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                if attempt > 0:
                    # Exponential backoff with jitter
                    delay = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(delay)
                
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                
                # Check response quality
                content = response.text
                if len(content) < 5000:
                    logger.warning(f"Response suspiciously short: {len(content)} chars")
                    continue
                
                # Check for common blocking patterns
                blocking_indicators = [
                    'Just a moment',
                    'Cloudflare', 
                    'Access denied',
                    'blocked',
                    'captcha',
                    'Please verify you are a human'
                ]
                
                content_lower = content.lower()
                if any(indicator in content_lower for indicator in blocking_indicators):
                    logger.warning("Detected anti-bot protection")
                    continue
                
                logger.info(f"Successfully fetched {url} ({len(content)} chars)")
                return content
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
        
        logger.error(f"All attempts failed for {url}")
        return None

    def parse_price_data(self, html: str, coffee_type: str) -> Optional[Dict[str, Any]]:
        """Enhanced parsing for all price types (current, open, high, low, etc.)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            market_status = self.get_market_status(coffee_type)
            
            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'coffee_type': coffee_type,
                'market_status': market_status,
                'source': 'investing.com',
                'market_info': self.markets[coffee_type]
            }
            
            # Extract all price types
            price_types = ['current_price', 'open_price', 'high_price', 'low_price', 'prev_close']
            
            for price_type in price_types:
                value = self.extract_price_value(soup, price_type)
                if value is not None:
                    data[price_type] = value
                    logger.info(f"Found {price_type}: {value}")
            
            # Extract change information
            change_value = self.extract_text_value(soup, 'change')
            if change_value:
                data['change'] = change_value
                # Try to parse numeric change
                change_numeric = self.parse_numeric_change(change_value)
                if change_numeric is not None:
                    data['change_numeric'] = change_numeric
            
            change_percent = self.extract_text_value(soup, 'change_percent')
            if change_percent:
                data['change_percent'] = change_percent
                # Try to parse numeric percent
                percent_numeric = self.parse_percent_change(change_percent)
                if percent_numeric is not None:
                    data['change_percent_numeric'] = percent_numeric
            
            # Extract volume
            volume = self.extract_text_value(soup, 'volume')
            if volume:
                data['volume'] = volume
            
            # Validate that we got at least current price
            if 'current_price' not in data:
                logger.error(f"No current price found for {coffee_type}")
                return None
            
            logger.info(f"Successfully parsed {coffee_type}: {data.get('current_price', 'N/A')}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {coffee_type}: {e}")
            return None

    def extract_price_value(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """Extract and parse numeric price values"""
        selectors = self.selectors.get(price_type, [])
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Clean and parse price
                    price_cleaned = re.sub(r'[^\d.,\-]', '', text)
                    price_cleaned = price_cleaned.replace(',', '')
                    
                    if price_cleaned:
                        price_value = float(price_cleaned)
                        logger.debug(f"Extracted {price_type} with selector '{selector}': {price_value}")
                        return price_value
            except (ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse {price_type} with selector '{selector}': {e}")
                continue
        
        return None

    def extract_text_value(self, soup: BeautifulSoup, value_type: str) -> Optional[str]:
        """Extract text values (like change, volume)"""
        selectors = self.selectors.get(value_type, [])
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        logger.debug(f"Extracted {value_type} with selector '{selector}': {text}")
                        return text
            except AttributeError:
                continue
        
        return None

    def parse_numeric_change(self, change_text: str) -> Optional[float]:
        """Parse numeric change from text like '+1.25' or '-0.5'"""
        try:
            # Extract number with sign
            match = re.search(r'([+-]?[\d.,]+)', change_text)
            if match:
                number_str = match.group(1).replace(',', '')
                return float(number_str)
        except:
            pass
        return None

    def parse_percent_change(self, percent_text: str) -> Optional[float]:
        """Parse percentage change from text like '+1.25%' or '-0.5%'"""
        try:
            # Extract percentage
            match = re.search(r'([+-]?[\d.,]+)', percent_text)
            if match:
                number_str = match.group(1).replace(',', '')
                return float(number_str)
        except:
            pass
        return None

    def scrape_coffee_prices(self) -> Dict[str, Any]:
        """Scrape current prices for all coffee types"""
        logger.info("Starting comprehensive coffee market scraping...")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'vietnam_time': datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S'),
            'markets': {},
            'success_count': 0,
            'total_markets': len(self.markets),
            'overall_market_status': 'mixed'
        }
        
        market_statuses = []
        
        for coffee_type, market_info in self.markets.items():
            logger.info(f"Scraping {coffee_type} from {market_info['name']}...")
            
            html = self.get_page_content(market_info['url'])
            if not html:
                results['markets'][coffee_type] = {
                    'error': 'Failed to fetch data',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                continue
            
            price_data = self.parse_price_data(html, coffee_type)
            if price_data:
                results['markets'][coffee_type] = price_data
                results['success_count'] += 1
                market_statuses.append(price_data['market_status'])
                
                # Add to price history for trend analysis
                if coffee_type not in self.price_history:
                    self.price_history[coffee_type] = []
                
                self.price_history[coffee_type].append({
                    'price': price_data.get('current_price'),
                    'timestamp': price_data['timestamp']
                })
                
                # Keep only last 100 data points
                if len(self.price_history[coffee_type]) > 100:
                    self.price_history[coffee_type] = self.price_history[coffee_type][-100:]
                
                logger.info(f"✅ Successfully scraped {coffee_type}")
            else:
                results['markets'][coffee_type] = {
                    'error': 'Failed to parse price data', 
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                logger.warning(f"❌ Failed to scrape {coffee_type}")
        
        # Determine overall market status
        if market_statuses:
            if all(status == 'open' for status in market_statuses):
                results['overall_market_status'] = 'open'
            elif all(status in ['closed_weekend', 'after_hours'] for status in market_statuses):
                results['overall_market_status'] = 'closed'
            else:
                results['overall_market_status'] = 'mixed'
        
        logger.info(f"Scraping completed: {results['success_count']}/{results['total_markets']} successful")
        return results

    def format_market_telegram_message(self, price_data: Dict[str, Any], message_type: str = "update") -> str:
        """Format comprehensive market data for Telegram with Vietnamese text"""
        vn_time = datetime.now(self.vn_tz).strftime('%d/%m/%Y %H:%M:%S')
        
        # Message header based on type
        if message_type == "market_open":
            header = "🔔 **THỊ TRƯỜNG CÀ PHÊ MỞ CỬA**"
        elif message_type == "market_close":
            header = "🔔 **THỊ TRƯỜNG CÀ PHÊ ĐÓNG CỬA**"
        else:
            header = "☕ **BÁO GIÁ CÀ PHÊ QUỐC TẾ**"
        
        message = f"{header}\n"
        message += f"📅 {vn_time} (GMT+7)\n"
        message += f"📊 Trạng thái thị trường: {self.get_market_status_vietnamese(price_data.get('overall_market_status', 'unknown'))}\n\n"
        
        markets = price_data.get('markets', {})
        
        # Robusta (London) 
        if 'robusta' in markets and 'current_price' in markets['robusta']:
            robusta = markets['robusta']
            message += self.format_single_market_info(robusta, "🌱 **ROBUSTA (London ICE)**")
        
        # Arabica (New York)
        if 'arabica' in markets and 'current_price' in markets['arabica']:
            arabica = markets['arabica']  
            message += self.format_single_market_info(arabica, "☕ **ARABICA (New York ICE)**", convert_unit=True)
        
        # Market summary
        success_rate = (price_data.get('success_count', 0) / price_data.get('total_markets', 1)) * 100
        
        if success_rate == 100:
            message += "✅ **Tất cả dữ liệu cập nhật thành công**"
        elif success_rate >= 50:
            message += "⚠️ **Một số dữ liệu không khả dụng**"
        else:
            message += "❌ **Có lỗi khi cập nhật dữ liệu**"
        
        message += f"\n\n🔗 **Nguồn:** Investing.com"
        message += f"\n🤖 **GiaNongSan Bot** - Cập nhật tự động"
        
        return message

    def format_single_market_info(self, market_data: Dict[str, Any], title: str, convert_unit: bool = False) -> str:
        """Format individual market information"""
        message = f"{title}\n"
        
        current_price = market_data.get('current_price')
        unit = market_data.get('market_info', {}).get('unit', '')
        
        if current_price is not None:
            if convert_unit and unit == 'cents/lb':
                # Convert cents/lb to USD/tonne for easier comparison
                price_usd_tonne = (current_price / 100) * 2204.62
                price_vnd = price_usd_tonne * 25000  # Updated exchange rate
                
                message += f"💰 **Giá hiện tại:** {current_price:.2f} cents/lb\n"
                message += f"💰 **USD/tấn:** ${price_usd_tonne:,.2f}\n"
                message += f"💸 **VND/tấn:** {price_vnd:,.0f}\n"
            else:
                price_vnd = current_price * 25000
                message += f"💰 **Giá hiện tại:** ${current_price:,.2f}/{unit.split('/')[-1] if '/' in unit else unit}\n"
                message += f"💸 **VND/tấn:** {price_vnd:,.0f}\n"
        
        # Show open/high/low if available
        if market_data.get('open_price'):
            message += f"📈 **Mở cửa:** {market_data['open_price']:.2f}\n"
        
        if market_data.get('high_price') and market_data.get('low_price'):
            message += f"📊 **Cao/Thấp:** {market_data['high_price']:.2f} / {market_data['low_price']:.2f}\n"
        
        # Change information
        change = market_data.get('change_numeric') 
        change_pct = market_data.get('change_percent_numeric')
        
        if change is not None and change_pct is not None:
            direction = "📈" if change >= 0 else "📉"
            sign = "+" if change >= 0 else ""
            message += f"{direction} **Thay đổi:** {sign}{change:.2f} ({sign}{change_pct:.2f}%)\n"
        
        # Volume
        if market_data.get('volume'):
            message += f"📊 **Khối lượng:** {market_data['volume']}\n"
        
        # Market status
        status_vn = self.get_market_status_vietnamese(market_data.get('market_status', 'unknown'))
        message += f"🕐 **Trạng thái:** {status_vn}\n\n"
        
        return message

    def get_market_status_vietnamese(self, status: str) -> str:
        """Convert market status to Vietnamese"""
        status_map = {
            'open': 'Đang mở',
            'closed': 'Đã đóng',
            'closed_weekend': 'Đóng cửa cuối tuần', 
            'pre_market': 'Trước giờ mở cửa',
            'after_hours': 'Sau giờ đóng cửa',
            'mixed': 'Hỗn hợp',
            'unknown': 'Không xác định'
        }
        return status_map.get(status, status)

def main():
    """Test the enhanced scraper"""
    scraper = InvestingMarketScraper()
    
    print("🚀 Starting enhanced Investing.com market scraper...")
    results = scraper.scrape_coffee_prices()
    
    print("\n📊 Raw Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    
    print("\n📱 Telegram Message Preview:")
    message = scraper.format_market_telegram_message(results)
    print(message)

if __name__ == "__main__":
    main()