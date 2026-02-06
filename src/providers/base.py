from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseProvider(ABC):
    """Abstract base class for coffee price providers"""
    
    @abstractmethod
    def get_prices(self) -> Dict[str, Any]:
        """
        Fetch prices and return a standardized dictionary.
        Returns:
            Dict containing price data
        """
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source"""
        pass
