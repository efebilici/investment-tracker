"""Investiny (Investing.com) data provider.

This module provides integration with the Investiny library to fetch
global market data including stocks, ETFs, funds, crypto, and more.

Note: This uses investiny as a more reliable alternative to investpy.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
    from investiny import search_assets, historical_data
    INVESTINY_AVAILABLE = True
except ImportError:
    INVESTINY_AVAILABLE = False
    search_assets = None
    historical_data = None

from ..data_providers import (
    DataProvider,
    PriceData,
    SearchResult,
    DATA_SOURCE_INVESTINY,
    ASSET_TYPE_STOCK,
    ASSET_TYPE_ETF,
    ASSET_TYPE_FUND,
    ASSET_TYPE_CRYPTO,
    ASSET_TYPE_BOND,
    ASSET_TYPE_COMMODITY,
    ASSET_TYPE_INDEX,
    ASSET_TYPE_CURRENCY,
)


class InvestinyProvider(DataProvider):
    """Provider for global market data via Investiny/Investing.com.
    
    Supports:
    - Stocks (global exchanges)
    - ETFs
    - Mutual funds
    - Cryptocurrencies
    - Bonds
    - Commodities
    - Indices
    - Currency pairs
    
    Example:
        >>> provider = InvestinyProvider()
        >>> price_data = provider.fetch_price("AAPL", asset_type="stock")
        >>> print(f"Apple: ${price_data.price}")
    """
    
    # Asset type mapping from our types to Investiny types
    ASSET_TYPE_MAP = {
        ASSET_TYPE_STOCK: "stock",
        ASSET_TYPE_ETF: "etf",
        ASSET_TYPE_FUND: "fund",
        ASSET_TYPE_CRYPTO: "crypto",
        ASSET_TYPE_BOND: "bond",
        ASSET_TYPE_COMMODITY: "commodity",
        ASSET_TYPE_INDEX: "index",
        ASSET_TYPE_CURRENCY: "fx",
    }
    
    # Reverse mapping
    INVESTINY_TO_ASSET_TYPE = {v: k for k, v in ASSET_TYPE_MAP.items()}
    
    def __init__(self, enabled: bool = True):
        """Initialize Investiny provider.
        
        Args:
            enabled: Whether this provider is enabled
        """
        super().__init__(name=DATA_SOURCE_INVESTINY, enabled=enabled)
    
    def is_available(self) -> bool:
        """Check if Investiny provider is available."""
        return self.enabled and INVESTINY_AVAILABLE
    
    def fetch_price(
        self, 
        symbol: str, 
        asset_type: str = ASSET_TYPE_STOCK,
        exchange: Optional[str] = None,
        **kwargs
    ) -> Optional[PriceData]:
        """Fetch current price for a global market symbol.
        
        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTC", "GLD")
            asset_type: Type of asset (stock, etf, fund, crypto, etc.)
            exchange: Optional exchange name for disambiguation
            **kwargs: Additional options
            
        Returns:
            PriceData with current price or None if not found
            
        Example:
            >>> provider = InvestinyProvider()
            >>> 
            >>> # Fetch Apple stock
            >>> data = provider.fetch_price("AAPL", asset_type="stock")
            >>> print(f"AAPL: ${data.price} {data.currency}")
            >>> 
            >>> # Fetch Bitcoin
            >>> data = provider.fetch_price("BTC", asset_type="crypto")
            >>> print(f"BTC: ${data.price}")
        """
        if not self.is_available():
            return None
        
        try:
            # Search for the asset
            investiny_type = self.ASSET_TYPE_MAP.get(asset_type, asset_type)
            search_results = search_assets(query=symbol, type=investiny_type)
            
            if not search_results:
                return None
            
            # Find the best match
            asset = None
            if len(search_results) == 1:
                asset = search_results[0]
            else:
                # Try to match exact symbol
                symbol_upper = symbol.upper()
                for result in search_results:
                    if result.get("ticker", "").upper() == symbol_upper:
                        asset = result
                        break
                # If no exact match, use first result
                if not asset:
                    asset = search_results[0]
            
            if not asset:
                return None
            
            # Get asset details
            asset_id = asset.get("ticker")
            if not asset_id:
                return None
            
            # Fetch historical data for recent price
            # Use last 7 days to get the most recent closing price
            today = datetime.now()
            from_date = (today - timedelta(days=7)).strftime("%m/%d/%Y")
            to_date = today.strftime("%m/%d/%Y")
            
            hist_data = historical_data(
                asset_id=asset_id,
                from_date=from_date,
                to_date=to_date,
            )
            
            if not hist_data:
                return None
            
            # Get the most recent closing price
            if isinstance(hist_data, dict) and "close" in hist_data:
                closes = hist_data["close"]
                if isinstance(closes, list) and len(closes) > 0:
                    latest_price = closes[-1]
                else:
                    latest_price = closes
            else:
                return None
            
            # Get currency
            currency = asset.get("currency", "USD")
            
            # Calculate 24h change if possible
            change_24h = None
            if isinstance(hist_data.get("close"), list) and len(hist_data["close"]) >= 2:
                closes = hist_data["close"]
                if len(closes) >= 2:
                    prev_close = closes[-2]
                    if prev_close > 0:
                        change_24h = ((latest_price - prev_close) / prev_close) * 100
            
            return PriceData(
                symbol=symbol.upper(),
                price=float(latest_price),
                currency=currency,
                timestamp=datetime.now(),
                source=DATA_SOURCE_INVESTINY,
                change_24h=change_24h,
                additional_info={
                    "name": asset.get("name"),
                    "full_name": asset.get("full_name"),
                    "exchange": asset.get("exchange"),
                    "asset_type": asset_type,
                    "investiny_id": asset_id,
                }
            )
            
        except Exception as e:
            print(f"Investiny fetch error for {symbol}: {e}")
            return None
    
    def search_symbols(
        self, 
        query: str, 
        asset_types: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs
    ) -> List[SearchResult]:
        """Search for global market symbols.
        
        Args:
            query: Search string (company name, symbol, etc.)
            asset_types: List of asset types to search (stock, etf, crypto, etc.)
            limit: Maximum results to return
            **kwargs: Additional search options
            
        Returns:
            List of matching SearchResult objects
            
        Example:
            >>> results = provider.search_symbols("apple", asset_types=["stock"])
            >>> for r in results:
            ...     print(f"{r.symbol}: {r.name} ({r.exchange})")
        """
        if not self.is_available():
            return []
        
        try:
            results = []
            
            # Default to all asset types if not specified
            types_to_search = asset_types
            if not types_to_search:
                types_to_search = list(self.ASSET_TYPE_MAP.keys())
            
            for asset_type in types_to_search:
                try:
                    investiny_type = self.ASSET_TYPE_MAP.get(asset_type, asset_type)
                    search_results = search_assets(
                        query=query, 
                        type=investiny_type
                    )
                    
                    if not search_results:
                        continue
                    
                    for asset in search_results[:limit // len(types_to_search) + 1]:
                        results.append(SearchResult(
                            symbol=asset.get("ticker", ""),
                            name=asset.get("name", ""),
                            full_name=asset.get("full_name"),
                            asset_type=self.INVESTINY_TO_ASSET_TYPE.get(
                                asset.get("type", ""), 
                                asset_type
                            ),
                            source=DATA_SOURCE_INVESTINY,
                            exchange=asset.get("exchange"),
                            currency=asset.get("currency", "USD"),
                            country=asset.get("country"),
                        ))
                        
                        if len(results) >= limit:
                            break
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    continue
            
            return results[:limit]
            
        except Exception as e:
            print(f"Investiny search error: {e}")
            return []
    
    def get_historical_data(
        self, 
        symbol: str, 
        asset_type: str = ASSET_TYPE_STOCK,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Fetch historical price data for a symbol.
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset
            from_date: Start date (MM/DD/YYYY format)
            to_date: End date (MM/DD/YYYY format)
            **kwargs: Additional options
            
        Returns:
            Dictionary with historical data or None
            
        Example:
            >>> data = provider.get_historical_data(
            ...     "AAPL",
            ...     from_date="01/01/2024",
            ...     to_date="12/31/2024"
            ... )
            >>> print(data["date"])
            >>> print(data["close"])
        """
        if not self.is_available():
            return None
        
        try:
            # Search for asset
            investiny_type = self.ASSET_TYPE_MAP.get(asset_type, asset_type)
            search_results = search_assets(query=symbol, type=investiny_type)
            
            if not search_results:
                return None
            
            asset = search_results[0]
            asset_id = asset.get("ticker")
            
            if not asset_id:
                return None
            
            # Use default date range if not specified
            if not from_date or not to_date:
                today = datetime.now()
                to_date = today.strftime("%m/%d/%Y")
                from_date = (today - timedelta(days=365)).strftime("%m/%d/%Y")
            
            hist_data = historical_data(
                asset_id=asset_id,
                from_date=from_date,
                to_date=to_date,
            )
            
            return hist_data
            
        except Exception as e:
            print(f"Investiny historical data error for {symbol}: {e}")
            return None
    
    def get_asset_info(self, symbol: str, asset_type: str = ASSET_TYPE_STOCK) -> Optional[Dict[str, Any]]:
        """Get detailed information about an asset.
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset
            
        Returns:
            Dictionary with asset information or None
        """
        if not self.is_available():
            return None
        
        try:
            investiny_type = self.ASSET_TYPE_MAP.get(asset_type, asset_type)
            search_results = search_assets(query=symbol, type=investiny_type)
            
            if not search_results:
                return None
            
            asset = search_results[0]
            asset_id = asset.get("ticker")
            
            if not asset_id:
                return None
            
            # Get additional info
            info = investing_info(asset_id=asset_id)
            
            return {
                "symbol": symbol,
                "name": asset.get("name"),
                "full_name": asset.get("full_name"),
                "type": asset_type,
                "exchange": asset.get("exchange"),
                "currency": asset.get("currency"),
                "country": asset.get("country"),
                "investiny_id": asset_id,
                "info": info,
            }
            
        except Exception as e:
            print(f"Investiny info error for {symbol}: {e}")
            return None
    
    def get_supported_asset_types(self) -> Dict[str, str]:
        """Get list of supported asset types.
        
        Returns:
            Dictionary mapping asset type codes to descriptions
        """
        return {
            ASSET_TYPE_STOCK: "Stocks",
            ASSET_TYPE_ETF: "ETFs",
            ASSET_TYPE_FUND: "Mutual Funds",
            ASSET_TYPE_CRYPTO: "Cryptocurrencies",
            ASSET_TYPE_BOND: "Bonds",
            ASSET_TYPE_COMMODITY: "Commodities",
            ASSET_TYPE_INDEX: "Indices",
            ASSET_TYPE_CURRENCY: "Currency Pairs",
        }
