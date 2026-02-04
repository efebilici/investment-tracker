"""Abstract data provider interfaces for fetching external investment data."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic


T = TypeVar('T')


@dataclass
class PriceData:
    """Represents price data fetched from an external provider.
    
    Attributes:
        symbol: The symbol/code used to fetch the data
        price: Current price in the specified currency
        currency: Currency code (e.g., 'USD', 'TRY', 'EUR')
        timestamp: When the price was fetched
        source: Provider name (e.g., 'tefas', 'investiny', 'manual')
        additional_info: Provider-specific additional data
        change_24h: Optional 24-hour price change percentage
        volume: Optional trading volume
    """
    symbol: str
    price: float
    currency: str
    timestamp: datetime
    source: str
    additional_info: Dict[str, Any] = field(default_factory=dict)
    change_24h: Optional[float] = None
    volume: Optional[float] = None


@dataclass
class CurrencyRate:
    """Represents a currency exchange rate.
    
    Attributes:
        base: Base currency code
        target: Target currency code
        rate: Exchange rate (1 base = rate target)
        timestamp: When the rate was fetched
        source: Provider name
    """
    base: str
    target: str
    rate: float
    timestamp: datetime
    source: str


@dataclass
class SearchResult:
    """Represents a search result for symbols/assets.
    
    Attributes:
        symbol: Trading symbol/code
        name: Display name
        full_name: Full/long name if available
        asset_type: Type (stock, etf, fund, crypto, etc.)
        exchange: Exchange name if available
        currency: Default currency
        country: Country of origin
        source: Which provider found this result
    """
    symbol: str
    name: str
    asset_type: str
    source: str
    full_name: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None


class DataProvider(ABC):
    """Abstract base class for all data providers.
    
    This defines the common interface that all providers must implement
    regardless of their underlying data source (TEFAS, Investiny, etc.)
    """
    
    def __init__(self, name: str, enabled: bool = True):
        """Initialize the provider.
        
        Args:
            name: Provider identifier
            enabled: Whether the provider is active
        """
        self.name = name
        self.enabled = enabled
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    @abstractmethod
    def fetch_price(self, symbol: str, **kwargs) -> Optional[PriceData]:
        """Fetch current price for a symbol.
        
        Args:
            symbol: The symbol/code to fetch
            **kwargs: Provider-specific options
            
        Returns:
            PriceData object or None if fetch fails
        """
        pass
    
    @abstractmethod
    def search_symbols(self, query: str, **kwargs) -> List[SearchResult]:
        """Search for symbols by name or partial symbol.
        
        Args:
            query: Search string
            **kwargs: Provider-specific options (asset_type, limit, etc.)
            
        Returns:
            List of matching SearchResult objects
        """
        pass
    
    def is_available(self) -> bool:
        """Check if the provider is available and working.
        
        Returns:
            True if provider can be used
        """
        return self.enabled
    
    def clear_cache(self) -> None:
        """Clear the provider's cache."""
        self._cache.clear()
        self._cache_timestamp = None


class CurrencyConverter(ABC):
    """Abstract base class for currency conversion.
    
    Implementations should handle fetching exchange rates and converting
    between different currencies.
    """
    
    def __init__(self, cache_duration_minutes: int = 60):
        """Initialize the converter.
        
        Args:
            cache_duration_minutes: How long to cache rates
        """
        self._cache_duration_minutes = cache_duration_minutes
        self._rates_cache: Dict[str, CurrencyRate] = {}
        self._last_update: Optional[datetime] = None
    
    @abstractmethod
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
            
        Raises:
            ValueError: If conversion not possible
        """
        pass
    
    @abstractmethod
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate (1 from_currency = rate to_currency)
        """
        pass
    
    def is_cache_valid(self) -> bool:
        """Check if cached rates are still valid.
        
        Returns:
            True if cache is fresh
        """
        if not self._last_update:
            return False
        elapsed = (datetime.now() - self._last_update).total_seconds() / 60
        return elapsed < self._cache_duration_minutes
    
    def clear_cache(self) -> None:
        """Clear the rates cache."""
        self._rates_cache.clear()
        self._last_update = None


class DataProviderManager:
    """Manages multiple data providers and coordinates between them.
    
    This provides a unified interface to query all available providers,
    search across all sources, and handle fallbacks.
    """
    
    def __init__(self):
        """Initialize the manager with no providers."""
        self._providers: Dict[str, DataProvider] = {}
        self._currency_converter: Optional[CurrencyConverter] = None
    
    def register_provider(self, provider: DataProvider) -> None:
        """Register a data provider.
        
        Args:
            provider: Provider instance to register
        """
        self._providers[provider.name] = provider
    
    def unregister_provider(self, name: str) -> None:
        """Unregister a provider by name.
        
        Args:
            name: Provider name to remove
        """
        if name in self._providers:
            del self._providers[name]
    
    def get_provider(self, name: str) -> Optional[DataProvider]:
        """Get a provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None
        """
        return self._providers.get(name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available (enabled) provider names.
        
        Returns:
            List of provider names
        """
        return [
            name for name, provider in self._providers.items()
            if provider.is_available()
        ]
    
    def search_all(self, query: str, **kwargs) -> List[SearchResult]:
        """Search across all available providers.
        
        Args:
            query: Search string
            **kwargs: Search options
            
        Returns:
            Combined list of results from all providers
        """
        results = []
        for provider in self._providers.values():
            if provider.is_available():
                try:
                    provider_results = provider.search_symbols(query, **kwargs)
                    results.extend(provider_results)
                except Exception:
                    # Log error but continue with other providers
                    continue
        return results
    
    def fetch_price_with_fallback(
        self, 
        symbol: str, 
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> Optional[PriceData]:
        """Fetch price with automatic fallback between providers.
        
        Args:
            symbol: Symbol to fetch
            preferred_provider: Try this provider first
            **kwargs: Fetch options
            
        Returns:
            PriceData from first successful provider
        """
        providers_to_try = []
        
        if preferred_provider and preferred_provider in self._providers:
            providers_to_try.append(preferred_provider)
        
        # Add other available providers
        for name in self.get_available_providers():
            if name not in providers_to_try:
                providers_to_try.append(name)
        
        for provider_name in providers_to_try:
            provider = self._providers[provider_name]
            try:
                price_data = provider.fetch_price(symbol, **kwargs)
                if price_data:
                    return price_data
            except Exception:
                continue
        
        return None
    
    def set_currency_converter(self, converter: CurrencyConverter) -> None:
        """Set the currency converter to use.
        
        Args:
            converter: Currency converter instance
        """
        self._currency_converter = converter
    
    def get_currency_converter(self) -> Optional[CurrencyConverter]:
        """Get the current currency converter.
        
        Returns:
            Currency converter or None
        """
        return self._currency_converter
    
    def clear_all_caches(self) -> None:
        """Clear caches for all providers and converter."""
        for provider in self._providers.values():
            provider.clear_cache()
        if self._currency_converter:
            self._currency_converter.clear_cache()


# Common asset types
ASSET_TYPE_STOCK = "stock"
ASSET_TYPE_ETF = "etf"
ASSET_TYPE_FUND = "fund"
ASSET_TYPE_CRYPTO = "crypto"
ASSET_TYPE_BOND = "bond"
ASSET_TYPE_COMMODITY = "commodity"
ASSET_TYPE_INDEX = "index"
ASSET_TYPE_CURRENCY = "currency"
ASSET_TYPE_MANUAL = "manual"

# Common data sources
DATA_SOURCE_MANUAL = "manual"
DATA_SOURCE_TEFAS = "tefas"
DATA_SOURCE_INVESTINY = "investiny"

# Currency codes
CURRENCY_USD = "USD"
CURRENCY_TRY = "TRY"
CURRENCY_EUR = "EUR"
CURRENCY_GBP = "GBP"
CURRENCY_JPY = "JPY"
CURRENCY_BTC = "BTC"
