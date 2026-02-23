import requests
import re
import logging
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseProvider
from ..config import Config
from bs4 import BeautifulSoup
from requests import Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request_with_retry(
    url: str,
    *,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
    retry_delay: Optional[float] = None,
    headers: Optional[dict] = None,
) -> Optional[Response]:
    """GET *url* with exponential-backoff retry.

    Returns the Response on success (status 200) or None after all retries.
    """
    timeout = timeout or Config.SCRAPER_TIMEOUT
    max_retries = max_retries or Config.SCRAPER_MAX_RETRIES
    retry_delay = retry_delay or Config.SCRAPER_RETRY_DELAY

    session = requests.Session()
    if headers:
        session.headers.update(headers)
    else:
        session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        })

    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
            logger.warning(
                "HTTP %s for %s (attempt %d/%d)",
                response.status_code, url, attempt, max_retries,
            )
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning(
                "Request error for %s (attempt %d/%d): %s",
                url, attempt, max_retries, exc,
            )

        if attempt < max_retries:
            sleep_time = retry_delay * (2 ** (attempt - 1))
            time.sleep(sleep_time)

    if last_exc:
        logger.error("All %d attempts failed for %s: %s", max_retries, url, last_exc)
    return None


def _parse_vn_number(s: str) -> float:
    """Parse Vietnamese formatted numbers like '94.700' → 94700.0"""
    return float(s.replace('.', '').replace(',', ''))


# ---------------------------------------------------------------------------
# Domestic scraper  (chocaphe.vn — per-province pages)
# ---------------------------------------------------------------------------

class ChocapheScraper(BaseProvider):
    """
    Scraper for Vietnamese domestic coffee prices from Chocaphe.vn.
    Uses per-province SSR pages for reliable data.
    """

    BASE_URL = "https://chocaphe.vn"
    PROVINCES = {
        'Đắk Lắk': '/gia-ca-phe-dak-lak.cfx',
        'Lâm Đồng': '/gia-ca-phe-lam-dong.cfx',
        'Gia Lai': '/gia-ca-phe-gia-lai.cfx',
        'Đắk Nông': '/gia-ca-phe-dak-nong.cfx',
    }

    def __init__(self, config=None):
        self.config = config

    @property
    def source_name(self) -> str:
        return "Chocaphe.vn"

    # ------------------------------------------------------------------

    def get_prices(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_province = {
                executor.submit(self._fetch_province, name, path): name
                for name, path in self.PROVINCES.items()
            }

            for future in as_completed(future_to_province, timeout=60):
                name = future_to_province[future]
                try:
                    data = future.result()
                    if data:
                        results[name] = data
                except Exception as exc:
                    logger.error("Error processing %s: %s", name, exc)

        return results

    def _fetch_province(self, name: str, path: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}{path}"
        response = _request_with_retry(url)
        if response is None:
            return None

        response.encoding = 'utf-8'

        try:
            return self._parse_province_page(response.text)
        except Exception as exc:
            logger.error("Error parsing %s: %s", name, exc)
            return None

    @staticmethod
    def _parse_province_page(html: str) -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')

        price = 0.0
        change = 0.0

        # Strategy 1: H1 tag
        h1 = soup.find('h1')
        if h1:
            text = h1.get_text()
            price_match = re.search(r'(\d+(?:\.\d+)+)\s*VNĐ/kg', text)
            if price_match:
                price = _parse_vn_number(price_match.group(1))

            change_match = re.search(r'(tăng|giảm)\s+(\d+(?:\.\d+)*)', text.lower())
            if change_match:
                direction, amount_str = change_match.groups()
                amount = _parse_vn_number(amount_str)
                change = -amount if direction == 'giảm' else amount

        # Strategy 2: Meta description fallback
        if price == 0:
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                text = meta.get('content', '')
                price_match = re.search(r'(\d+(?:\.\d+)+)\s*VNĐ/kg', text)
                if price_match:
                    price = _parse_vn_number(price_match.group(1))

        if price > 0:
            return {
                'price': price,
                'change': change,
                'change_percent': 0,
                'currency': 'VND/kg',
                'success': True,
            }
        return None


# ---------------------------------------------------------------------------
# International scraper  (chocaphe.vn — live prices page)
# ---------------------------------------------------------------------------

class ChocapheIntlScraper(BaseProvider):
    """
    Scraper for international coffee prices from
    https://chocaphe.vn/gia-ca-phe-truc-tuyen.cfp
    """
    URL = "https://chocaphe.vn/gia-ca-phe-truc-tuyen.cfp"

    def __init__(self, config=None):
        self.config = config

    @property
    def source_name(self) -> str:
        return "Chocaphe.vn (Intl)"

    def get_prices(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        response = _request_with_retry(self.URL)
        if response is None:
            logger.error("Failed to fetch international prices")
            return results

        response.encoding = 'utf-8'

        try:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Combine title + meta description for searching
            text_sources = []
            if soup.title:
                text_sources.append(soup.title.get_text())
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                text_sources.append(meta.get('content', ''))

            full_text = " ".join(text_sources).lower()

            # --- Robusta ---
            robusta_match = re.search(
                r'robusta.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*usd/tấn', full_text,
            )
            if robusta_match:
                price_str = robusta_match.group(1).replace(',', '')
                try:
                    results['Robusta (London)'] = {
                        'price': float(price_str),
                        'change': 0,
                        'change_percent': 0,
                        'currency': 'USD/Ton',
                        'success': True,
                    }
                except ValueError:
                    logger.warning("Could not parse Robusta price: %s", price_str)

            # --- Arabica ---
            arabica_match = re.search(
                r'arabica.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*cent/lb', full_text,
            )
            if arabica_match:
                price_str = arabica_match.group(1).replace(',', '')
                try:
                    results['Arabica (US)'] = {
                        'price': float(price_str),
                        'change': 0,
                        'change_percent': 0,
                        'currency': 'Cent/lb',
                        'success': True,
                    }
                except ValueError:
                    logger.warning("Could not parse Arabica price: %s", price_str)

        except Exception as exc:
            logger.error("Error scraping intl prices: %s", exc)

        return results
