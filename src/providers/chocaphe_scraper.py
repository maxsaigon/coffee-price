import requests
import re
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from .base import BaseProvider
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ChocapheScraper(BaseProvider):
    """
    Scraper for Vietnamese domestic coffee prices from Chocaphe.vn.
    Uses multi-page fetching strategy (SSR) to get reliable data for specific provinces.
    """
    
    BASE_URL = "https://chocaphe.vn"
    PROVINCES = {
        'Đắk Lắk': '/gia-ca-phe-dak-lak.cfx',
        'Lâm Đồng': '/gia-ca-phe-lam-dong.cfx',
        'Gia Lai': '/gia-ca-phe-gia-lai.cfx',
        'Đắk Nông': '/gia-ca-phe-dak-nong.cfx'
    }
    
    def __init__(self, config=None):
        self.config = config

    @property
    def source_name(self) -> str:
        return "Chocaphe.vn"
    
    def get_prices(self) -> Dict[str, Any]:
        results = {}
        
        # Parallel fetching for speed
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_province = {
                executor.submit(self._fetch_province, name, path): name 
                for name, path in self.PROVINCES.items()
            }
            
            for future in future_to_province:
                name = future_to_province[future]
                try:
                    data = future.result()
                    if data:
                        results[name] = data
                except Exception as e:
                    logger.error(f"Error processing {name}: {e}")
                    
        return results

    def _fetch_province(self, name: str, path: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}{path}"
        try:
            response = requests.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {name} from {url}: Status {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Helper to parse integers from "94.700" format
            def parse_vn_num(s):
                return float(s.replace('.', '').replace(',', ''))

            price = 0.0
            change = 0.0
            
            # --- Strategy 1: Parse H1 Tag ---
            # Ex: "Giá cà phê Đắk Lắk hôm nay...: 94.700 VNĐ/kg giảm 800 VNĐ/kg..."
            h1 = soup.find('h1')
            if h1:
                text = h1.get_text()
                
                # Extract Price
                price_match = re.search(r'(\d+(?:\.\d+)+)\s*VNĐ/kg', text)
                if price_match:
                    price = parse_vn_num(price_match.group(1))
                    
                # Extract Change
                # Look for "tăng X" or "giảm X"
                # Note: The text might be "tăng 100" or "giảm 1.000"
                change_match = re.search(r'(tăng|giảm)\s+(\d+(?:\.\d+)*)', text.lower())
                if change_match:
                    direction = change_match.group(1)
                    amount = parse_vn_num(change_match.group(2))
                    if direction == 'giảm':
                        change = -amount
                    else:
                        change = amount
                        
            # --- Strategy 2: Fallback to Meta Description ---
            if price == 0:
                meta = soup.find('meta', {'name': 'description'})
                if meta:
                    text = meta.get('content', '')
                    price_match = re.search(r'(\d+(?:\.\d+)+)\s*VNĐ/kg', text)
                    if price_match:
                        price = parse_vn_num(price_match.group(1))
                        
            if price > 0:
                return {
                    'price': price,
                    'change': change,
                    'change_percent': 0, # Not easily available in H1/Meta
                    'currency': 'VND/kg',
                    'success': True
                }
            
            return None

        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            return None

class ChocapheIntlScraper(BaseProvider):
    """
    Scraper for International coffee prices from Chocaphe.vn.
    Source: https://chocaphe.vn/gia-ca-phe-truc-tuyen.cfp
    """
    URL = "https://chocaphe.vn/gia-ca-phe-truc-tuyen.cfp"

    def __init__(self, config=None):
        self.config = config

    @property
    def source_name(self) -> str:
        return "Chocaphe.vn (Intl)"

    def get_prices(self) -> Dict[str, Any]:
        results = {}
        try:
            # Use requests to fetch the page
            scraper_session = requests.Session()
            # Mimic browser to avoid potential blocking (though curl worked fine)
            scraper_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            response = scraper_session.get(self.URL, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch Intl prices: Status {response.status_code}")
                return results

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Combine Title and Description for searching
            text_sources = []
            if soup.title:
                text_sources.append(soup.title.get_text())
            
            meta = soup.find('meta', {'name': 'description'})
            if meta:
                text_sources.append(meta.get('content', ''))
                
            full_text = " ".join(text_sources).lower()
            
            # --- Robusta ---
            # Pattern: robusta ... 3,755 ... usd/tấn
            # Regex needs to be flexible for spaces/text in between
            # "robusta 3,755 usd/tấn"
            robusta_match = re.search(r'robusta.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*usd/tấn', full_text)
            if robusta_match:
                price_str = robusta_match.group(1).replace(',', '') # Remove comma thousands separator
                try:
                    price = float(price_str)
                    results['Robusta (London)'] = {
                        'price': price,
                        'change': 0, # Not parsed
                        'change_percent': 0,
                        'currency': 'USD/Ton',
                        'success': True
                    }
                except ValueError:
                    logger.warning(f"Could not parse Robusta price: {price_str}")
                
            # --- Arabica ---
            # Pattern: arabica ... 296.55 ... cent/lb
            arabica_match = re.search(r'arabica.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*cent/lb', full_text)
            if arabica_match:
                price_str = arabica_match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    results['Arabica (US)'] = {
                        'price': price,
                        'change': 0,
                        'change_percent': 0,
                        'currency': 'Cent/lb',
                        'success': True
                    }
                except ValueError:
                    logger.warning(f"Could not parse Arabica price: {price_str}")

        except Exception as e:
            logger.error(f"Error scraping intl prices: {e}")
            
        return results
