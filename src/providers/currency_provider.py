"""Currency conversion provider using forex-python and fallback APIs.

This module provides multi-source currency conversion with caching support.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import requests

try:
    from forex_python.converter import CurrencyRates, RatesNotAvailableError
    from forex_python.bitcoin import BtcConverter
    FOREX_PYTHON_AVAILABLE = True
except ImportError:
    FOREX_PYTHON_AVAILABLE = False
    CurrencyRates = None
    RatesNotAvailableError = Exception
    BtcConverter = None

from ..data_providers import CurrencyConverter, CurrencyRate


class CurrencyConverterProvider(CurrencyConverter):
    """Multi-source currency converter with caching.
    
    Primary source: forex-python (European Central Bank rates)
    Fallback source: exchange-api (free, no rate limits)
    
    Supports 150+ currencies plus Bitcoin.
    
    Example:
        >>> converter = CurrencyConverterProvider()
        >>> 
        >>> # Convert USD to TRY
        >>> amount_try = converter.convert(100, "USD", "TRY")
        >>> print(f"100 USD = {amount_try:.2f} TRY")
        >>> 
        >>> # Get exchange rate
        >>> rate = converter.get_rate("EUR", "USD")
        >>> print(f"1 EUR = {rate:.4f} USD")
    """
    
    # Major currencies commonly used
    MAJOR_CURRENCIES = [
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZF",
        "TRY", "CNY", "INR", "BRL", "MXN", "ZAR", "RUB", "KRW",
        "SGD", "HKD", "SEK", "NOK", "DKK", "PLN", "HUF", "CZK",
        "ILS", "AED", "SAR", "THB", "MYR", "IDR", "PHP", "VND",
    ]
    
    # Currency symbols for display
    CURRENCY_SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CHF": "Fr",
        "CAD": "C$",
        "AUD": "A$",
        "TRY": "₺",
        "CNY": "¥",
        "INR": "₹",
        "BRL": "R$",
        "MXN": "$",
        "ZAR": "R",
        "RUB": "₽",
        "KRW": "₩",
        "SGD": "S$",
        "HKD": "HK$",
        "SEK": "kr",
        "NOK": "kr",
        "DKK": "kr",
        "PLN": "zł",
        "HUF": "Ft",
        "CZK": "Kč",
        "ILS": "₪",
        "AED": "د.إ",
        "SAR": "﷼",
        "THB": "฿",
        "MYR": "RM",
        "IDR": "Rp",
        "PHP": "₱",
        "VND": "₫",
        "BTC": "₿",
    }
    
    def __init__(self, cache_duration_minutes: int = 60):
        """Initialize currency converter.
        
        Args:
            cache_duration_minutes: How long to cache exchange rates
        """
        super().__init__(cache_duration_minutes)
        self._currency_rates: Optional[Any] = None
        self._btc_converter: Optional[Any] = None
    
    def _get_currency_rates(self) -> Any:
        """Get or create CurrencyRates instance."""
        if self._currency_rates is None:
            if not FOREX_PYTHON_AVAILABLE:
                raise RuntimeError(
                    "forex-python library not installed. "
                    "Install with: uv add forex-python"
                )
            self._currency_rates = CurrencyRates()
        return self._currency_rates
    
    def _get_btc_converter(self) -> Any:
        """Get or create BtcConverter instance."""
        if self._btc_converter is None:
            if not FOREX_PYTHON_AVAILABLE:
                raise RuntimeError(
                    "forex-python library not installed. "
                    "Install with: uv add forex-python"
                )
            self._btc_converter = BtcConverter()
        return self._btc_converter
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., "USD")
            to_currency: Target currency code (e.g., "TRY")
            
        Returns:
            Converted amount
            
        Raises:
            ValueError: If conversion fails
            
        Example:
            >>> converter = CurrencyConverterProvider()
            >>> amount = converter.convert(100, "USD", "EUR")
            >>> print(f"100 USD = {amount:.2f} EUR")
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency, no conversion needed
        if from_currency == to_currency:
            return amount
        
        # Try forex-python first
        if FOREX_PYTHON_AVAILABLE:
            try:
                rates = self._get_currency_rates()
                return rates.convert(from_currency, to_currency, amount)
            except RatesNotAvailableError:
                # Fallback to exchange-api
                pass
            except Exception:
                # Any other error, try fallback
                pass
        
        # Fallback to exchange-api
        return self._convert_via_api(amount, from_currency, to_currency)
    
    def _convert_via_api(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert using exchange-api as fallback.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
            
        Raises:
            ValueError: If API call fails
        """
        rate = self._get_rate_via_api(from_currency, to_currency)
        if rate is None:
            raise ValueError(
                f"Could not get exchange rate for {from_currency} to {to_currency}"
            )
        return amount * rate
    
    def _get_rate_via_api(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate from exchange-api.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate or None if failed
        """
        cache_key = f"{from_currency}_{to_currency}"
        
        # Check cache
        if self.is_cache_valid() and cache_key in self._rates_cache:
            cached_rate = self._rates_cache[cache_key]
            return cached_rate.rate
        
        try:
            # Primary API endpoint
            url = (
                f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/"
                f"v1/currencies/{from_currency.lower()}.json"
            )
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            rates = data.get(from_currency.lower(), {})
            rate = rates.get(to_currency.lower())
            
            if rate is None:
                return None
            
            # Cache the rate
            self._rates_cache[cache_key] = CurrencyRate(
                base=from_currency,
                target=to_currency,
                rate=float(rate),
                timestamp=datetime.now(),
                source="exchange-api",
            )
            self._last_update = datetime.now()
            
            return float(rate)
            
        except Exception as e:
            # Try fallback API endpoint
            try:
                url = (
                    f"https://latest.currency-api.pages.dev/"
                    f"v1/currencies/{from_currency.lower()}.json"
                )
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                rates = data.get(from_currency.lower(), {})
                rate = rates.get(to_currency.lower())
                
                if rate is None:
                    return None
                
                # Cache the rate
                self._rates_cache[cache_key] = CurrencyRate(
                    base=from_currency,
                    target=to_currency,
                    rate=float(rate),
                    timestamp=datetime.now(),
                    source="exchange-api-fallback",
                )
                self._last_update = datetime.now()
                
                return float(rate)
                
            except Exception:
                return None
    
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate (1 from_currency = rate to_currency)
            
        Raises:
            ValueError: If rate cannot be retrieved
        """
        # Convert 1 unit to get the rate
        return self.convert(1.0, from_currency, to_currency)
    
    def get_btc_price(self, currency: str = "USD") -> float:
        """Get Bitcoin price in specified currency.
        
        Args:
            currency: Currency code (default USD)
            
        Returns:
            Bitcoin price
            
        Raises:
            ValueError: If price cannot be retrieved
        """
        if not FOREX_PYTHON_AVAILABLE:
            # Fallback to exchange-api for BTC
            rate = self._get_rate_via_api("BTC", currency)
            if rate is None:
                raise ValueError(f"Could not get BTC price in {currency}")
            return rate
        
        try:
            btc_converter = self._get_btc_converter()
            return btc_converter.get_latest_price(currency)
        except Exception as e:
            # Fallback to API
            rate = self._get_rate_via_api("BTC", currency)
            if rate is None:
                raise ValueError(f"Could not get BTC price in {currency}: {e}")
            return rate
    
    def convert_to_btc(self, amount: float, currency: str = "USD") -> float:
        """Convert amount to Bitcoin.
        
        Args:
            amount: Amount in specified currency
            currency: Currency code
            
        Returns:
            Amount in Bitcoin
        """
        if not FOREX_PYTHON_AVAILABLE:
            # Manual conversion
            btc_price = self.get_btc_price(currency)
            if btc_price <= 0:
                raise ValueError("Invalid BTC price")
            return amount / btc_price
        
        try:
            btc_converter = self._get_btc_converter()
            return btc_converter.convert_to_btc(amount, currency)
        except Exception:
            # Fallback
            btc_price = self.get_btc_price(currency)
            if btc_price <= 0:
                raise ValueError("Invalid BTC price")
            return amount / btc_price
    
    def get_all_rates(self, base_currency: str) -> Dict[str, float]:
        """Get all exchange rates for a base currency.
        
        Args:
            base_currency: Base currency code
            
        Returns:
            Dictionary mapping currency codes to rates
        """
        base_currency = base_currency.upper()
        
        try:
            if FOREX_PYTHON_AVAILABLE:
                rates = self._get_currency_rates()
                return rates.get_rates(base_currency)
        except Exception:
            pass
        
        # Fallback to API
        try:
            url = (
                f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/"
                f"v1/currencies/{base_currency.lower()}.json"
            )
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            rates = data.get(base_currency.lower(), {})
            return {k.upper(): float(v) for k, v in rates.items()}
            
        except Exception:
            return {}
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get symbol for a currency code.
        
        Args:
            currency_code: Currency code (e.g., "USD")
            
        Returns:
            Currency symbol (e.g., "$")
        """
        return self.CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)
    
    def format_amount(self, amount: float, currency_code: str) -> str:
        """Format amount with currency symbol.
        
        Args:
            amount: Amount to format
            currency_code: Currency code
            
        Returns:
            Formatted string with symbol
        """
        symbol = self.get_currency_symbol(currency_code)
        return f"{symbol}{amount:,.2f}"
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currency codes.
        
        Returns:
            List of currency codes
        """
        # Return major currencies as a safe subset
        # In reality, the APIs support 150+ currencies
        return self.MAJOR_CURRENCIES.copy()
    
    def is_currency_supported(self, currency_code: str) -> bool:
        """Check if a currency is supported.
        
        Args:
            currency_code: Currency code to check
            
        Returns:
            True if supported
        """
        # Most currencies are supported, this is a basic check
        return len(currency_code) == 3 and currency_code.isalpha()
