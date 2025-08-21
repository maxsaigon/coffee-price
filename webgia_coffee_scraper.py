#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebGia Coffee Price Scraper
Crawls coffee prices from https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/
Vietnamese source for international coffee prices (more reliable than investing.com)
"""

import requests
import time
import re
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

class WebGiaCoffeeScraper:
    """
    Scraper for coffee futures prices from WebGia.com
    Supports Robusta (London), Arabica (NYC), and additional markets
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Target URL
        self.base_url = 'https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/'
        
        # Coffee market mappings (Vietnamese to English)
        self.coffee_markets = {
            'robusta_london': {
                'name_vi': 'Cà phê Robusta London',
                'name_en': 'Robusta Coffee (London)',
                'unit': 'USD/tonne',
                'symbol': 'LCF',
                'market': 'London Commodity Exchange'
            },
            'arabica_newyork': {
                'name_vi': 'Cà phê Arabica New York',
                'name_en': 'Arabica Coffee (NYC)', 
                'unit': 'cents/lb',
                'symbol': 'KC',
                'market': 'Intercontinental Exchange'
            },
            'arabica_brazil': {
                'name_vi': 'Cà phê Arabica Brazil',
                'name_en': 'Arabica Coffee (Brazil)',
                'unit': 'USD/bag',
                'symbol': 'BMF',
                'market': 'Brazil Mercantile & Futures Exchange'
            }
        }
        
        # CSS selectors for price extraction
        self.selectors = {
            'price_table': 'table.table',
            'price_rows': 'tbody tr',
            'price_cells': 'td',
            'price_container': '.price-container',
            'market_name': '.market-name, .commodity-name',
            'price_value': '.price-value, .current-price',
            'price_change': '.price-change, .change-value',
            'update_time': '.update-time, .last-updated'
        }
    
    def setup_session(self):
        """Configure session with Vietnamese-friendly headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })
    
    def get_page_content(self, max_retries: int = 3) -> Optional[str]:
        """Fetch page content with retry mechanism"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {self.base_url} (attempt {attempt + 1}/{max_retries})")
                
                # Add delay between attempts
                if attempt > 0:
                    time.sleep(2 ** attempt)
                
                response = self.session.get(self.base_url, timeout=15)
                response.raise_for_status()
                
                if len(response.text) < 1000:
                    logger.warning(f"Response too short ({len(response.text)} chars)")
                    continue
                
                logger.info(f"Successfully fetched WebGia page ({len(response.text)} chars)")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed for {self.base_url}")
                    return None
        
        return None
    
    def parse_coffee_prices(self, html: str) -> Dict[str, Any]:
        """Parse coffee price data from WebGia HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = {}
            
            # Check if page has dynamic content placeholders
            if 'webgia.com' in html and 'xem tại webgia.com' in html:
                logger.warning("Detected placeholder content - prices may be loaded dynamically")
                return self.try_selenium_fallback()
            
            # Look for coffee-specific headings and their associated tables
            coffee_sections = [
                ('robusta_london', ['Giá cà phê Robusta London', 'robusta london']),
                ('arabica_newyork', ['Giá cà phê Arabica New York', 'arabica new york']),
                ('arabica_brazil', ['Giá cà phê Arabica Brazil', 'arabica brazil'])
            ]
            
            for market_key, heading_patterns in coffee_sections:
                market_data = self.find_market_data(soup, heading_patterns, market_key)
                if market_data:
                    results[market_key] = market_data
                    logger.info(f"Successfully parsed {market_key}: {market_data.get('current_price', 'N/A')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing coffee prices: {e}")
            return {}
    
    def find_market_data(self, soup: BeautifulSoup, heading_patterns: list, market_key: str) -> Optional[Dict[str, Any]]:
        """Find market data by looking for specific headings"""
        try:
            # Find heading
            heading = None
            for pattern in heading_patterns:
                heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5'], 
                                  string=lambda text: text and pattern.lower() in text.lower())
                if heading:
                    logger.debug(f"Found heading for {market_key}: {heading.get_text().strip()}")
                    break
            
            if not heading:
                logger.debug(f"No heading found for {market_key}")
                return None
            
            # Find the table following this heading
            current = heading
            table = None
            
            # Look in next siblings
            for sibling in heading.find_all_next():
                if sibling.name == 'table':
                    table = sibling
                    break
                # Stop if we hit another coffee heading
                if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    if any(coffee in sibling.get_text().lower() for coffee in ['cà phê', 'coffee']):
                        break
            
            if not table:
                logger.debug(f"No table found for {market_key}")
                return None
            
            # Parse the table
            return self.parse_market_table(table, market_key)
            
        except Exception as e:
            logger.error(f"Error finding market data for {market_key}: {e}")
            return None
    
    def parse_market_table(self, table, market_key: str) -> Optional[Dict[str, Any]]:
        """Parse a specific market table"""
        try:
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                return None
            
            # Skip header row, look at data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Skip rows with placeholder text
                if any('webgia.com' in text for text in cell_texts):
                    continue
                
                # Try to extract price from the row
                market_data = self.extract_price_data(cell_texts, row)
                if market_data and 'current_price' in market_data:
                    market_data['market_key'] = market_key
                    return market_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing market table for {market_key}: {e}")
            return None
    
    def try_selenium_fallback(self) -> Dict[str, Any]:
        """Try to get prices using Selenium when JavaScript is required"""
        try:
            logger.info("Attempting Selenium fallback for dynamic content")
            
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            try:
                logger.info("Loading WebGia page with Selenium...")
                driver.get(self.base_url)
                
                # Wait for content to load
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_element(By.TAG_NAME, "table")
                )
                
                # Wait a bit more for dynamic content
                time.sleep(3)
                
                # Get the updated HTML
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try parsing again with dynamic content
                results = {}
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        
                        # Skip placeholder content
                        if any('webgia.com' in text for text in cell_texts):
                            continue
                        
                        # Look for price patterns
                        price_data = self.extract_price_data(cell_texts, row)
                        if price_data and 'current_price' in price_data:
                            # Try to determine which market this is
                            market_key = self.identify_market_from_context(table, soup)
                            if market_key:
                                results[market_key] = price_data
                                logger.info(f"Selenium extracted {market_key}: {price_data['current_price']}")
                
                return results
                
            finally:
                driver.quit()
                
        except ImportError:
            logger.warning("Selenium not available for dynamic content fallback")
            return {}
        except Exception as e:
            logger.error(f"Selenium fallback failed: {e}")
            return {}
    
    def identify_market_from_context(self, table, soup: BeautifulSoup) -> Optional[str]:
        """Identify market type from table context"""
        try:
            # Find preceding heading
            current = table
            while current.previous_sibling:
                current = current.previous_sibling
                if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    heading_text = current.get_text().lower()
                    
                    if 'robusta' in heading_text and 'london' in heading_text:
                        return 'robusta_london'
                    elif 'arabica' in heading_text and 'new york' in heading_text:
                        return 'arabica_newyork'
                    elif 'arabica' in heading_text and 'brazil' in heading_text:
                        return 'arabica_brazil'
            
            return None
            
        except Exception as e:
            logger.error(f"Error identifying market from context: {e}")
            return None
    
    def extract_price_data(self, cell_texts: List[str], row_element) -> Optional[Dict[str, Any]]:
        """Extract price data from table row"""
        try:
            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'webgia.com'
            }
            
            # Try different cell arrangements
            for i, cell_text in enumerate(cell_texts):
                # Look for price patterns (numbers with currency symbols or decimals)
                if re.search(r'[\d,]+\.?\d*', cell_text) and not cell_text.isalpha():
                    
                    # Clean price text
                    price_match = re.search(r'([\d,]+\.?\d*)', cell_text.replace(',', ''))
                    if price_match:
                        try:
                            price_value = float(price_match.group(1))
                            data['current_price'] = price_value
                            data['price_display'] = cell_text
                            logger.debug(f"Extracted price: {price_value} from '{cell_text}'")
                        except ValueError:
                            continue
                
                # Look for change indicators
                if any(indicator in cell_text for indicator in ['+', '-', '%', '↑', '↓']):
                    data['change'] = cell_text
                    logger.debug(f"Extracted change: {cell_text}")
                
                # Market name (usually first cell)
                if i == 0:
                    data['market_name'] = cell_text
            
            # Validate we have at least a price
            if 'current_price' in data:
                return data
            else:
                logger.debug(f"No valid price found in row: {cell_texts}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting price data: {e}")
            return None
    
    def identify_market_type(self, market_name: str, cell_texts: List[str]) -> Optional[str]:
        """Identify which coffee market based on text content"""
        market_name = market_name.lower()
        full_text = ' '.join(cell_texts).lower()
        
        # Check for specific market indicators
        if 'robusta' in market_name or 'london' in full_text:
            return 'robusta_london'
        elif 'arabica' in market_name and ('new york' in full_text or 'nyc' in full_text or 'ny' in full_text):
            return 'arabica_newyork' 
        elif 'arabica' in market_name and ('brazil' in full_text or 'bmf' in full_text or 'bra' in full_text):
            return 'arabica_brazil'
        elif 'arabica' in market_name:  # Default arabica to NYC
            return 'arabica_newyork'
        elif 'robusta' in full_text:
            return 'robusta_london'
        
        return None
    
    def scrape_all_prices(self) -> Dict[str, Any]:
        """Scrape all coffee prices from WebGia"""
        logger.info("Starting WebGia coffee price scraping...")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'webgia.com',
            'international': {},
            'vietnam': {},
            'success_count': 0,
            'total_count': 0
        }
        
        # Get page content
        html = self.get_page_content()
        if not html:
            logger.error("Failed to get page content")
            return results
        
        # Parse prices
        price_data = self.parse_coffee_prices(html)
        
        if not price_data:
            logger.warning("No price data extracted from WebGia")
            return results
        
        # Process extracted data
        for market_key, data in price_data.items():
            if market_key in self.coffee_markets:
                market_info = self.coffee_markets[market_key]
                
                # Enrich data with market information
                enhanced_data = {
                    **data,
                    'name': market_info['name_en'],
                    'name_vi': market_info['name_vi'],
                    'unit': market_info['unit'],
                    'symbol': market_info['symbol'],
                    'market': market_info['market']
                }
                
                results['international'][market_key] = enhanced_data
                results['success_count'] += 1
                
                logger.info(f"✅ Successfully scraped {market_key}: {data.get('current_price', 'N/A')}")
            
            results['total_count'] += 1
        
        logger.info(f"WebGia scraping completed: {results['success_count']}/{results['total_count']} successful")
        return results
    
    def format_telegram_message(self, price_data: Dict[str, Any]) -> str:
        """Format price data for Telegram message (Vietnamese)"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        message = f"☕ **BÁO GIÁ CÀ PHÊ QUỐC TẾ**\n"
        message += f"📅 {timestamp} (GMT+7)\n\n"
        
        international = price_data.get('international', {})
        
        # Robusta London
        if 'robusta_london' in international:
            robusta = international['robusta_london']
            if 'current_price' in robusta:
                price = robusta['current_price']
                change = robusta.get('change', 'N/A')
                price_vnd = price * 26000  # Using updated VND rate
                
                message += f"🌱 **ROBUSTA (London)**\n"
                message += f"💰 Giá: ${price:,.2f}/tấn\n"
                message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
                message += f"📈 Thay đổi: {change}\n\n"
        
        # Arabica New York
        if 'arabica_newyork' in international:
            arabica = international['arabica_newyork']
            if 'current_price' in arabica:
                price = arabica['current_price']
                change = arabica.get('change', 'N/A')
                
                # Convert cents/lb to USD/tonne if needed
                if arabica.get('unit') == 'cents/lb':
                    price_usd_tonne = (price / 100) * 2204.62
                    price_vnd = price_usd_tonne * 26000
                    
                    message += f"☕ **ARABICA (New York)**\n"
                    message += f"💰 Giá: {price:.2f} cents/lb\n"
                    message += f"💰 USD: ${price_usd_tonne:,.2f}/tấn\n"
                    message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
                    message += f"📈 Thay đổi: {change}\n\n"
                else:
                    price_vnd = price * 26000
                    message += f"☕ **ARABICA (New York)**\n"
                    message += f"💰 Giá: ${price:,.2f}/tấn\n"
                    message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
                    message += f"📈 Thay đổi: {change}\n\n"
        
        # Arabica Brazil (if available)
        if 'arabica_brazil' in international:
            brazil = international['arabica_brazil']
            if 'current_price' in brazil:
                price = brazil['current_price']
                change = brazil.get('change', 'N/A')
                
                message += f"🇧🇷 **ARABICA (Brazil)**\n"
                message += f"💰 Giá: ${price:,.2f}/bag\n"
                message += f"📈 Thay đổi: {change}\n\n"
        
        # Success indicator
        success_rate = price_data.get('success_count', 0) / max(price_data.get('total_count', 1), 1) * 100
        
        if success_rate == 100:
            message += "✅ Tất cả dữ liệu cập nhật thành công"
        elif success_rate >= 50:
            message += "⚠️ Một số dữ liệu không khả dụng"
        else:
            message += "❌ Có lỗi khi cập nhật dữ liệu"
        
        message += f"\n\n🔗 Nguồn: WebGia.com"
        message += f"\n🤖 Tự động cập nhật bởi GiaNongSan Bot"
        
        return message

def main():
    """Test function"""
    scraper = WebGiaCoffeeScraper()
    
    print("🚀 Starting WebGia coffee price scraper...")
    results = scraper.scrape_all_prices()
    
    print("\n📊 Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    if results.get('success_count', 0) > 0:
        print("\n📱 Telegram Message Preview:")
        message = scraper.format_telegram_message(results)
        print(message)
    else:
        print("\n❌ No price data extracted - check selectors or website structure")

if __name__ == "__main__":
    main()