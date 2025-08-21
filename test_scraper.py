# test_scraper.py - Script kiểm tra scraper
import sys
import json
from datetime import datetime

def test_basic_scraping():
    """Test cơ bản scraping từ Investing.com"""
    from investing_coffee_scraper import InvestingCoffeeScraper
    
    print("=" * 50)
    print("🧪 KIỂM TRA SCRAPER")
    print("=" * 50)
    
    scraper = InvestingCoffeeScraper()
    
    # Test scraping Robusta
    print("\n1️⃣ Test Robusta (London)...")
    robusta_html = scraper.get_page_content(scraper.urls['robusta']['url'])
    
    if robusta_html:
        print("✅ Đã lấy được HTML Robusta")
        robusta_data = scraper.parse_coffee_price(robusta_html, 'robusta')
        
        if robusta_data and 'current_price' in robusta_data:
            print(f"✅ Giá Robusta: ${robusta_data['current_price']}")
            print(f"   Change: {robusta_data.get('change', 'N/A')}")
            print(f"   Volume: {robusta_data.get('volume', 'N/A')}")
        else:
            print("⚠️ Không parse được giá Robusta")
    else:
        print("❌ Không thể truy cập trang Robusta")
    
    # Test scraping Arabica
    print("\n2️⃣ Test Arabica (New York)...")
    arabica_html = scraper.get_page_content(scraper.urls['arabica']['url'])
    
    if arabica_html:
        print("✅ Đã lấy được HTML Arabica")
        arabica_data = scraper.parse_coffee_price(arabica_html, 'arabica')
        
        if arabica_data and 'current_price' in arabica_data:
            print(f"✅ Giá Arabica: {arabica_data['current_price']} cents/lb")
            print(f"   Change: {arabica_data.get('change', 'N/A')}")
            print(f"   Volume: {arabica_data.get('volume', 'N/A')}")
        else:
            print("⚠️ Không parse được giá Arabica")
    else:
        print("❌ Không thể truy cập trang Arabica")
    
    # Test full scraping
    print("\n3️⃣ Test full scraping...")
    all_prices = scraper.scrape_all_prices()
    
    if all_prices and all_prices.get('international'):
        print("✅ Scraping hoàn tất!")
        print(f"   Số loại cà phê quốc tế: {len(all_prices['international'])}")
        print(f"   Số nguồn VN: {len(all_prices.get('vietnam', {}))}")
        
        # Lưu kết quả test
        test_file = f"test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(all_prices, f, ensure_ascii=False, indent=2)
        print(f"\n📁 Kết quả đã lưu vào: {test_file}")
        
        # Test format message
        print("\n4️⃣ Test format Telegram message...")
        message = scraper.format_telegram_message(all_prices)
        print("📱 Preview tin nhắn Telegram:")
        print("-" * 40)
        print(message[:500] + "..." if len(message) > 500 else message)
        print("-" * 40)
        
        return True
    else:
        print("❌ Scraping thất bại")
        return False

def test_with_selenium():
    """
    Backup option: Sử dụng Selenium nếu requests bị block
    """
    print("\n" + "=" * 50)
    print("🌐 TEST VỚI SELENIUM (Backup Option)")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Cấu hình Chrome headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Test với Robusta
        print("\n🔄 Đang test với Selenium...")
        driver.get('https://www.investing.com/commodities/london-coffee')
        
        # Đợi element load
        wait = WebDriverWait(driver, 10)
        price_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="instrument-price-last"]'))
        )
        
        price = price_element.text
        print(f"✅ Giá Robusta (via Selenium): {price}")
        
        driver.quit()
        return True
        
    except ImportError:
        print("⚠️ Selenium chưa được cài đặt")
        print("   Chạy: pip install selenium")
        print("   Và cài đặt ChromeDriver")
        return False
    except Exception as e:
        print(f"❌ Lỗi Selenium: {e}")
        return False

def test_cloudflare_bypass():
    """
    Test bypass Cloudflare protection nếu có
    """
    print("\n" + "=" * 50)
    print("🛡️ TEST CLOUDFLARE BYPASS")
    print("=" * 50)
    
    try:
        import cloudscraper
        
        scraper = cloudscraper.create_scraper()
        response = scraper.get('https://www.investing.com/commodities/london-coffee')
        
        if response.status_code == 200:
            print("✅ Cloudscraper hoạt động tốt")
            print(f"   Response length: {len(response.text)} chars")
            
            # Kiểm tra có data không
            if 'instrument-price' in response.text:
                print("✅ Tìm thấy data giá trong response")
            else:
                print("⚠️ Không tìm thấy data giá")
            
            return True
        else:
            print(f"❌ Status code: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️ Cloudscraper chưa được cài đặt")
        print("   Chạy: pip install cloudscraper")
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BẮT ĐẦU KIỂM TRA HỆ THỐNG")
    print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Basic scraping
    basic_test = test_basic_scraping()
    
    # Test 2: Cloudflare bypass (nếu basic fail)
    if not basic_test:
        print("\n⚠️ Basic scraping thất bại, thử Cloudflare bypass...")
        cf_test = test_cloudflare_bypass()
        
        # Test 3: Selenium (last resort)
        if not cf_test:
            print("\n⚠️ Cloudflare bypass thất bại, thử Selenium...")
            selenium_test = test_with_selenium()
    
    print("\n" + "=" * 50)
    print("📊 KẾT QUẢ KIỂM TRA")
    print("=" * 50)
    
    if basic_test:
        print("✅ Hệ thống hoạt động tốt với requests cơ bản")
    else:
        print("⚠️ Cần sử dụng phương pháp bypass")
        print("   Đề xuất: Sử dụng Cloudscraper hoặc Selenium")
        print("\n📌 HƯỚNG DẪN XỬ LÝ:")
        print("1. Thử với Cloudscraper trước (nhanh hơn)")
        print("2. Nếu không được, dùng Selenium")
        print("3. Cân nhắc sử dụng proxy rotation")
        print("4. Hoặc chuyển sang API chính thức (nếu có)")
    
    print("\n✨ Test hoàn tất!")