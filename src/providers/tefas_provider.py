"""TEFAS (Turkey Electronic Fund Trading Platform) data provider.

This module provides integration with the Tefas Crawler library to fetch
Turkish mutual fund and ETF data.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from tefas import Crawler
    TEFAS_AVAILABLE = True
except ImportError:
    TEFAS_AVAILABLE = False
    Crawler = None

from ..data_providers import (
    DataProvider,
    PriceData,
    SearchResult,
    DATA_SOURCE_TEFAS,
    ASSET_TYPE_FUND,
    ASSET_TYPE_ETF,
)


class TefasProvider(DataProvider):
    """Provider for Turkish fund data from TEFAS.
    
    Supports:
    - Mutual funds (YAT)
    - Exchange Traded Funds (EMK, BYF)
    - Real-time price data
    - Fund portfolio composition
    
    Example:
        >>> provider = TefasProvider()
        >>> price_data = provider.fetch_price("YAC", kind="YAT")
        >>> print(f"Price: {price_data.price} TRY")
    """
    
    # Fund type codes used by TEFAS
    FUND_TYPE_MUTUAL = "YAT"  # Yatırım Fonu (Mutual Fund)
    FUND_TYPE_ETF_EQUITY = "EMK"  # Borsa Yatırım Fonu - Equity ETF
    FUND_TYPE_ETF_INDEX = "BYF"  # Borsa Yatırım Fonu - Index ETF
    
    FUND_TYPES = {
        FUND_TYPE_MUTUAL: "Mutual Fund",
        FUND_TYPE_ETF_EQUITY: "ETF - Equity",
        FUND_TYPE_ETF_INDEX: "ETF - Index",
    }
    
    def __init__(self, enabled: bool = True):
        """Initialize TEFAS provider.
        
        Args:
            enabled: Whether this provider is enabled
        """
        super().__init__(name=DATA_SOURCE_TEFAS, enabled=enabled)
        self._crawler: Optional[Any] = None
    
    def _get_crawler(self) -> Any:
        """Get or create TEFAS crawler instance."""
        if self._crawler is None:
            if not TEFAS_AVAILABLE:
                raise RuntimeError(
                    "Tefas Crawler library not installed. "
                    "Install with: uv add tefas-crawler"
                )
            self._crawler = Crawler()
        return self._crawler
    
    def is_available(self) -> bool:
        """Check if TEFAS provider is available."""
        return self.enabled and TEFAS_AVAILABLE
    
    def fetch_price(
        self, 
        symbol: str, 
        kind: str = FUND_TYPE_MUTUAL,
        **kwargs
    ) -> Optional[PriceData]:
        """Fetch current price for a Turkish fund.
        
        Args:
            symbol: Fund code (e.g., "YAC", "AAK", "IPB")
            kind: Fund type - "YAT" (mutual), "EMK" (ETF equity), "BYF" (ETF index)
            **kwargs: Additional options
            
        Returns:
            PriceData with current fund price or None if not found
            
        Example:
            >>> provider = TefasProvider()
            >>> data = provider.fetch_price("YAC", kind="YAT")
            >>> print(f"{data.symbol}: {data.price} {data.currency}")
        """
        if not self.is_available():
            return None
        
        try:
            crawler = self._get_crawler()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch fund data for today
            result = crawler.fetch(
                start=today,
                end=today,
                name=symbol.upper(),
                columns=["code", "date", "price", "title", "market_cap"],
                kind=kind,
            )
            
            if result.empty:
                return None
            
            row = result.iloc[0]
            
            return PriceData(
                symbol=symbol.upper(),
                price=float(row["price"]),
                currency="TRY",
                timestamp=datetime.now(),
                source=DATA_SOURCE_TEFAS,
                additional_info={
                    "title": row.get("title"),
                    "market_cap": float(row["market_cap"]) if pd.notna(row.get("market_cap")) else None,
                    "kind": kind,
                    "kind_description": self.FUND_TYPES.get(kind, "Unknown"),
                }
            )
            
        except Exception as e:
            # Log error but return None to allow fallback
            print(f"TEFAS fetch error for {symbol}: {e}")
            return None
    
    def search_symbols(
        self, 
        query: str, 
        kind: Optional[str] = None,
        limit: int = 20,
        **kwargs
    ) -> List[SearchResult]:
        """Search for Turkish funds by name or code.
        
        Args:
            query: Search string (fund name or code)
            kind: Filter by fund type (YAT, EMK, BYF), or None for all
            limit: Maximum results to return
            **kwargs: Additional search options
            
        Returns:
            List of matching SearchResult objects
            
        Example:
            >>> results = provider.search_symbols("yatırım", kind="YAT")
            >>> for r in results:
            ...     print(f"{r.symbol}: {r.name}")
        """
        if not self.is_available():
            return []
        
        try:
            crawler = self._get_crawler()
            today = datetime.now().strftime("%Y-%m-%d")
            
            results = []
            fund_types = [kind] if kind else list(self.FUND_TYPES.keys())
            
            for fund_type in fund_types:
                try:
                    # Fetch all funds of this type
                    all_funds = crawler.fetch(
                        start=today,
                        columns=["code", "title"],
                        kind=fund_type,
                    )
                    
                    if all_funds.empty:
                        continue
                    
                    # Filter by query (case-insensitive)
                    query_upper = query.upper()
                    matches = all_funds[
                        all_funds["code"].str.contains(query_upper, case=False, na=False) |
                        all_funds["title"].str.contains(query, case=False, na=False)
                    ]
                    
                    for _, row in matches.head(limit // len(fund_types)).iterrows():
                        results.append(SearchResult(
                            symbol=row["code"],
                            name=row["title"],
                            full_name=row["title"],
                            asset_type=ASSET_TYPE_FUND if fund_type == self.FUND_TYPE_MUTUAL else ASSET_TYPE_ETF,
                            source=DATA_SOURCE_TEFAS,
                            currency="TRY",
                            country="Turkey",
                        ))
                    
                except Exception as e:
                    continue
            
            return results[:limit]
            
        except Exception as e:
            print(f"TEFAS search error: {e}")
            return []
    
    def get_fund_portfolio(self, symbol: str, kind: str = FUND_TYPE_MUTUAL) -> Optional[Dict[str, Any]]:
        """Get detailed portfolio composition for a fund.
        
        Args:
            symbol: Fund code
            kind: Fund type
            
        Returns:
            Dictionary with portfolio breakdown or None
        """
        if not self.is_available():
            return None
        
        try:
            crawler = self._get_crawler()
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch all available columns including portfolio composition
            result = crawler.fetch(
                start=today,
                name=symbol.upper(),
                kind=kind,
            )
            
            if result.empty:
                return None
            
            row = result.iloc[0]
            
            # Extract portfolio composition percentages
            portfolio = {
                "symbol": symbol,
                "name": row.get("title"),
                "price": float(row["price"]),
                "currency": "TRY",
                "market_cap": float(row["market_cap"]) if pd.notna(row.get("market_cap")) else None,
            }
            
            # Add asset allocation if available
            allocation_fields = [
                "stock", "government_bond", "bank_bills", "repo",
                "foreign_currency_bills", "eurobonds", "precious_metals",
                "fund_participation_certificate", "real_estate_certificate",
            ]
            
            allocation = {}
            for field in allocation_fields:
                if field in row and pd.notna(row[field]):
                    allocation[field] = float(row[field])
            
            if allocation:
                portfolio["asset_allocation"] = allocation
            
            return portfolio
            
        except Exception as e:
            print(f"TEFAS portfolio fetch error for {symbol}: {e}")
            return None
    
    def get_supported_fund_types(self) -> Dict[str, str]:
        """Get list of supported fund types.
        
        Returns:
            Dictionary mapping fund type codes to descriptions
        """
        return self.FUND_TYPES.copy()


# Import pandas for type checking
try:
    import pandas as pd
except ImportError:
    pd = None
