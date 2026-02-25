import logging
import time
from typing import Dict, Any, Optional

import requests

from .base import BaseProvider
from ..config import Config

logger = logging.getLogger(__name__)

# Tickers to display from vang.today, mapped to short Vietnamese labels.
GOLD_TICKERS = {
    'SJL1L10':  'SJC 9999',
    'DOJINHTV': 'DOJI',
}


class GoldPriceProvider(BaseProvider):
    """Fetch domestic & world gold prices from vang.today (free, no key)."""

    API_URL = "https://vang.today/api/prices"

    @property
    def source_name(self) -> str:
        return "vang.today"

    # ------------------------------------------------------------------

    def get_prices(self) -> Dict[str, Any]:
        """Return gold price data keyed by Vietnamese label.

        Includes both domestic gold (SJC, DOJI) and world gold (XAU/USD).
        """
        raw = self._fetch_api()
        if raw is None:
            return {}

        prices_map = raw.get("prices", {})
        results: Dict[str, Any] = {}

        # --- Domestic gold ---
        for ticker, label in GOLD_TICKERS.items():
            item = prices_map.get(ticker)
            if item is None:
                continue
            results[label] = {
                'buy': item['buy'],
                'sell': item['sell'],
                'change_buy': item.get('change_buy', 0),
                'change_sell': item.get('change_sell', 0),
                'currency': 'VND',
                'success': True,
            }

        # --- World gold (XAU/USD) ---
        xau = prices_map.get("XAUUSD")
        if xau is not None:
            results['Vàng TG'] = {
                'price': xau['buy'],       # spot price
                'change': xau.get('change_buy', 0),
                'currency': 'USD/oz',
                'success': True,
            }

        return results

    # ------------------------------------------------------------------

    def _fetch_api(self) -> Optional[Dict[str, Any]]:
        """GET the API with retry logic."""
        max_retries = Config.SCRAPER_MAX_RETRIES
        retry_delay = Config.SCRAPER_RETRY_DELAY
        timeout = Config.SCRAPER_TIMEOUT

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(self.API_URL, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()

                if not data.get("success"):
                    logger.warning(
                        "vang.today returned success=false (attempt %d/%d)",
                        attempt, max_retries,
                    )
                    if attempt < max_retries:
                        time.sleep(retry_delay * (2 ** (attempt - 1)))
                    continue

                return data

            except Exception as exc:
                logger.warning(
                    "Error fetching vang.today (attempt %d/%d): %s",
                    attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    time.sleep(retry_delay * (2 ** (attempt - 1)))

        logger.error("All %d attempts failed for vang.today", max_retries)
        return None
