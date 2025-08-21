#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coffee Price Scraper from Investing.com
Crawls Robusta (London) and Arabica (NYC) coffee futures prices
"""

import requests
import time
import re
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coffee_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InvestingCoffeeScraper:
    """
    Scraper for coffee futures prices from Investing.com
    Supports multiple fallback strategies and Vietnamese market focus
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Target URLs for coffee futures
        self.urls = {
            'robusta': {
                'url': 'https://www.investing.com/commodities/london-coffee',
                'name': 'Robusta Coffee (London)',
                'unit': 'USD/tonne',
                'symbol': 'LCF'
            },
            'arabica': {
                'url': 'https://www.investing.com/commodities/us-coffee-c',
                'name': 'Arabica Coffee (NYC)',
                'unit': 'cents/lb',
                'symbol': 'KC'
            }
        }
        
        # Price selectors (updated for current Investing.com structure)
        self.selectors = {
            'price': [
                '[data-test="instrument-price-last"]',
                '.text-2xl',
                '.instrument-price_last__JQN7_',
                '.pid-8830-last',  # Robusta specific
                '.pid-8832-last',  # Arabica specific
            ],
            'change': [
                '[data-test="instrument-price-change"]',
                '.instrument-price_change__GYX5t',
                '.pid-8830-pc',
                '.pid-8832-pc',
            ],
            'change_percent': [
                '[data-test="instrument-price-change-percent"]',
                '.instrument-price_change-percent__5_bhJ',
                '.pid-8830-pcp',
                '.pid-8832-pcp',
            ],
            'volume': [
                '.pid-8830-turnover',
                '.pid-8832-turnover',
                '[data-test="trading-volume"]'
            ]
        }
    
    def setup_session(self):
        """Configure session with headers to mimic real browser"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def get_page_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch page content with retry mechanism
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    time.sleep(2 ** attempt)
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                if len(response.text) < 1000:
                    logger.warning(f"Response too short ({len(response.text)} chars), might be blocked")
                    continue
                
                if 'Just a moment' in response.text or 'Cloudflare' in response.text:
                    logger.warning("Detected Cloudflare protection")
                    return None
                
                logger.info(f"Successfully fetched {url}")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for {url}")
                    return None
        
        return None
    
    def parse_coffee_price(self, html: str, coffee_type: str) -> Optional[Dict[str, Any]]:
        """
        Parse coffee price data from HTML
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'coffee_type': coffee_type,
                'source': 'investing.com'
            }
            
            # Try to find price using multiple selectors
            price_text = None
            for selector in self.selectors['price']:
                price_element = soup.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    logger.info(f"Found price with selector '{selector}': {price_text}")
                    break
            
            if not price_text:
                logger.error(f"Could not find price for {coffee_type}")
                return None
            
            # Clean and parse price
            price_cleaned = re.sub(r'[^\d.,\-]', '', price_text)
            price_cleaned = price_cleaned.replace(',', '')
            
            try:
                current_price = float(price_cleaned)
                data['current_price'] = current_price
                data['price_display'] = price_text
            except ValueError:
                logger.error(f"Could not parse price: {price_text}")
                return None
            
            # Try to get change data
            for selector in self.selectors['change']:
                change_element = soup.select_one(selector)
                if change_element:
                    change_text = change_element.get_text(strip=True)
                    data['change'] = change_text
                    break
            
            # Try to get change percentage
            for selector in self.selectors['change_percent']:
                pct_element = soup.select_one(selector)
                if pct_element:
                    pct_text = pct_element.get_text(strip=True)
                    data['change_percent'] = pct_text
                    break
            
            # Try to get volume
            for selector in self.selectors['volume']:
                vol_element = soup.select_one(selector)
                if vol_element:
                    vol_text = vol_element.get_text(strip=True)
                    data['volume'] = vol_text
                    break
            
            # Add metadata
            data['unit'] = self.urls[coffee_type]['unit']
            data['name'] = self.urls[coffee_type]['name']
            data['symbol'] = self.urls[coffee_type]['symbol']
            
            logger.info(f"Successfully parsed {coffee_type}: {current_price}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing {coffee_type} price: {e}")
            return None
    
    def scrape_single_coffee(self, coffee_type: str) -> Optional[Dict[str, Any]]:
        """
        Scrape price for a single coffee type
        """
        if coffee_type not in self.urls:
            logger.error(f"Unknown coffee type: {coffee_type}")
            return None
        
        url = self.urls[coffee_type]['url']
        html = self.get_page_content(url)
        
        if not html:
            logger.error(f"Failed to get content for {coffee_type}")
            return None
        
        return self.parse_coffee_price(html, coffee_type)
    
    def scrape_all_prices(self) -> Dict[str, Any]:
        """
        Scrape prices for all coffee types
        """
        logger.info("Starting full coffee price scraping...")
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'international': {},
            'vietnam': {},  # Placeholder for future Vietnam sources
            'success_count': 0,
            'total_count': len(self.urls)
        }
        
        for coffee_type in self.urls.keys():
            logger.info(f"Scraping {coffee_type}...")
            price_data = self.scrape_single_coffee(coffee_type)
            
            if price_data:
                results['international'][coffee_type] = price_data
                results['success_count'] += 1
                logger.info(f"✅ Successfully scraped {coffee_type}")
            else:
                logger.warning(f"❌ Failed to scrape {coffee_type}")
                results['international'][coffee_type] = {
                    'error': 'Failed to scrape',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        logger.info(f"Scraping completed: {results['success_count']}/{results['total_count']} successful")
        return results
    
    def format_telegram_message(self, price_data: Dict[str, Any]) -> str:
        """
        Format price data for Telegram message (Vietnamese)
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        message = f"☕ **BÁO GIÁ CÀ PHÊ QUỐC TẾ**\n"
        message += f"📅 {timestamp} (GMT+7)\n\n"
        
        international = price_data.get('international', {})
        
        # Robusta Price
        if 'robusta' in international and 'current_price' in international['robusta']:
            robusta = international['robusta']
            price = robusta['current_price']
            change = robusta.get('change', 'N/A')
            change_pct = robusta.get('change_percent', 'N/A')
            
            # Convert to Vietnamese dong (approximate, 1 USD = 24,000 VND)
            price_vnd = price * 24000
            
            message += f"🌱 **ROBUSTA (London)**\n"
            message += f"💰 Giá: ${price:,.2f}/tấn\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            message += f"📈 Thay đổi: {change} ({change_pct})\n\n"
        
        # Arabica Price
        if 'arabica' in international and 'current_price' in international['arabica']:
            arabica = international['arabica']
            price = arabica['current_price']
            change = arabica.get('change', 'N/A')
            change_pct = arabica.get('change_percent', 'N/A')
            
            # Convert cents/lb to USD/tonne (1 tonne = 2204.62 lbs)
            price_usd_tonne = (price / 100) * 2204.62
            price_vnd = price_usd_tonne * 24000
            
            message += f"☕ **ARABICA (New York)**\n"
            message += f"💰 Giá: {price:.2f} cents/lb\n"
            message += f"💰 USD: ${price_usd_tonne:,.2f}/tấn\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            message += f"📈 Thay đổi: {change} ({change_pct})\n\n"
        
        # Add market analysis
        success_rate = price_data.get('success_count', 0) / price_data.get('total_count', 1) * 100
        
        if success_rate == 100:
            message += "✅ Tất cả dữ liệu cập nhật thành công"
        elif success_rate >= 50:
            message += "⚠️ Một số dữ liệu không khả dụng"
        else:
            message += "❌ Có lỗi khi cập nhật dữ liệu"
        
        message += f"\n\n🔗 Nguồn: Investing.com"
        message += f"\n🤖 Tự động cập nhật bởi GiaNongSan Bot"
        
        return message
    
    def get_fallback_data(self, coffee_type: str) -> Optional[Dict[str, Any]]:
        """
        Fallback method using alternative scraping if main method fails
        """
        logger.info(f"Trying fallback method for {coffee_type}")
        
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper()
            
            url = self.urls[coffee_type]['url']
            response = scraper.get(url, timeout=15)
            
            if response.status_code == 200:
                return self.parse_coffee_price(response.text, coffee_type)
            
        except ImportError:
            logger.warning("Cloudscraper not available for fallback")
        except Exception as e:
            logger.error(f"Fallback method failed: {e}")
        
        return None

def main():
    """Main function for testing"""
    scraper = InvestingCoffeeScraper()
    
    print("🚀 Starting coffee price scraper...")
    results = scraper.scrape_all_prices()
    
    print("\n📊 Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print("\n📱 Telegram Message Preview:")
    message = scraper.format_telegram_message(results)
    print(message)

if __name__ == "__main__":
    main()