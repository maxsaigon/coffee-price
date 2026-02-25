"""
Coffee Price Tracker — main entry point.

Usage:
    python -m src.main update    # Scrape prices and send Telegram notification
    python -m src.main test      # Dry-run (print only, no Telegram)
"""

import sys
import argparse
import logging
from datetime import datetime

from src.config import Config
from src.providers.chocaphe_scraper import ChocapheScraper, ChocapheIntlScraper
from src.providers.financial_provider import GoldPriceProvider
from src.services.telegram_bot import TelegramService
from src.services.formatter import MessageFormatter

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _fetch_all_data():
    """Fetch data from every provider.  Returns three dicts (or None)."""

    logger.info("Fetching international prices…")
    try:
        international_data = ChocapheIntlScraper().get_prices() or None
    except Exception as exc:
        logger.error("International scraper failed: %s", exc)
        international_data = None

    logger.info("Fetching domestic prices…")
    try:
        domestic_data = ChocapheScraper().get_prices() or None
    except Exception as exc:
        logger.error("Domestic scraper failed: %s", exc)
        domestic_data = None

    logger.info("Fetching gold prices…")
    try:
        gold_data = GoldPriceProvider().get_prices() or None
    except Exception as exc:
        logger.error("Gold price provider failed: %s", exc)
        gold_data = None

    return international_data, domestic_data, gold_data


def run_update(*, send_telegram: bool = True) -> bool:
    """Run a full price update cycle.

    Returns True if data was scraped (and optionally sent) successfully.
    """
    start = datetime.now()
    logger.info("=" * 50)
    logger.info("Starting price update at %s", start.isoformat())

    international_data, domestic_data, gold_data = _fetch_all_data()

    # Check that we have at least *some* data
    has_any_data = any([international_data, domestic_data, gold_data])
    if not has_any_data:
        logger.error("All providers returned no data — aborting")
        if send_telegram:
            _send_error_alert("Tất cả nguồn dữ liệu đều thất bại. Vui lòng kiểm tra hệ thống.")
        return False

    # Format message
    message = MessageFormatter.format_full_report(
        international_data, domestic_data, gold_data,
    )

    # Preview
    print("\n--- PREVIEW ---")
    print(message)
    print("---------------\n")

    # Send
    if send_telegram:
        bot = TelegramService()
        if not bot.send_message(message):
            logger.error("Failed to send Telegram message")
            return False

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("Price update completed in %.1fs", elapsed)
    return True


def _send_error_alert(detail: str) -> None:
    """Best-effort error notification via Telegram."""
    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        alert = (
            f"🚨 *LỖI HỆ THỐNG*\n"
            f"📅 {now}\n\n"
            f"{detail}\n\n"
            f"🤖 GiaNongSan Bot"
        )
        TelegramService().send_message(alert)
    except Exception as exc:
        logger.error("Could not send error alert: %s", exc)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Coffee Price Tracker")
    parser.add_argument(
        'command',
        choices=['update', 'test'],
        default='update',
        nargs='?',
    )
    args = parser.parse_args()

    if not Config.validate():
        sys.exit(1)

    if args.command == 'test':
        success = run_update(send_telegram=False)
    else:
        success = run_update(send_telegram=True)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
