import logging
import time
from typing import Dict, Any, Optional

import yfinance as yf

from .base import BaseProvider
from ..config import Config

logger = logging.getLogger(__name__)


class FinancialProvider(BaseProvider):
    """Provider for Gold price and USD/VND rate via Yahoo Finance."""

    TICKERS = {
        'Gold (World)': {'symbol': 'GC=F', 'currency': 'USD/oz'},
        'USD/VND':      {'symbol': 'VND=X', 'currency': 'VND'},
    }

    @property
    def source_name(self) -> str:
        return "Yahoo Finance"

    # ------------------------------------------------------------------

    def get_prices(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        for name, meta in self.TICKERS.items():
            data = self._fetch_ticker(
                name,
                meta['symbol'],
                meta['currency'],
            )
            if data is not None:
                results[name] = data

        return results

    def _fetch_ticker(
        self,
        name: str,
        symbol: str,
        currency: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single ticker with retry logic.

        Uses ``period='5d'`` instead of ``'1d'`` so that weekends /
        holidays still return the last available close.
        """
        max_retries = Config.SCRAPER_MAX_RETRIES
        retry_delay = Config.SCRAPER_RETRY_DELAY

        for attempt in range(1, max_retries + 1):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")

                if hist.empty:
                    logger.warning(
                        "No data for %s (%s), attempt %d/%d",
                        name, symbol, attempt, max_retries,
                    )
                    if attempt < max_retries:
                        time.sleep(retry_delay * (2 ** (attempt - 1)))
                    continue

                current = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Open'].iloc[-1])
                change = current - prev_close
                percent = (change / prev_close * 100) if prev_close else 0.0

                return {
                    'price': current,
                    'change': change,
                    'change_percent': percent,
                    'currency': currency,
                    'success': True,
                }

            except Exception as exc:
                logger.warning(
                    "Error fetching %s (attempt %d/%d): %s",
                    name, attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    time.sleep(retry_delay * (2 ** (attempt - 1)))

        logger.error("All %d attempts failed for %s (%s)", max_retries, name, symbol)
        return None
