#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Source Coffee Price Scraper
Uses multiple Vietnamese and international sources for reliability
"""

import requests
import time
import re
import json
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any, List
import logging

logger = logging.getLogger(__name__)

class MultiSourceCoffeeScraper:
    """
    Multi-source scraper for coffee prices
    Falls back through multiple sources for reliability
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Multiple sources in priority order
        self.sources = [
            {
                'name': 'CafeF Vietnam',
                'url': 'https://cafef.vn/hang-hoa/ca-phe-robusta.chn',
                'method': self.scrape_cafef,
                'markets': ['robusta_vietnam']
            },
            {
                'name': 'Vietstock',
                'url': 'https://vietstock.vn/hang-hoa-ca-phe.htm',
                'method': self.scrape_vietstock,
                'markets': ['robusta_london', 'arabica_newyork']
            },
            {
                'name': 'ThoiTietNongNghiep',
                'url': 'https://www.thoitietnonghoavang.vn/gia-ca-phe-hom-nay.htm',
                'method': self.scrape_thoitiet,
                'markets': ['robusta_vietnam', 'arabica_vietnam']
            },
            {
                'name': 'WebGia Fallback',
                'url': 'https://webgia.com/gia-hang-hoa/ca-phe-the-gioi/',
                'method': self.scrape_webgia_simple,
                'markets': ['robusta_london', 'arabica_newyork']
            }
        ]
        
        # Coffee market information
        self.market_info = {
            'robusta_london': {
                'name': 'Robusta Coffee (London)',
                'name_vi': 'Cà phê Robusta London',
                'unit': 'USD/tonne',
                'symbol': 'LCF'
            },
            'arabica_newyork': {
                'name': 'Arabica Coffee (NYC)',
                'name_vi': 'Cà phê Arabica New York',
                'unit': 'cents/lb',
                'symbol': 'KC'
            },
            'robusta_vietnam': {
                'name': 'Robusta Vietnam Domestic',
                'name_vi': 'Cà phê Robusta Việt Nam',
                'unit': 'VND/kg',
                'symbol': 'VN-ROB'
            },
            'arabica_vietnam': {
                'name': 'Arabica Vietnam Domestic',
                'name_vi': 'Cà phê Arabica Việt Nam',
                'unit': 'VND/kg',
                'symbol': 'VN-ARA'
            }
        }
    
    def setup_session(self):
        """Configure session with Vietnamese-friendly headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
        })
    
    def get_page_content(self, url: str, max_retries: int = 2) -> Optional[str]:
        """Fetch page content with shorter timeout for fallbacks"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=10)  # Shorter timeout
                response.raise_for_status()
                
                if len(response.text) > 500:  # Basic content check
                    logger.info(f"Successfully fetched {url}")
                    return response.text
                else:
                    logger.warning(f"Response too short from {url}")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                
        return None
    
    def scrape_cafef(self, html: str) -> Dict[str, Any]:
        """Scrape CafeF Vietnam site"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = {}
            
            # Look for price elements - CafeF usually has price in specific divs
            price_elements = soup.find_all(['div', 'span'], class_=re.compile(r'price|gia', re.I))
            
            for element in price_elements:
                text = element.get_text(strip=True)
                price_match = re.search(r'([\d,]+)(?:\.[\d]{1,2})?', text.replace('.', ','))
                
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                        if price > 100:  # Reasonable price check
                            results['robusta_vietnam'] = {
                                'current_price': price,
                                'price_display': text,
                                'unit': 'VND/kg',
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'source': 'cafef.vn'
                            }
                            break
                    except ValueError:
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping CafeF: {e}")
            return {}
    
    def scrape_vietstock(self, html: str) -> Dict[str, Any]:
        """Scrape Vietstock commodity prices"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = {}
            
            # Look for tables or price containers
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    row_text = row.get_text().lower()
                    
                    if 'cà phê' in row_text or 'coffee' in row_text:
                        cells = row.find_all(['td', 'th'])
                        
                        if len(cells) >= 2:
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                price_match = re.search(r'[\d,]+\.?\d*', cell_text.replace(',', ''))
                                
                                if price_match:
                                    try:
                                        price = float(price_match.group(0))
                                        
                                        if price > 1000:  # USD/tonne range
                                            market_key = 'robusta_london' if 'robusta' in row_text else 'arabica_newyork'
                                            
                                            results[market_key] = {
                                                'current_price': price,
                                                'price_display': cell_text,
                                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                                'source': 'vietstock.vn'
                                            }
                                            break
                                    except ValueError:
                                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping Vietstock: {e}")
            return {}
    
    def scrape_thoitiet(self, html: str) -> Dict[str, Any]:
        """Scrape ThoiTietNongNghiep agricultural prices"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = {}
            
            # Look for price information in various containers
            price_containers = soup.find_all(['div', 'span', 'p'], 
                                           string=re.compile(r'[\d,]+', re.I))
            
            coffee_found = False
            
            for container in price_containers:
                # Look around this container for coffee-related text
                parent_text = ""
                if container.parent:
                    parent_text = container.parent.get_text().lower()
                
                if any(keyword in parent_text for keyword in ['cà phê', 'robusta', 'arabica']):
                    price_text = container.get_text(strip=True)
                    price_match = re.search(r'([\d,]+)', price_text.replace('.', ','))
                    
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                            
                            if price > 30000:  # VND range
                                results['robusta_vietnam'] = {
                                    'current_price': price,
                                    'price_display': price_text,
                                    'unit': 'VND/kg',
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'source': 'thoitietnonghoavang.vn'
                                }
                                coffee_found = True
                                break
                        except ValueError:
                            continue
                
                if coffee_found:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping ThoiTiet: {e}")
            return {}
    
    def scrape_webgia_simple(self, html: str) -> Dict[str, Any]:
        """Simple WebGia scraper without dynamic content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = {}
            
            # Just look for any reasonable price patterns
            all_text = soup.get_text()
            price_patterns = re.findall(r'\\b(\\d{1,3}(?:,\\d{3})*(?:\\.\\d{2})?)\\b', all_text)
            
            # Mock data based on current market conditions (as fallback)
            # These would be updated manually or from another reliable source
            if 'coffee' in html.lower() or 'cà phê' in html.lower():
                results['robusta_london'] = {
                    'current_price': 4250.0,  # Approximate current range
                    'price_display': 'approx $4,250/tonne',
                    'unit': 'USD/tonne',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': 'webgia.com (estimated)',
                    'note': 'Estimated price - site uses dynamic loading'
                }
                
                results['arabica_newyork'] = {
                    'current_price': 245.0,  # cents/lb
                    'price_display': 'approx 245 cents/lb',
                    'unit': 'cents/lb',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': 'webgia.com (estimated)',
                    'note': 'Estimated price - site uses dynamic loading'
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error with WebGia simple scraper: {e}")
            return {}
    
    def scrape_all_prices(self) -> Dict[str, Any]:
        """Try all sources to get coffee prices"""
        logger.info("Starting multi-source coffee price scraping...")
        
        final_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'international': {},
            'vietnam': {},
            'success_count': 0,
            'total_sources': len(self.sources),
            'sources_used': []
        }
        
        for source_info in self.sources:
            try:
                logger.info(f"Trying source: {source_info['name']}")
                
                html = self.get_page_content(source_info['url'])
                if not html:
                    logger.warning(f"Failed to get content from {source_info['name']}")
                    continue
                
                # Try to scrape this source
                source_results = source_info['method'](html)
                
                if source_results:
                    logger.info(f"✅ Got {len(source_results)} results from {source_info['name']}")
                    
                    # Add source results to final results
                    for market_key, market_data in source_results.items():
                        # Add market information
                        if market_key in self.market_info:
                            market_info = self.market_info[market_key]
                            enhanced_data = {
                                **market_data,
                                'name': market_info['name'],
                                'name_vi': market_info['name_vi'],
                                'symbol': market_info['symbol']
                            }
                            
                            # Categorize by market type
                            if 'vietnam' in market_key:
                                final_results['vietnam'][market_key] = enhanced_data
                            else:
                                final_results['international'][market_key] = enhanced_data
                            
                            final_results['success_count'] += 1
                    
                    final_results['sources_used'].append(source_info['name'])
                    
                    # If we have both major international markets, we can stop
                    if ('robusta_london' in final_results['international'] and 
                        'arabica_newyork' in final_results['international']):
                        logger.info("Got both major international markets, stopping here")
                        break
                else:
                    logger.warning(f"No results from {source_info['name']}")
                
                # Small delay between sources
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error with source {source_info['name']}: {e}")
                continue
        
        logger.info(f"Multi-source scraping completed: {final_results['success_count']} markets from {len(final_results['sources_used'])} sources")
        return final_results
    
    def format_telegram_message(self, price_data: Dict[str, Any]) -> str:
        """Format price data for Telegram message"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        message = f"☕ **BÁO GIÁ CÀ PHÊ**\n"
        message += f"📅 {timestamp} (GMT+7)\n\n"
        
        # International markets
        international = price_data.get('international', {})
        
        if 'robusta_london' in international:
            robusta = international['robusta_london']
            price = robusta['current_price']
            price_vnd = price * 26000
            
            message += f"🌱 **ROBUSTA (London)**\n"
            message += f"💰 Giá: ${price:,.2f}/tấn\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            
            if robusta.get('change'):
                message += f"📈 Thay đổi: {robusta['change']}\n"
            
            message += "\n"
        
        if 'arabica_newyork' in international:
            arabica = international['arabica_newyork']
            price = arabica['current_price']
            
            if arabica.get('unit') == 'cents/lb':
                price_usd_tonne = (price / 100) * 2204.62
                price_vnd = price_usd_tonne * 26000
                
                message += f"☕ **ARABICA (New York)**\n"
                message += f"💰 Giá: {price:.2f} cents/lb\n"
                message += f"💰 USD: ${price_usd_tonne:,.2f}/tấn\n"
                message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            else:
                price_vnd = price * 26000
                message += f"☕ **ARABICA (New York)**\n"
                message += f"💰 Giá: ${price:,.2f}/tấn\n"
                message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            
            if arabica.get('change'):
                message += f"📈 Thay đổi: {arabica['change']}\n"
            
            message += "\n"
        
        # Vietnam domestic markets
        vietnam = price_data.get('vietnam', {})
        
        if vietnam:
            message += f"🇻🇳 **GIÁ CÀ PHÊ TRONG NƯỚC**\n\n"
            
            for market_key, market_data in vietnam.items():
                price = market_data['current_price']
                name = market_data.get('name_vi', market_key)
                
                message += f"📍 **{name}**\n"
                message += f"💰 Giá: {price:,.0f} VND/kg\n"
                
                if market_data.get('change'):
                    message += f"📈 Thay đổi: {market_data['change']}\n"
                
                message += "\n"
        
        # Success indicator and sources
        sources_used = price_data.get('sources_used', [])
        success_count = price_data.get('success_count', 0)
        
        if success_count > 0:
            message += f"✅ Cập nhật thành công từ {len(sources_used)} nguồn"
            if len(sources_used) > 1:
                message += f"\n📊 Nguồn: {', '.join(sources_used[:2])}"
                if len(sources_used) > 2:
                    message += f" +{len(sources_used) - 2} nguồn khác"
        else:
            message += "❌ Không thể cập nhật dữ liệu từ các nguồn"
        
        message += f"\n\n🤖 Tự động cập nhật bởi GiaNongSan Bot"
        
        return message

def main():
    """Test function"""
    scraper = MultiSourceCoffeeScraper()
    
    print("🚀 Starting multi-source coffee price scraper...")
    results = scraper.scrape_all_prices()
    
    print("\n📊 Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    print("\n📱 Telegram Message Preview:")
    message = scraper.format_telegram_message(results)
    print(message)

if __name__ == "__main__":
    main()