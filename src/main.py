import sys
import argparse
import logging
from datetime import datetime
from src.config import Config
# from src.providers.yfinance_client import YFinanceProvider # Removed
from src.providers.chocaphe_scraper import ChocapheScraper, ChocapheIntlScraper
from src.services.telegram_bot import TelegramService

# Setup Logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def format_telegram_message(international_data, domestic_data):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    message = f"☕ *CẬP NHẬT GIÁ CAFE*\n"
    message += f"📅 _Thời gian: {now}_\n\n"
    
    # International Section
    message += "🌍 *THỊ TRƯỜNG QUỐC TẾ*\n"
    if international_data:
        for name, data in international_data.items():
            if data.get('success'):
                price = data['price']
                open_price = data.get('open', 0)
                change = data['change']
                percent = data['change_percent']
                icon = "📈" if change >= 0 else "📉"
                
                message += f"▪️ *{name}*\n"
                message += f"   💰 Giá: `{price:,.2f}`\n"
                # Only show open/change if we have meaningful data (change != 0 or open != 0)
                # Since scraper returns 0 for now, we might want to hide it or keep it simple
                # Keeping it simple for now, but maybe suppressing 0.00 is better?
                # For Chocaphe Intl, open/change is 0.
                if change != 0:
                     message += f"   🌅 Mở cửa: `{open_price:,.2f}`\n"
                     message += f"   {icon} Thay đổi: `{change:+.2f}` (`{percent:+.2f}%`)\n"
            else:
                message += f"▪️ *{name}*: ⚠️ N/A\n"
    else:
        message += "⚠️ Không có dữ liệu quốc tế\n"
        
    message += "\n"
    
    # Domestic Section
    message += "🇻🇳 *THỊ TRƯỜNG VIỆT NAM* (VND/kg)\n"
    if domestic_data:
        # Sort locations to ensure consistent order
        defined_order = ['Đắk Lắk', 'Lâm Đồng', 'Gia Lai', 'Đắk Nông']
        locations = sorted(domestic_data.keys(), key=lambda x: defined_order.index(x) if x in defined_order else 99)
        
        for location in locations:
            data = domestic_data[location]
            if data.get('success'):
                price = data['price']
                change = data['change']
                icon = "📈" if change > 0 else "📉" if change < 0 else "➖"
                
                # Format: Dak Lak: 80,500 (+200)
                message += f"▪️ *{location}*: `{price:,.0f}`"
                if change != 0:
                    message += f" ({icon} `{change:+,.0f}`)"
                message += "\n"
    else:
        message += "⚠️ Không có dữ liệu trong nước\n"

    return message

def run_update(send_telegram=True):
    logger.info("Starting price update...")
    
    # 1. Fetch International Prices
    # Replace yfinance with Chocaphe Intl
    yf_provider = ChocapheIntlScraper()
    international_data = yf_provider.get_prices()
    
    # 2. Fetch Domestic Prices
    dom_provider = ChocapheScraper()
    domestic_data = dom_provider.get_prices()
    
    # 3. Format Message
    message = format_telegram_message(international_data, domestic_data)
    
    # 4. Print Preview
    print("\n--- PREVIEW ---")
    print(message)
    print("---------------\n")
    
    # 5. Send Telegram
    if send_telegram:
        bot = TelegramService()
        bot.send_message(message)

def main():
    parser = argparse.ArgumentParser(description="Coffee Price Tracker")
    parser.add_argument('command', choices=['update', 'test'], default='update', nargs='?')
    args = parser.parse_args()
    
    # Validate Config
    if not Config.validate():
        sys.exit(1)
        
    if args.command == 'test':
        # Run without sending to Telegram
        run_update(send_telegram=False)
    else:
        run_update(send_telegram=True)

if __name__ == "__main__":
    main()
