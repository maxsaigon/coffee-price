#!/usr/bin/env python3
"""Debug the Telegram message formatting"""

import asyncio
from enhanced_multi_source_scraper import EnhancedMultiSourceScraper
from telegram_bot import TelegramBot

async def debug_message():
    """Debug the message formatting"""
    print("🔍 Debugging Telegram message...")
    
    # Get scraper data
    scraper = EnhancedMultiSourceScraper()
    price_data = scraper.scrape_all_prices()
    
    # Format message
    message = scraper.format_telegram_message(price_data)
    
    print("📄 Generated message:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    
    # Check message length
    print(f"📏 Message length: {len(message)} characters")
    
    # Try to send with different parse modes
    bot = TelegramBot()
    
    print("\n🧪 Testing different parse modes...")
    
    # Test with HTML
    print("Trying HTML parse mode...")
    try:
        html_message = message.replace('*', '<b>').replace('*', '</b>')
        success = await bot.send_message(html_message, parse_mode="HTML")
        print(f"HTML result: {success}")
    except Exception as e:
        print(f"HTML failed: {e}")
    
    # Test without parse mode
    print("Trying without parse mode...")
    try:
        plain_message = message.replace('*', '')
        success = await bot.send_message(plain_message, parse_mode="")
        print(f"Plain result: {success}")
    except Exception as e:
        print(f"Plain failed: {e}")
    
    # Test with MarkdownV2
    print("Trying MarkdownV2...")
    try:
        success = await bot.send_message(message, parse_mode="MarkdownV2")
        print(f"MarkdownV2 result: {success}")
    except Exception as e:
        print(f"MarkdownV2 failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_message())