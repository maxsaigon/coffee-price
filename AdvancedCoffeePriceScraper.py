"""
Advanced Coffee Price Scraper với các tính năng anti-detection
Hỗ trợ bypass Cloudflare và rotation proxy
"""

import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass
from enum import Enum

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperMode(Enum):
    """Các chế độ scraping"""
    BASIC = "basic"
    CLOUDSCRAPER = "cloudscraper"
    SELENIUM = "selenium"

@dataclass
class CoffeePrice:
    """Data class cho giá cà phê"""
    current_price: float
    change: float = 0
    change_percent: float = 0
    open: float = 0
    high: float = 0
    low: float = 0
    volume: int = 0
    last_update: str = ""
    coffee_type: str = ""
    unit: str = ""
    source: str = "Investing.com"

class AdvancedCoffeeScraper:
    """
    Scraper nâng cao với khả năng bypass protection
    """
    
    def __init__(self, mode: ScraperMode = ScraperMode.CLOUDSCRAPER, use_proxy: bool = False):
        self.mode = mode
        self.use_proxy = use_proxy
        self.session = self._init_session()
        
        # URLs configuration
        self.urls = {
            'robusta': {
                'url': 'https://www.investing.com/commodities/london-coffee',
                'name': 'Coffee Robusta (London)',
                'unit': 'USD/MT',
                'selectors': {
                    'price': ['[data-test="instrument-price-last"]', '.text-2xl', '.instrument-price_last'],
                    'change': ['[data-test="instrument-price-change"]', '.instrument-price_change'],
                    'percent': ['[data-test="instrument-price-change-percent"]', '.instrument-price_change-percent'],
                    'open': ['[data-test="open"]', 'dd:contains("Open") + dd'],
                    'high': ['[data-test="high"]', 'dd:contains("Day\'s Range")'],
                    'volume': ['[data-test="volume"]', 'dd:contains("Volume") + dd']
                }
            },
            'arabica': {
                'url': 'https://www.investing.com/commodities/us-coffee-c',
                'name': 'Coffee C Arabica (New York)',
                'unit': 'USc/lb',
                'selectors': {
                    # Same selectors structure
                    'price': ['[data-test="instrument-price-last"]', '.text-2xl', '.instrument-price_last'],
                    'change': ['[data-test="instrument-price-change"]', '.instrument-price_change'],
                    'percent': ['[data-test="instrument-price-change-percent"]', '.instrument-price_change-percent']
                }
            }
        }
        
        # Proxy list (free proxies - thay bằng proxy premium cho production)
        self.proxy_list = [
            # 'http://proxy1:port',
            # 'http://proxy2:port',
        ] if use_proxy else []
        
    def _init_session(self):
        """Khởi tạo session dựa trên mode"""
        if self.mode == ScraperMode.CLOUDSCRAPER:
            # Cloudscraper với browser emulation
            return cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
        elif self.mode == ScraperMode.BASIC:
            session = requests.Session()
            session.headers.update(self._get_headers())
            return session
        else:
            # Selenium mode - return None, sẽ init khi cần
            return None
    
    def _get_headers(self) -> Dict:
        """Headers giả lập browser thật"""
        headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        ]
        return random.choice(headers_list)
    
    def _get_proxy(self) -> Optional[Dict]:
        """Lấy proxy ngẫu nhiên"""
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            return {'http': proxy, 'https': proxy}
        return None
    
    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch URL với retry logic và anti-detection
        """
        for attempt in range(max_retries):
            try:
                # Random delay
                time.sleep(random.uniform(2, 5))
                
                if self.mode == ScraperMode.SELENIUM:
                    return self._fetch_with_selenium(url)
                
                # Sử dụng session (requests hoặc cloudscraper)
                proxy = self._get_proxy() if self.use_proxy else None
                response = self.session.get(
                    url,
                    proxies=proxy,
                    timeout=15
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Fetched {url} successfully")
                    return response.text
                elif response.status_code == 403:
                    logger.warning(f"⚠️ 403 Forbidden - trying different method")
                    if self.mode == ScraperMode.BASIC:
                        # Switch to cloudscraper
                        self.mode = ScraperMode.CLOUDSCRAPER
                        self.session = self._init_session()
                else:
                    logger.warning(f"Status {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
        
        return None
    
    def _fetch_with_selenium(self, url: str) -> Optional[str]:
        """
        Fallback: Sử dụng Selenium cho các trường hợp khó
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Thêm user agent
            options.add_argument(f'user-agent={self._get_headers()["User-Agent"]}')
            
            driver = webdriver.Chrome(options=options)
            
            # Execute CDP commands để bypass detection
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self._get_headers()["User-Agent"]
            })
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(url)
            
            # Wait for content
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="instrument-price-last"], .text-2xl'))
            )
            
            html = driver.page_source
            driver.quit()
            
            return html
            
        except Exception as e:
            logger.error(f"Selenium error: {e}")
            return None
    
    def _parse_price_advanced(self, soup: BeautifulSoup, selectors: Dict) -> Dict:
        """
        Parse với multiple selector fallbacks
        """
        data = {}
        
        # Try multiple selectors for each field
        for field, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    element = soup.select_one(selector)
                    if element:
                        text = element.text.strip()
                        
                        # Clean và convert theo field type
                        if field in ['price', 'change', 'percent', 'open', 'high', 'low']:
                            # Remove các ký tự không phải số
                            clean_text = text.replace(',', '').replace('%', '').replace('+', '').replace('(', '').replace(')', '')
                            
                            # Handle range format (e.g., "2,450 - 2,470")
                            if ' - ' in clean_text and field == 'high':
                                parts = clean_text.split(' - ')
                                data['low'] = float(parts[0])
                                data['high'] = float(parts[1])
                            else:
                                value = float(clean_text)
                                data[field] = value
                        
                        elif field == 'volume':
                            volume_text = text.replace(',', '')
                            if 'K' in volume_text:
                                data[field] = int(float(volume_text.replace('K', '')) * 1000)
                            elif 'M' in volume_text:
                                data[field] = int(float(volume_text.replace('M', '')) * 1000000)
                            else:
                                data[field] = int(float(volume_text)) if volume_text.replace('.', '').isdigit() else 0
                        
                        break  # Found value, move to next field
                        
                except (ValueError, AttributeError) as e:
                    continue
        
        return data
    
    def scrape_coffee_price(self, coffee_type: str) -> Optional[CoffeePrice]:
        """
        Scrape giá một loại cà phê
        """
        config = self.urls.get(coffee_type)
        if not config:
            logger.error(f"Unknown coffee type: {coffee_type}")
            return None
        
        logger.info(f"🔄 Scraping {coffee_type}...")
        
        html = self._fetch_with_retry(config['url'])
        if not html:
            logger.error(f"Failed to fetch {coffee_type}")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Parse with advanced selectors
        data = self._parse_price_advanced(soup, config.get('selectors', {}))
        
        if 'price' not in data:
            logger.warning(f"Could not find price for {coffee_type}")
            return None
        
        # Create CoffeePrice object
        return CoffeePrice(
            current_price=data.get('price', 0),
            change=data.get('change', 0),
            change_percent=data.get('percent', 0),
            open=data.get('open', 0),
            high=data.get('high', 0),
            low=data.get('low', 0),
            volume=data.get('volume', 0),
            last_update=datetime.now().isoformat(),
            coffee_type=coffee_type,
            unit=config['unit']
        )
    
    def scrape_all(self) -> Dict:
        """
        Scrape tất cả giá cà phê
        """
        results = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode.value,
            'data': {}
        }
        
        for coffee_type in self.urls.keys():
            price_data = self.scrape_coffee_price(coffee_type)
            
            if price_data:
                results['data'][coffee_type] = {
                    'price': price_data.current_price,
                    'change': price_data.change,
                    'change_percent': price_data.change_percent,
                    'open': price_data.open,
                    'high': price_data.high,
                    'low': price_data.low,
                    'volume': price_data.volume,
                    'unit': price_data.unit,
                    'last_update': price_data.last_update
                }
                logger.info(f"✅ {coffee_type}: ${price_data.current_price} {price_data.unit}")
            else:
                results['success'] = False
                logger.error(f"❌ Failed to scrape {coffee_type}")
        
        return results
    
    def monitor_prices(self, interval_minutes: int = 30, callback=None):
        """
        Monitor giá liên tục
        """
        logger.info(f"📊 Starting price monitoring (interval: {interval_minutes} min)")
        
        while True:
            try:
                results = self.scrape_all()
                
                if callback:
                    callback(results)
                else:
                    print(json.dumps(results, indent=2))
                
                # Save to file
                with open(f'coffee_prices_{datetime.now().strftime("%Y%m%d_%H%M")}.json', 'w') as f:
                    json.dump(results, f, indent=2)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            # Wait for next cycle
            logger.info(f"💤 Waiting {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)


# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Coffee Price Scraper')
    parser.add_argument('--mode', choices=['basic', 'cloudscraper', 'selenium'], 
                       default='cloudscraper', help='Scraping mode')
    parser.add_argument('--monitor', action='store_true', help='Enable continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Monitor interval in minutes')
    parser.add_argument('--proxy', action='store_true', help='Use proxy rotation')
    
    args = parser.parse_args()
    
    # Initialize scraper
    mode_map = {
        'basic': ScraperMode.BASIC,
        'cloudscraper': ScraperMode.CLOUDSCRAPER,
        'selenium': ScraperMode.SELENIUM
    }
    
    scraper = AdvancedCoffeeScraper(
        mode=mode_map[args.mode],
        use_proxy=args.proxy
    )
    
    if args.monitor:
        # Continuous monitoring
        scraper.monitor_prices(interval_minutes=args.interval)
    else:
        # Single run
        results = scraper.scrape_all()
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Save to file
        filename = f'coffee_prices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Results saved to: {filename}")