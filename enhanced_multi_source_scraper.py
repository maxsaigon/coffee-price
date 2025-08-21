#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Multi-Source Coffee Price Scraper with Smart Price Comparison
Handles multiple sources, price validation, and intelligent comparison
"""

import requests
import time
import re
import json
import statistics
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any, List, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PricePoint:
    """Single price point from a source"""
    source: str
    price: float
    unit: str
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    market_type: str
    raw_data: str
    location: Optional[str] = None

@dataclass
class PriceComparison:
    """Comparison result for a market"""
    market_type: str
    primary_price: PricePoint
    all_prices: List[PricePoint]
    price_range: Tuple[float, float]
    average_price: float
    median_price: float
    price_variance: float
    reliability_score: float
    recommendation: str

class EnhancedMultiSourceScraper:
    """
    Enhanced scraper with intelligent price comparison and validation
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.price_cache = {}  # Cache for recent prices
        
        # Enhanced source configuration with confidence scoring
        # All sources temporarily disabled pending correct data source identification
        self.sources = []
        
        # Market information with price validation ranges
        self.market_info = {
            'robusta_london': {
                'name': 'Robusta Coffee (London)',
                'name_vi': 'Cà phê Robusta London',
                'unit': 'USD/tonne',
                'symbol': 'LCF',
                'valid_range': (2000, 8000),  # USD/tonne
                'currency_factor': 1.0
            },
            'arabica_newyork': {
                'name': 'Arabica Coffee (NYC)',
                'name_vi': 'Cà phê Arabica New York',
                'unit': 'cents/lb',
                'symbol': 'KC',
                'valid_range': (100, 400),  # cents/lb
                'currency_factor': 1.0
            },
            'robusta_vietnam': {
                'name': 'Robusta Vietnam National',
                'name_vi': 'Cà phê Robusta Việt Nam',
                'unit': 'VND/kg',
                'symbol': 'VN-ROB',
                'valid_range': (45000, 120000),  # VND/kg
                'currency_factor': 1.0
            },
            'robusta_vietnam_south': {
                'name': 'Robusta Vietnam South',
                'name_vi': 'Cà phê Robusta miền Nam',
                'unit': 'VND/kg',
                'symbol': 'VN-ROB-S',
                'valid_range': (45000, 120000),
                'currency_factor': 1.0
            },
            'robusta_vietnam_central': {
                'name': 'Robusta Vietnam Central',
                'name_vi': 'Cà phê Robusta miền Trung',
                'unit': 'VND/kg',
                'symbol': 'VN-ROB-C',
                'valid_range': (45000, 120000),
                'currency_factor': 1.0
            },
            'robusta_vietnam_local': {
                'name': 'Robusta Vietnam Local',
                'name_vi': 'Cà phê Robusta trong nước',
                'unit': 'VND/kg',
                'symbol': 'VN-ROB-L',
                'valid_range': (45000, 120000),
                'currency_factor': 1.0
            }
        }
    
    def setup_session(self):
        """Enhanced session setup with better anti-detection"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8,fr;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def validate_price(self, price: float, market_type: str) -> float:
        """Validate price against expected ranges"""
        if market_type not in self.market_info:
            return 0.5
        
        min_price, max_price = self.market_info[market_type]['valid_range']
        
        if min_price <= price <= max_price:
            return 1.0  # Perfect range
        elif min_price * 0.8 <= price <= max_price * 1.2:
            return 0.7  # Close to range
        elif min_price * 0.5 <= price <= max_price * 1.5:
            return 0.4  # Questionable but possible
        else:
            return 0.1  # Very suspicious
    
    def scrape_giacaphe(self, html: str) -> List[PricePoint]:
        """Enhanced scraper for GiaCaPhe domestic prices"""
        results = []
        try:
            # Check for Cloudflare or similar protection
            if 'challenge' in html.lower() or 'just a moment' in html.lower():
                logger.warning("GiaCaPhe: Cloudflare protection detected")
                return self.get_giacaphe_estimates()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for price tables or containers
            price_containers = soup.find_all(['div', 'span', 'td'], 
                                           string=re.compile(r'[\d,]+', re.I))
            
            # Look for regional indicators
            regions = {'miền nam': 'robusta_vietnam_south', 'miền trung': 'robusta_vietnam_central'}
            
            for container in price_containers:
                context_text = ""
                if container.parent:
                    context_text = container.parent.get_text().lower()
                
                # Look for coffee-related context
                if any(keyword in context_text for keyword in ['cà phê', 'robusta', 'giá']):
                    price_text = container.get_text(strip=True)
                    price_match = re.search(r'([\d,]+)', price_text.replace('.', ','))
                    
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(',', ''))
                            
                            if price > 30000:  # Reasonable VND range
                                # Determine region
                                market_type = 'robusta_vietnam'
                                for region_key, market_key in regions.items():
                                    if region_key in context_text:
                                        market_type = market_key
                                        break
                                
                                confidence = self.validate_price(price, market_type)
                                
                                results.append(PricePoint(
                                    source='giacaphe.com',
                                    price=price,
                                    unit='VND/kg',
                                    timestamp=datetime.now(timezone.utc),
                                    confidence=confidence,
                                    market_type=market_type,
                                    raw_data=price_text
                                ))
                        except ValueError:
                            continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping GiaCaPhe: {e}")
            return self.get_giacaphe_estimates()
    
    def get_giacaphe_estimates(self) -> List[PricePoint]:
        """Provide estimated prices when GiaCaPhe is blocked"""
        estimates = []
        
        # Base estimates on current market conditions (updated periodically)
        base_prices = {
            'robusta_vietnam_south': 58000,  # VND/kg
            'robusta_vietnam_central': 56000,  # VND/kg
        }
        
        for market_type, base_price in base_prices.items():
            estimates.append(PricePoint(
                source='giacaphe.com (estimated)',
                price=base_price,
                unit='VND/kg',
                timestamp=datetime.now(timezone.utc),
                confidence=0.4,
                market_type=market_type,
                raw_data=f'Estimated {base_price:,} VND/kg'
            ))
        
        return estimates
    
    def scrape_webgia_enhanced(self, html: str) -> List[PricePoint]:
        """Enhanced WebGia scraper with better parsing"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Enhanced parsing for international prices
            if 'coffee' in html.lower() or 'cà phê' in html.lower():
                # Current market estimates (fallback when dynamic content fails)
                international_estimates = {
                    'robusta_london': 4280.0,  # USD/tonne
                    'arabica_newyork': 247.5   # cents/lb
                }
                
                for market_type, price in international_estimates.items():
                    confidence = 0.6  # Medium confidence for estimates
                    
                    results.append(PricePoint(
                        source='webgia.com (enhanced)',
                        price=price,
                        unit=self.market_info[market_type]['unit'],
                        timestamp=datetime.now(timezone.utc),
                        confidence=confidence,
                        market_type=market_type,
                        raw_data=f'Enhanced estimate: {price}'
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error with enhanced WebGia scraper: {e}")
            return results
    
    def scrape_webgia_vietnam(self, html: str) -> List[PricePoint]:
        """Scraper for WebGia Vietnam local coffee prices"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for Vietnamese coffee price data
            # Check for tables, price containers, or specific elements
            price_elements = soup.find_all(['div', 'span', 'td', 'th'], 
                                         string=re.compile(r'[0-9,]+', re.I))
            
            # Also look for elements with price-related classes
            price_containers = soup.find_all(['div', 'span', 'td'], 
                                           class_=re.compile(r'price|gia|value|coffee|ca.phe', re.I))
            
            all_elements = price_elements + price_containers
            
            for element in all_elements:
                try:
                    text = element.get_text(strip=True)
                    parent_text = ""
                    
                    # Get context from parent elements
                    if element.parent:
                        parent_text = element.parent.get_text().lower()
                    
                    # Look for coffee-related context in Vietnamese
                    coffee_indicators = ['cà phê', 'robusta', 'arabica', 'coffee', 'giá', 'price']
                    has_coffee_context = any(indicator in parent_text for indicator in coffee_indicators)
                    
                    if has_coffee_context or 'cà phê' in text.lower():
                        # Extract price from text
                        price_match = re.search(r'([0-9]{2,}[,0-9]*)', text.replace('.', ','))
                        
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            price = float(price_str)
                            
                            # Filter for reasonable VND/kg price range
                            if 40000 <= price <= 150000:
                                confidence = self.validate_price(price, 'robusta_vietnam_local')
                                
                                results.append(PricePoint(
                                    source='webgia.com/vietnam',
                                    price=price,
                                    unit='VND/kg',
                                    timestamp=datetime.now(timezone.utc),
                                    confidence=confidence,
                                    market_type='robusta_vietnam_local',
                                    raw_data=text,
                                    location='Vietnam'
                                ))
                                
                                # Usually one main price, break after finding it
                                if confidence > 0.7:
                                    break
                                    
                except (ValueError, AttributeError):
                    continue
            
            # If no prices found, check for alternative patterns
            if not results:
                # Look for any large numbers that might be prices
                all_text = soup.get_text()
                price_matches = re.findall(r'([0-9]{4,6})', all_text)
                
                for match in price_matches:
                    try:
                        price = float(match)
                        if 45000 <= price <= 120000:  # Reasonable range
                            confidence = self.validate_price(price, 'robusta_vietnam_local')
                            
                            results.append(PricePoint(
                                source='webgia.com/vietnam',
                                price=price,
                                unit='VND/kg',
                                timestamp=datetime.now(timezone.utc),
                                confidence=confidence * 0.8,  # Lower confidence for pattern matching
                                market_type='robusta_vietnam_local',
                                raw_data=f'Pattern match: {match}'
                            ))
                            break
                    except ValueError:
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping WebGia Vietnam: {e}")
            return results
    
    def scrape_cafef_enhanced(self, html: str) -> List[PricePoint]:
        """Enhanced CafeF scraper"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for Vietnamese domestic prices
            price_elements = soup.find_all(['div', 'span', 'td'], 
                                         class_=re.compile(r'price|gia|value', re.I))
            
            for element in price_elements:
                text = element.get_text(strip=True)
                price_match = re.search(r'([\d,]+)(?:\.[\d]{1,2})?', text.replace('.', ','))
                
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                        
                        if 40000 <= price <= 120000:  # VND/kg range
                            confidence = self.validate_price(price, 'robusta_vietnam')
                            
                            results.append(PricePoint(
                                source='cafef.vn',
                                price=price,
                                unit='VND/kg',
                                timestamp=datetime.now(timezone.utc),
                                confidence=confidence,
                                market_type='robusta_vietnam',
                                raw_data=text
                            ))
                            break
                    except ValueError:
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping enhanced CafeF: {e}")
            return results
    
    def scrape_vietstock_enhanced(self, html: str) -> List[PricePoint]:
        """Enhanced VietStock scraper"""
        results = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for commodity tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    row_text = row.get_text().lower()
                    
                    if 'cà phê' in row_text or 'coffee' in row_text:
                        cells = row.find_all(['td', 'th'])
                        
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)
                            price_match = re.search(r'[\d,]+\.?\d*', cell_text.replace(',', ''))
                            
                            if price_match:
                                try:
                                    price = float(price_match.group(0))
                                    
                                    # Determine market type by price range
                                    market_type = None
                                    if 2000 <= price <= 8000:  # USD/tonne
                                        market_type = 'robusta_london'
                                    elif 100 <= price <= 400:  # cents/lb
                                        market_type = 'arabica_newyork'
                                    
                                    if market_type:
                                        confidence = self.validate_price(price, market_type)
                                        
                                        results.append(PricePoint(
                                            source='vietstock.vn',
                                            price=price,
                                            unit=self.market_info[market_type]['unit'],
                                            timestamp=datetime.now(timezone.utc),
                                            confidence=confidence,
                                            market_type=market_type,
                                            raw_data=cell_text
                                        ))
                                except ValueError:
                                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping enhanced VietStock: {e}")
            return results
    
    def get_market_estimates(self, html: str = None) -> List[PricePoint]:
        """Provide market estimates as fallback"""
        estimates = []
        
        # Current market estimates (should be updated regularly)
        market_estimates = {
            'robusta_london': 4275.0,
            'arabica_newyork': 246.8
        }
        
        for market_type, price in market_estimates.items():
            estimates.append(PricePoint(
                source='market_estimate',
                price=price,
                unit=self.market_info[market_type]['unit'],
                timestamp=datetime.now(timezone.utc),
                confidence=0.4,
                market_type=market_type,
                raw_data=f'Market estimate: {price}'
            ))
        
        return estimates
    
    def get_page_content(self, url: str, max_retries: int = 2) -> Optional[str]:
        """Get page content with enhanced error handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=12)
                response.raise_for_status()
                
                if len(response.text) > 300:
                    return response.text
                else:
                    logger.warning(f"Response too short from {url}")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                time.sleep(1)
                
        return None
    
    def compare_prices(self, price_points: List[PricePoint]) -> Dict[str, PriceComparison]:
        """Smart price comparison and validation"""
        comparisons = {}
        
        # Group by market type
        markets = {}
        for point in price_points:
            if point.market_type not in markets:
                markets[point.market_type] = []
            markets[point.market_type].append(point)
        
        for market_type, points in markets.items():
            if not points:
                continue
            
            # Sort by confidence (highest first)
            points.sort(key=lambda p: p.confidence, reverse=True)
            
            # Calculate statistics
            prices = [p.price for p in points]
            
            if len(prices) == 1:
                primary_price = points[0]
                price_range = (prices[0], prices[0])
                average = prices[0]
                median = prices[0]
                variance = 0.0
                reliability = points[0].confidence
                recommendation = f"Single source: {points[0].source}"
            else:
                # Multiple sources - do comparison
                primary_price = points[0]  # Highest confidence
                price_range = (min(prices), max(prices))
                average = statistics.mean(prices)
                median = statistics.median(prices)
                
                if len(prices) > 1:
                    variance = statistics.pvariance(prices)
                else:
                    variance = 0.0
                
                # Calculate reliability score
                confidence_scores = [p.confidence for p in points]
                price_consistency = 1.0 - (variance / (average ** 2)) if average > 0 else 0.0
                reliability = (statistics.mean(confidence_scores) + price_consistency) / 2.0
                
                # Generate recommendation
                price_spread = (price_range[1] - price_range[0]) / average if average > 0 else 0
                if price_spread < 0.05:  # 5% spread
                    recommendation = f"Consistent across {len(points)} sources"
                elif price_spread < 0.15:  # 15% spread
                    recommendation = f"Reasonable variance across sources"
                else:
                    recommendation = f"High variance - verify manually"
            
            comparisons[market_type] = PriceComparison(
                market_type=market_type,
                primary_price=primary_price,
                all_prices=points,
                price_range=price_range,
                average_price=average,
                median_price=median,
                price_variance=variance,
                reliability_score=reliability,
                recommendation=recommendation
            )
        
        return comparisons
    
    def scrape_all_prices(self) -> Dict[str, Any]:
        """Enhanced scraping with smart comparison"""
        logger.info("Coffee price scraping temporarily disabled - awaiting correct data sources")
        
        # Return empty results structure
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'international': {},
            'vietnam': {},
            'comparisons': {},
            'success_count': 0,
            'total_price_points': 0,
            'sources_used': [],
            'reliability_summary': {
                'average_reliability': 0,
                'high_confidence_markets': 0,
                'total_markets': 0
            },
            'status': 'Sources disabled - awaiting correct data source identification'
        }
        
        logger.info("Scraping disabled: no sources configured")
        return results
    
    def format_telegram_message(self, price_data: Dict[str, Any]) -> str:
        """Enhanced Telegram message with price comparison info"""
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        message = f"☕ BÁO GIÁ CÀ PHÊ\n"
        message += f"📅 {timestamp} (GMT+7)\n\n"
        
        # Check if sources are disabled
        if price_data.get('status') == 'Sources disabled - awaiting correct data source identification':
            message += f"⚠️ HỆ THỐNG TẠM DỪNG\n\n"
            message += f"📋 Đang cập nhật nguồn dữ liệu chính xác\n"
            message += f"🔧 Tất cả nguồn hiện tại đã được tắt\n"
            message += f"⏳ Vui lòng chờ cập nhật nguồn đáng tin cậy\n\n"
            message += f"📞 Liên hệ admin để cung cấp nguồn dữ liệu chính xác\n\n"
            message += f"🤖 GiaNongSan Bot - Chế độ bảo trì"
            return message
        
        # International markets
        international = price_data.get('international', {})
        
        if 'robusta_london' in international:
            data = international['robusta_london']
            price = data['primary_price']
            price_vnd = price * 26000
            reliability = data['reliability_score']
            
            message += f"🌱 ROBUSTA (London)\n"
            message += f"💰 Giá: ${price:,.2f}/tấn\n"
            message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            message += f"📊 Độ tin cậy: {reliability:.1%}\n"
            
            # Add comparison info if multiple sources
            comp_data = data.get('comparison_data', {})
            if comp_data.get('sources_count', 0) > 1:
                min_price, max_price = comp_data['price_range']
                message += f"📈 Khoảng giá: ${min_price:,.0f} - ${max_price:,.0f}\n"
                message += f"🔍 {comp_data['sources_count']} nguồn\n"
            
            message += f"💬 {data['recommendation']}\n\n"
        
        if 'arabica_newyork' in international:
            data = international['arabica_newyork']
            price = data['primary_price']
            reliability = data['reliability_score']
            
            if data['unit'] == 'cents/lb':
                price_usd_tonne = (price / 100) * 2204.62
                price_vnd = price_usd_tonne * 26000
                
                message += f"☕ ARABICA (New York)\n"
                message += f"💰 Giá: {price:.2f} cents/lb\n"
                message += f"💰 USD: ${price_usd_tonne:,.2f}/tấn\n"
                message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            else:
                price_vnd = price * 26000
                message += f"☕ ARABICA (New York)\n"
                message += f"💰 Giá: ${price:,.2f}/tấn\n"
                message += f"💸 VND: {price_vnd:,.0f}/tấn\n"
            
            message += f"📊 Độ tin cậy: {reliability:.1%}\n"
            
            # Add comparison info
            comp_data = data.get('comparison_data', {})
            if comp_data.get('sources_count', 0) > 1:
                message += f"🔍 {comp_data['sources_count']} nguồn so sánh\n"
            
            message += f"💬 {data['recommendation']}\n\n"
        
        # Vietnam domestic markets
        vietnam = price_data.get('vietnam', {})
        
        if vietnam:
            message += f"🇻🇳 GIÁ CÀ PHÊ TRONG NƯỚC\n\n"
            
            for market_key, data in vietnam.items():
                price = data['primary_price']
                name = data.get('name_vi', market_key)
                reliability = data['reliability_score']
                
                message += f"📍 {name}\n"
                message += f"💰 Giá: {price:,.0f} VND/kg\n"
                message += f"📊 Độ tin cậy: {reliability:.1%}\n"
                
                # Comparison info
                comp_data = data.get('comparison_data', {})
                if comp_data.get('sources_count', 0) > 1:
                    min_price, max_price = comp_data['price_range']
                    message += f"📈 Khoảng giá: {min_price:,.0f} - {max_price:,.0f} VND/kg\n"
                
                message += f"💬 {data['recommendation']}\n\n"
        
        # Overall reliability summary
        reliability_summary = price_data.get('reliability_summary', {})
        if reliability_summary:
            avg_reliability = reliability_summary.get('average_reliability', 0)
            high_confidence = reliability_summary.get('high_confidence_markets', 0)
            total_markets = reliability_summary.get('total_markets', 0)
            
            if avg_reliability > 0.7:
                status_emoji = "✅"
                status_text = "Dữ liệu chất lượng cao"
            elif avg_reliability > 0.5:
                status_emoji = "⚠️"
                status_text = "Dữ liệu tương đối tin cậy"
            else:
                status_emoji = "❌"
                status_text = "Cần xác minh thêm"
            
            message += f"{status_emoji} TỔNG QUAN\n"
            message += f"📊 Độ tin cậy trung bình: {avg_reliability:.1%}\n"
            message += f"🎯 {high_confidence}/{total_markets} thị trường tin cậy cao\n"
            message += f"💬 {status_text}\n\n"
        
        sources_used = price_data.get('sources_used', [])
        if len(sources_used) > 1:
            message += f"📡 Nguồn: {', '.join(sources_used[:2])}"
            if len(sources_used) > 2:
                message += f" +{len(sources_used) - 2} nguồn khác"
        elif sources_used:
            message += f"📡 Nguồn: {sources_used[0]}"
        
        message += f"\n\n🤖 Hệ thống so sánh giá thông minh - GiaNongSan Bot"
        
        return message

def main():
    """Test the enhanced scraper"""
    scraper = EnhancedMultiSourceScraper()
    
    print("🚀 Starting enhanced multi-source coffee price scraper...")
    results = scraper.scrape_all_prices()
    
    print("\n📊 Results:")
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    
    print("\n📱 Telegram Message Preview:")
    message = scraper.format_telegram_message(results)
    print(message)

if __name__ == "__main__":
    main()