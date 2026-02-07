import yfinance as yf
from typing import Dict, Any
from .base import BaseProvider
import logging

logger = logging.getLogger(__name__)

class FinancialProvider(BaseProvider):
    """
    Provider for financial data (Gold, Currency) using Yahoo Finance.
    """
    
    @property
    def source_name(self) -> str:
        return "Yahoo Finance"
        
    def get_prices(self) -> Dict[str, Any]:
        results = {}
        tickers = {
            'Gold (World)': 'GC=F',
            'USD/VND': 'VND=X'
        }
        
        try:
            # Fetch data for all tickers at once (optimization)
            # But yf.Tickers might be better if we want individual histories
            # Let's iterate for simplicity and individual error handling
            
            for name, symbol in tickers.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d")
                    
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev_close = hist['Open'].iloc[-1] # Approximation or use previous close
                        # Ideally calculate change from previous close, but open is a decent proxy for intra-day moved
                        change = current - prev_close
                        percent = (change / prev_close) * 100 if prev_close else 0
                        
                        currency = 'USD/oz' if 'Gold' in name else 'VND'
                        
                        results[name] = {
                            'price': current,
                            'change': change,
                            'change_percent': percent,
                            'currency': currency,
                            'success': True
                        }
                    else:
                        logger.warning(f"No data for {name} ({symbol})")
                
                except Exception as e:
                    logger.error(f"Error fetching {name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in FinancialProvider: {e}")
            
        return results
