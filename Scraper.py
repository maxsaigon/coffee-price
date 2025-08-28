import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from typing import Dict, Optional, List
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InvestingCoffeeScraper:
    """
    Scraper cho dữ liệu giá cà phê từ Investing.com
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_headers()
        
        # URLs cho các loại cà phê trên Investing.com
        self.urls = {
            'robusta': {
                'url': 'https://www.investing.com/commodities/london-coffee',
                'name': 'Coffee Robusta (London)',
                'unit': 'USD/MT'  # USD per Metric Ton
            },
            'arabica': {
                'url': 'https://www.investing.com/commodities/us-coffee-c',
                'name': 'Coffee C Arabica (New York)',
                'unit': 'USc/lb'  # US cents per pound
            }
        }
        
    def setup_headers(self):
        """
        Thiết lập headers để tránh bị block
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(self.headers)
    
    def get_page_content(self, url: str) -> Optional[str]:
        """
        Lấy nội dung HTML của trang
        """
        try:
            # Random delay để tránh rate limiting
            time.sleep(random.uniform(2, 4))
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Lỗi khi truy cập {url}: {e}")
            return None
    
    def parse_coffee_price(self, html: str, coffee_type: str) -> Dict:
        """
        Parse giá cà phê từ HTML
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        try:
            # Tìm giá hiện tại - Investing.com thường dùng class này
            price_element = soup.find('div', {'data-test': 'instrument-price-last'})
            if not price_element:
                # Backup selector
                price_element = soup.find('span', {'class': 'text-2xl'})
                if not price_element:
                    price_element = soup.find('div', {'class': 'instrument-price_last'})
            
            if price_element:
                price_text = price_element.text.strip().replace(',', '')
                data['current_price'] = float(price_text)
            
            # Tìm thay đổi giá
            change_element = soup.find('div', {'data-test': 'instrument-price-change'})
            if not change_element:
                change_element = soup.find('span', {'class': lambda x: x and 'instrument-price_change' in x})
            
            if change_element:
                change_text = change_element.text.strip()
                # Xử lý format: +1.50 hoặc -1.50
                data['change'] = float(change_text.replace(',', '').replace('+', ''))
            
            # Tìm phần trăm thay đổi
            percent_element = soup.find('div', {'data-test': 'instrument-price-change-percent'})
            if not percent_element:
                percent_element = soup.find('span', {'class': lambda x: x and 'instrument-price_change-percent' in x})
            
            if percent_element:
                percent_text = percent_element.text.strip()
                # Xử lý format: (+1.50%) hoặc (-1.50%)
                percent_clean = percent_text.replace('(', '').replace(')', '').replace('%', '').replace('+', '')
                data['change_percent'] = float(percent_clean)
            
            # Tìm thông tin phiên giao dịch
            # Giá mở cửa
            open_element = soup.find('dd', {'data-test': 'open'})
            if not open_element:
                open_element = soup.find('span', text='Open')
                if open_element:
                    open_element = open_element.find_next_sibling('span')
            
            if open_element:
                data['open'] = float(open_element.text.strip().replace(',', ''))
            
            # Giá cao nhất trong ngày
            high_element = soup.find('dd', {'data-test': 'high'})
            if not high_element:
                high_element = soup.find('span', text="Day's Range")
                if high_element:
                    range_text = high_element.find_next_sibling('span').text
                    if ' - ' in range_text:
                        low, high = range_text.split(' - ')
                        data['day_low'] = float(low.strip().replace(',', ''))
                        data['day_high'] = float(high.strip().replace(',', ''))
            
            if high_element and 'day_high' not in data:
                data['day_high'] = float(high_element.text.strip().replace(',', ''))
            
            # Giá thấp nhất trong ngày
            low_element = soup.find('dd', {'data-test': 'low'})
            if low_element and 'day_low' not in data:
                data['day_low'] = float(low_element.text.strip().replace(',', ''))
            
            # Volume giao dịch
            volume_element = soup.find('dd', {'data-test': 'volume'})
            if not volume_element:
                volume_element = soup.find('span', text='Volume')
                if volume_element:
                    volume_element = volume_element.find_next_sibling('span')
            
            if volume_element:
                volume_text = volume_element.text.strip()
                # Xử lý format: 1.2K, 1.5M, etc.
                volume_clean = volume_text.replace(',', '')
                if 'K' in volume_clean:
                    data['volume'] = float(volume_clean.replace('K', '')) * 1000
                elif 'M' in volume_clean:
                    data['volume'] = float(volume_clean.replace('M', '')) * 1000000
                else:
                    data['volume'] = float(volume_clean) if volume_clean.replace('.', '').isdigit() else 0
            
            # Thời gian cập nhật
            time_element = soup.find('time', {'data-test': 'timestamp'})
            if not time_element:
                time_element = soup.find('span', {'class': lambda x: x and 'instrument-metadata_time' in x})
            
            if time_element:
                data['last_update'] = time_element.text.strip()
            
            # Thêm metadata
            data['coffee_type'] = coffee_type
            data['unit'] = self.urls[coffee_type]['unit']
            data['name'] = self.urls[coffee_type]['name']
            data['source'] = 'Investing.com'
            data['scraped_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Đã lấy giá {coffee_type}: ${data.get('current_price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Lỗi khi parse dữ liệu {coffee_type}: {e}")
            
        return data
    
    def get_vietnamese_coffee_prices(self) -> Dict:
        """
        Lấy giá cà phê Việt Nam từ các nguồn khác
        Có thể scrape từ giacaphe.com hoặc cafef.vn
        """
        vn_prices = {}
        
        try:
            # Ví dụ scraping từ một trang tin Việt Nam
            # Đây là placeholder - cần điều chỉnh theo cấu trúc thực tế
            
            # Option 1: Scrape từ cafef.vn
            cafef_url = "https://cafef.vn/hang-hoa-nguyen-lieu.chn"
            
            # Option 2: API từ một số nguồn Việt Nam (nếu có)
            
            # Giá mẫu - thay bằng scraping thực tế
            vn_prices = {
                'robusta_daklak': {
                    'price': 122500,  # VND/kg
                    'change': 500,
                    'location': 'Đắk Lắk',
                    'unit': 'VND/kg'
                },
                'robusta_lamDong': {
                    'price': 121800,
                    'change': 300,
                    'location': 'Lâm Đồng',
                    'unit': 'VND/kg'
                },
                'arabica_vn': {
                    'price': 95000,
                    'change': -1000,
                    'location': 'Lâm Đồng',
                    'unit': 'VND/kg'
                }
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy giá VN: {e}")
            
        return vn_prices
    
    def scrape_all_prices(self) -> Dict:
        """
        Scrape tất cả giá cà phê
        """
        all_prices = {
            'international': {},
            'vietnam': {},
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'status': 'success'
            }
        }
        
        # Scrape giá quốc tế từ Investing.com
        for coffee_type, info in self.urls.items():
            logger.info(f"🔄 Đang scrape {coffee_type}...")
            
            html = self.get_page_content(info['url'])
            if html:
                price_data = self.parse_coffee_price(html, coffee_type)
                if price_data:
                    all_prices['international'][coffee_type] = price_data
            else:
                logger.warning(f"⚠️ Không thể lấy dữ liệu {coffee_type}")
        
        # Lấy giá Việt Nam
        vn_prices = self.get_vietnamese_coffee_prices()
        if vn_prices:
            all_prices['vietnam'] = vn_prices
        
        return all_prices
    
    def format_telegram_message(self, prices: Dict) -> str:
        """
        Format dữ liệu thành tin nhắn Telegram
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        message = f"☕ **BÁO CÁO GIÁ CÀ PHÊ**\n"
        message += f"📅 {now}\n"
        message += "=" * 35 + "\n\n"
        
        # Giá quốc tế
        if prices.get('international'):
            message += "🌍 **THỊ TRƯỜNG QUỐC TẾ**\n\n"
            
            for coffee_type, data in prices['international'].items():
                if data.get('current_price'):
                    trend = "📈" if data.get('change', 0) > 0 else "📉"
                    
                    message += f"**{data.get('name', coffee_type.upper())}**\n"
                    message += f"💰 Giá: {data['current_price']:,.2f} {data.get('unit', '')}\n"
                    
                    if 'change' in data:
                        message += f"{trend} Thay đổi: {data['change']:+.2f} "
                        if 'change_percent' in data:
                            message += f"({data['change_percent']:+.2f}%)"
                        message += "\n"
                    
                    if 'day_low' in data and 'day_high' in data:
                        message += f"📊 Biên độ: {data['day_low']:,.2f} - {data['day_high']:,.2f}\n"
                    
                    if 'volume' in data:
                        message += f"📈 Volume: {data['volume']:,.0f}\n"
                    
                    message += "\n"
        
        # Giá Việt Nam
        if prices.get('vietnam'):
            message += "🇻🇳 **THỊ TRƯỜNG VIỆT NAM**\n\n"
            
            for location, data in prices['vietnam'].items():
                if isinstance(data, dict) and 'price' in data:
                    trend = "📈" if data.get('change', 0) > 0 else "📉"
                    
                    message += f"**{location.replace('_', ' ').title()}**\n"
                    message += f"📍 {data.get('location', '')}\n"
                    message += f"💰 Giá: {data['price']:,.0f} {data.get('unit', 'VND/kg')}\n"
                    
                    if 'change' in data:
                        message += f"{trend} Thay đổi: {data['change']:+,.0f} VND\n"
                    
                    message += "\n"
        
        # Phân tích thị trường
        message += "=" * 35 + "\n"
        message += "📊 **PHÂN TÍCH THỊ TRƯỜNG**\n"
        message += self.generate_market_analysis(prices)
        
        return message
    
    def generate_market_analysis(self, prices: Dict) -> str:
        """
        Tạo phân tích thị trường tự động
        """
        analysis = []
        
        # Phân tích giá quốc tế
        if prices.get('international'):
            robusta = prices['international'].get('robusta', {})
            arabica = prices['international'].get('arabica', {})
            
            if robusta.get('change_percent') and arabica.get('change_percent'):
                r_change = robusta['change_percent']
                a_change = arabica['change_percent']
                
                if r_change > 0 and a_change > 0:
                    analysis.append("• ✅ Cả hai loại cà phê đều tăng giá")
                elif r_change < 0 and a_change < 0:
                    analysis.append("• ⚠️ Thị trường đang điều chỉnh giảm")
                else:
                    analysis.append("• 🔄 Thị trường đang phân hóa")
                
                if abs(r_change) > 2:
                    analysis.append(f"• 💥 Robusta biến động mạnh: {r_change:+.2f}%")
                
                if abs(a_change) > 2:
                    analysis.append(f"• 💥 Arabica biến động mạnh: {a_change:+.2f}%")
                
                # So sánh với biên độ ngày
                if robusta.get('day_high') and robusta.get('day_low'):
                    daily_range = ((robusta['day_high'] - robusta['day_low']) / robusta['day_low']) * 100
                    if daily_range > 3:
                        analysis.append(f"• 📈 Biên độ Robusta cao: {daily_range:.1f}%")
        
        # Thêm ghi chú về giờ giao dịch
        analysis.append("\n💡 **Lưu ý:**")
        analysis.append("• Giá London: Giao dịch 15:00-01:30 (giờ VN)")
        analysis.append("• Giá New York: Giao dịch 15:30-02:20 (giờ VN)")
        
        return "\n".join(analysis) if analysis else "• Thị trường ổn định"
    
    def save_to_file(self, data: Dict, filename: str = "coffee_prices.json"):
        """
        Lưu dữ liệu vào file JSON
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Đã lưu dữ liệu vào {filename}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu file: {e}")


# Sử dụng với Telegram integration
class CoffeePriceTelegramBot:
    """
    Tích hợp scraper với Telegram
    """
    
    def __init__(self, telegram_token: str, chat_id: str):
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.scraper = InvestingCoffeeScraper()
        self.telegram_url = f"https://api.telegram.org/bot{telegram_token}"
    
    def send_message(self, message: str) -> bool:
        """
        Gửi tin nhắn qua Telegram
        """
        try:
            url = f"{self.telegram_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Lỗi gửi Telegram: {e}")
            return False
    
    def run(self):
        """
        Chạy workflow chính
        """
        logger.info("🚀 Bắt đầu Coffee Price Monitor")
        
        # Scrape dữ liệu
        prices = self.scraper.scrape_all_prices()
        
        # Lưu vào file
        self.scraper.save_to_file(prices)
        
        # Format và gửi qua Telegram
        message = self.scraper.format_telegram_message(prices)
        
        if self.send_message(message):
            logger.info("✅ Đã gửi báo cáo qua Telegram")
        else:
            logger.error("❌ Không thể gửi tin nhắn Telegram")
        
        return prices


if __name__ == "__main__":
    import os
    
    # Chạy scraper độc lập (không cần Telegram)
    scraper = InvestingCoffeeScraper()
    prices = scraper.scrape_all_prices()
    
    # In kết quả
    print(json.dumps(prices, indent=2, ensure_ascii=False))
    
    # Lưu vào file
    scraper.save_to_file(prices)
    
    # Nếu có Telegram config thì gửi
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    
    if TELEGRAM_TOKEN and CHAT_ID:
        bot = CoffeePriceTelegramBot(TELEGRAM_TOKEN, CHAT_ID)
        bot.run()