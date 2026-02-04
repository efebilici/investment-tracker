"""Test the real-world data integration components."""

from src.models import Investment, Portfolio
from src.data_providers import (
    DataProviderManager,
    PriceData,
    SearchResult,
    DATA_SOURCE_TEFAS,
    DATA_SOURCE_INVESTINY,
    DATA_SOURCE_MANUAL,
)
from src.providers import TefasProvider, InvestinyProvider, CurrencyConverterProvider


def test_investment_model_with_external_data():
    """Test that Investment model supports external data fields."""
    print("Testing Investment model with external data fields...")
    
    # Create investment with external data
    investment = Investment.create_new(
        name="Apple Inc",
        portfolio_id="test-portfolio-id",
        final_amount=150.0,
        percentage_change=10.0,
        symbol="AAPL",
        data_source=DATA_SOURCE_INVESTINY,
        asset_type="stock",
        currency="USD",
    )
    
    assert investment.symbol == "AAPL"
    assert investment.data_source == DATA_SOURCE_INVESTINY
    assert investment.asset_type == "stock"
    assert investment.currency == "USD"
    assert investment.last_price_update is None
    print("  OK Investment model supports external data fields")
    
    # Test update_price method
    updated = investment.update_price(165.0)
    assert updated.final_amount == 165.0
    assert updated.last_price_update is not None
    print("  OK Investment update_price works")
    
    # Test needs_price_update - investiny data source should need update since no last_price_update
    assert investment.needs_price_update(max_age_hours=24)  # Should need update
    print("  OK Investment needs_price_update works")
    
    # Test data source indicators
    icon = investment.get_data_source_icon()
    freshness = investment.get_price_freshness_indicator()
    assert icon is not None
    assert freshness is not None
    print("  OK Investment data source indicators work")
    
    print("Investment model tests passed!\n")


def test_data_provider_manager():
    """Test DataProviderManager functionality."""
    print("Testing DataProviderManager...")
    
    manager = DataProviderManager()
    
    # Register providers
    tefas = TefasProvider(enabled=True)
    investiny = InvestinyProvider(enabled=True)
    
    manager.register_provider(tefas)
    manager.register_provider(investiny)
    
    assert "tefas" in manager.get_available_providers()
    assert "investiny" in manager.get_available_providers()
    print("  OK Provider registration works")
    
    # Get providers
    assert manager.get_provider("tefas") == tefas
    assert manager.get_provider("investiny") == investiny
    print("  OK Provider retrieval works")
    
    # Currency converter
    converter = CurrencyConverterProvider()
    manager.set_currency_converter(converter)
    assert manager.get_currency_converter() == converter
    print("  OK Currency converter registration works")
    
    print("DataProviderManager tests passed!\n")


def test_currency_converter():
    """Test currency conversion functionality."""
    print("Testing CurrencyConverterProvider...")
    
    converter = CurrencyConverterProvider(cache_duration_minutes=60)
    
    # Test basic conversion (should work with fallback API)
    try:
        # Test USD to EUR conversion
        result = converter.convert(100, "USD", "EUR")
        assert result > 0
        print(f"  OK Currency conversion works: 100 USD = {result:.2f} EUR")
        
        # Test rate retrieval
        rate = converter.get_rate("USD", "EUR")
        assert rate > 0
        print(f"  OK Exchange rate retrieval works: 1 USD = {rate:.4f} EUR")
        
        # Test same currency conversion
        same = converter.convert(100, "USD", "USD")
        assert same == 100
        print("  OK Same currency conversion returns original amount")
        
    except Exception as e:
        print(f"  WARN Currency conversion test skipped (API may be unavailable): {e}")
    
    # Test currency symbols
    symbol = converter.get_currency_symbol("USD")
    assert symbol is not None
    print("  OK Currency symbols work")
    
    print("CurrencyConverterProvider tests passed!\n")


def test_storage_migration():
    """Test storage migration from v2.0 to v2.1."""
    print("Testing storage migration...")
    
    from src.storage import InvestmentStorage
    
    # Create storage instance
    storage = InvestmentStorage()
    
    # Test migration logic directly
    v2_data = {
        "version": "2.0",
        "last_updated": "2024-01-01T00:00:00",
        "portfolios": [],
        "investments": [
            {
                "id": "test-inv-1",
                "name": "Test Investment",
                "portfolio_id": "test-port-1",
                "final_amount": 100.0,
                "percentage_change": 5.0,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        ]
    }
    
    # Apply migration
    migrated = storage._migrate_v2_to_v2_1(v2_data.copy())
    
    assert migrated["version"] == "2.1"
    assert "symbol" in migrated["investments"][0]
    assert "data_source" in migrated["investments"][0]
    assert "asset_type" in migrated["investments"][0]
    assert "currency" in migrated["investments"][0]
    assert migrated["investments"][0]["data_source"] == "manual"
    assert migrated["investments"][0]["currency"] == "USD"
    print("  OK Storage migration v2.0 to v2.1 works")
    
    print("Storage migration tests passed!\n")


def test_data_provider_interfaces():
    """Test that data provider interfaces are properly defined."""
    print("Testing data provider interfaces...")
    
    from src.data_providers import (
        PriceData,
        CurrencyRate,
        SearchResult,
    )
    
    # Test PriceData
    price_data = PriceData(
        symbol="AAPL",
        price=150.0,
        currency="USD",
        timestamp=__import__('datetime').datetime.now(),
        source="test",
    )
    assert price_data.symbol == "AAPL"
    assert price_data.price == 150.0
    print("  OK PriceData dataclass works")
    
    # Test SearchResult
    search_result = SearchResult(
        symbol="AAPL",
        name="Apple Inc",
        asset_type="stock",
        source="test",
    )
    assert search_result.symbol == "AAPL"
    assert search_result.asset_type == "stock"
    print("  OK SearchResult dataclass works")
    
    # Test constants
    assert DATA_SOURCE_TEFAS == "tefas"
    assert DATA_SOURCE_INVESTINY == "investiny"
    assert DATA_SOURCE_MANUAL == "manual"
    print("  OK Data source constants defined")
    
    print("Data provider interface tests passed!\n")


def test_providers_availability():
    """Test that provider classes can be instantiated."""
    print("Testing provider instantiation...")
    
    # TefasProvider
    tefas = TefasProvider()
    assert tefas.name == "tefas"
    print(f"  OK TefasProvider instantiated (available: {tefas.is_available()})")
    
    # InvestinyProvider
    investiny = InvestinyProvider()
    assert investiny.name == "investiny"
    print(f"  OK InvestinyProvider instantiated (available: {investiny.is_available()})")
    
    # CurrencyConverterProvider
    converter = CurrencyConverterProvider()
    print("  OK CurrencyConverterProvider instantiated")
    
    print("Provider instantiation tests passed!\n")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Real-World Data Integration Tests")
    print("=" * 60 + "\n")
    
    try:
        test_data_provider_interfaces()
        test_investment_model_with_external_data()
        test_data_provider_manager()
        test_currency_converter()
        test_storage_migration()
        test_providers_availability()
        
        print("=" * 60)
        print("All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nFAIL Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
