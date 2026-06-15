import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from .base import BaseProvider
from ..config import Config

logger = logging.getLogger(__name__)

# Tickers to display from vang.today, mapped to short Vietnamese labels.
# Keep labels explicit: these codes are product/region specific, not generic brands.
GOLD_TICKERS = {
    'SJL1L10': 'SJC 1L/10L',
    'SJ9999': 'Nhẫn SJC',
    'DOHNL': 'DOJI HN',
    'DOHCML': 'DOJI HCM',
    'PQHNVM': 'PNJ HN',
}

DOMESTIC_GOLD_MIN = 50_000_000
DOMESTIC_GOLD_MAX = 300_000_000
DOMESTIC_SPREAD_MAX = 20_000_000
XAU_MIN = 1_000
XAU_MAX = 10_000
FUEL_MIN = 10_000
FUEL_MAX = 60_000


class GoldPriceProvider(BaseProvider):
    """Fetch domestic & world gold prices with validation and source metadata."""

    API_URL = "https://vang.today/api/prices"
    XAU_BACKUP_URL = "https://api.gold-api.com/price/XAU"

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
        source_timestamp = raw.get("timestamp")
        source_time = self._format_source_time(raw)
        age_minutes = self._age_minutes(source_timestamp)
        results: Dict[str, Any] = {}

        # --- Domestic gold ---
        for ticker, label in GOLD_TICKERS.items():
            item = prices_map.get(ticker)
            if item is None:
                continue
            if not self._valid_domestic_item(ticker, item):
                continue
            results[label] = {
                'buy': item['buy'],
                'sell': item['sell'],
                'change_buy': item.get('change_buy', 0),
                'change_sell': item.get('change_sell', 0),
                'currency': 'VND/lượng',
                'ticker': ticker,
                'source': self.source_name,
                'source_time': source_time,
                'age_minutes': age_minutes,
                'stale': self._is_stale(age_minutes),
                'success': True,
            }

        # --- World gold (XAU/USD) ---
        xau = prices_map.get("XAUUSD")
        if xau is not None and self._valid_xau_item("vang.today", xau):
            price = float(xau['buy'])
            backup = self._fetch_backup_xau()
            source_diff_percent = None
            verified = True
            if backup is not None:
                backup_price = backup.get('price')
                source_diff_percent = self._diff_percent(price, backup_price)
                verified = source_diff_percent <= Config.GOLD_XAU_MAX_SOURCE_DIFF_PERCENT

            results['Vàng TG'] = {
                'price': price,
                'change': xau.get('change_buy', 0),
                'currency': 'USD/oz',
                'ticker': 'XAUUSD',
                'source': self.source_name,
                'source_time': source_time,
                'age_minutes': age_minutes,
                'backup_source': backup.get('source') if backup else None,
                'backup_price': backup.get('price') if backup else None,
                'source_diff_percent': source_diff_percent,
                'verified': verified,
                'stale': self._is_stale(age_minutes),
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

    def _fetch_backup_xau(self) -> Optional[Dict[str, Any]]:
        """Fetch a second XAU/USD quote for sanity checking."""
        try:
            resp = requests.get(self.XAU_BACKUP_URL, timeout=Config.SCRAPER_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            price = float(data["price"])
            if not (XAU_MIN <= price <= XAU_MAX):
                logger.warning("gold-api XAU out of range: %s", price)
                return None
            return {
                'source': 'gold-api.com',
                'price': price,
                'updated_at': data.get('updatedAt'),
            }
        except Exception as exc:
            logger.warning("Could not fetch backup XAU quote: %s", exc)
            return None

    @staticmethod
    def _valid_domestic_item(ticker: str, item: Dict[str, Any]) -> bool:
        try:
            buy = float(item['buy'])
            sell = float(item['sell'])
        except (KeyError, TypeError, ValueError):
            logger.warning("Invalid domestic gold schema for %s: %s", ticker, item)
            return False

        if not (DOMESTIC_GOLD_MIN <= buy <= DOMESTIC_GOLD_MAX):
            logger.warning("Domestic gold buy out of range for %s: %s", ticker, buy)
            return False
        if not (DOMESTIC_GOLD_MIN <= sell <= DOMESTIC_GOLD_MAX):
            logger.warning("Domestic gold sell out of range for %s: %s", ticker, sell)
            return False
        if sell < buy:
            logger.warning("Domestic gold sell < buy for %s: buy=%s sell=%s", ticker, buy, sell)
            return False
        if sell - buy > DOMESTIC_SPREAD_MAX:
            logger.warning("Domestic gold spread too wide for %s: %s", ticker, sell - buy)
            return False
        return True

    @staticmethod
    def _valid_xau_item(source: str, item: Dict[str, Any]) -> bool:
        try:
            price = float(item['buy'])
        except (KeyError, TypeError, ValueError):
            logger.warning("Invalid XAU schema from %s: %s", source, item)
            return False
        if not (XAU_MIN <= price <= XAU_MAX):
            logger.warning("XAU price out of range from %s: %s", source, price)
            return False
        return True

    @staticmethod
    def _format_source_time(raw: Dict[str, Any]) -> Optional[str]:
        timestamp = raw.get("timestamp")
        if timestamp:
            try:
                dt = datetime.fromtimestamp(int(timestamp), ZoneInfo(Config.TIMEZONE))
                return dt.strftime("%d/%m %H:%M")
            except (TypeError, ValueError, OSError):
                pass

        date = raw.get("date")
        time_text = raw.get("time")
        if date and time_text:
            return f"{date} {time_text}"
        return time_text or date

    @staticmethod
    def _age_minutes(timestamp: Optional[int]) -> Optional[float]:
        if not timestamp:
            return None
        try:
            now = datetime.now(ZoneInfo(Config.TIMEZONE)).timestamp()
            return max(0, (now - int(timestamp)) / 60)
        except (TypeError, ValueError, OSError):
            return None

    @staticmethod
    def _is_stale(age_minutes: Optional[float]) -> bool:
        return age_minutes is not None and age_minutes > Config.GOLD_MAX_STALE_MINUTES

    @staticmethod
    def _diff_percent(a: float, b: float) -> float:
        base = (abs(a) + abs(b)) / 2
        if base == 0:
            return 0
        return abs(a - b) / base * 100


class ExchangeRateProvider(BaseProvider):
    """Fetch USD/VND rate from open.er-api.com (free, no key)."""

    API_URL = "https://open.er-api.com/v6/latest/USD"

    @property
    def source_name(self) -> str:
        return "ExchangeRate-API"

    def get_prices(self) -> Dict[str, Any]:
        """Return USD/VND mid-market rate."""
        max_retries = Config.SCRAPER_MAX_RETRIES
        retry_delay = Config.SCRAPER_RETRY_DELAY
        timeout = Config.SCRAPER_TIMEOUT

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(self.API_URL, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()

                if data.get("result") == "success":
                    vnd = data["rates"].get("VND")
                    if vnd is not None:
                        return {
                            'USD/VND': {
                                'rate': round(vnd),
                                'success': True,
                            }
                        }

                logger.warning("VND rate not found (attempt %d/%d)", attempt, max_retries)

            except Exception as exc:
                logger.warning(
                    "Error fetching exchange rates (attempt %d/%d): %s",
                    attempt, max_retries, exc,
                )

            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** (attempt - 1)))

        logger.error("All %d attempts failed for exchange rates", max_retries)
        return {}


class FuelPriceProvider(BaseProvider):
    """Fetch domestic Petrolimex fuel prices from Webgia."""

    URL = "https://webgia.com/gia-xang-dau/petrolimex/"
    PRODUCTS = {
        "Xăng RON 95-III": "R95",
        "Xăng E5 RON 92-II": "E5",
        "DO 0,05S-II": "DO",
    }

    @property
    def source_name(self) -> str:
        return "webgia.com/Petrolimex"

    def get_prices(self) -> Dict[str, Any]:
        raw = self._fetch_page()
        if raw is None:
            return {}

        return self._parse_page(raw, Config.FUEL_REGION)

    def _fetch_page(self) -> Optional[str]:
        for attempt in range(1, Config.SCRAPER_MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    self.URL,
                    timeout=Config.SCRAPER_TIMEOUT,
                    headers={
                        'User-Agent': (
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/120.0.0.0 Safari/537.36'
                        )
                    },
                )
                resp.raise_for_status()
                resp.encoding = 'utf-8'
                return resp.text
            except Exception as exc:
                logger.warning(
                    "Error fetching fuel prices (attempt %d/%d): %s",
                    attempt, Config.SCRAPER_MAX_RETRIES, exc,
                )
                if attempt < Config.SCRAPER_MAX_RETRIES:
                    time.sleep(Config.SCRAPER_RETRY_DELAY * (2 ** (attempt - 1)))

        logger.error("All %d attempts failed for fuel prices", Config.SCRAPER_MAX_RETRIES)
        return None

    def _parse_page(self, html: str, region: int) -> Dict[str, Any]:
        if region not in (1, 2):
            logger.warning("Unsupported fuel region %s, falling back to region 2", region)
            region = 2

        soup = BeautifulSoup(html, 'html.parser')
        
        # Locate the table containing Petrolimex products (safe from header/ad tables)
        table = None
        for t in soup.find_all('table'):
            t_text = t.get_text()
            if "RON 95" in t_text or "Sản phẩm" in t_text:
                table = t
                break
        
        if table is None:
            table = soup.find('table')

        if table is None:
            logger.warning("Fuel price table not found")
            return {}

        source_time = self._extract_source_time(soup)
        results: Dict[str, Any] = {}
        price_col = region

        for row in table.find_all('tr'):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(['td', 'th'])]
            if len(cells) < 3:
                continue

            product = cells[0]
            short = self.PRODUCTS.get(product)
            if short is None:
                continue

            price = self._parse_price(cells[price_col])
            if price is None:
                continue

            results[short] = {
                'price': price,
                'currency': 'VND/lít',
                'region': region,
                'source': self.source_name,
                'source_time': source_time,
                'success': True,
            }

        return results

    @staticmethod
    def _parse_price(value: str) -> Optional[int]:
        try:
            price = int(value.replace('.', '').replace(',', '').strip())
        except ValueError:
            logger.warning("Invalid fuel price: %s", value)
            return None

        if not (FUEL_MIN <= price <= FUEL_MAX):
            logger.warning("Fuel price out of range: %s", price)
            return None
        return price

    @staticmethod
    def _extract_source_time(soup: BeautifulSoup) -> Optional[str]:
        text = soup.get_text(" ", strip=True)
        match = re.search(r"Cập nhật lúc\s+(\d{2}:\d{2}:\d{2})\s+(\d{2})/(\d{2})/(\d{4})", text)
        if not match:
            return None

        time_text, day, month, _year = match.groups()
        return f"{day}/{month} {time_text[:5]}"
