import yfinance as yf
import logging
from typing import Dict, Any
from .base import BaseProvider

logger = logging.getLogger(__name__)

class YFinanceProvider(BaseProvider):
    """Provider for International Coffee Prices using Yahoo Finance"""
    
    SYMBOLS = {
        'Arabica (US)': 'KC=F',   # NYC Arabica Futures (cents/lb)
        'Robusta (London)': 'RM=F', # ICE Robusta Futures (USD/tonne)
        # 'Robusta (Alt)': 'RC=F'   # Alternative requested by user (often not valid on Yahoo)
    }
    
    @property
    def source_name(self) -> str:
        return "Yahoo Finance"
    
    def get_prices(self) -> Dict[str, Any]:
        results = {}
        
        try:
            # Fetch data for all symbols at once
            tickers = yf.Tickers(' '.join(self.SYMBOLS.values()))
            
            for name, symbol in self.SYMBOLS.items():
                try:
                    ticker = tickers.tickers[symbol]
                    
                    # Use history for reliability
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty:
                        # Get latest available close and open
                        price = hist['Close'].iloc[-1]
                        open_price = hist['Open'].iloc[-1]
                        
                        # Get previous close (either previous day or previous candle)
                        if len(hist) > 1:
                            prev_close = hist['Close'].iloc[-2]
                        else:
                            prev_close = price
                            
                        # Calculate change
                        change = price - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
                        
                        results[name] = {
                            'price': price,
                            'open': open_price,
                            'change': change,
                            'change_percent': change_percent,
                            'currency': 'USD' if 'US' in name else 'USD/T',
                            'success': True
                        }
                    else:
                        logger.warning(f"No data found for {name} ({symbol})")
                        results[name] = {'success': False, 'error': 'No data'}
                            
                except Exception as e:
                    logger.error(f"Error fetching {name} ({symbol}): {e}")
                    results[name] = {'success': False, 'error': str(e)}
                    
        except Exception as e:
            logger.error(f"Critical error in YFinanceProvider: {e}")
            
        return results
